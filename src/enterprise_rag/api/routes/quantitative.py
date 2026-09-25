import time

from fastapi import APIRouter, Depends

from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.api.deps import get_manager_agent
from enterprise_rag.api.schemas import QueryRequest, QueryResponse

router = APIRouter(tags=["agents"])


@router.post(
    "/agents/quantitative",
    response_model=QueryResponse,
    summary="Direct NL-to-SQL lookup, bypassing the manager's classifier",
)
def quantitative(request: QueryRequest, manager: ManagerAgent = Depends(get_manager_agent)) -> QueryResponse:
    start = time.perf_counter()
    result = manager.quantitative_agent.answer(request.query)
    return QueryResponse(
        type="quantitative",
        answer=result.answer,
        sql=result.sql,
        agents_used=["quantitative"],
        execution_time_ms=(time.perf_counter() - start) * 1000,
    )
