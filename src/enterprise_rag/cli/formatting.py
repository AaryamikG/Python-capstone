from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel

from enterprise_rag.schemas import ManagerAnswer

console = Console()

_TYPE_LABELS = {
    "qualitative": "Qualitative (document search)",
    "quantitative": "Quantitative (SQL)",
    "complex": "Complex (multi-agent)",
    "ambiguous": "Clarification needed",
}


def render_answer(result: ManagerAnswer) -> None:
    label = _TYPE_LABELS.get(result.type, result.type)
    body = result.answer

    if result.type == "qualitative" and result.citations:
        sources = "\n".join(f"- {c.format()}" for c in result.citations)
        body = f"{body}\n\n**Sources**\n{sources}"
    elif result.type == "quantitative" and result.sql:
        body = f"{body}\n\n**SQL**\n```sql\n{result.sql}\n```"

    console.print(
        Panel(
            Markdown(body),
            title=f"[bold]{label}[/bold]",
            subtitle=f"{result.execution_time_ms:.0f} ms",
            subtitle_align="right",
        )
    )


def render_error(message: str) -> None:
    console.print(f"[bold red]Error:[/bold red] {message}")
