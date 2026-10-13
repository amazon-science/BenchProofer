# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

"""Read-only "ask-an-agent" loop with sandboxed tools.

A genuine tool-use loop (`bedrock-runtime.converse` with `toolConfig`): the model
can call read-only tools we implement — read a bundle file, read/list any repo
file at the instance's base_commit, fetch the verdict/gates, search instances —
and we execute them and feed results back until it answers. Every tool is
read-only and path-guarded to the benchmark's bundle/mirror roots (the same
guards as the rest of the site); the agent cannot write or escape. Every tool is
scoped to the current (benchmark, backend, instance) cell. Generous rate limit + a
hard per-turn iteration/token cap guard only against a runaway loop. Each turn is
logged to the comments DB's agent_log table.
"""
from __future__ import annotations

import json
import threading
import time
from contextlib import contextmanager

from . import comments, data, paths, repo, settings


class RateLimited(Exception):
    pass


# ----- rate limiter (token bucket over a sliding minute) -----
_lock = threading.Lock()
_calls: list[float] = []


def _rate_ok() -> bool:
    now = time.time()
    with _lock:
        cutoff = now - 60
        while _calls and _calls[0] < cutoff:
            _calls.pop(0)
        if len(_calls) >= settings.AGENT_RATE_PER_MIN:
            return False
        _calls.append(now)
        return True


# ----- read-only tools -----
def _t_read_bundle_file(bm: str, bk: str, instance_id: str, name: str) -> str:
    txt = data.read_bundle_file(bm, bk, instance_id, name)
    return txt if txt is not None else f"(no such bundle file: {name})"


def _t_list_bundle(bm: str, bk: str, instance_id: str) -> str:
    names = []
    d = paths.bundle_dir(bm, bk, instance_id)
    if d.is_dir():
        names += sorted(p.name for p in d.iterdir() if p.is_file())
    inst = paths.instance_dir(bm, instance_id)
    if inst.is_dir():
        names += sorted(p.name for p in inst.iterdir() if p.is_file())
    return "\n".join(names) if names else "(no bundle)"


def _t_read_repo_file(bm: str, bk: str, instance_id: str, path: str) -> str:
    txt = repo.file_at_base(bm, instance_id, path)
    return txt if txt is not None else f"(no such file at base_commit: {path})"


def _t_list_repo_tree(bm: str, bk: str, instance_id: str, subdir: str = "") -> str:
    entries = repo.tree_at_base(bm, instance_id, subdir)
    if entries is None:
        return f"(no such dir: {subdir})"
    return "\n".join(f"{'d' if e['type']=='tree' else 'f'} {e['path']}" for e in entries)


def _t_get_verdict(bm: str, bk: str, instance_id: str) -> str:
    notes = data.audit_notes(bm, bk, instance_id)
    if not notes:
        return "(no audit verdicts recorded)"
    import json as _json
    return _json.dumps(notes, indent=2)[:20000]


def _t_get_metadata(bm: str, bk: str, instance_id: str) -> str:
    return json.dumps(data.meta(bm, bk, instance_id), indent=2)[:20000]


def _t_get_issue(bm: str, bk: str, instance_id: str) -> str:
    row = data.dataset_row(bm, instance_id) or {}
    return (f"# problem_statement\n{row.get('problem_statement','')}\n\n"
            f"# hints_text\n{row.get('hints_text','')}")


def _t_search_instances(bm: str, bk: str, _instance_id: str, query: str = "") -> str:
    ql = (query or "").lower()
    hits = [i for i in data.all_instance_ids(bm) if ql in i.lower()][:50]
    return "\n".join(hits) if hits else "(no matches)"


TOOLS = {
    "read_bundle_file": (_t_read_bundle_file,
                         "Read a file from the instance's twin-artifact bundle: the "
                         "formal model and its prepatch twins (the backend decides "
                         "their names — use list_bundle), refinement.md, mapping.md, "
                         "axiom_check.py, patch.diff, meta.json.",
                         {"name": "the bundle filename"}),
    "list_bundle": (_t_list_bundle, "List the files in the instance's bundle.", {}),
    "read_repo_file": (_t_read_repo_file,
                       "Read any file in the project at the instance's base_commit "
                       "(read-only). Use to inspect the changed function, its callees, "
                       "or the F2P tests.",
                       {"path": "repo-relative path, e.g. pkg/utils/text.py"}),
    "list_repo_tree": (_t_list_repo_tree, "List one directory level of the repo at base_commit.",
                       {"subdir": "repo-relative dir (empty for root)"}),
    "get_verdict": (_t_get_verdict,
                    "Get the recorded agentic audit verdicts (G-EQ + panel roles) from "
                    "meta.json.", {}),
    "get_metadata": (_t_get_metadata,
                     "Get the instance meta.json (gates, modeled functions, axioms).", {}),
    "get_issue": (_t_get_issue, "Get the problem_statement and hints_text.", {}),
    "search_instances": (_t_search_instances, "Find instance ids matching a substring.",
                         {"query": "substring to search"}),
}


def _tool_config():
    specs = []
    for name, (_fn, desc, params) in TOOLS.items():
        props = {k: {"type": "string", "description": v} for k, v in params.items()}
        specs.append({"toolSpec": {
            "name": name, "description": desc,
            "inputSchema": {"json": {"type": "object", "properties": props,
                                     "required": list(props.keys())}},
        }})
    return {"tools": specs}


def _run_tool(name: str, inp: dict, bm: str, bk: str, instance_id: str) -> str:
    fn = TOOLS.get(name, (None,))[0]
    if fn is None:
        return f"(unknown tool: {name})"
    # all tools are scoped to the current cell; the model supplies only the rest
    kwargs = dict(inp or {})
    kwargs.pop("instance_id", None)  # never let the model pick a different instance silently
    kwargs.pop("bk", None)
    kwargs.pop("backend", None)
    kwargs.pop("bm", None)
    kwargs.pop("benchmark", None)
    try:
        out = fn(bm, bk, instance_id, **kwargs)
    except TypeError:
        try:
            out = fn(bm, bk, instance_id)
        except Exception as e:  # noqa: BLE001
            return f"(tool error: {e})"
    except Exception as e:  # noqa: BLE001
        return f"(tool error: {e})"
    return out[:60000] if isinstance(out, str) else str(out)


def _system(bm: str, bk: str) -> str:
    label = settings.BACKEND_LABELS.get(bk, bk)
    bm_label = settings.benchmark_label(bm)
    return (
    f"You are a meticulous formal-methods reviewer for the {bm_label} x "
    f"{bk} verified-twin benchmark ({label}). "
    "Each instance ships a formally verified model of a bug fix plus an equivalent real "
    "patch that resolves the instance's hidden tests. You answer the reviewer's question "
    "about ONE instance, using ONLY the read-only tools to gather evidence (read the model, "
    "the prepatch, the refinement map, the axioms, the real changed file at base_commit, the "
    "verdict, the issue). Be concrete and cite what you read (file + the relevant lines). "
    "Common questions: is the spec too weak (could a wrong impl satisfy it)? is an axiom an "
    "over-claim vs the real callee? does the model faithfully mirror the patch? is there "
    "leakage? Keep the answer focused and use Markdown. You CANNOT modify anything.")


def ask(bm: str, bk: str, instance_id: str, question: str,
        convo_id: int | None = None) -> dict:
    """Run one turn. If convo_id is given, continue that conversation (the prior
    Bedrock message history is reloaded and the new question appended); otherwise
    start a fresh conversation. Returns the answer for this turn plus the convo_id
    and the full running transcript so the UI can render the whole thread."""
    if not settings.AGENT_ENABLED:
        raise RuntimeError("agent disabled")
    if not _rate_ok():
        raise RateLimited()
    import boto3  # local import so the rest of the app loads even if boto3 absent
    # Build a FRESH session+client every call so the credential chain is re-read.
    # boto3's module-global default session caches credentials at first use, so a
    # long-running server would otherwise keep using expired ones after they are
    # refreshed. A new Session() re-resolves the chain.
    client = {"c": boto3.Session().client("bedrock-runtime", region_name=settings.BEDROCK_REGION)}

    def _converse(**kw):
        """Call converse; if the credentials expired mid-conversation, rebuild the
        session once and retry, so a refresh while the server runs self-heals."""
        try:
            return client["c"].converse(**kw)
        except Exception as e:  # noqa: BLE001
            code = getattr(e, "response", {}).get("Error", {}).get("Code", "") \
                if hasattr(e, "response") else ""
            if code in ("ExpiredTokenException", "ExpiredToken",
                        "UnrecognizedClientException", "InvalidSignatureException"):
                client["c"] = boto3.Session().client(
                    "bedrock-runtime", region_name=settings.BEDROCK_REGION)
                return client["c"].converse(**kw)
            raise

    prior, transcript = _load_convo(convo_id, bm, bk, instance_id)
    user_text = (f"Instance under review: {instance_id} "
                 f"(benchmark: {settings.benchmark_label(bm)}, backend: {bk})\n\n"
                 f"Reviewer question: {question}"
                 if not prior else question)
    messages = prior + [{"role": "user", "content": [{"text": user_text}]}]
    tool_calls = []
    answer = ""
    for _ in range(settings.AGENT_MAX_TOOL_ITERS):
        resp = _converse(
            modelId=settings.BEDROCK_MODEL,
            system=[{"text": _system(bm, bk)}],
            messages=messages,
            toolConfig=_tool_config(),
            inferenceConfig={"maxTokens": settings.AGENT_MAX_TOKENS},
        )
        out_msg = resp["output"]["message"]
        messages.append(out_msg)
        stop = resp.get("stopReason")
        if stop == "tool_use":
            tool_results = []
            for block in out_msg["content"]:
                if "toolUse" not in block:
                    continue
                tu = block["toolUse"]
                result = _run_tool(tu["name"], tu.get("input", {}), bm, bk, instance_id)
                tool_calls.append({"name": tu["name"],
                                   "input": json.dumps(tu.get("input", {}))[:120]})
                tool_results.append({"toolResult": {
                    "toolUseId": tu["toolUseId"],
                    "content": [{"text": result}],
                }})
            messages.append({"role": "user", "content": tool_results})
            continue
        # final answer
        answer = "".join(b.get("text", "") for b in out_msg["content"] if "text" in b)
        break
    else:
        answer = (answer or "") + "\n\n_(stopped: reached the tool-iteration cap)_"

    answer = answer or "(no answer produced)"
    transcript = transcript + [{"role": "user", "text": question},
                               {"role": "agent", "text": answer, "tool_calls": tool_calls}]
    convo_id = _save_convo(convo_id, bm, bk, instance_id, messages, transcript)
    _log(bm, bk, instance_id, question, answer, tool_calls)
    return {"answer": answer, "tool_calls": tool_calls,
            "convo_id": convo_id, "transcript": transcript}


# ----- conversation persistence (multi-turn) -----
@contextmanager
def _convo_db():
    """The shared review connection, with the conversation table ensured.

    Shared rather than its own: these tables live in the same file as the
    comments, and a second connection to a database on a network filesystem
    contends for its locks -- see `comments.db`, whose docstring records what
    that cost.
    """
    with comments.db() as c:
        c.execute("""CREATE TABLE IF NOT EXISTS agent_convo(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            benchmark TEXT NOT NULL DEFAULT 'pro',
            backend TEXT NOT NULL DEFAULT 'nagini', instance_id TEXT NOT NULL,
            messages TEXT NOT NULL, transcript TEXT NOT NULL DEFAULT '[]',
            created_at REAL, updated_at REAL)""")
        yield c


def _load_convo(convo_id: int | None, bm: str, bk: str,
                instance_id: str) -> tuple[list, list]:
    """Return (bedrock_messages, ui_transcript) for an existing convo, scoped to
    this instance; ([], []) for a new one. The instance scope prevents replaying a
    conversation under a different instance's context."""
    if not convo_id:
        return [], []
    try:
        with _convo_db() as c:
            row = c.execute("SELECT messages, transcript FROM agent_convo"
                            " WHERE id=? AND benchmark=? AND backend=? AND instance_id=?",
                            (convo_id, bm, bk, instance_id)).fetchone()
    except Exception:  # noqa: BLE001
        return [], []
    if not row:
        return [], []
    try:
        return json.loads(row[0]), json.loads(row[1])
    except (ValueError, TypeError):
        return [], []


def _save_convo(convo_id: int | None, bm: str, bk: str, instance_id: str,
                messages: list, transcript: list) -> int:
    now = time.time()
    msg_json, tr_json = json.dumps(messages), json.dumps(transcript)
    with _convo_db() as c:
        if convo_id:
            c.execute("UPDATE agent_convo SET messages=?, transcript=?, updated_at=? "
                      "WHERE id=? AND benchmark=? AND backend=? AND instance_id=?",
                      (msg_json, tr_json, now, convo_id, bm, bk, instance_id))
            return convo_id
        cur = c.execute("INSERT INTO agent_convo(benchmark,backend,instance_id,messages,"
                        "transcript,created_at,updated_at) VALUES(?,?,?,?,?,?,?)",
                        (bm, bk, instance_id, msg_json, tr_json, now, now))
        return int(cur.lastrowid or 0)


def _log(bm: str, bk: str, instance_id: str, question: str, answer: str,
         tool_calls: list) -> None:
    try:
        with comments.db() as c:
            c.execute("""CREATE TABLE IF NOT EXISTS agent_log(
                id INTEGER PRIMARY KEY AUTOINCREMENT, benchmark TEXT DEFAULT 'pro',
                backend TEXT, instance_id TEXT,
                question TEXT, answer TEXT, tool_calls TEXT, created_at REAL)""")
            c.execute("INSERT INTO agent_log(benchmark,backend,instance_id,question,answer,"
                      "tool_calls,created_at) VALUES(?,?,?,?,?,?,?)",
                      (bm, bk, instance_id, question, answer,
                       json.dumps(tool_calls), time.time()))
    except Exception:  # noqa: BLE001 — logging must never break the request
        pass
