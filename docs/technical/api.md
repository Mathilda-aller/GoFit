# GoFit business API

The frontend talks only to the business center. All routes are versioned under
`/api/v1`.

## Available now

```text
GET /api/v1/health
GET /api/v1/media/videos/{file_name}

POST /api/v1/videos/import
GET  /api/v1/videos/{video_id}/processing

GET    /api/v1/action-cards
GET    /api/v1/action-cards/{card_id}
POST   /api/v1/action-cards/{card_id}/saved
DELETE /api/v1/action-cards/{card_id}/saved

GET    /api/v1/plans
POST   /api/v1/plans
GET    /api/v1/plans/{plan_id}
PATCH  /api/v1/plans/{plan_id}
POST   /api/v1/plans/{plan_id}/items
DELETE /api/v1/plans/{plan_id}/items/{item_id}

POST  /api/v1/plans/{plan_id}/sessions
GET   /api/v1/sessions/{session_id}
POST  /api/v1/sessions/{session_id}/end
PATCH /api/v1/sessions/{session_id}/items/{item_id}
POST  /api/v1/sessions/{session_id}/feedback

GET /api/v1/recommendations?planId={plan_id}
GET /api/v1/experiences?exerciseId={exercise_id}&problemTag={problem_tag}
GET /api/v1/me
```

The MVP uses `demo_user_001` as the current user. Request and response bodies
use camelCase.

## Key request examples

### Import video

```json
{
  "videoId": "video_lateral_raise",
  "assetFileName": "01-lateral-raise.mp4"
}
```

If a public action card already exists, the response includes its `cardId` and
returns `status: "COMPLETED"`.

### Create plan

```json
{
  "name": "今天练肩",
  "initialCardId": "lateral-raise"
}
```

### Rename or reorder plan

```json
{
  "name": "今天练肩",
  "status": "SAVED",
  "orderedItemIds": ["plan_item_1", "plan_item_2"]
}
```

### Add card to plan

```json
{
  "cardId": "front-raise"
}
```

The same action card cannot be added twice to the same plan. Repeated requests
return the unchanged plan.

### Submit training feedback

```json
{
  "itemId": "session_item_123",
  "feedbackType": "OTHER_FELT",
  "feltMuscles": ["手臂"]
}
```

Supported `feedbackType` values:

```text
TARGET_FELT
OTHER_FELT
NO_FEELING
NO_CLEAR_FEELING
TOO_HARD
TOO_DIFFICULT
DISCOMFORT
```

`OTHER_FELT + 手臂` maps to `ARMS_FELT_MORE`, `NO_FEELING` maps to
`NO_TARGET_FEELING`, and `DISCOMFORT` sets `shouldShowSafety: true`.

`GET /experiences` also accepts optional `currentVideoId` and `fromTraining`
query parameters so the frontend can preserve page context.

## Business rules

- A reusable training plan and a copied training session are separate records.
- Starting training copies the current plan items into `training_session_items`.
- Training feedback updates only the session item, not the original plan.
- One action card may appear in many plans, but only once per plan.
- Recommendations return at most 3 candidates and never add cards automatically.
- If the AI recommendation service is unavailable, business center returns a
  local deterministic fallback with `ruleVersion: "p0-v1-local"`.
- Peer experience responses include grouped summaries plus original comments
  and source videos. Safety-tagged feedback should use the safety branch instead
  of ordinary peer advice.
