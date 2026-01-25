# GitHub Actions Workflows

## Quick Overview

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| **CI Pipeline** | `ci.yml` | PR & Push to main | Run tests, lint code, build Docker images |
| **CD Pipeline** | `cd.yml` | Merge to main | Deploy to DigitalOcean production |

## CI Pipeline (`ci.yml`)

Runs automatically on every Pull Request and push to `main`/`develop`.

### Jobs:
1. **Backend Tests** - Jest tests with PostgreSQL & Redis
2. **ML Service Tests** - Pytest tests for Python service
3. **Mobile Tests** - Flutter analyze and tests
4. **Docker Build** - Verify images build correctly
5. **Security Scan** - Check for secrets and vulnerabilities

### Status Badges:
```markdown
![CI](https://github.com/Alujack/ai-anti-spam-shield-crm/actions/workflows/ci.yml/badge.svg)
```

## CD Pipeline (`cd.yml`)

Runs when code is merged to `main` branch.

### Steps:
1. Run CI tests (reuses ci.yml)
2. Build Docker images
3. Push to GitHub Container Registry (ghcr.io)
4. SSH to DigitalOcean server
5. Pull new images and restart services
6. Health check verification
7. Auto-rollback on failure

## Required Secrets

Configure in **Settings → Secrets → Actions**:

| Secret | Description |
|--------|-------------|
| `DROPLET_IP` | DigitalOcean server IP |
| `DROPLET_USER` | SSH username (root) |
| `DROPLET_SSH_KEY` | Private SSH key |
| `DOMAIN` | Your domain name |

## Manual Triggers

You can manually trigger the CD pipeline:
1. Go to **Actions** tab
2. Select **CD Pipeline**
3. Click **Run workflow**

## Monitoring

- View all runs: [Actions Tab](../../actions)
- View CI results: Check PR status checks
- View CD results: Check deployment logs

## Learn More

See full documentation: [docs/CICD-GUIDE.md](../../docs/CICD-GUIDE.md)
