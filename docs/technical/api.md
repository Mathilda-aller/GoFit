# GoFit business API

The frontend talks only to the business center. All routes are versioned under
`/api/v1`.

## Available now

```text
GET /api/v1/health
```

## Planned MVP areas

```text
POST /videos/import
GET  /videos/{video_id}/processing
GET  /action-cards/{card_id}

GET  /plans
POST /plans
PATCH /plans/{plan_id}
POST /plans/{plan_id}/items
DELETE /plans/{plan_id}/items/{item_id}

POST /plans/{plan_id}/sessions
GET  /sessions/{session_id}
PATCH /sessions/{session_id}/items/{item_id}
POST /sessions/{session_id}/feedback

GET  /recommendations
GET  /experiences
```

These routes should be added together with request and response examples when
the corresponding feature module is implemented. The API must keep the
distinction between a reusable training plan and a copied training session.
