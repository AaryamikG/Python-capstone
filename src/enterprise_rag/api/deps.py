from functools import lru_cache

from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.config import Settings
from enterprise_rag.core import build_manager_agent


@lru_cache
def get_settings() -> Settings:
    return Settings()


@lru_cache
def get_manager_agent() -> ManagerAgent:
    return build_manager_agent(get_settings())
