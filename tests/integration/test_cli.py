"""Drives the CLI's REPL and single-shot modes with a fake ManagerAgent injected in place of
build_manager_agent, so no real Gemini call is ever made from these tests."""

import enterprise_rag.cli.main as cli_main
from enterprise_rag.schemas import ManagerAnswer


class FakeManagerAgent:
    def __init__(self):
        self.queries: list[str] = []

    def handle_query(self, query: str) -> ManagerAnswer:
        self.queries.append(query)
        return ManagerAnswer(type="qualitative", answer=f"answer to: {query}", agents_used=["qualitative"])


def test_single_shot_query_mode(monkeypatch, capsys):
    fake_manager = FakeManagerAgent()
    monkeypatch.setattr(cli_main, "build_manager_agent", lambda settings: fake_manager)

    exit_code = cli_main.main(["--query", "What is our security policy?"])

    assert exit_code == 0
    assert fake_manager.queries == ["What is our security policy?"]
    out = capsys.readouterr().out
    assert "answer to: What is our security policy?" in out


def test_repl_processes_queries_until_quit(monkeypatch, capsys):
    fake_manager = FakeManagerAgent()
    monkeypatch.setattr(cli_main, "build_manager_agent", lambda settings: fake_manager)

    inputs = iter(["first question", "second question", ":quit"])
    monkeypatch.setattr("builtins.input", lambda *args, **kwargs: next(inputs))

    exit_code = cli_main.main([])

    assert exit_code == 0
    assert fake_manager.queries == ["first question", "second question"]
    out = capsys.readouterr().out
    assert "answer to: first question" in out
    assert "answer to: second question" in out
    assert "Goodbye" in out


def test_repl_exits_cleanly_on_eof(monkeypatch, capsys):
    fake_manager = FakeManagerAgent()
    monkeypatch.setattr(cli_main, "build_manager_agent", lambda settings: fake_manager)

    def _raise_eof(*args, **kwargs):
        raise EOFError

    monkeypatch.setattr("builtins.input", _raise_eof)

    exit_code = cli_main.main([])

    assert exit_code == 0
    assert fake_manager.queries == []


def test_startup_failure_returns_nonzero_exit_code(monkeypatch, capsys):
    def _raise_value_error(settings):
        raise ValueError("GEMINI_API_KEY is not set.")

    monkeypatch.setattr(cli_main, "build_manager_agent", _raise_value_error)

    exit_code = cli_main.main(["--query", "anything"])

    assert exit_code == 1
    assert "GEMINI_API_KEY" in capsys.readouterr().out
