# P2 adversarial audit — pytest-dev__pytest-5787

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.1 / 3.2 (POSITIVE CONTROL): round-tripping a chained (len>=2) failure
# through _to_json/_from_json yields an ExceptionChainRepr with the same number
# of links, not collapsed to a single exception.
import copy
import _pytest._code
from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport


def make_chain():
    try:
        try:
            raise ValueError("inner-cause")
        except ValueError as e:
            raise RuntimeError("outer-effect") from e
    except Exception:
        return _pytest._code.ExceptionInfo.from_current().getrepr(style="long")


lr = make_chain()
assert isinstance(lr, ExceptionChainRepr), type(lr)
n_orig = len(lr.chain)
print("original chain links:", n_orig)
assert n_orig >= 2, "need a genuine multi-stage chain for the discriminating test"

rep = TestReport(
    nodeid="test_mod.py::test_x",
    location=("test_mod.py", 1, "test_x"),
    keywords={},
    outcome="failed",
    longrepr=lr,
    when="call",
    sections=[],
)
d = rep._to_json()
rep2 = TestReport._from_json(copy.deepcopy(d))
lr2 = rep2.longrepr
print("reconstructed longrepr type:", type(lr2).__name__)
ok = isinstance(lr2, ExceptionChainRepr) and len(lr2.chain) == n_orig
print("reconstructed chain links:", getattr(lr2, "chain", None) and len(lr2.chain))
if not ok:
    print("FAIL: chain collapsed or wrong type")
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.1 / 1.2: _to_json on a chained report records an ordered collection
# ('chain') with the same count/order and, per link, traceback + crash + the
# description string (or None for the final link).
import _pytest._code
from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport


def make_chain():
    try:
        try:
            raise ValueError("inner-cause")
        except ValueError as e:
            raise RuntimeError("outer-effect") from e
    except Exception:
        return _pytest._code.ExceptionInfo.from_current().getrepr(style="long")


lr = make_chain()
assert isinstance(lr, ExceptionChainRepr)
orig = lr.chain
print("orig link count:", len(orig))

rep = TestReport(
    nodeid="t.py::x", location=("t.py", 1, "x"), keywords={},
    outcome="failed", longrepr=lr, when="call", sections=[],
)
d = rep._to_json()
chain = d["longrepr"].get("chain")
print("serialized chain is list:", isinstance(chain, list))
if not isinstance(chain, list) or len(chain) != len(orig):
    print("FAIL: chain not recorded with matching count")
    raise SystemExit(1)

# per-link structure: (traceback, crash, description)
orig_descs = [c[2] for c in orig]
ser_descs = []
for link in chain:
    assert isinstance(link, (list, tuple)) and len(link) == 3, link
    tb, crash, desc = link
    # traceback record must contain reprentries; crash must be dict-like
    assert isinstance(tb, dict) and "reprentries" in tb, tb.keys() if isinstance(tb, dict) else tb
    assert isinstance(crash, dict), type(crash)
    ser_descs.append(desc)
print("orig descriptions:", orig_descs)
print("serialized descriptions:", ser_descs)
if ser_descs != orig_descs:
    print("FAIL: descriptions not preserved in order")
    raise SystemExit(1)
# final link description must be absent (None)
if ser_descs[-1] is not None:
    print("FAIL: final link should have no description")
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.2: after round-trip of a >=2 chain, each intermediate/originating
# exception's traceback text AND each link's description are recoverable from
# the reconstructed representation (chain not collapsed, content preserved).
import copy
import _pytest._code
from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport


def make_chain():
    try:
        try:
            raise ValueError("INNER_MARKER_TEXT")
        except ValueError as e:
            raise RuntimeError("OUTER_MARKER_TEXT") from e
    except Exception:
        return _pytest._code.ExceptionInfo.from_current().getrepr(style="long")


lr = make_chain()
assert isinstance(lr, ExceptionChainRepr)

# collect original traceback text per link
def link_text(link):
    tb = link[0]
    out = []
    for e in tb.reprentries:
        out.extend(getattr(e, "lines", []) or [])
    return "\n".join(str(x) for x in out)

orig_texts = [link_text(l) for l in lr.chain]
orig_descs = [l[2] for l in lr.chain]

rep = TestReport(
    nodeid="t.py::x", location=("t.py", 1, "x"), keywords={},
    outcome="failed", longrepr=lr, when="call", sections=[],
)
rep2 = TestReport._from_json(copy.deepcopy(rep._to_json()))
lr2 = rep2.longrepr
assert isinstance(lr2, ExceptionChainRepr) and len(lr2.chain) == len(lr.chain)

new_texts = [link_text(l) for l in lr2.chain]
new_descs = [l[2] for l in lr2.chain]
print("orig descs:", orig_descs)
print("new  descs:", new_descs)
# Descriptions must match
if new_descs != orig_descs:
    print("FAIL: descriptions lost after round-trip")
    raise SystemExit(1)
# Each link's traceback text must be recoverable
for i, (a, b) in enumerate(zip(orig_texts, new_texts)):
    if a != b:
        print("FAIL: traceback text mismatch at link", i)
        print("orig:", repr(a))
        print("new :", repr(b))
        raise SystemExit(1)
# ensure both markers survive somewhere in the chain
joined = "\n".join(new_texts)
if "INNER_MARKER_TEXT" not in joined or "OUTER_MARKER_TEXT" not in joined:
    print("FAIL: exception marker text missing after round-trip")
    raise SystemExit(1)
print("OK: full chain text + descriptions recovered")
raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 1.3 / 2.3 / 4.1: a single-exception ReprExceptionInfo round-trips to a
# ReprExceptionInfo (NOT an ExceptionChainRepr), and serialized data records the
# absence of a chain. Also preserves sections (Req 4.1) and works for
# CollectReport (Req 2.5).
import copy
import _pytest._code
from _pytest._code.code import ReprExceptionInfo, ExceptionChainRepr
from _pytest.reports import TestReport, CollectReport


def make_single():
    # build a genuine ReprExceptionInfo (single exception, non-chained)
    try:
        raise ValueError("solo")
    except Exception:
        chain_repr = _pytest._code.ExceptionInfo.from_current().getrepr(style="long")
    rt, rc, _ = chain_repr.chain[0]
    return ReprExceptionInfo(reprtraceback=rt, reprcrash=rc)


for cls, kwargs in (
    (TestReport, dict(nodeid="t.py::x", location=("t.py", 1, "x"), keywords={}, outcome="failed", when="call")),
    (CollectReport, dict(nodeid="t.py", outcome="failed", result=[])),
):
    lr = make_single()
    lr.addsection("Captured stdout", "hello-world")
    rep = cls(longrepr=lr, sections=[], **kwargs)
    d = rep._to_json()
    # absence of chain recorded
    if d["longrepr"].get("chain") is not None:
        print("FAIL: single-exception serialization did not record chain absence for", cls.__name__)
        raise SystemExit(1)
    rep2 = cls._from_json(copy.deepcopy(d))
    lr2 = rep2.longrepr
    print(cls.__name__, "reconstructed type:", type(lr2).__name__)
    if not isinstance(lr2, ReprExceptionInfo) or isinstance(lr2, ExceptionChainRepr):
        print("FAIL: single-exception did not reconstruct as ReprExceptionInfo for", cls.__name__)
        raise SystemExit(1)
    # sections preserved (addsection stores (name, content, sep))
    secs = [tuple(s) for s in lr2.sections]
    if not any(s[0] == "Captured stdout" and s[1] == "hello-world" for s in secs):
        print("FAIL: sections lost for", cls.__name__, lr2.sections)
        raise SystemExit(1)
print("OK: single-exception round-trip fidelity for TestReport and CollectReport")
raise SystemExit(0)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 3.3 (sections on chained repr survive round-trip),
# Req 3.4 (reconstructed chained repr renders to a terminal writer w/o error),
# Req 4.5 (serialized data is builtin-only).
import copy
import _pytest._code
from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport


def make_chain():
    try:
        try:
            raise ValueError("inner")
        except ValueError as e:
            raise RuntimeError("outer") from e
    except Exception:
        return _pytest._code.ExceptionInfo.from_current().getrepr(style="long")


lr = make_chain()
lr.addsection("Captured log", "some-log-line")
rep = TestReport(
    nodeid="t.py::x", location=("t.py", 1, "x"), keywords={},
    outcome="failed", longrepr=lr, when="call", sections=[],
)
d = rep._to_json()

# Req 4.5: builtin-only
ALLOWED = (dict, list, tuple, str, int, float, bool, type(None))
def check_builtin(o, path="root"):
    if not isinstance(o, ALLOWED):
        print("FAIL: non-builtin type", type(o).__name__, "at", path)
        raise SystemExit(1)
    if isinstance(o, dict):
        for k, v in o.items():
            check_builtin(k, path + ".key")
            check_builtin(v, path + "." + str(k))
    elif isinstance(o, (list, tuple)):
        for i, v in enumerate(o):
            check_builtin(v, path + "[%d]" % i)
check_builtin(d)
print("builtin-only: OK")

rep2 = TestReport._from_json(copy.deepcopy(d))
lr2 = rep2.longrepr
assert isinstance(lr2, ExceptionChainRepr)

# Req 3.3: sections preserved (addsection stores (name, content, sep))
secs = [tuple(s) for s in lr2.sections]
if not any(s[0] == "Captured log" and s[1] == "some-log-line" for s in secs):
    print("FAIL: sections lost on chained round-trip:", lr2.sections)
    raise SystemExit(1)
print("sections preserved: OK")

# Req 3.4: renders to terminal writer without error
import io
try:
    from _pytest._io import TerminalWriter
    tw = TerminalWriter(io.StringIO())
except Exception:
    import py
    tw = py.io.TerminalWriter(io.StringIO())
lr2.toterminal(tw)
print("rendered to terminal writer without error: OK")
raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
#!/usr/bin/env python
# Req 4.2 / 4.3 / 4.4: framing preserved.
#  - result serialized as None; path attrs -> str (4.2)
#  - plain-string longrepr preserved as-is and recoverable (4.3)
#  - unknown per-frame traceback "type" raises an error (4.4)
import copy
import py
from _pytest.reports import TestReport, CollectReport


# 4.3: plain string longrepr
rep = TestReport(nodeid="t.py::x", location=("t.py", 1, "x"), keywords={},
                 outcome="failed", longrepr="just a string", when="call", sections=[])
d = rep._to_json()
if d["longrepr"] != "just a string":
    print("FAIL: string longrepr not preserved:", repr(d["longrepr"]))
    raise SystemExit(1)
rep2 = TestReport._from_json(copy.deepcopy(d))
if rep2.longrepr != "just a string":
    print("FAIL: string longrepr not recoverable:", repr(rep2.longrepr))
    raise SystemExit(1)
print("string longrepr round-trip: OK")

# 4.2: result -> None, path -> str
cr = CollectReport(nodeid="t.py", outcome="passed", longrepr=None, result=[object()])
d2 = cr._to_json()
if d2.get("result") is not None:
    print("FAIL: result not serialized as None:", d2.get("result"))
    raise SystemExit(1)
print("result serialized as None: OK")

rep3 = TestReport(nodeid="t.py::x", location=("t.py", 1, "x"), keywords={},
                  outcome="passed", longrepr=None, when="call", sections=[])
# add an arbitrary py.path.local-valued attribute (extra kwargs land on __dict__)
rep3.__dict__["somepath"] = py.path.local(".")
d3 = rep3._to_json()
if not isinstance(d3["somepath"], str):
    print("FAIL: py.path.local not converted to str:", type(d3["somepath"]))
    raise SystemExit(1)
print("path attr -> str: OK")

# 4.4: unknown reprentry type raises
bad = TestReport(nodeid="t.py::x", location=("t.py", 1, "x"), keywords={},
                 outcome="failed", longrepr="x", when="call", sections=[])
import _pytest._code
try:
    raise ValueError("z")
except Exception:
    lr = _pytest._code.ExceptionInfo.from_current().getrepr(style="long")
rep4 = TestReport(nodeid="t.py::x", location=("t.py", 1, "x"), keywords={},
                  outcome="failed", longrepr=lr, when="call", sections=[])
d4 = rep4._to_json()
# corrupt the recorded per-frame type
d4["longrepr"]["reprtraceback"]["reprentries"][0]["type"] = "NotARealType"
raised = False
try:
    TestReport._from_json(copy.deepcopy(d4))
except Exception as e:
    raised = True
    print("unknown type raised:", type(e).__name__, str(e)[:80])
    if "NotARealType" not in str(e):
        print("FAIL: error does not report the unexpected type")
        raise SystemExit(1)
if not raised:
    print("FAIL: unknown reprentry type did not raise")
    raise SystemExit(1)
print("unknown reprentry type raises reporting the type: OK")
raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# Req 3.1 / 3.2 (POSITIVE CONTROL): round-tripping a chained (len>=2) failure
# through _to_json/_from_json yields an ExceptionChainRepr with the same number
# of links, not collapsed to a single exception.
import copy
import _pytest._code
from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport


def make_chain():
    try:
        try:
            raise ValueError("inner-cause")
        except ValueError as e:
            raise RuntimeError("outer-effect") from e
    except Exception:
        return _pytest._code.ExceptionInfo.from_current().getrepr(style="long")


lr = make_chain()
assert isinstance(lr, ExceptionChainRepr), type(lr)
n_orig = len(lr.chain)
print("original chain links:", n_orig)
assert n_orig >= 2, "need a genuine multi-stage chain for the discriminating test"

rep = TestReport(
    nodeid="test_mod.py::test_x",
    location=("test_mod.py", 1, "test_x"),
    keywords={},
    outcome="failed",
    longrepr=lr,
    when="call",
    sections=[],
)
d = rep._to_json()
rep2 = TestReport._from_json(copy.deepcopy(d))
lr2 = rep2.longrepr
print("reconstructed longrepr type:", type(lr2).__name__)
ok = isinstance(lr2, ExceptionChainRepr) and len(lr2.chain) == n_orig
print("reconstructed chain links:", getattr(lr2, "chain", None) and len(lr2.chain))
if not ok:
    print("FAIL: chain collapsed or wrong type")
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5787: preserve chained exceptions across report serialization in src/_pytest/reports.py (_to_json/_from_json).

### PROBES (all HOLD on gold-patched tree):
- probe_1 (Req 3.1/3.2, POSITIVE CONTROL): round-trip a genuine len-2 chained failure (raise ... from ...) through _to_json/_from_json -> longrepr is ExceptionChainRepr with the same link count, not collapsed. HOLDS patched, VIOLATED at base (base collapses to single exception). prepatch_reproduced=true.
- probe_2 (Req 1.1/1.2): _to_json records a 'chain' list with matching count/order; each link is (traceback-dict-with-reprentries, crash-dict, description); descriptions preserved in order; final link description is None. HOLDS patched, VIOLATED at base.
- probe_3 (Req 3.2): after round-trip, per-link traceback text AND descriptions recoverable; INNER/OUTER marker text both survive. HOLDS patched, VIOLATED at base.
- probe_4 (Req 1.3/2.3/4.1/2.5): single-exception ReprExceptionInfo round-trips to ReprExceptionInfo (not ExceptionChainRepr); 'chain' recorded as None; sections preserved; verified for both TestReport and CollectReport.
- probe_5 (Req 3.3/3.4/4.5): sections on a chained repr survive round-trip; serialized data is builtin-only (recursive type check); reconstructed chained repr renders to a TerminalWriter without error.
- probe_6 (Req 4.2/4.3/4.4): result serialized as None; py.path.local attr -> str; plain-string longrepr preserved and recoverable; corrupting a per-frame reprentry 'type' to an unknown value causes _from_json to raise reporting the unexpected type name.

### Discrimination
- Positive control probe_1 FAILS at base and HOLDS patched (re-run confirmed).
- WRONG-FIX CANDIDATE (weak.diff): identical to gold except the deserialize chain-reconstruction branch is gated on `if False`, so serialization still records the full chain (Req 1 satisfied, probe_2 passes) but reconstruction always builds a single ReprExceptionInfo. This candidate is REJECTED by probe_1, probe_3 and probe_5 (chain collapses; text/sections lost), demonstrating the suite discriminates a requirements-partial wrong implementation. probe_2/4/6 pass under it as expected (serialize + single-exception + framing unaffected).

Minor note: probes exit non-zero cleanly on failure; addsection stores (name, content, sep) triples and fspath is a read-only property — probes account for both. All required runs completed in-image.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
#!/usr/bin/env python
# Req 3.1 / 3.2 (POSITIVE CONTROL): round-tripping a chained (len>=2) failure
# through _to_json/_from_json yields an ExceptionChainRepr with the same number
# of links, not collapsed to a single exception.
import copy
import _pytest._code
from _pytest._code.code import ExceptionChainRepr
from _pytest.reports import TestReport


def make_chain():
    try:
        try:
            raise ValueError("inner-cause")
        except ValueError as e:
            raise RuntimeError("outer-effect") from e
    except Exception:
        return _pytest._code.ExceptionInfo.from_current().getrepr(style="long")


lr = make_chain()
assert isinstance(lr, ExceptionChainRepr), type(lr)
n_orig = len(lr.chain)
print("original chain links:", n_orig)
assert n_orig >= 2, "need a genuine multi-stage chain for the discriminating test"

rep = TestReport(
    nodeid="test_mod.py::test_x",
    location=("test_mod.py", 1, "test_x"),
    keywords={},
    outcome="failed",
    longrepr=lr,
    when="call",
    sections=[],
)
d = rep._to_json()
rep2 = TestReport._from_json(copy.deepcopy(d))
lr2 = rep2.longrepr
print("reconstructed longrepr type:", type(lr2).__name__)
ok = isinstance(lr2, ExceptionChainRepr) and len(lr2.chain) == n_orig
print("reconstructed chain links:", getattr(lr2, "chain", None) and len(lr2.chain))
if not ok:
    print("FAIL: chain collapsed or wrong type")
    raise SystemExit(1)
print("OK")
raise SystemExit(0)
```

Prepatch bug re-encoded as an attack: `True`.

Instance pytest-dev__pytest-5787: preserve chained exceptions across report serialization in src/_pytest/reports.py (_to_json/_from_json).

### PROBES (all HOLD on gold-patched tree):
- probe_1 (Req 3.1/3.2, POSITIVE CONTROL): round-trip a genuine len-2 chained failure (raise ... from ...) through _to_json/_from_json -> longrepr is ExceptionChainRepr with the same link count, not collapsed. HOLDS patched, VIOLATED at base (base collapses to single exception). prepatch_reproduced=true.
- probe_2 (Req 1.1/1.2): _to_json records a 'chain' list with matching count/order; each link is (traceback-dict-with-reprentries, crash-dict, description); descriptions preserved in order; final link description is None. HOLDS patched, VIOLATED at base.
- probe_3 (Req 3.2): after round-trip, per-link traceback text AND descriptions recoverable; INNER/OUTER marker text both survive. HOLDS patched, VIOLATED at base.
- probe_4 (Req 1.3/2.3/4.1/2.5): single-exception ReprExceptionInfo round-trips to ReprExceptionInfo (not ExceptionChainRepr); 'chain' recorded as None; sections preserved; verified for both TestReport and CollectReport.
- probe_5 (Req 3.3/3.4/4.5): sections on a chained repr survive round-trip; serialized data is builtin-only (recursive type check); reconstructed chained repr renders to a TerminalWriter without error.
- probe_6 (Req 4.2/4.3/4.4): result serialized as None; py.path.local attr -> str; plain-string longrepr preserved and recoverable; corrupting a per-frame reprentry 'type' to an unknown value causes _from_json to raise reporting the unexpected type name.

### Discrimination
- Positive control probe_1 FAILS at base and HOLDS patched (re-run confirmed).
- WRONG-FIX CANDIDATE (weak.diff): identical to gold except the deserialize chain-reconstruction branch is gated on `if False`, so serialization still records the full chain (Req 1 satisfied, probe_2 passes) but reconstruction always builds a single ReprExceptionInfo. This candidate is REJECTED by probe_1, probe_3 and probe_5 (chain collapses; text/sections lost), demonstrating the suite discriminates a requirements-partial wrong implementation. probe_2/4/6 pass under it as expected (serialize + single-exception + framing unaffected).

Minor note: probes exit non-zero cleanly on failure; addsection stores (name, content, sep) triples and fspath is a read-only property — probes account for both. All required runs completed in-image.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Probe HOLDS on gold-patched tree (chain len 3, reconstructed ExceptionChainRepr len 3, rendered OK, PASS); VIOLATED at base (no 'chain' key). Requirements 1-4 correspond exactly to _report_to_json/_report_kwargs_from_json in the diff. Modeling boundary is correct: it pins the serialize/deserialize round-trip chain-preservation behavior rather than an internal helper. No mandated-but-absent, forbidden-but-present, wrong-boundary, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** The requirements.md describes behavior; every seemingly test-shaped detail is either public via the problem_statement or a legitimate behavioral translation localized to real, pre-existing code symbols.

- Named symbols (src/_pytest/reports.py, _to_json, _from_json, ExceptionChainRepr, ReprExceptionInfo, _pytest._code.code) are all pre-existing codebase identifiers and constitute legitimate localization of the change. None of the fix-invented identifiers leak: the gold patch's new names (_report_to_json, _report_kwargs_from_json, serialize_repr_entry/traceback/crash, the "chain" dict key) and the test's tw_mock fixture / test_chained_exceptions / test_deserialization_failure names are absent from the document.
- The two description strings quoted in the intro ("The above exception was the direct cause..." / "During handling of the above exception...") appear VERBATIM in the public problem_statement's terminal output, so they are not hidden-test-derived.
- The (traceback, crash-location, description) link triple is the genuine public shape of ExceptionChainRepr.chain, described as behavior; "description absent for the final/outermost link" is a real structural property (matching desc2 is None) stated behaviorally, not a transcription of the test's unpacking.
- "chain of length two or more" (Req 3.2) is general and consistent with the public example (length-3 chains); it does not mirror the test's fixed 2-link fixture as a parametrization id.
- "both TestReport and CollectReport" (Req 2.5) uses public report-type names for localization; it does not transmit the [TestReport]/[CollectReport] parametrization ids or the CollectReport error_during_import trick.
- Req 4 items (path->string coercion, result recorded as absent 'for now', unrecognized frame type raises) describe pre-existing serialization framing and PASS_TO_PASS-tested behavior, described behaviorally.

No test file paths, node ids, quoted test/gold code, fix-invented identifiers, or parametrization-mirroring enumerations are present. This is the intended translate-tests-into-behavior pattern, not test transmission.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
