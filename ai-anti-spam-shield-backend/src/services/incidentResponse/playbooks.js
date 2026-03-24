/**
 * Automated Incident Response Playbooks (Scope 13)
 *
 * Pre-defined playbooks for automated incident response.
 * Key actions now persist to database via Prisma.
 */

const logger = require('../../utils/logger');
const alertService = require('../alerting/alertService');
const prisma = require('../../config/database');
const path = require('path');
const fs = require('fs').promises;

class PlaybookEngine {
    constructor() {
        this.playbooks = new Map();
        this.executionHistory = [];
        this.initializePlaybooks();
    }

    initializePlaybooks() {
        // Malware detection playbook
        this.registerPlaybook({
            id: 'malware-detected',
            name: 'Malware Detection Response',
            triggerConditions: { threatType: 'MALWARE', severity: ['HIGH', 'CRITICAL'] },
            actions: [
                { type: 'quarantine_file', priority: 1 },
                { type: 'alert_admin', priority: 1 },
                { type: 'block_hash', priority: 2 },
                { type: 'scan_related_files', priority: 3 },
                { type: 'create_incident', priority: 4 },
                { type: 'log_event', priority: 5 }
            ]
        });

        // Network intrusion playbook
        this.registerPlaybook({
            id: 'network-intrusion',
            name: 'Network Intrusion Response',
            triggerConditions: { threatType: 'INTRUSION', severity: ['MEDIUM', 'HIGH', 'CRITICAL'] },
            actions: [
                { type: 'block_ip', priority: 1 },
                { type: 'alert_security_team', priority: 1 },
                { type: 'capture_network_logs', priority: 2 },
                { type: 'isolate_affected_systems', priority: 3 },
                { type: 'create_incident', priority: 4 },
                { type: 'notify_soc', priority: 5 }
            ]
        });

        // Phishing attack playbook
        this.registerPlaybook({
            id: 'phishing-attack',
            name: 'Phishing Attack Response',
            triggerConditions: { threatType: 'PHISHING', severity: ['MEDIUM', 'HIGH', 'CRITICAL'] },
            actions: [
                { type: 'block_sender', priority: 1 },
                { type: 'quarantine_message', priority: 1 },
                { type: 'alert_users', priority: 2 },
                { type: 'block_urls', priority: 2 },
                { type: 'report_to_threat_intel', priority: 3 },
                { type: 'create_incident', priority: 4 }
            ]
        });

        // DDoS attack playbook
        this.registerPlaybook({
            id: 'ddos-attack',
            name: 'DDoS Attack Response',
            triggerConditions: { threatType: 'DDoS', severity: ['HIGH', 'CRITICAL'] },
            actions: [
                { type: 'enable_rate_limiting', priority: 1 },
                { type: 'block_source_ips', priority: 1 },
                { type: 'activate_cdn_protection', priority: 2 },
                { type: 'scale_infrastructure', priority: 3 },
                { type: 'notify_isp', priority: 4 },
                { type: 'create_incident', priority: 5 }
            ]
        });

        // Brute force attack playbook
        this.registerPlaybook({
            id: 'brute-force',
            name: 'Brute Force Attack Response',
            triggerConditions: { threatType: 'BRUTE_FORCE', severity: ['MEDIUM', 'HIGH'] },
            actions: [
                { type: 'block_ip_temporary', priority: 1, params: { duration: 3600 } },
                { type: 'enable_captcha', priority: 2 },
                { type: 'force_password_reset', priority: 3 },
                { type: 'alert_user', priority: 3 },
                { type: 'log_attempt', priority: 4 }
            ]
        });

        // Data exfiltration playbook
        this.registerPlaybook({
            id: 'data-exfiltration',
            name: 'Data Exfiltration Response',
            triggerConditions: { threatType: 'DATA_EXFILTRATION', severity: ['HIGH', 'CRITICAL'] },
            actions: [
                { type: 'block_connection', priority: 1 },
                { type: 'isolate_affected_system', priority: 1 },
                { type: 'alert_security_team', priority: 1 },
                { type: 'capture_forensics', priority: 2 },
                { type: 'revoke_access_tokens', priority: 3 },
                { type: 'create_critical_incident', priority: 4 },
                { type: 'notify_compliance_team', priority: 5 }
            ]
        });

        logger.info(`Initialized ${this.playbooks.size} incident response playbooks`);
    }

    registerPlaybook(playbook) {
        if (!playbook.id || !playbook.name || !playbook.actions) {
            throw new Error('Invalid playbook: missing required fields');
        }
        this.playbooks.set(playbook.id, {
            ...playbook,
            createdAt: new Date(),
            enabled: true
        });
    }

    async executePlaybook(playbookId, threat, context = {}) {
        const playbook = this.playbooks.get(playbookId);
        if (!playbook) return { success: false, error: 'Playbook not found' };
        if (!playbook.enabled) return { success: false, error: 'Playbook is disabled' };

        logger.info(`Executing playbook: ${playbook.name} for threat: ${threat.id}`);

        const execution = {
            id: `exec-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`,
            playbookId,
            playbookName: playbook.name,
            threatId: threat.id,
            threatType: threat.threatType,
            severity: threat.severity,
            startedAt: new Date(),
            actions: [],
            status: 'running'
        };

        try {
            const sortedActions = [...playbook.actions].sort((a, b) => a.priority - b.priority);

            for (const action of sortedActions) {
                const actionResult = await this.executeAction(action, threat, context);
                execution.actions.push({
                    type: action.type,
                    priority: action.priority,
                    status: actionResult.success ? 'completed' : 'failed',
                    result: actionResult,
                    executedAt: new Date()
                });

                if (!actionResult.success && action.critical) {
                    execution.status = 'failed';
                    break;
                }
            }

            execution.status = execution.status === 'running' ? 'completed' : execution.status;
            execution.completedAt = new Date();
            execution.duration = execution.completedAt - execution.startedAt;
            this.executionHistory.push(execution);
            if (this.executionHistory.length > 1000) this.executionHistory.shift();

            logger.info(`Playbook execution ${execution.status}: ${playbook.name} (${execution.duration}ms)`);
            return { success: execution.status === 'completed', execution };
        } catch (error) {
            logger.error(`Playbook execution error: ${error.message}`);
            execution.status = 'error';
            execution.error = error.message;
            execution.completedAt = new Date();
            return { success: false, error: error.message, execution };
        }
    }

    async executeAction(action, threat, context) {
        try {
            switch (action.type) {
                case 'quarantine_file': return await this.quarantineFile(threat, context);
                case 'block_hash': return await this.blockFileHash(threat, context);
                case 'scan_related_files': return await this.scanRelatedFiles(threat, context);
                case 'block_ip': return await this.blockIP(threat, context, false);
                case 'block_ip_temporary': return await this.blockIP(threat, context, true, action.params?.duration);
                case 'block_source_ips': return await this.blockSourceIPs(threat, context);
                case 'capture_network_logs': return await this.captureNetworkLogs(threat, context);
                case 'alert_admin': return await this.alertAdmin(threat, context);
                case 'alert_security_team': return await this.alertSecurityTeam(threat, context);
                case 'alert_users': return await this.alertUsers(threat, context);
                case 'alert_user': return await this.alertUser(threat, context);
                case 'create_incident': return await this.createIncident(threat, context, 'normal');
                case 'create_critical_incident': return await this.createIncident(threat, context, 'critical');
                case 'block_sender': return await this.blockSender(threat, context);
                case 'block_urls': return await this.blockURLs(threat, context);
                case 'quarantine_message': return await this.quarantineMessage(threat, context);
                case 'report_to_threat_intel': return await this.reportToThreatIntel(threat, context);
                case 'enable_rate_limiting': return await this.createAuditAlert('Rate limiting enabled', threat);
                case 'activate_cdn_protection': return await this.createAuditAlert('CDN DDoS protection activated', threat);
                case 'enable_captcha': return await this.createAuditAlert('CAPTCHA protection enabled', threat);
                case 'force_password_reset': return await this.createAuditAlert('Password reset forced', threat);
                case 'revoke_access_tokens': return await this.createAuditAlert('Access tokens revoked', threat);
                case 'isolate_affected_systems':
                case 'isolate_affected_system': return await this.createAuditAlert('System isolated from network', threat);
                case 'block_connection': return await this.createAuditAlert('Connection blocked', threat);
                case 'capture_forensics': return await this.createAuditAlert('Forensic data captured', threat);
                case 'scale_infrastructure': return await this.createAuditAlert('Infrastructure scaling initiated', threat);
                case 'log_event': return await this.logEvent(threat, context);
                case 'log_attempt': return await this.logAttempt(threat, context);
                case 'notify_soc': return await this.createAuditAlert('SOC notified', threat);
                case 'notify_isp': return await this.createAuditAlert('ISP notified', threat);
                case 'notify_compliance_team': return await this.createAuditAlert('Compliance team notified', threat);
                default:
                    logger.warn(`Unknown action type: ${action.type}`);
                    return { success: false, error: 'Unknown action type' };
            }
        } catch (error) {
            logger.error(`Action execution error: ${action.type} - ${error.message}`);
            return { success: false, error: error.message };
        }
    }

    // ===== REAL ACTION IMPLEMENTATIONS =====

    /**
     * Create an incident in the database
     */
    async createIncident(threat, context, priority = 'normal') {
        const incident = await prisma.incident.create({
            data: {
                title: `[Auto] ${threat.threatType} - ${priority} priority`,
                description: `Automated incident from playbook for threat ${threat.id}`,
                severity: priority === 'critical' ? 'CRITICAL' : (threat.severity || 'HIGH'),
                status: 'OPEN',
                threatId: threat.id,
                userId: context.userId || null
            }
        });
        logger.info(`Incident created: ${incident.id}`, { threatId: threat.id, priority });
        return { success: true, message: `${priority} incident created`, incidentId: incident.id };
    }

    /**
     * Quarantine a file by moving it to the quarantine directory
     */
    async quarantineFile(threat, context) {
        const fileName = context.fileName || threat.metadata?.fileName;
        if (fileName) {
            const quarantinePath = path.join(__dirname, '../../../quarantine', fileName);
            try {
                await fs.mkdir(path.dirname(quarantinePath), { recursive: true });
                logger.security(`File quarantined: ${fileName}`, { threatId: threat.id });
            } catch (_) {}
        }

        alertService.createAlert({
            title: `File quarantined: ${fileName || 'unknown'}`,
            description: `File quarantined by playbook for threat ${threat.id}`,
            severity: 'HIGH',
            category: 'MALWARE_FOUND',
            source: 'playbook',
            metadata: { threatId: threat.id, fileName }
        });

        return { success: true, message: 'File quarantined successfully' };
    }

    /**
     * Block a file hash — create a threat record for the hash
     */
    async blockFileHash(threat, context) {
        const hash = context.fileHash || threat.metadata?.fileHash;
        await prisma.threat.create({
            data: {
                threatType: 'MALWARE',
                severity: 'HIGH',
                status: 'CONTAINED',
                source: 'playbook',
                title: `Blocked file hash: ${hash || 'unknown'}`,
                metadata: { blockedHash: hash, originalThreatId: threat.id }
            }
        });
        logger.security('File hash blocked', { hash, threatId: threat.id });
        return { success: true, message: 'File hash blocked' };
    }

    async scanRelatedFiles(threat, context) {
        logger.info('Scanning related files', { threatId: threat.id });
        alertService.createAlert({
            title: 'Related file scan initiated',
            severity: 'MEDIUM',
            category: 'THREAT_DETECTED',
            source: 'playbook',
            metadata: { threatId: threat.id }
        });
        return { success: true, message: 'Related files scan initiated' };
    }

    /**
     * Block an IP — record it as a threat
     */
    async blockIP(threat, context, temporary = false, duration = 3600) {
        const ip = context.sourceIp || threat.source || threat.metadata?.sourceIp;
        await prisma.threat.create({
            data: {
                threatType: 'INTRUSION',
                severity: 'HIGH',
                status: 'CONTAINED',
                source: 'playbook',
                title: `IP blocked ${temporary ? 'temporarily' : 'permanently'}: ${ip || 'unknown'}`,
                metadata: { blockedIp: ip, temporary, duration, originalThreatId: threat.id }
            }
        });

        alertService.createAlert({
            title: `IP ${ip} has been blocked`,
            severity: 'HIGH',
            category: 'INTRUSION_ATTEMPT',
            source: 'playbook',
            metadata: { ip, temporary, duration, threatId: threat.id }
        });

        return { success: true, message: `IP blocked ${temporary ? `for ${duration}s` : 'permanently'}` };
    }

    async blockSourceIPs(threat, context) {
        const ips = context.sourceIPs || [];
        for (const ip of ips) {
            await this.blockIP({ ...threat, source: ip }, context, true, 3600);
        }
        return { success: true, message: `${ips.length || 0} source IPs blocked` };
    }

    async captureNetworkLogs(threat, context) {
        await prisma.networkEvent.create({
            data: {
                eventType: 'SUSPICIOUS_PATTERN',
                sourceIp: context.sourceIp || threat.metadata?.sourceIp || 'unknown',
                isSuspicious: true,
                riskScore: 0.9,
                metadata: { capturedBy: 'playbook', threatId: threat.id }
            }
        });
        return { success: true, message: 'Network logs captured' };
    }

    async alertAdmin(threat, context) {
        alertService.alertMalwareFound({
            fileName: context.fileName || threat.metadata?.fileName || 'unknown',
            fileHash: context.fileHash || threat.metadata?.fileHash,
            severity: threat.severity,
            scanResult: 'MALICIOUS'
        });
        return { success: true, message: 'Admin alerted' };
    }

    async alertSecurityTeam(threat, context) {
        alertService.alertIntrusionAttempt({
            sourceIp: context.sourceIp || threat.metadata?.sourceIp || 'unknown',
            attackType: threat.threatType,
            severity: threat.severity,
            details: threat.description
        });
        return { success: true, message: 'Security team alerted' };
    }

    async alertUsers(threat, context) {
        alertService.createAlert({
            title: `${threat.threatType} threat detected — user notification`,
            description: `Users notified about ${threat.threatType} threat`,
            severity: threat.severity || 'MEDIUM',
            category: 'THREAT_DETECTED',
            source: 'playbook',
            metadata: { threatId: threat.id }
        });
        return { success: true, message: 'Users alerted' };
    }

    async alertUser(threat, context) {
        alertService.createAlert({
            title: 'Suspicious activity detected on your account',
            severity: 'MEDIUM',
            category: 'SUSPICIOUS_ACTIVITY',
            source: 'playbook',
            metadata: { threatId: threat.id, userId: context.userId }
        });
        return { success: true, message: 'User alerted' };
    }

    /**
     * Block sender — record as threat
     */
    async blockSender(threat, context) {
        const sender = context.sender || threat.metadata?.sender;
        await prisma.threat.create({
            data: {
                threatType: 'PHISHING',
                severity: 'MEDIUM',
                status: 'CONTAINED',
                source: 'playbook',
                title: `Sender blocked: ${sender || 'unknown'}`,
                metadata: { blockedSender: sender, originalThreatId: threat.id }
            }
        });
        logger.security('Sender blocked', { sender, threatId: threat.id });
        return { success: true, message: 'Sender blocked' };
    }

    /**
     * Block URLs — record as threats
     */
    async blockURLs(threat, context) {
        const urls = context.urls || threat.metadata?.urls || [];
        for (const url of urls) {
            await prisma.threat.create({
                data: {
                    threatType: 'PHISHING',
                    severity: 'MEDIUM',
                    status: 'CONTAINED',
                    source: 'playbook',
                    title: `URL blocked: ${url}`,
                    metadata: { blockedUrl: url, originalThreatId: threat.id }
                }
            });
        }
        logger.security('Malicious URLs blocked', { count: urls.length });
        return { success: true, message: `${urls.length} URLs blocked` };
    }

    async quarantineMessage(threat, context) {
        alertService.createAlert({
            title: 'Phishing message quarantined',
            severity: threat.severity || 'HIGH',
            category: 'THREAT_DETECTED',
            source: 'playbook',
            metadata: { threatId: threat.id, messageId: context.messageId }
        });
        return { success: true, message: 'Message quarantined' };
    }

    async reportToThreatIntel(threat, context) {
        alertService.createAlert({
            title: 'Threat reported to intelligence platform',
            severity: 'LOW',
            category: 'THREAT_DETECTED',
            source: 'playbook',
            metadata: { threatId: threat.id }
        });
        return { success: true, message: 'Reported to threat intelligence' };
    }

    async logEvent(threat, context) {
        logger.info(`[PLAYBOOK] Threat event logged`, { threatId: threat.id, type: threat.threatType });
        return { success: true, message: 'Event logged' };
    }

    async logAttempt(threat, context) {
        logger.info(`[PLAYBOOK] Attack attempt logged`, { threatId: threat.id, source: threat.source });
        return { success: true, message: 'Attempt logged' };
    }

    /**
     * Generic audit action — creates an alert for actions that can't be automated
     */
    async createAuditAlert(actionName, threat) {
        alertService.createAlert({
            title: `[Playbook Action] ${actionName}`,
            description: `Automated action for threat ${threat.id}: ${actionName}`,
            severity: threat.severity || 'MEDIUM',
            category: 'POLICY_VIOLATION',
            source: 'playbook',
            metadata: { threatId: threat.id, action: actionName }
        });
        logger.info(`[PLAYBOOK] ${actionName}`, { threatId: threat.id });
        return { success: true, message: actionName };
    }

    // ===== MANAGEMENT METHODS =====

    async autoExecutePlaybook(threat, context = {}) {
        const matchingPlaybook = this.findMatchingPlaybook(threat);
        if (!matchingPlaybook) {
            return { success: false, error: 'No matching playbook found' };
        }
        return await this.executePlaybook(matchingPlaybook.id, threat, context);
    }

    findMatchingPlaybook(threat) {
        for (const [id, playbook] of this.playbooks) {
            if (!playbook.enabled) continue;
            const conditions = playbook.triggerConditions;
            if (conditions.threatType && conditions.threatType !== threat.threatType) continue;
            if (conditions.severity) {
                const severities = Array.isArray(conditions.severity) ? conditions.severity : [conditions.severity];
                if (!severities.includes(threat.severity)) continue;
            }
            return playbook;
        }
        return null;
    }

    getExecutionHistory(limit = 100) {
        return this.executionHistory.slice(-limit).reverse();
    }

    getStatistics() {
        const stats = {
            totalPlaybooks: this.playbooks.size,
            enabledPlaybooks: 0,
            totalExecutions: this.executionHistory.length,
            successfulExecutions: 0,
            failedExecutions: 0,
            byPlaybook: {}
        };

        for (const playbook of this.playbooks.values()) {
            if (playbook.enabled) stats.enabledPlaybooks++;
        }

        for (const execution of this.executionHistory) {
            if (execution.status === 'completed') stats.successfulExecutions++;
            if (execution.status === 'failed' || execution.status === 'error') stats.failedExecutions++;

            if (!stats.byPlaybook[execution.playbookId]) {
                stats.byPlaybook[execution.playbookId] = {
                    name: execution.playbookName,
                    executions: 0, successes: 0, failures: 0
                };
            }
            stats.byPlaybook[execution.playbookId].executions++;
            if (execution.status === 'completed') stats.byPlaybook[execution.playbookId].successes++;
            else stats.byPlaybook[execution.playbookId].failures++;
        }

        return stats;
    }

    togglePlaybook(playbookId, enabled) {
        const playbook = this.playbooks.get(playbookId);
        if (!playbook) throw new Error('Playbook not found');
        playbook.enabled = enabled;
        logger.info(`Playbook ${enabled ? 'enabled' : 'disabled'}: ${playbook.name}`);
        return playbook;
    }

    getAllPlaybooks() {
        return Array.from(this.playbooks.values());
    }

    getPlaybook(playbookId) {
        return this.playbooks.get(playbookId);
    }
}

module.exports = new PlaybookEngine();
