# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Agent read-only tools: correctness + sandboxing. Live Bedrock test is opt-in."""
import os

import pytest
from conftest import BM, IID, require_mirror   # tools take (benchmark, backend, instance, ...)

from backend import agent


def test_tools_read_only_and_scoped():
    require_mirror(BM, IID)
    # bundle file
    assert "Ansible" in agent._t_read_repo_file(BM, "nagini", IID, "README.md")
    assert "model.py" in agent._t_list_bundle(BM, "nagini", IID)
    assert "Ensures" in agent._t_read_bundle_file(BM, "nagini", IID, "model.py")
    # verdict / meta / issue
    assert agent._t_get_metadata(BM, "nagini", IID).strip().startswith("{")
    assert "problem_statement" in agent._t_get_issue(BM, "nagini", IID)
    # search
    assert IID in agent._t_search_instances(BM, "nagini", IID, "0ea40e09")


def test_tools_scoped_to_the_benchmark_row():
    """A Pro instance is invisible from the verified row's tools (and search only
    returns that row's ids) — the cell is the sandbox boundary."""
    from backend import data
    assert agent._t_read_bundle_file("verified", "nagini", IID, "model.py").startswith("(no such")
    assert agent._t_list_bundle("verified", "nagini", IID) == "(no bundle)"
    assert agent._t_search_instances("verified", "nagini", IID, "0ea40e09") == "(no matches)"
    vid = data.all_instance_ids("verified")[0]
    assert vid in agent._t_search_instances("verified", "nagini", vid, vid[:12])


def test_tool_path_guards():
    # traversal in any tool returns a safe sentinel, never escapes
    assert agent._t_read_repo_file(BM, "nagini", IID, "../../../etc/passwd").startswith("(no such")
    assert agent._t_read_bundle_file(BM, "nagini", IID,
                                     "../../pyproject.toml").startswith("(no such")


def test_run_tool_ignores_instance_override():
    # the model cannot silently switch instances OR cells via the tool input
    out = agent._run_tool("read_bundle_file",
                          {"instance_id": "some__other-1", "name": "model.py",
                           "benchmark": "verified", "bm": "verified"},
                          BM, "nagini", IID)
    assert "Ensures" in out  # still read the route's cell+instance, not the injected one


def test_tool_config_shape():
    cfg = agent._tool_config()
    names = {t["toolSpec"]["name"] for t in cfg["tools"]}
    assert {"read_bundle_file", "read_repo_file", "list_repo_tree", "get_verdict"} <= names


@pytest.mark.skipif(os.environ.get("VIZ_LIVE_AGENT") != "1",
                    reason="set VIZ_LIVE_AGENT=1 to run the live Bedrock call")
def test_live_agent():
    res = agent.ask(BM, "nagini", IID, "In one sentence, what does the model specify?")
    assert res["answer"] and len(res["tool_calls"]) >= 1


def test_multiturn_conversation(tmp_path, monkeypatch):
    """Multi-turn: a follow-up reloads the prior message history and the running
    transcript grows. Bedrock is mocked (no live call)."""
    from backend import paths, settings
    monkeypatch.setattr(paths, "REVIEW_DB", tmp_path / "convo.sqlite")
    monkeypatch.setattr(settings, "AGENT_ENABLED", True)

    seen_lengths = []

    class _FakeClient:
        def converse(self, **kw):
            # record how many messages were sent (proves history is replayed)
            seen_lengths.append(len(kw["messages"]))
            return {"stopReason": "end_turn",
                    "output": {"message": {"role": "assistant",
                                           "content": [{"text": "ok, answer."}]}}}

    class _FakeSession:
        def client(self, *a, **k):
            return _FakeClient()

    class _FakeBoto:
        # agent.ask builds a fresh boto3.Session() per call (creds refresh); mock it
        @staticmethod
        def Session(*a, **k):
            return _FakeSession()

    monkeypatch.setitem(__import__("sys").modules, "boto3", _FakeBoto)

    r1 = agent.ask(BM, "nagini", IID, "first question")
    assert r1["convo_id"] and len(r1["transcript"]) == 2  # user + agent
    r2 = agent.ask(BM, "nagini", IID, "follow-up", convo_id=r1["convo_id"])
    assert r2["convo_id"] == r1["convo_id"]               # same conversation
    assert len(r2["transcript"]) == 4                     # 2 prior + 2 new turns
    # the 2nd turn must have replayed the prior history (more messages than the 1st)
    assert seen_lengths[-1] > seen_lengths[0], seen_lengths


def test_conversation_scoped_to_instance(tmp_path, monkeypatch):
    """A convo_id from one instance cannot be continued under another instance."""
    from backend import paths, settings
    monkeypatch.setattr(paths, "REVIEW_DB", tmp_path / "scope.sqlite")
    monkeypatch.setattr(settings, "AGENT_ENABLED", True)

    class _FakeClient:
        def converse(self, **kw):
            return {"stopReason": "end_turn",
                    "output": {"message": {"role": "assistant", "content": [{"text": "x"}]}}}

    _sess = type("S", (), {"client": lambda self, *a, **k: _FakeClient()})
    monkeypatch.setitem(__import__("sys").modules, "boto3",
                        type("B", (), {"Session": staticmethod(lambda *a, **k: _sess())}))
    r1 = agent.ask(BM, "nagini", IID, "q", convo_id=None)
    prior, transcript = agent._load_convo(r1["convo_id"], BM, "nagini", "some__other-1")
    assert prior == [] and transcript == []  # not visible under a different instance
    prior, transcript = agent._load_convo(r1["convo_id"], BM, "velvet", IID)
    assert prior == [] and transcript == []  # nor under a different backend
    prior, transcript = agent._load_convo(r1["convo_id"], "verified", "nagini", IID)
    assert prior == [] and transcript == []  # nor under a different benchmark row


def test_builds_fresh_session_each_call(tmp_path, monkeypatch):
    """Regression: ask() must build a FRESH boto3.Session() per call so it re-reads
    ~/.aws/credentials (boto3's default session caches creds → a long-running server
    would keep using expired creds after a refresh)."""
    from backend import paths, settings
    monkeypatch.setattr(paths, "REVIEW_DB", tmp_path / "fresh.sqlite")
    monkeypatch.setattr(settings, "AGENT_ENABLED", True)
    sessions_built = []

    class _FakeClient:
        def converse(self, **kw):
            return {"stopReason": "end_turn",
                    "output": {"message": {"role": "assistant", "content": [{"text": "ok"}]}}}

    class _FakeSession:
        def __init__(self): sessions_built.append(1)
        def client(self, *a, **k): return _FakeClient()

    monkeypatch.setitem(__import__("sys").modules, "boto3",
                        type("B", (), {"Session": staticmethod(_FakeSession)}))
    agent.ask(BM, "nagini", IID, "q1")
    agent.ask(BM, "nagini", IID, "q2")
    # one fresh Session per ask() call (not a cached/global one)
    assert len(sessions_built) == 2, sessions_built


def test_retries_on_expired_token(tmp_path, monkeypatch):
    """Regression: if a call hits ExpiredTokenException mid-run, ask() rebuilds the
    session (re-reading creds) and retries once instead of surfacing the error."""
    from backend import paths, settings
    monkeypatch.setattr(paths, "REVIEW_DB", tmp_path / "retry.sqlite")
    monkeypatch.setattr(settings, "AGENT_ENABLED", True)

    class _Expired(Exception):
        response = {"Error": {"Code": "ExpiredTokenException"}}

    state = {"calls": 0, "sessions": 0}

    class _FakeClient:
        def converse(self, **kw):
            state["calls"] += 1
            if state["calls"] == 1:          # first attempt: expired
                raise _Expired()
            return {"stopReason": "end_turn",
                    "output": {"message": {"role": "assistant", "content": [{"text": "ok"}]}}}

    class _FakeSession:
        def __init__(self): state["sessions"] += 1
        def client(self, *a, **k): return _FakeClient()

    monkeypatch.setitem(__import__("sys").modules, "boto3",
                        type("B", (), {"Session": staticmethod(_FakeSession)}))
    r = agent.ask(BM, "nagini", IID, "q")
    assert r["answer"] == "ok"               # recovered, no error surfaced
    assert state["sessions"] >= 2            # rebuilt the session on expiry
    assert state["calls"] == 2               # retried exactly once
