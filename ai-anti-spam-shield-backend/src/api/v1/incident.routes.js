const express = require('express');
const router = express.Router();
const authMiddleware = require('../../middlewares/auth');
const prisma = require('../../config/database');

/**
 * Incident Management Routes
 */

// POST /api/v1/incidents
router.post('/', authMiddleware, async (req, res) => {
    try {
        const { title, description, severity, threatId } = req.body;

        if (!title || !severity) {
            return res.status(400).json({ success: false, message: 'Title and severity are required' });
        }

        const data = {
            title,
            description,
            severity,
            status: 'OPEN',
            userId: req.user?.id
        };
        if (threatId) data.threatId = threatId;

        const incident = await prisma.incident.create({ data });

        res.status(201).json({
            success: true,
            message: 'Incident created successfully',
            data: incident
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/incidents
router.get('/', authMiddleware, async (req, res) => {
    try {
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
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// GET /api/v1/incidents/:id
router.get('/:id', authMiddleware, async (req, res) => {
    try {
        const incident = await prisma.incident.findUnique({
            where: { id: req.params.id },
            include: { threat: true }
        });

        if (!incident) {
            return res.status(404).json({ success: false, message: 'Incident not found' });
        }

        res.status(200).json({ success: true, data: incident });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// PUT /api/v1/incidents/:id
router.put('/:id', authMiddleware, async (req, res) => {
    try {
        const { status, assignedTo, notes } = req.body;

        const incident = await prisma.incident.findUnique({ where: { id: req.params.id } });
        if (!incident) {
            return res.status(404).json({ success: false, message: 'Incident not found' });
        }

        const data = {};
        if (status) data.status = status;
        if (assignedTo) data.assignedTo = assignedTo;
        if (notes) data.notes = notes;
        if (status === 'RESOLVED') data.resolvedAt = new Date();

        const updatedIncident = await prisma.incident.update({
            where: { id: req.params.id },
            data
        });

        res.status(200).json({
            success: true,
            message: 'Incident updated successfully',
            data: updatedIncident
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

// POST /api/v1/incidents/:id/close
router.post('/:id/close', authMiddleware, async (req, res) => {
    try {
        const { resolution } = req.body;

        const incident = await prisma.incident.findUnique({ where: { id: req.params.id } });
        if (!incident) {
            return res.status(404).json({ success: false, message: 'Incident not found' });
        }

        const closedIncident = await prisma.incident.update({
            where: { id: req.params.id },
            data: {
                status: 'CLOSED',
                closedAt: new Date(),
                resolution
            }
        });

        res.status(200).json({
            success: true,
            message: 'Incident closed successfully',
            data: closedIncident
        });
    } catch (error) {
        res.status(500).json({ success: false, message: error.message });
    }
});

module.exports = router;
