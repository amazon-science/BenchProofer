#!/usr/bin/env python3
"""G-CONF differential conformance check for pytest-dev__pytest-5787 (nagini).

SHADOW: the impl regions of model.py (`serialize_chain`, `deserialize_chain`),
copied verbatim below with the contract calls (Requires/Ensures/Invariant/
Assert) stripped. The model's carrier is a plain Python List[int] already, so
no PSeq shim is needed; the @Pure helper `copy_link` copies over as a plain
function. There is no @ContractOnly callee in the bundle.

ORACLE: the REAL patched repo functions the model models per mapping.md
section 1 — `_pytest.reports._report_to_json` (the serialize step) and
`_pytest.reports._report_kwargs_from_json` (the deserialize step). The gate
applies patch.diff to /testbed before this script runs and the repo's package
is importable from the patched tree, so those module-level helpers exist and
are the patched code.

TYPE BRIDGE (mapping.md section 2): a chain is the `.chain` list of a real
`ExceptionChainRepr`, one link per list element; the model collapses each link
`(reprtraceback, reprcrash, description)` to one opaque `int` token, and
`len`/indexing/list order are preserved 1:1. The bridge realizes a token as a
real link whose crash message carries `str(token)` (a bijection on the tokens
used in a trial), so the abstraction function is
    proj(link) = int(crash message of the link)
applied per index. The comparison per trial:
  serialize:   shadow serialize_chain(tokens) vs
               [proj(entry) for entry in real transport form's chain list]
  deserialize: shadow deserialize_chain(transport tokens) vs
               [proj(link) for link in the real rebuilt chain]
plus light structural cross-checks (the rebuilt object is a chain-bearing
representation of the same length; per-index description survives; the input
chain object is not mutated — the contracts give the inputs only a read
fraction).

INPUT DOMAIN: both modeled functions Require a list of length >= 1 (a
single-stage failure is the degenerate length-1 chain), nothing else. Trials
draw chain lengths 1..8 (plus boundary lengths 1, 2, 3, 200) with arbitrary
int tokens, including repeats and negatives.

>= 1e5 Requires-satisfying inputs: 8 boundary + 52000 fuzz trials, each trial
exercising BOTH modeled functions (>= 104016 checked calls total).
Pinned fuzz seed: 5787.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import os
import random
import sys

SEED = 5787
N_FUZZ = 52_000


# --- shadow: model.py impl regions, contracts stripped -------------------------

def copy_link(link):
    # @Pure helper from the model: the content-preserving structural copy of
    # one link, the identity on its token.
    return link


def serialize_chain(chain):
    out = []  # type: list
    i = 0
    while i < len(chain):
        old = out  # type: list
        out = out + [chain[i]]
        i = i + 1
    return out


def deserialize_chain(transport):
    out = []  # type: list
    i = 0
    while i < len(transport):
        old = out  # type: list
        out = out + [transport[i]]
        i = i + 1
    return out


# --- oracle: the real patched repo functions -----------------------------------

def _import_real():
    # The repo lays its package out under <checkout>/src; make sure the
    # patched in-tree source wins over any stale ambient install.
    for base in ("/testbed", os.getcwd()):
        src = os.path.join(base, "src")
        if os.path.isdir(os.path.join(src, "_pytest")) and src not in sys.path:
            sys.path.insert(0, src)
    from _pytest.reports import _report_to_json, _report_kwargs_from_json
    from _pytest._code.code import (
        ExceptionChainRepr,
        ReprEntryNative,
        ReprFileLocation,
        ReprTraceback,
    )
    return (_report_to_json, _report_kwargs_from_json, ExceptionChainRepr,
            ReprEntryNative, ReprFileLocation, ReprTraceback)


class _FakeReport:
    """Minimal report stand-in: the serialize step reads report.__dict__ and
    report.longrepr; every other field here is a primitive that passes through
    the transport form unchanged."""

    def __init__(self, longrepr):
        self.nodeid = "conf::trial"
        self.location = ("conf.py", 1, "trial")
        self.keywords = {}
        self.outcome = "failed"
        self.when = "call"
        self.sections = []
        self.duration = 0.0
        self.user_properties = []
        self.result = None
        self.longrepr = longrepr


def _make_link(token, k, real):
    """One real chain link carrying `token`: (ReprTraceback, ReprFileLocation,
    description). The crash message carries the token (the bridge projection);
    the description carries it too, as an order cross-check."""
    (_ser, _des, _ECR, ReprEntryNative, ReprFileLocation, ReprTraceback) = real
    entry = ReprEntryNative(["line for %d" % token])
    tb = ReprTraceback(reprentries=[entry], extraline=None, style="long")
    crash = ReprFileLocation("conf.py", k + 1, str(token))
    description = "desc:%d" % token
    return (tb, crash, description)


def _proj_serialized(entry):
    """Token of one link of the transport form (a (tb_dict, crash_dict,
    description) triple of primitives)."""
    _tb, crash, _desc = entry
    return int(crash["message"])


def _proj_rebuilt(link):
    """Token of one link of the rebuilt chain (real repr objects)."""
    _tb, crash, _desc = link
    return int(crash.message)


def _check_trial(tokens, real):
    """Run serialize + deserialize on shadow and oracle over the same abstract
    input; return an error string on any observable disagreement, else None."""
    (_report_to_json, _report_kwargs_from_json, ExceptionChainRepr,
     _REN, _RFL, _RTB) = real

    # ---- shadow ----
    s_transport = serialize_chain(list(tokens))
    s_rebuilt = deserialize_chain(list(s_transport))

    # ---- oracle: serialize ----
    chain = [_make_link(t, k, real) for k, t in enumerate(tokens)]
    longrepr = ExceptionChainRepr(list(chain))
    report = _FakeReport(longrepr)
    n_before = len(longrepr.chain)
    data = _report_to_json(report)
    lr = data["longrepr"]
    if lr is None or lr.get("chain") is None:
        return ("serialize disagreement on tokens=%r:\n  shadow=%r\n"
                "  real transport form carries no chain list (longrepr=%r)"
                % (tokens, s_transport, type(lr).__name__))
    o_transport = [_proj_serialized(e) for e in lr["chain"]]
    if s_transport != o_transport:
        return ("serialize disagreement on tokens=%r:\n  shadow=%r\n  real  =%r"
                % (tokens, s_transport, o_transport))
    # per-index description cross-check (catches token-coincidence reorders)
    o_desc = [e[2] for e in lr["chain"]]
    e_desc = ["desc:%d" % t for t in tokens]
    if o_desc != e_desc:
        return ("serialize order disagreement on tokens=%r:\n"
                "  expected descriptions=%r\n  real descriptions=%r"
                % (tokens, e_desc, o_desc))
    # read-only input: the serialize step must not mutate the chain
    if len(longrepr.chain) != n_before:
        return ("serialize mutated its input chain on tokens=%r (len %d -> %d)"
                % (tokens, n_before, len(longrepr.chain)))

    # ---- oracle: deserialize (on the real transport form) ----
    kwargs = _report_kwargs_from_json(data)
    rebuilt = kwargs["longrepr"]
    rebuilt_chain = getattr(rebuilt, "chain", None)
    if not isinstance(rebuilt, ExceptionChainRepr) or rebuilt_chain is None:
        return ("deserialize disagreement on transport=%r:\n  shadow=%r\n"
                "  real rebuilt a chain-less representation (%s)"
                % (o_transport, s_rebuilt, type(rebuilt).__name__))
    o_rebuilt = [_proj_rebuilt(l) for l in rebuilt_chain]
    if s_rebuilt != o_rebuilt:
        return ("deserialize disagreement on transport=%r:\n"
                "  shadow=%r\n  real  =%r" % (o_transport, s_rebuilt, o_rebuilt))
    r_desc = [l[2] for l in rebuilt_chain]
    if r_desc != e_desc:
        return ("deserialize order disagreement on transport=%r:\n"
                "  expected descriptions=%r\n  real descriptions=%r"
                % (o_transport, e_desc, r_desc))
    # composed round trip: the rebuilt chain equals the original
    if o_rebuilt != list(tokens):
        return ("round-trip disagreement on tokens=%r: rebuilt=%r"
                % (tokens, o_rebuilt))
    return None


def main():
    real = _import_real()
    rng = random.Random(SEED)

    boundary = [
        [0],                      # degenerate single-stage chain
        [7],
        [-3],
        [1, 2],                   # the smallest genuinely multi-stage chain
        [5, 5],                   # repeated tokens
        [3, 2, 1],
        [0, -1, 0, -1, 0],
        list(range(200)),         # long chain
    ]
    n_checked = 0
    for tokens in boundary:
        err = _check_trial(tokens, real)
        if err:
            print("DISAGREEMENT (boundary): " + err)
            return 1
        n_checked += 2  # both modeled functions exercised

    for _ in range(N_FUZZ):
        n = rng.randint(1, 8)
        tokens = [rng.randint(-10**6, 10**6) for _ in range(n)]
        err = _check_trial(tokens, real)
        if err:
            print("DISAGREEMENT (fuzz): " + err)
            return 1
        n_checked += 2

    print("G-CONF OK: shadow == real patched repo (de)serializers on %d "
          "boundary + %d fuzz trials (%d modeled-function calls, seed %d): "
          "the transport form carries every link of the chain in order, and "
          "reconstruction reproduces every transport link in order, so the "
          "round trip is the identity on chains of any length >= 1."
          % (len(boundary), N_FUZZ, n_checked, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
