#!/usr/bin/env python3
"""G-CONF differential conformance for sphinx-doc__sphinx-8475 (nagini).

Shadow: the impl region of model.py, contracts stripped, copied verbatim
(`probe_outcome` + the pure helper `is_retryable` as a plain function).

Real callee: the modeled slice is the light-probe -> full-probe fallback block
inside `check_uri` (a nested closure in
`sphinx.builders.linkcheck.CheckExternalLinksBuilder.check_thread`, per
mapping.md section 1). A closure cannot be imported and called directly, and
its inputs are live network probes, so this script runs the REAL patched code
mechanically: it imports the patched module (PYTHONPATH=/testbed, gold patch
applied by the gate), locates the inner probe/fallback `try` statement in the
module's own source via `ast`, compiles that statement verbatim, and executes
it with the module's OWN global names in scope (so the `except` clause is
resolved exactly as the patched module resolves it) against a stub transport
whose probe calls succeed or raise real `requests.exceptions` instances
according to the model's outcome-kind encoding (mapping.md section 2):

    kind 0 -> the probe call returns and raise_for_status() does not raise
    kind 1 -> raise_for_status() raises a real HTTPError instance
    kind 2 -> the light probe call itself raises a real TooManyRedirects
              (this failure mode arises while the transport follows an
              unbounded relocation chain, i.e. from the call, not from the
              status check)
    kind 3 -> the probe call raises some other real RequestException subclass

The effective outcome KIND flowing out of the executed block (the surviving
response = kind 0, or the propagating exception classified by its real class)
is diffed against the shadow over the exhaustive input square plus >= 1e5
fuzzed Requires-satisfying inputs (kinds in {0..3}, kind-3 drawn from a pool
of distinct real exception classes). The script also cross-checks that the
full probe was consulted by the real code exactly when the shadow's dispatch
predicate says a retryable light-probe failure occurred.

Pinned seed: 108475. stdlib only. Exit 0 iff zero disagreements.
"""
import ast
import json
import random
import sys

import sphinx.builders.linkcheck as lc

from requests.exceptions import (
    HTTPError,
    TooManyRedirects,
    RequestException,
    ConnectionError,
    Timeout,
    ConnectTimeout,
    ReadTimeout,
    SSLError,
    ProxyError,
    ChunkedEncodingError,
    ContentDecodingError,
    InvalidURL,
)

SEED = 108475
N_FUZZ = 110_000

# Real exception classes producing a kind-3 (non-retryable, "other") failure.
KIND3_POOL = [
    RequestException, ConnectionError, Timeout, ConnectTimeout, ReadTimeout,
    SSLError, ProxyError, ChunkedEncodingError, ContentDecodingError,
    InvalidURL,
]


# ---------------------------------------------------------------------------
# Shadow: impl region of model.py, contracts stripped, copied verbatim.
# ---------------------------------------------------------------------------
def is_retryable(kind):
    return kind == 1 or kind == 2


def probe_outcome(head_kind, get_kind):
    # The full-probe outcome replaces the light-probe outcome EXACTLY when the
    # light probe failed with a retryable kind (is_retryable is false for a
    # success, kind 0); otherwise the light-probe outcome (a success, or a
    # non-retryable failure) stands.
    if is_retryable(head_kind):
        result = get_kind
    else:
        result = head_kind
    return result


# ---------------------------------------------------------------------------
# Real callee: extract and compile the inner probe/fallback try-statement
# from the patched module's source.
# ---------------------------------------------------------------------------
def _load_inner_try():
    with open(lc.__file__) as f:
        src = f.read()
    tree = ast.parse(src)
    for fn in ast.walk(tree):
        if isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)) \
                and fn.name == "check_uri":
            for node in ast.walk(fn):
                if not isinstance(node, ast.Try):
                    continue
                # The inner statement's own body issues the light probe
                # directly (an assignment whose value is a `.head(...)` call);
                # the enclosing outer try only contains it indirectly.
                for stmt in node.body:
                    if (isinstance(stmt, ast.Assign)
                            and isinstance(stmt.value, ast.Call)
                            and isinstance(stmt.value.func, ast.Attribute)
                            and stmt.value.func.attr == "head"):
                        mod = ast.Module(body=[node], type_ignores=[])
                        return compile(mod, lc.__file__, "exec")
    raise RuntimeError("could not locate the light-probe/full-probe fallback "
                       "try-statement inside check_uri in %s" % lc.__file__)


INNER_TRY = _load_inner_try()


class _Resp:
    """Stub probe response: raise_for_status raises the given real instance."""

    def __init__(self, exc):
        self._exc = exc

    def raise_for_status(self):
        if self._exc is not None:
            raise self._exc


class _Transport:
    """Stub of the module-local request helpers driven by outcome kinds.

    kind 1 surfaces from raise_for_status (a status-level error on a returned
    response); kinds 2 and 3 surface from the probe call itself (transport-
    level failures). All raised instances are REAL requests exception objects.
    """

    def __init__(self, head_kind, get_kind, k3_head, k3_get):
        self._head_kind = head_kind
        self._get_kind = get_kind
        self._k3_head = k3_head
        self._k3_get = k3_get
        self.get_consulted = False

    @staticmethod
    def _outcome(kind, k3_cls):
        if kind == 0:
            return _Resp(None)
        if kind == 1:
            return _Resp(HTTPError("status-level failure"))
        if kind == 2:
            # arises while the transport follows relocations, i.e. from the
            # probe call itself
            raise TooManyRedirects("relocation budget exhausted")
        if kind == 3:
            raise k3_cls("other transport failure")
        raise AssertionError(kind)

    def head(self, url, **kw):
        return self._outcome(self._head_kind, self._k3_head)

    def get(self, url, **kw):
        self.get_consulted = True
        return self._outcome(self._get_kind, self._k3_get)


class _App:
    class app:  # noqa: N801 - attribute shape only
        config = None


def real_probe(head_kind, get_kind, k3_head, k3_get):
    """Execute the REAL patched try-statement; return (effective_kind,
    full_probe_consulted)."""
    transport = _Transport(head_kind, get_kind, k3_head, k3_get)
    # Names resolve exactly as the patched module resolves them: the module's
    # own globals (which include the names its except clause references),
    # overlaid with the block's locals and the stub transport.
    ns = dict(lc.__dict__)
    ns.update({
        "requests": transport,
        "req_url": "https://example.invalid/resource",
        "auth_info": None,
        "kwargs": {},
        "self": _App(),
    })
    try:
        exec(INNER_TRY, ns)
    except HTTPError:
        return 1, transport.get_consulted
    except TooManyRedirects:
        return 2, transport.get_consulted
    except RequestException:
        return 3, transport.get_consulted
    # block completed: the surviving response passed its status check
    return 0, transport.get_consulted


# ---------------------------------------------------------------------------
# Differential driver
# ---------------------------------------------------------------------------
def check_one(head_kind, get_kind, k3_head, k3_get, tag):
    want = probe_outcome(head_kind, get_kind)
    got, get_consulted = real_probe(head_kind, get_kind, k3_head, k3_get)
    if got != want:
        print("DISAGREE %s: head_kind=%d get_kind=%d (k3_head=%s k3_get=%s) "
              "-> real=%d shadow=%d"
              % (tag, head_kind, get_kind, k3_head.__name__,
                 k3_get.__name__, got, want))
        return False
    expect_consulted = is_retryable(head_kind)
    if get_consulted != expect_consulted:
        print("DISAGREE %s (dispatch): head_kind=%d get_kind=%d -> real code "
              "consulted the full probe=%r, shadow dispatch predicate=%r"
              % (tag, head_kind, get_kind, get_consulted, expect_consulted))
        return False
    return True


def main():
    # sanity: the module under test resolves the widened failure set, and the
    # two retried classes are disjoint (matches axiom_check.py's obligations)
    assert not issubclass(TooManyRedirects, HTTPError)
    assert not issubclass(HTTPError, TooManyRedirects)

    checked = 0

    # exhaustive over the input square, with every kind-3 class pairing
    for head_kind in range(4):
        for get_kind in range(4):
            for k3_head in KIND3_POOL:
                for k3_get in KIND3_POOL:
                    if not check_one(head_kind, get_kind, k3_head, k3_get,
                                     "exhaustive"):
                        return 1
                    checked += 1

    # fuzz (pinned seed 108475)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        head_kind = rng.randint(0, 3)
        get_kind = rng.randint(0, 3)
        k3_head = rng.choice(KIND3_POOL)
        k3_get = rng.choice(KIND3_POOL)
        if not check_one(head_kind, get_kind, k3_head, k3_get, "fuzz"):
            return 1
        checked += 1

    print(json.dumps({"checked": checked, "disagreements": 0,
                      "seed": SEED,
                      "shadow": "model.py impl region (verbatim)",
                      "oracle": "patched check_uri inner try-statement, "
                                "compiled from module source and executed "
                                "with real requests exception classes"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
