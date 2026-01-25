# CI/CD Pipeline Documentation

## AI Anti-Spam Shield - DevOps Guide

This document explains the Continuous Integration and Continuous Deployment (CI/CD) pipeline for the AI Anti-Spam Shield project. It's designed to help you understand DevOps concepts and how they're implemented.

---

## Table of Contents

1. [What is CI/CD?](#what-is-cicd)
2. [Architecture Overview](#architecture-overview)
3. [CI Pipeline (Testing)](#ci-pipeline-testing)
4. [CD Pipeline (Deployment)](#cd-pipeline-deployment)
5. [GitHub Actions Explained](#github-actions-explained)
6. [Setting Up Secrets](#setting-up-secrets)
7. [Docker & Container Registry](#docker--container-registry)
8. [Deployment Flow](#deployment-flow)
9. [Rollback Strategy](#rollback-strategy)
10. [Best Practices](#best-practices)
11. [Troubleshooting](#troubleshooting)
12. [Learning Resources](#learning-resources)

---

## What is CI/CD?

### Continuous Integration (CI)

**Definition:** CI is the practice of automatically testing code changes every time a developer pushes code or creates a pull request.

**Why it matters:**
- Catches bugs early before they reach production
- Ensures code quality standards are maintained
- Provides fast feedback to developers
- Prevents "integration hell" when merging code

**In our project:**
```
Developer pushes code → GitHub Actions runs tests → Pass/Fail feedback
```

### Continuous Deployment (CD)

**Definition:** CD automatically deploys tested code to production servers when it passes all checks.

**Why it matters:**
- Reduces manual deployment errors
- Enables faster release cycles
- Ensures consistent deployment process
- Allows for quick rollbacks if issues occur

**In our project:**
```
Code merged to main → Build Docker images → Push to registry → Deploy to DigitalOcean
```

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        DEVELOPER WORKFLOW                        │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│   1. Developer writes code locally                               │
│                    ↓                                             │
│   2. Developer creates Pull Request                              │
│                    ↓                                             │
│   ┌────────────────────────────────────────────────────────┐    │
│   │              CI PIPELINE (ci.yml)                       │    │
│   │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │    │
│   │  │ Backend  │ │    ML    │ │  Mobile  │ │ Security │  │    │
│   │  │  Tests   │ │  Tests   │ │  Tests   │ │   Scan   │  │    │
│   │  │  (Jest)  │ │ (Pytest) │ │(Flutter) │ │ (Trivy)  │  │    │
│   │  └──────────┘ └──────────┘ └──────────┘ └──────────┘  │    │
│   │                      ↓                                 │    │
│   │              Docker Build Test                         │    │
│   └────────────────────────────────────────────────────────┘    │
│                    ↓                                             │
│   3. Code Review & Approval                                      │
│                    ↓                                             │
│   4. Merge to main branch                                        │
│                    ↓                                             │
│   ┌────────────────────────────────────────────────────────┐    │
│   │              CD PIPELINE (cd.yml)                       │    │
│   │                                                         │    │
│   │   Build Images → Push to ghcr.io → Deploy to Server    │    │
│   │                                                         │    │
│   └────────────────────────────────────────────────────────┘    │
│                    ↓                                             │
│   5. Live on Production! 🚀                                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## CI Pipeline (Testing)

**File:** `.github/workflows/ci.yml`

### Trigger Events

```yaml
on:
  pull_request:
    branches: [main, develop]
  push:
    branches: [main, develop]
```

This means CI runs when:
- A Pull Request is created targeting `main` or `develop`
- Code is pushed directly to `main` or `develop`

### Jobs Overview

| Job | Purpose | Tools Used |
|-----|---------|------------|
| `backend-test` | Test Node.js API | Jest, PostgreSQL, Redis |
| `ml-service-test` | Test Python ML service | Pytest, ruff |
| `mobile-test` | Test Flutter app | flutter test, flutter analyze |
| `docker-build` | Verify Docker builds | Docker Buildx |
| `security-scan` | Check for vulnerabilities | Trufflehog, Trivy |

### Service Containers

CI uses "service containers" to provide databases for testing:

```yaml
services:
  postgres:
    image: postgres:15-alpine
    env:
      POSTGRES_USER: test
      POSTGRES_PASSWORD: test
      POSTGRES_DB: aishield_test
```

**Concept:** Service containers are like mini Docker Compose - they spin up temporary databases that exist only for the duration of the test.

### Caching

Caching speeds up CI by saving downloaded dependencies:

```yaml
- uses: actions/setup-node@v4
  with:
    cache: 'npm'
    cache-dependency-path: ai-anti-spam-shield-backend/package-lock.json
```

**Before caching:** ~3 minutes to install npm packages
**After caching:** ~10 seconds (uses cached packages)

---

## CD Pipeline (Deployment)

**File:** `.github/workflows/cd.yml`

### Trigger Events

```yaml
on:
  push:
    branches: [main]
  workflow_dispatch:  # Manual trigger
```

CD only runs when:
- Code is merged/pushed to `main`
- Manually triggered from GitHub UI

### Concurrency Control

```yaml
concurrency:
  group: deployment-${{ github.ref }}
  cancel-in-progress: false
```

**Purpose:** Prevents two deployments from running simultaneously, which could cause conflicts.

### Deployment Steps

1. **Build Docker Images**
   ```yaml
   - uses: docker/build-push-action@v5
     with:
       context: ./ai-anti-spam-shield-backend
       push: true
       tags: ghcr.io/user/repo/backend:latest
   ```

2. **SSH to Server**
   ```yaml
   - uses: appleboy/ssh-action@v1.0.3
     with:
       host: ${{ secrets.DROPLET_IP }}
       username: ${{ secrets.DROPLET_USER }}
       key: ${{ secrets.DROPLET_SSH_KEY }}
       script: |
         docker compose pull
         docker compose up -d
   ```

3. **Health Check**
   ```yaml
   - name: Health Check
     run: |
       curl https://your-domain.com/health
   ```

---

## GitHub Actions Explained

### Workflow Structure

```yaml
name: Pipeline Name        # Display name in GitHub UI

on:                        # When to run
  push:
    branches: [main]

env:                       # Global variables
  NODE_VERSION: '20'

jobs:                      # List of jobs
  job-name:
    runs-on: ubuntu-latest # VM type
    steps:                 # List of steps
      - name: Step name
        run: echo "Hello"
```

### Key Concepts

| Concept | Description | Example |
|---------|-------------|---------|
| **Workflow** | Automated process defined in YAML | `ci.yml` |
| **Job** | Group of steps that run on same VM | `backend-test` |
| **Step** | Individual task within a job | `npm test` |
| **Action** | Reusable workflow component | `actions/checkout@v4` |
| **Runner** | VM that executes the workflow | `ubuntu-latest` |
| **Secret** | Encrypted variable | `${{ secrets.API_KEY }}` |

### Expressions

```yaml
# Conditional execution
if: github.event_name == 'push'

# Access context
${{ github.actor }}           # Username who triggered
${{ github.sha }}             # Commit SHA
${{ secrets.MY_SECRET }}      # Secret value
${{ needs.job1.result }}      # Result of previous job
```

### Job Dependencies

```yaml
jobs:
  test:
    runs-on: ubuntu-latest
    # No dependencies, runs immediately

  build:
    needs: test              # Waits for 'test' to complete
    runs-on: ubuntu-latest

  deploy:
    needs: [test, build]     # Waits for both
    runs-on: ubuntu-latest
```

---

## Setting Up Secrets

### Required Secrets

Navigate to: **GitHub Repo** → **Settings** → **Secrets and variables** → **Actions**

| Secret | Description | How to Get |
|--------|-------------|------------|
| `DROPLET_IP` | Server IP address | DigitalOcean Dashboard |
| `DROPLET_USER` | SSH username | Usually `root` |
| `DROPLET_SSH_KEY` | Private SSH key | `cat ~/.ssh/id_rsa` |
| `DOMAIN` | Your domain | `aiscamshield.codes` |

### Creating SSH Key for Deployment

```bash
# On your local machine
ssh-keygen -t ed25519 -C "github-actions-deploy"

# Copy public key to server
ssh-copy-id -i ~/.ssh/id_ed25519.pub root@YOUR_SERVER_IP

# Copy private key (this goes in GitHub Secrets)
cat ~/.ssh/id_ed25519
```

### Security Best Practices

1. **Never commit secrets** - Always use GitHub Secrets
2. **Rotate keys regularly** - Change SSH keys every 6 months
3. **Use least privilege** - Create deployment-specific SSH keys
4. **Audit access** - Review who has access to secrets

---

## Docker & Container Registry

### GitHub Container Registry (ghcr.io)

**What:** Free container registry provided by GitHub
**Why:** Store Docker images close to your CI/CD pipeline

### Image Naming Convention

```
ghcr.io/USERNAME/REPO/SERVICE:TAG

Example:
ghcr.io/alujack/ai-anti-spam-shield-crm/backend:latest
ghcr.io/alujack/ai-anti-spam-shield-crm/backend:abc1234
```

### Docker Build Caching

```yaml
- uses: docker/build-push-action@v5
  with:
    cache-from: type=gha      # Load cache from GitHub Actions
    cache-to: type=gha,mode=max  # Save cache to GitHub Actions
```

**Benefit:** Subsequent builds are 5-10x faster because unchanged layers are cached.

### Multi-Stage Builds

Our Dockerfiles use multi-stage builds:

```dockerfile
# Stage 1: Build
FROM node:20-slim AS builder
COPY package*.json ./
RUN npm ci

# Stage 2: Run (smaller final image)
FROM node:20-slim AS runner
COPY --from=builder /app/node_modules ./node_modules
COPY . .
CMD ["node", "app.js"]
```

**Benefit:** Final image is smaller because build tools aren't included.

---

## Deployment Flow

### Step-by-Step Process

```
1. GitHub Actions starts CD workflow
           ↓
2. Build Docker images locally in GitHub runner
           ↓
3. Push images to ghcr.io (GitHub Container Registry)
           ↓
4. SSH into DigitalOcean server
           ↓
5. Pull new images from ghcr.io
           ↓
6. Stop old containers (docker compose down)
           ↓
7. Start new containers (docker compose up -d)
           ↓
8. Wait for services to be healthy
           ↓
9. Run health check (curl /health endpoint)
           ↓
10. Success! Or rollback if failed...
```

### Zero-Downtime Deployment (Future Enhancement)

For true zero-downtime, consider:

1. **Blue-Green Deployment**
   - Run two identical environments
   - Switch traffic between them

2. **Rolling Updates**
   - Update containers one at a time
   - Keep some instances running

---

## Rollback Strategy

### Automatic Rollback

If deployment fails, the CD pipeline automatically:

```yaml
- name: Rollback on Failure
  if: failure()
  script: |
    git checkout HEAD~1
    docker compose down
    docker compose up -d
```

### Manual Rollback

```bash
# SSH to server
ssh root@YOUR_SERVER_IP

# View available image tags
docker images | grep ai-shield

# Rollback to previous commit
cd /root/ai-anti-spam-shield
git log --oneline -5  # See recent commits
git checkout COMMIT_SHA
docker compose -f deploy/digitalocean/docker-compose.prod.yml up -d
```

### Image-Based Rollback

```bash
# Use specific image tag instead of :latest
docker compose pull ghcr.io/user/repo/backend:abc1234
docker compose up -d
```

---

## Best Practices

### 1. Branch Protection

Enable in **Settings** → **Branches** → **Add rule**:

- ✅ Require pull request reviews
- ✅ Require status checks to pass
- ✅ Require branches to be up to date

### 2. Meaningful Commit Messages

```
Good: "Add user authentication with JWT tokens"
Bad:  "fix stuff"
```

### 3. Small, Frequent Deployments

- Deploy often (daily or more)
- Smaller changes = easier to debug
- Faster feedback loops

### 4. Monitor Your Deployments

Check these after each deployment:
- [ ] Health endpoint returns 200
- [ ] Logs show no errors
- [ ] Key features work manually

### 5. Keep Secrets Secure

- Never commit `.env` files
- Rotate secrets periodically
- Use different secrets for staging/production

---

## Troubleshooting

### Common Issues

#### CI Pipeline Fails

| Problem | Solution |
|---------|----------|
| Tests timeout | Increase timeout in jest.config.js |
| Dependencies not found | Check cache-dependency-path |
| Docker build fails | Check Dockerfile syntax |

#### CD Pipeline Fails

| Problem | Solution |
|---------|----------|
| SSH connection refused | Verify DROPLET_SSH_KEY secret |
| Image pull fails | Check ghcr.io login |
| Health check fails | Wait longer, check server logs |

### Debugging Commands

```bash
# View GitHub Actions logs
# Go to: GitHub → Actions → Click on workflow run

# View server logs
ssh root@YOUR_SERVER_IP
docker compose logs -f backend

# Check container status
docker ps -a

# Check if port is open
curl -v http://localhost:3000/health
```

### Re-running Failed Workflows

1. Go to **GitHub** → **Actions**
2. Click on failed workflow
3. Click **Re-run failed jobs**

---

## Learning Resources

### DevOps Fundamentals

| Resource | Link |
|----------|------|
| GitHub Actions Docs | https://docs.github.com/en/actions |
| Docker Docs | https://docs.docker.com/ |
| DevOps Roadmap | https://roadmap.sh/devops |

### Video Tutorials

| Topic | Search Term |
|-------|-------------|
| GitHub Actions Basics | "GitHub Actions tutorial for beginners" |
| Docker for Beginners | "Docker crash course" |
| CI/CD Explained | "CI/CD pipeline explained" |

### Practice Projects

1. **GitHub Actions Starter** - Create a simple workflow that runs "Hello World"
2. **Docker Basics** - Containerize a simple Node.js app
3. **Deploy to Cloud** - Deploy a static site to any cloud provider

---

## Quick Reference

### Useful Commands

```bash
# Manually trigger CD workflow
gh workflow run cd.yml

# View workflow runs
gh run list

# View secrets (names only)
gh secret list

# Check deployment status
curl https://aiscamshield.codes/health
```

### File Locations

| File | Purpose |
|------|---------|
| `.github/workflows/ci.yml` | CI pipeline definition |
| `.github/workflows/cd.yml` | CD pipeline definition |
| `deploy/digitalocean/docker-compose.prod.yml` | Production compose file |
| `deploy/digitalocean/docker-compose.cicd.yml` | CI/CD compose file |

---

## Summary

You now have a complete CI/CD pipeline that:

1. **Automatically tests** code on every Pull Request
2. **Builds Docker images** and pushes to GitHub Container Registry
3. **Deploys to DigitalOcean** when code is merged to main
4. **Rolls back automatically** if deployment fails
5. **Scans for security issues** in dependencies

This is the foundation of modern DevOps practices. As you learn more, you can enhance it with:

- Staging environments
- Performance testing
- Monitoring and alerting
- Feature flags
- A/B testing

Happy learning! 🚀
