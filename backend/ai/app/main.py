from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.routes.action_card_jobs import router as action_card_jobs_router
from app.api.routes.action_cards import router as action_cards_router
from app.api.routes.health import router as health_router
from app.api.routes.recommendations import router as recommendations_router
from app.api.routes.peer_experiences import router as peer_experiences_router
from app.errors import SkillError, request_id_from_body


app = FastAPI(
    title="GoFit AI Center",
    version="0.1.0",
    description="Evidence-grounded AI API for the GoFit hackathon MVP.",
)

app.include_router(health_router, prefix="/internal/v1")
app.include_router(action_cards_router, prefix="/internal/v1")
app.include_router(action_card_jobs_router, prefix="/internal/v1")
app.include_router(recommendations_router, prefix="/internal/v1")
app.include_router(peer_experiences_router, prefix="/internal/v1")


@app.exception_handler(SkillError)
async def handle_skill_error(_request: Request, error: SkillError) -> JSONResponse:
    not_found_codes = {"MOCK_FIXTURE_NOT_FOUND", "ACTION_CARD_JOB_NOT_FOUND"}
    status_code = 404 if error.code in not_found_codes else 422
    return JSONResponse(status_code=status_code, content=error.as_response())


@app.exception_handler(RequestValidationError)
async def handle_request_validation(
    request: Request,
    error: RequestValidationError,
) -> JSONResponse:
    body = error.body
    request_id = request_id_from_body(body)
    if request.url.path == "/internal/v1/recommendations/rank":
        skill_error = SkillError(
            "INVALID_RECOMMENDATION_REQUEST",
            "请求不符合动作推荐契约。",
            request_id=request_id,
        )
        return JSONResponse(status_code=422, content=skill_error.as_response())
    if request.url.path.startswith("/internal/v1/peer-experiences/"):
        skill_error = SkillError(
            "INVALID_PEER_EXPERIENCE_REQUEST",
            "请求不符合练友经验接口契约。",
            request_id=request_id,
        )
        return JSONResponse(status_code=422, content=skill_error.as_response())
    if request.url.path == "/internal/v1/action-card-jobs":
        skill_error = SkillError(
            "INVALID_VIDEO_WORKFLOW_REQUEST",
            "视频处理任务请求不符合约定格式。",
            request_id=request_id,
        )
        return JSONResponse(status_code=422, content=skill_error.as_response())

    locations = [tuple(str(part) for part in item.get("loc", ())) for item in error.errors()]
    messages = [str(item.get("msg", "")) for item in error.errors()]

    if any("endMs must be greater than startMs" in message for message in messages):
        skill_error = SkillError(
            "INVALID_EVIDENCE_RANGE",
            "证据或媒体候选的结束时间必须晚于开始时间。",
            request_id=request_id,
        )
    elif any(location[-1:] == ("evidence",) for location in locations):
        skill_error = SkillError(
            "NO_EVIDENCE",
            "缺少生成动作卡所需的来源证据。",
            request_id=request_id,
        )
    elif any("standardActionCandidates" in location for location in locations):
        skill_error = SkillError(
            "NO_STANDARD_ACTION_CANDIDATES",
            "缺少业务后端提供的标准动作候选。",
            request_id=request_id,
        )
    else:
        skill_error = SkillError(
            "OUTPUT_VALIDATION_FAILED",
            "请求不符合动作卡契约。",
            request_id=request_id,
        )

    return JSONResponse(status_code=422, content=skill_error.as_response())


@app.exception_handler(Exception)
async def handle_unexpected_error(request: Request, _error: Exception) -> JSONResponse:
    if request.url.path == "/internal/v1/recommendations/rank":
        skill_error = SkillError(
            "RECOMMENDATION_FAILED",
            "动作推荐失败，请继续手动选择动作。",
            request_id=request.headers.get("X-Request-Id"),
            retryable=False,
        )
        return JSONResponse(status_code=500, content=skill_error.as_response())
    if request.url.path.startswith("/internal/v1/peer-experiences/"):
        skill_error = SkillError(
            "PEER_EXPERIENCE_FAILED",
            "练友经验整理失败，暂时只展示原评论。",
            request_id=request.headers.get("X-Request-Id"),
            retryable=False,
        )
        return JSONResponse(status_code=500, content=skill_error.as_response())

    skill_error = SkillError(
        "OUTPUT_VALIDATION_FAILED",
        "动作卡生成失败，服务未返回内部异常细节。",
        request_id=request.headers.get("X-Request-Id"),
        retryable=False,
    )
    return JSONResponse(status_code=500, content=skill_error.as_response())
