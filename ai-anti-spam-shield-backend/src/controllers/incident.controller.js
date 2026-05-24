const asyncHandler = require('../utils/asyncHandler');
const ApiError = require('../utils/apiError');
const prisma = require('../config/database');

exports.createIncident = asyncHandler(async (req, res) => {
    const { title, description, severity, threatId } = req.body;

    if (!title || !severity) {
        throw new ApiError(400, 'title and severity are required');
    }

    const incident = await prisma.incident.create({
        data: {
            title,
            description,
            severity,
            threatId,
            userId: req.user?.id,
            status: 'OPEN'
        }
    });

    res.status(201).json({ success: true, data: incident });
});

exports.listIncidents = asyncHandler(async (req, res) => {
    const { status, severity, page = 1, limit = 20 } = req.query;

    const where = {};
    if (status) where.status = status;
    if (severity) where.severity = severity;

    const skip = (parseInt(page) - 1) * parseInt(limit);
    const [incidents, total] = await Promise.all([
        prisma.incident.findMany({
            where,
            skip,
            take: parseInt(limit),
            orderBy: { createdAt: 'desc' },
            include: { threat: true }
        }),
        prisma.incident.count({ where })
    ]);

    res.status(200).json({
        success: true,
        data: {
            incidents,
            pagination: {
                page: parseInt(page),
                limit: parseInt(limit),
                total,
                pages: Math.ceil(total / parseInt(limit))
            }
        }
    });
});

exports.getIncidentById = asyncHandler(async (req, res) => {
    const incident = await prisma.incident.findUnique({
        where: { id: req.params.id },
        include: { threat: true }
    });

    if (!incident) throw new ApiError(404, 'Incident not found');

    res.status(200).json({ success: true, data: incident });
});

exports.updateIncident = asyncHandler(async (req, res) => {
    const { status, assignedTo, notes, severity } = req.body;

    const existing = await prisma.incident.findUnique({ where: { id: req.params.id } });
    if (!existing) throw new ApiError(404, 'Incident not found');

    const data = {};
    if (status !== undefined) data.status = status;
    if (assignedTo !== undefined) data.assignedTo = assignedTo;
    if (notes !== undefined) data.notes = notes;
    if (severity !== undefined) data.severity = severity;
    if (status === 'RESOLVED') data.resolvedAt = new Date();

    const incident = await prisma.incident.update({
        where: { id: req.params.id },
        data
    });

    res.status(200).json({ success: true, data: incident });
});

exports.closeIncident = asyncHandler(async (req, res) => {
    const { resolution } = req.body;

    const existing = await prisma.incident.findUnique({ where: { id: req.params.id } });
    if (!existing) throw new ApiError(404, 'Incident not found');

    const incident = await prisma.incident.update({
        where: { id: req.params.id },
        data: {
            status: 'CLOSED',
            resolution,
            closedAt: new Date(),
            resolvedAt: existing.resolvedAt || new Date()
        }
    });

    res.status(200).json({ success: true, data: incident });
});
