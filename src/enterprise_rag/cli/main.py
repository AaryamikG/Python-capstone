import argparse
import sys

from enterprise_rag.agents.manager_agent import ManagerAgent
from enterprise_rag.cli.formatting import console, render_answer, render_error
from enterprise_rag.config import Settings
from enterprise_rag.core import build_manager_agent
from enterprise_rag.logging_config import configure_logging, get_logger

logger = get_logger(__name__)

BANNER = (
    "Enterprise Documentation Assistant\n"
    "Ask a question about company policy/process (qualitative) or data (quantitative).\n"
    "Type :quit or :exit to leave.\n"
)


def _run_query(manager: ManagerAgent, query: str) -> None:
    try:
        result = manager.handle_query(query)
        render_answer(result)
    except Exception as exc:  # noqa: BLE001 - CLI top-level guard, never crash the REPL
        logger.error("cli_query_failed", exc_info=True, extra={"event_data": {"query": query}})
        render_error(str(exc))


def _repl(manager: ManagerAgent) -> None:
    console.print(BANNER)
    while True:
        try:
            query = console.input("[bold cyan]> [/bold cyan]").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\nGoodbye.")
            return

        if not query:
            continue
        if query.lower() in {":quit", ":exit", "quit", "exit"}:
            console.print("Goodbye.")
            return

        _run_query(manager, query)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Enterprise Documentation Assistant CLI")
    parser.add_argument("--query", "-q", help="Run a single query and exit instead of starting the REPL.")
    args = parser.parse_args(argv)

    settings = Settings()
    configure_logging(settings.log_level)

    try:
        manager = build_manager_agent(settings)
    except ValueError as exc:
        render_error(f"Startup failed: {exc}")
        return 1

    if args.query:
        _run_query(manager, args.query)
    else:
        _repl(manager)
    return 0


if __name__ == "__main__":
    sys.exit(main())
