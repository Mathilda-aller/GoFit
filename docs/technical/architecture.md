# GoFit MVP architecture

## Scope

This is a local, interactive hackathon MVP. The architecture optimizes for a
clear ownership boundary and a runnable demo, not for production scale.

## Runtime shape

```text
Frontend
   |
   | REST
   v
Business center
   |-- SQLite
   |-- local storage/ media paths
   |-- demo user context
   |
   | internal contract
   v
AI center placeholder or AI implementation
```

## What is intentionally deferred

- public account and login flows
- cloud object storage and MinIO
- Redis, Celery, and distributed workers
- Kubernetes, autoscaling, and production monitoring
- arbitrary user video ingestion
- complete action knowledge base

## Core ownership rule

The AI center returns structured suggestions and analysis results. The business
center validates them, applies permissions and product rules, and decides what
is persisted or shown to the frontend.
