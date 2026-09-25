import time

from fastapi import APIRouter, Depends

from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.api.deps import get_manager_agent
from enterprise_rag.api.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["agents"])


@router.post(
    "/agents/qualitative",
    response_model=QueryResponse,
    summary="Direct qualitative RAG lookup, bypassing the manager's classifier",
)
def qualitative(request: QueryRequest, manager: ManagerAgent = Depends(get_manager_agent)) -> QueryResponse:
    start = time.perf_counter()
    result = manager.qualitative_agent.answer(request.query)
    return QueryResponse(
        type="qualitative",
        answer=result.answer,
        citations=[c.model_dump() for c in result.citations],
        agents_used=["qualitative"],
        execution_time_ms=(time.perf_counter() - start) * 1000,
    )
