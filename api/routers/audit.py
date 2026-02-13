"""Audit and analytics endpoints (dummy data for now)."""

from datetime import datetime, timezone

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/audit", tags=["audit"])


class UserCountResponse(BaseModel):
    total_users: int
    active_users_30d: int
    new_users_7d: int


class MostUsedLLMResponse(BaseModel):
    model: str
    request_count: int
    usage_percent: float


class MostUsedModuleResponse(BaseModel):
    module: str
    visit_count: int
    usage_percent: float


class ModuleTrafficStat(BaseModel):
    module: str
    visit_count: int
    share_percent: float


class ModuleTrafficResponse(BaseModel):
    total_visits: int
    items: list[ModuleTrafficStat]


class ModelRequestStat(BaseModel):
    model: str
    request_count: int
    share_percent: float


class ModelRequestsResponse(BaseModel):
    total_requests: int
    items: list[ModelRequestStat]


class TokensPerRequestResponse(BaseModel):
    avg_tokens_in: float
    avg_tokens_out: float


class AudioTranscriptionStatsResponse(BaseModel):
    audio_files_transcribed: int
    total_duration_seconds: int


class CaseWorkflowStatsResponse(BaseModel):
    started: int
    completed: int
    completion_rate_percent: float


class UsageStatsResponse(BaseModel):
    daily_active_users: int
    monthly_active_users: int
    avg_session_duration_seconds: int
    avg_requests_per_user: float
    success_rate_percent: float
    total_api_requests_24h: int


class AuditSummaryResponse(BaseModel):
    users: UserCountResponse
    most_used_llm: MostUsedLLMResponse
    model_requests: ModelRequestsResponse
    module_traffic: ModuleTrafficResponse
    tokens_per_request: TokensPerRequestResponse
    audio_transcription: AudioTranscriptionStatsResponse
    case_workflows: CaseWorkflowStatsResponse
    most_used_module: MostUsedModuleResponse
    usage: UsageStatsResponse
    generated_at: str


def _generated_at() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dummy_model_requests() -> ModelRequestsResponse:
    model_counts = [
        ("gpt-4.1-mini", 18347),
        ("gpt-4.1", 12990),
        ("claude-3-7-sonnet", 8311),
        ("gemini-2.0-flash", 5022),
    ]
    total = sum(count for _, count in model_counts)
    items = [
        ModelRequestStat(
            model=model,
            request_count=count,
            share_percent=round((count / total) * 100, 1) if total else 0.0,
        )
        for model, count in model_counts
    ]
    return ModelRequestsResponse(total_requests=total, items=items)


def _dummy_module_traffic() -> ModuleTrafficResponse:
    module_counts = [
        ("investigation-details", 7392),
        ("investigations-hub", 5220),
        ("document-collections", 3810),
        ("audit-metrics", 1684),
    ]
    total = sum(count for _, count in module_counts)
    items = [
        ModuleTrafficStat(
            module=module,
            visit_count=count,
            share_percent=round((count / total) * 100, 1) if total else 0.0,
        )
        for module, count in module_counts
    ]
    return ModuleTrafficResponse(total_visits=total, items=items)


def _dummy_tokens_per_request() -> TokensPerRequestResponse:
    return TokensPerRequestResponse(
        avg_tokens_in=1384.6,
        avg_tokens_out=612.4,
    )


def _dummy_audio_transcription_stats() -> AudioTranscriptionStatsResponse:
    return AudioTranscriptionStatsResponse(
        audio_files_transcribed=1846,
        total_duration_seconds=532440,
    )


def _dummy_case_workflow_stats() -> CaseWorkflowStatsResponse:
    started = 932
    completed = 704
    completion_rate_percent = round((completed / started) * 100, 1) if started else 0.0
    return CaseWorkflowStatsResponse(
        started=started,
        completed=completed,
        completion_rate_percent=completion_rate_percent,
    )


@router.get("/users/count", response_model=UserCountResponse)
async def get_user_count():
    """Return current user count stats (dummy values)."""
    return UserCountResponse(
        total_users=1242,
        active_users_30d=817,
        new_users_7d=54,
    )


@router.get("/llms/most-used", response_model=MostUsedLLMResponse)
async def get_most_used_llm():
    """Return most used LLM info (dummy values)."""
    model_requests = _dummy_model_requests()
    top_model = max(model_requests.items, key=lambda item: item.request_count)
    return MostUsedLLMResponse(
        model=top_model.model,
        request_count=top_model.request_count,
        usage_percent=top_model.share_percent,
    )


@router.get("/llms/requests", response_model=ModelRequestsResponse)
async def get_requests_by_model():
    """Return request volume and share by model (dummy values)."""
    return _dummy_model_requests()


@router.get("/modules/most-used", response_model=MostUsedModuleResponse)
async def get_most_used_module():
    """Return most used module/page info (dummy values)."""
    module_traffic = _dummy_module_traffic()
    top_module = max(module_traffic.items, key=lambda item: item.visit_count)
    return MostUsedModuleResponse(
        module=top_module.module,
        visit_count=top_module.visit_count,
        usage_percent=top_module.share_percent,
    )


@router.get("/modules/traffic", response_model=ModuleTrafficResponse)
async def get_module_traffic():
    """Return module visit volume and share (dummy values)."""
    return _dummy_module_traffic()


@router.get("/tokens/per-request", response_model=TokensPerRequestResponse)
async def get_tokens_per_request():
    """Return tokens in/out per request metrics (dummy values)."""
    return _dummy_tokens_per_request()


@router.get("/audio/transcriptions", response_model=AudioTranscriptionStatsResponse)
async def get_audio_transcription_stats():
    """Return audio transcription volume metrics (dummy values)."""
    return _dummy_audio_transcription_stats()


@router.get("/workflows/cases", response_model=CaseWorkflowStatsResponse)
async def get_case_workflow_stats():
    """Return case workflow started/completed metrics (dummy values)."""
    return _dummy_case_workflow_stats()


@router.get("/usage", response_model=UsageStatsResponse)
async def get_usage_stats():
    """Return general usage statistics (dummy values)."""
    return UsageStatsResponse(
        daily_active_users=291,
        monthly_active_users=817,
        avg_session_duration_seconds=742,
        avg_requests_per_user=16.8,
        success_rate_percent=99.2,
        total_api_requests_24h=12573,
    )


@router.get("/summary", response_model=AuditSummaryResponse)
async def get_audit_summary():
    """Return consolidated audit summary (dummy values)."""
    model_requests = _dummy_model_requests()
    top_model = max(model_requests.items, key=lambda item: item.request_count)
    module_traffic = _dummy_module_traffic()
    top_module = max(module_traffic.items, key=lambda item: item.visit_count)

    return AuditSummaryResponse(
        users=UserCountResponse(
            total_users=1242,
            active_users_30d=817,
            new_users_7d=54,
        ),
        most_used_llm=MostUsedLLMResponse(
            model=top_model.model,
            request_count=top_model.request_count,
            usage_percent=top_model.share_percent,
        ),
        model_requests=model_requests,
        module_traffic=module_traffic,
        tokens_per_request=_dummy_tokens_per_request(),
        audio_transcription=_dummy_audio_transcription_stats(),
        case_workflows=_dummy_case_workflow_stats(),
        most_used_module=MostUsedModuleResponse(
            module=top_module.module,
            visit_count=top_module.visit_count,
            usage_percent=top_module.share_percent,
        ),
        usage=UsageStatsResponse(
            daily_active_users=291,
            monthly_active_users=817,
            avg_session_duration_seconds=742,
            avg_requests_per_user=16.8,
            success_rate_percent=99.2,
            total_api_requests_24h=12573,
        ),
        generated_at=_generated_at(),
    )
