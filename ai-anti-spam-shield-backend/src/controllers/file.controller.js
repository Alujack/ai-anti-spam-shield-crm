const asyncHandler = require('../utils/asyncHandler');
const ApiError = require('../utils/apiError');
const path = require('path');
const fs = require('fs').promises;
const crypto = require('crypto');
const prisma = require('../config/database');
const threatIntelService = require('../services/threatIntelligence/service');
const alertService = require('../services/alerting/alertService');

// Suspicious file extensions / MIME types
const SUSPICIOUS_MIMES = [
    'application/x-executable', 'application/x-msdownload', 'application/x-msdos-program',
    'application/x-sh', 'application/x-bat', 'application/vnd.microsoft.portable-executable'
];
const SUSPICIOUS_EXTENSIONS = ['.exe', '.bat', '.cmd', '.scr', '.pif', '.com', '.vbs', '.js', '.wsf', '.ps1'];

/**
 * @desc    Scan uploaded file for malware
 * @route   POST /api/v1/files/scan
 */
exports.scanFile = asyncHandler(async (req, res) => {
    if (!req.file) {
        throw new ApiError(400, 'No file uploaded');
    }

    const { filename, path: filePath, size, mimetype } = req.file;

    try {
        const fileHash = await calculateFileHash(filePath);
        const ext = path.extname(filename).toLowerCase();

        // Try VirusTotal hash lookup
        let vtResult = null;
        let scanResult = 'CLEAN';
        let riskScore = 0;
        let scanDetails = { entropy: 0, suspiciousPatterns: [], fileSignature: mimetype };

        try {
            vtResult = await threatIntelService.checkFileHash(fileHash);
            if (vtResult && vtResult.checked !== false) {
                if (vtResult.isMalicious) {
                    scanResult = 'MALICIOUS';
                    riskScore = vtResult.detectionRate / 100;
                } else if (vtResult.suspicious > 0) {
                    scanResult = 'SUSPICIOUS';
                    riskScore = 0.5;
                }
            }
        } catch (err) {
            // VirusTotal not configured or failed — use heuristic fallback
        }

        // Heuristic fallback if VT didn't flag it
        if (scanResult === 'CLEAN') {
            if (SUSPICIOUS_MIMES.includes(mimetype) || SUSPICIOUS_EXTENSIONS.includes(ext)) {
                scanResult = 'SUSPICIOUS';
                riskScore = 0.4;
                scanDetails.suspiciousPatterns.push(`Suspicious file type: ${ext || mimetype}`);
            }
        }

        // Calculate file entropy
        try {
            const fileBuffer = await fs.readFile(filePath);
            scanDetails.entropy = calculateEntropy(fileBuffer);
            if (scanDetails.entropy > 7.5) {
                if (scanResult === 'CLEAN') scanResult = 'SUSPICIOUS';
                riskScore = Math.max(riskScore, 0.3);
                scanDetails.suspiciousPatterns.push('High entropy (possibly packed/encrypted)');
            }
        } catch (_) {}

        // Save to database
        const fileScan = await prisma.fileScan.create({
            data: {
                fileHash,
                fileName: filename,
                fileType: mimetype,
                fileSize: BigInt(size),
                scanResult,
                riskScore,
                scanDetails,
                virusTotalResult: vtResult || undefined,
                userId: req.user?.id
            }
        });

        // If malicious, create threat and alert
        if (scanResult === 'MALICIOUS') {
            await prisma.threat.create({
                data: {
                    threatType: 'MALWARE',
                    severity: 'HIGH',
                    status: 'DETECTED',
                    source: 'file_scanner',
                    confidenceScore: riskScore,
                    title: `Malware detected in file: ${filename}`,
                    description: `File ${filename} (hash: ${fileHash}) flagged as malicious`,
                    metadata: { fileHash, fileName: filename, vtResult },
                    fileScanId: fileScan.id
                }
            });

            alertService.alertMalwareFound({
                fileName: filename,
                fileHash,
                severity: 'HIGH',
                scanResult,
                virusTotalScore: vtResult?.detectionRate
            });

            // Move to quarantine
            const quarantinePath = path.join(__dirname, '../../quarantine', filename);
            await fs.mkdir(path.dirname(quarantinePath), { recursive: true });
            await fs.rename(filePath, quarantinePath);
        } else {
            // Clean up uploaded file
            await fs.unlink(filePath).catch(() => {});
        }

        // Convert BigInt for JSON serialization
        const responseData = {
            id: fileScan.id,
            fileHash,
            fileName: filename,
            fileType: mimetype,
            fileSize: size,
            scanResult,
            riskScore,
            scanDetails,
            virusTotalResult: vtResult,
            scannedAt: fileScan.scannedAt,
            status: scanResult === 'MALICIOUS' ? 'quarantined' : 'processed'
        };

        res.status(200).json({
            success: true,
            message: 'File scanned successfully',
            data: responseData
        });
    } catch (error) {
        try { await fs.unlink(filePath); } catch (_) {}
        throw error;
    }
});

/**
 * @desc    Get file scan result by ID
 * @route   GET /api/v1/files/scan/:id
 */
exports.getScanResult = asyncHandler(async (req, res) => {
    const fileScan = await prisma.fileScan.findUnique({
        where: { id: req.params.id },
        include: { threats: true }
    });

    if (!fileScan) {
        throw new ApiError(404, 'Scan result not found');
    }

    res.status(200).json({
        success: true,
        data: {
            ...fileScan,
            fileSize: Number(fileScan.fileSize)
        }
    });
});

/**
 * @desc    Quarantine a file
 * @route   POST /api/v1/files/quarantine
 */
exports.quarantineFile = asyncHandler(async (req, res) => {
    const { fileHash, reason } = req.body;

    if (!fileHash) {
        throw new ApiError(400, 'File hash is required');
    }

    const fileScan = await prisma.fileScan.findFirst({ where: { fileHash } });
    if (!fileScan) {
        throw new ApiError(404, 'File not found in scan records');
    }

    await prisma.fileScan.update({
        where: { id: fileScan.id },
        data: { scanResult: 'MALICIOUS', riskScore: 1.0 }
    });

    // Create a threat record for the quarantine action
    await prisma.threat.create({
        data: {
            threatType: 'MALWARE',
            severity: 'HIGH',
            status: 'CONTAINED',
            source: 'manual_quarantine',
            confidenceScore: 1.0,
            title: `File manually quarantined: ${fileScan.fileName}`,
            description: reason || 'Manual quarantine',
            metadata: { fileHash, fileName: fileScan.fileName },
            fileScanId: fileScan.id
        }
    });

    res.status(200).json({
        success: true,
        message: 'File quarantined successfully',
        data: {
            fileHash,
            fileName: fileScan.fileName,
            quarantinedAt: new Date(),
            reason: reason || 'Manual quarantine'
        }
    });
});

/**
 * @desc    Get file scan statistics
 * @route   GET /api/v1/files/statistics
 */
exports.getFileStatistics = asyncHandler(async (req, res) => {
    const [totalScans, byResult, recentScans] = await Promise.all([
        prisma.fileScan.count(),
        prisma.fileScan.groupBy({ by: ['scanResult'], _count: { scanResult: true } }),
        prisma.fileScan.findMany({
            orderBy: { scannedAt: 'desc' },
            take: 10,
            select: { id: true, fileName: true, scanResult: true, riskScore: true, scannedAt: true }
        })
    ]);

    const resultMap = { CLEAN: 0, SUSPICIOUS: 0, MALICIOUS: 0 };
    byResult.forEach(r => { resultMap[r.scanResult] = r._count.scanResult; });

    res.status(200).json({
        success: true,
        data: {
            totalScans,
            cleanFiles: resultMap.CLEAN,
            suspiciousFiles: resultMap.SUSPICIOUS,
            maliciousFiles: resultMap.MALICIOUS,
            quarantinedFiles: resultMap.MALICIOUS,
            recentScans
        }
    });
});

// Helper: calculate file hash
async function calculateFileHash(filePath) {
    const fileBuffer = await fs.readFile(filePath);
    const hashSum = crypto.createHash('sha256');
    hashSum.update(fileBuffer);
    return hashSum.digest('hex');
}

// Helper: calculate Shannon entropy
function calculateEntropy(buffer) {
    const freq = new Array(256).fill(0);
    for (let i = 0; i < buffer.length; i++) {
        freq[buffer[i]]++;
    }
    let entropy = 0;
    for (let i = 0; i < 256; i++) {
        if (freq[i] > 0) {
            const p = freq[i] / buffer.length;
            entropy -= p * Math.log2(p);
        }
    }
    return Math.round(entropy * 100) / 100;
}
