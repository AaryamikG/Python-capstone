from fastapi import APIRouter, Depends

from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.api.deps import get_manager_agent
from enterprise_rag.api.schemas import QueryRequest, QueryResponse
from enterprise_rag.schemas import ClassificationResult

router = APIRouter(tags=["manager"])


@router.post("/query", response_model=QueryResponse, summary="Full manager pipeline: classify, route, answer")
def query(request: QueryRequest, manager: ManagerAgent = Depends(get_manager_agent)) -> QueryResponse:
    result = manager.handle_query(request.query)
    return QueryResponse(**result.model_dump())


@router.post(
    "/agents/manager/classify",
    response_model=ClassificationResult,
    summary="Classify a query without routing to any sub-agent (debugging aid)",
)
def classify(request: QueryRequest, manager: ManagerAgent = Depends(get_manager_agent)) -> ClassificationResult:
    return manager.classify(request.query)
