# Cursor Development Plan for AI-Driven Anti-Scam Project

## Overview

This document outlines a complete development roadmap for building the AI-driven anti-scam project using Cursor. It covers backend, AI service, mobile app, Docker, integration, and deployment.

---

## 1. Project Structure

```
ai-anti-scam/
│
├── backend/
├── ai-service/
├── mobile/
└── docs/
```

---

## 2. Backend Development Plan (Node.js + Express + Prisma)

### Steps

1. Initialize backend
2. Configure Prisma + PostgreSQL
3. Create folder structure (controllers, services, routes)
4. Implement authentication endpoints
5. Build message scanning endpoint
6. Integrate AI service
7. Add history + reporting APIs
8. Add logging & error handling
9. Write tests

---

## 3. AI Model Service (FastAPI + Transformers)

### Steps

1. Prepare dataset
2. Train text classification model
3. Save and export model
4. Build FastAPI inference service
5. Add explainability features
6. Test prediction API

---

## 4. Mobile App Development (Flutter)

### Steps

1. Create project structure
2. Add packages (dio, riverpod, shared_preferences)
3. Implement screens:

   * Login
   * Register
   * Home
   * Result
   * History
   * Settings
4. Implement API service
5. Handle state management
6. Add UI polish & animations

---

## 5. Integration (App → Backend → AI)

### Steps

1. Connect mobile to backend auth
2. Connect mobile to scan-text endpoint
3. Backend forwards to AI service
4. Save scan history
5. Display history in mobile app

---

## 6. Dockerization

### Components

* backend
* ai-service
* postgres
* adminer

### Steps

1. Create Dockerfile for backend
2. Create Dockerfile for AI service
3. Generate docker-compose.yml
4. Add environment variables
5. Test multi-service startup

---

## 7. Deployment

### Options

* Railway
* Render
* DigitalOcean

### Steps

1. Deploy AI service
2. Deploy backend API
3. Connect database
4. Build release APK for demo

---

## 8. Final Presentation

### Required Sections

1. Problem statement
2. AI model overview
3. Architecture diagram
4. Screenshots
5. Workflow demo
6. Dataset explanation
7. Accuracy metrics
8. Future improvements

---

## 9. Development Milestones

### Week 1

* Backend skeleton
* AI dataset preparation

### Week 2

* AI model training
* Inference service complete

### Week 3

* Backend integration
* Mobile UI skeleton

### Week 4

* Full integration

### Week 5

* Docker + Deployment

### Week 6

* Final polish + Slides

---

## 10. Done

You now have the full Cursor plan for smooth development.
