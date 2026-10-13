# P2 adversarial audit — sphinx-doc__sphinx-9602

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# Req 1.1,1.2,1.3,1.4: Literal[True, False] renders as
#   xref 'Literal', '[', Text 'True', ', ', Text 'False', ']'
# args are plain Text (NOT pending_xref).
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
from docutils import nodes

env = SimpleNamespace(
    config=SimpleNamespace(python_use_unqualified_type_names=False),
    ref_context={})
r = _parse_annotation("Literal[True, False]", env)
got = [(type(n).__name__, n.astext()) for n in r]
print("nodes:", got)

def is_xref(n): return isinstance(n, addnodes.pending_xref)
def is_punct(n): return isinstance(n, addnodes.desc_sig_punctuation)
def is_text(n): return isinstance(n, nodes.Text)

ok = (
    len(r) == 6
    and is_xref(r[0]) and r[0].astext() == "Literal"
    and is_punct(r[1]) and r[1].astext() == "["
    and is_text(r[2]) and not is_xref(r[2]) and r[2].astext() == "True"
    and is_punct(r[3]) and r[3].astext() == ", "
    and is_text(r[4]) and not is_xref(r[4]) and r[4].astext() == "False"
    and is_punct(r[5]) and r[5].astext() == "]"
)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# Req 1.2 (+1.3,1.4): typing.Literal[0, 1, 'abc'] -> ints as decimals,
# string single-quoted 'abc'; head xref, brackets/commas punctuation.
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
from docutils import nodes
env = SimpleNamespace(config=SimpleNamespace(python_use_unqualified_type_names=False), ref_context={})
r = _parse_annotation("typing.Literal[0, 1, 'abc']", env)
got = [(type(n).__name__, n.astext()) for n in r]
print("nodes:", got)
def X(n): return isinstance(n, addnodes.pending_xref)
def P(n): return isinstance(n, addnodes.desc_sig_punctuation)
def T(n): return isinstance(n, nodes.Text) and not X(n)
exp = [
 (X, "typing.Literal"), (P, "["),
 (T, "0"), (P, ", "), (T, "1"), (P, ", "), (T, "'abc'"),
 (P, "]"),
]
ok = len(r) == len(exp) and all(chk(n) and n.astext()==txt for n,(chk,txt) in zip(r,exp))
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# Req 1.1 / 1.5: NO argument value inside Literal[...] becomes a pending_xref.
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
env = SimpleNamespace(config=SimpleNamespace(python_use_unqualified_type_names=False), ref_context={})
for ann in ["Literal[True, False]", "typing.Literal[0, 1, 'abc']", "Literal['x']"]:
    r = _parse_annotation(ann, env)
    # head (index 0) may be an xref; args must not be.
    args_xrefs = [type(n).__name__ for n in r[1:] if isinstance(n, addnodes.pending_xref)]
    print(ann, "-> arg xrefs:", args_xrefs)
    if args_xrefs:
        print("FAIL"); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# Req 2.1: bare 'int' -> pending_xref reftype 'class'
# Req 2.2: 'None' -> pending_xref reftype 'obj'
# Req 2.3: List[int] -> head + inner names as xrefs, brackets punctuation
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
env = SimpleNamespace(config=SimpleNamespace(python_use_unqualified_type_names=False), ref_context={})

r = _parse_annotation("int", env)
print("int:", [(type(n).__name__, n.astext(), n.get('reftype')) for n in r])
if not (len(r)==1 and isinstance(r[0], addnodes.pending_xref) and r[0].get('reftype')=='class' and r[0].get('reftarget')=='int'):
    print("FAIL int"); raise SystemExit(1)

r = _parse_annotation("None", env)
print("None:", [(type(n).__name__, n.astext(), n.get('reftype')) for n in r])
if not (len(r)==1 and isinstance(r[0], addnodes.pending_xref) and r[0].get('reftype')=='obj' and r[0].get('reftarget')=='None'):
    print("FAIL None"); raise SystemExit(1)

r = _parse_annotation("List[int]", env)
seq = [(type(n).__name__, n.astext()) for n in r]
print("List[int]:", seq)
def X(n): return isinstance(n, addnodes.pending_xref)
def P(n): return isinstance(n, addnodes.desc_sig_punctuation)
ok = (len(r)==4 and X(r[0]) and r[0].astext()=="List" and P(r[1]) and r[1].astext()=="["
      and X(r[2]) and r[2].astext()=="int" and r[2].get('reftype')=='class'
      and P(r[3]) and r[3].astext()=="]")
print("PASS" if ok else "FAIL List"); raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# Req 2.4 / 2.3: empty parenthesised group and ellipsis inside a parametrised
# type render as punctuation nodes (unchanged).
#   Tuple[()]      -> '(' ')' punctuation
#   Callable[..., int] -> '...' punctuation, 'int' xref
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
env = SimpleNamespace(config=SimpleNamespace(python_use_unqualified_type_names=False), ref_context={})

r = _parse_annotation("Tuple[()]", env)
seq = [(type(n).__name__, n.astext()) for n in r]
print("Tuple[()]:", seq)
punct = [n.astext() for n in r if isinstance(n, addnodes.desc_sig_punctuation)]
if not ('(' in punct and ')' in punct):
    print("FAIL: empty parens not punctuation"); raise SystemExit(1)
# No pending_xref should be emitted for the empty group '(' or ')'
if any(isinstance(n, addnodes.pending_xref) and n.astext() in ('(', ')') for n in r):
    print("FAIL: paren became xref"); raise SystemExit(1)

r = _parse_annotation("Callable[..., int]", env)
seq = [(type(n).__name__, n.astext()) for n in r]
print("Callable[..., int]:", seq)
ell = [n for n in r if isinstance(n, addnodes.desc_sig_punctuation) and n.astext()=="..."]
if not ell:
    print("FAIL: ellipsis not punctuation"); raise SystemExit(1)
if any(isinstance(n, addnodes.pending_xref) and n.astext()=="..." for n in r):
    print("FAIL: ellipsis became xref"); raise SystemExit(1)
if not any(isinstance(n, addnodes.pending_xref) and n.astext()=="int" for n in r):
    print("FAIL: int not xref"); raise SystemExit(1)
print("PASS"); raise SystemExit(0)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# Req 2.5: unparseable annotation -> single pending_xref for whole string.
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
env = SimpleNamespace(config=SimpleNamespace(python_use_unqualified_type_names=False), ref_context={})
ann = "List[int"   # missing closing bracket -> SyntaxError
r = _parse_annotation(ann, env)
print("result:", [(type(n).__name__, n.astext()) for n in r])
ok = (len(r)==1 and isinstance(r[0], addnodes.pending_xref) and r[0].get('reftarget')==ann)
print("PASS" if ok else "FAIL"); raise SystemExit(0 if ok else 1)
```

Attack 7 — `probe_7.py` → holds on the patched tree (good)

```python
# Req 3.1 / 3.3: A string constant appearing OUTSIDE a Literal argument list
# is displayed with surrounding quotes (canonical source repr). Numeric
# constant unchanged. Non-Literal type names remain xrefs (order preserved).
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
from docutils import nodes
env = SimpleNamespace(config=SimpleNamespace(python_use_unqualified_type_names=False), ref_context={})

# Tuple['x'] : the string constant should show with quotes 'x'
r = _parse_annotation("Tuple['x']", env)
seq = [(type(n).__name__, n.astext()) for n in r]
print("Tuple['x']:", seq)
# Find the element carrying the string value; its displayed text must contain quotes.
texts = [n.astext() for n in r]
if "'x'" not in "".join(texts):
    print("FAIL: string constant not shown with quotes"); raise SystemExit(1)
# It must NOT show as bare x without quotes anywhere as the sole rep
# (guard: ensure the quoted form present)
print("PASS"); raise SystemExit(0)
```

Attack 8 — `probe_8.py` → holds on the patched tree (good)

```python
# Req 3.2 / 3.1: numeric constant outside Literal renders as its decimal
# digits (source repr unchanged). Tuple[int, 5] -> '5' present as decimal text.
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
from docutils import nodes
env = SimpleNamespace(config=SimpleNamespace(python_use_unqualified_type_names=False), ref_context={})
r = _parse_annotation("Tuple[int, 5]", env)
seq = [(type(n).__name__, n.astext()) for n in r]
print("Tuple[int, 5]:", seq)
# 'int' remains xref
if not any(isinstance(n, addnodes.pending_xref) and n.astext()=="int" for n in r):
    print("FAIL: int not xref"); raise SystemExit(1)
# '5' shown as decimal
joined = "".join(n.astext() for n in r)
if "5" not in joined:
    print("FAIL: numeric literal missing"); raise SystemExit(1)
# and 5 should not be an xref target of a class (numeric not a type name xref ideally text)
print("PASS"); raise SystemExit(0)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1,1.2,1.3,1.4: Literal[True, False] renders as
#   xref 'Literal', '[', Text 'True', ', ', Text 'False', ']'
# args are plain Text (NOT pending_xref).
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
from docutils import nodes

env = SimpleNamespace(
    config=SimpleNamespace(python_use_unqualified_type_names=False),
    ref_context={})
r = _parse_annotation("Literal[True, False]", env)
got = [(type(n).__name__, n.astext()) for n in r]
print("nodes:", got)

def is_xref(n): return isinstance(n, addnodes.pending_xref)
def is_punct(n): return isinstance(n, addnodes.desc_sig_punctuation)
def is_text(n): return isinstance(n, nodes.Text)

ok = (
    len(r) == 6
    and is_xref(r[0]) and r[0].astext() == "Literal"
    and is_punct(r[1]) and r[1].astext() == "["
    and is_text(r[2]) and not is_xref(r[2]) and r[2].astext() == "True"
    and is_punct(r[3]) and r[3].astext() == ", "
    and is_text(r[4]) and not is_xref(r[4]) and r[4].astext() == "False"
    and is_punct(r[5]) and r[5].astext() == "]"
)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9602: Literal[...] arg values must render as plain Text, not pending_xref. All probes call sphinx.domains.python._parse_annotation directly with a minimal SimpleNamespace env (config.python_use_unqualified_type_names=False, ref_context={}) — no pytest.

Probe -> requirement -> result (PATCHED / BASE):
- probe_1 (POSITIVE CONTROL) Req 1.1/1.2/1.3/1.4: Literal[True, False] -> [xref 'Literal', '[', Text 'True', ', ', Text 'False', ']'], args are Text not xref. HOLDS patched / FAIL base (base emits xref 'True','False').
- probe_2 Req 1.2/1.3/1.4: typing.Literal[0, 1, 'abc'] -> ints as decimals, string single-quoted 'abc', head xref, comma-space punctuation. HOLDS patched / FAIL base.
- probe_3 Req 1.1/1.5: no argument inside Literal[...]/typing.Literal[...]/Literal['x'] is a pending_xref. HOLDS patched / FAIL base.
- probe_4 Req 2.1/2.2/2.3: bare 'int' -> xref reftype class; 'None' -> xref reftype obj; List[int] -> head+inner xrefs, brackets punctuation. HOLDS both (regression).
- probe_5 Req 2.4/2.3: Tuple[()] empty parens -> '(' ')' punctuation; Callable[..., int] ellipsis -> '...' punctuation, int xref. HOLDS both (regression). (Initial version wrongly assumed Callable[[],int] gives parens; corrected: empty parens come from empty tuple Tuple[()].)
- probe_6 Req 2.5: unparseable 'List[int' -> single pending_xref for whole string. HOLDS both (regression).
- probe_7 Req 3.1/3.3: string constant outside Literal, Tuple['x'], shown with surrounding quotes ('x'). HOLDS patched / FAIL base (base drops quotes -> bare x).
- probe_8 Req 3.2/3.1: numeric constant Tuple[int, 5] -> int stays xref, '5' decimal present. HOLDS both (regression).

### CANDIDATE PATCHES (both apply at base_commit, both REJECTED by suite -> suite discriminates wrong impls):
- weak_reprOnly: only the repr(node.value) change, WITHOUT the nodes.literal wrap/unwrap. Args still become xrefs. Rejected by probes 1,2,3.
- weak_noTyping: full mechanism but only matches head 'Literal', not 'typing.Literal'. Rejected by probes 2,3 (typing.Literal args still xref'd). Note this candidate would ALSO fail the hidden test test_parse_annotation_Literal (its typing.Literal case), consistent with rejection.

No requirement-conforming alternative patch was found that fails the hidden tests. Note: G-PANEL-2 flagged an unfaithfulness (Req 3.1 mandates quoted string constants OUTSIDE Literal, which the gold patch does produce via repr, so requirements are faithful to gold on this point for G-EQ purposes; the base-vs-patched divergence probe_7 encodes is real and intended by the gold patch). G-EQ (spec-too-weak) is SOUND: >=5 probes hold, positive control discriminates, >=1 wrong candidate rejected.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 8 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 8 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py`, `probe_7.py`, `probe_8.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (8):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts, and on this backend both roles put it through the same derivation: every block below is a requirement probe run on the gold-patched tree, and the `machine verdict:` line each role publishes above reports BOTH that its probes hold there and how many candidate patches the probe suite rejected — so the two roles re-ran ONE probe suite and each recorded its own outcome for every probe in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `probe_1.py` → holds on the patched tree (good)

Attack 2 — `probe_2.py` → holds on the patched tree (good)

Attack 3 — `probe_3.py` → holds on the patched tree (good)

Attack 4 — `probe_4.py` → holds on the patched tree (good)

Attack 5 — `probe_5.py` → holds on the patched tree (good)

Attack 6 — `probe_6.py` → holds on the patched tree (good)

Attack 7 — `probe_7.py` → holds on the patched tree (good)

Attack 8 — `probe_8.py` → holds on the patched tree (good)

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# Req 1.1,1.2,1.3,1.4: Literal[True, False] renders as
#   xref 'Literal', '[', Text 'True', ', ', Text 'False', ']'
# args are plain Text (NOT pending_xref).
from types import SimpleNamespace
from sphinx.domains.python import _parse_annotation
from sphinx import addnodes
from docutils import nodes

env = SimpleNamespace(
    config=SimpleNamespace(python_use_unqualified_type_names=False),
    ref_context={})
r = _parse_annotation("Literal[True, False]", env)
got = [(type(n).__name__, n.astext()) for n in r]
print("nodes:", got)

def is_xref(n): return isinstance(n, addnodes.pending_xref)
def is_punct(n): return isinstance(n, addnodes.desc_sig_punctuation)
def is_text(n): return isinstance(n, nodes.Text)

ok = (
    len(r) == 6
    and is_xref(r[0]) and r[0].astext() == "Literal"
    and is_punct(r[1]) and r[1].astext() == "["
    and is_text(r[2]) and not is_xref(r[2]) and r[2].astext() == "True"
    and is_punct(r[3]) and r[3].astext() == ", "
    and is_text(r[4]) and not is_xref(r[4]) and r[4].astext() == "False"
    and is_punct(r[5]) and r[5].astext() == "]"
)
print("PASS" if ok else "FAIL")
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance sphinx-doc__sphinx-9602: Literal[...] arg values must render as plain Text, not pending_xref. All probes call sphinx.domains.python._parse_annotation directly with a minimal SimpleNamespace env (config.python_use_unqualified_type_names=False, ref_context={}) — no pytest.

Probe -> requirement -> result (PATCHED / BASE):
- probe_1 (POSITIVE CONTROL) Req 1.1/1.2/1.3/1.4: Literal[True, False] -> [xref 'Literal', '[', Text 'True', ', ', Text 'False', ']'], args are Text not xref. HOLDS patched / FAIL base (base emits xref 'True','False').
- probe_2 Req 1.2/1.3/1.4: typing.Literal[0, 1, 'abc'] -> ints as decimals, string single-quoted 'abc', head xref, comma-space punctuation. HOLDS patched / FAIL base.
- probe_3 Req 1.1/1.5: no argument inside Literal[...]/typing.Literal[...]/Literal['x'] is a pending_xref. HOLDS patched / FAIL base.
- probe_4 Req 2.1/2.2/2.3: bare 'int' -> xref reftype class; 'None' -> xref reftype obj; List[int] -> head+inner xrefs, brackets punctuation. HOLDS both (regression).
- probe_5 Req 2.4/2.3: Tuple[()] empty parens -> '(' ')' punctuation; Callable[..., int] ellipsis -> '...' punctuation, int xref. HOLDS both (regression). (Initial version wrongly assumed Callable[[],int] gives parens; corrected: empty parens come from empty tuple Tuple[()].)
- probe_6 Req 2.5: unparseable 'List[int' -> single pending_xref for whole string. HOLDS both (regression).
- probe_7 Req 3.1/3.3: string constant outside Literal, Tuple['x'], shown with surrounding quotes ('x'). HOLDS patched / FAIL base (base drops quotes -> bare x).
- probe_8 Req 3.2/3.1: numeric constant Tuple[int, 5] -> int stays xref, '5' decimal present. HOLDS both (regression).

### CANDIDATE PATCHES (both apply at base_commit, both REJECTED by suite -> suite discriminates wrong impls):
- weak_reprOnly: only the repr(node.value) change, WITHOUT the nodes.literal wrap/unwrap. Args still become xrefs. Rejected by probes 1,2,3.
- weak_noTyping: full mechanism but only matches head 'Literal', not 'typing.Literal'. Rejected by probes 2,3 (typing.Literal args still xref'd). Note this candidate would ALSO fail the hidden test test_parse_annotation_Literal (its typing.Literal case), consistent with rejection.

No requirement-conforming alternative patch was found that fails the hidden tests. Note: G-PANEL-2 flagged an unfaithfulness (Req 3.1 mandates quoted string constants OUTSIDE Literal, which the gold patch does produce via repr, so requirements are faithful to gold on this point for G-EQ purposes; the base-vs-patched divergence probe_7 encodes is real and intended by the gold patch). G-EQ (spec-too-weak) is SOUND: >=5 probes hold, positive control discriminates, >=1 wrong candidate rejected.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** The change is repr(node.value) on ast.Constant plus a Literal-detection branch wrapping Text args in nodes.literal (unwrapped to bypass xref conversion). Requirements Req1 pin the Literal args→plain-text behavior; Req2 preserves non-Literal xref/punct structure; Req3 correctly encodes the incidental repr() side effect (quoted strings outside Literal). Minor imprecision: Req 1.2 says string 'single-quoted form' whereas repr() uses double quotes if the string contains a single quote — but this is a narrow edge that does not mandate behavior the code lacks nor mispin the changed boundary (the issue/tests concern True/1/'abc'-style values), so it does not rise to UNFAITHFUL. meta.json's recorded G-PANEL-2 fail predates or missed that Req 3.3 explicitly legitimizes the Annotated[int,'meta'] quote divergence.

Counterexample / evidence:

```
N/A — FAITHFUL. Probe evidence: BASE Annotated[int,'meta'] third element = xref target 'meta'; PATCHED = xref target "'meta'"; numeric Literal[1,2] args render as '1'/'2' in both, consistent with Req 3.3's 'numeric constant renders exactly as before'.
```


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements localize the change to sphinx/domains/python.py's _parse_annotation/unparse and Literal/typing.Literal handling — all public via the problem_statement (which explicitly names Literal[True], typing.Literal, nitpick -n -W). No test names/paths/ids (test_parse_annotation_Literal), no quoted test/gold code, no fix-invented identifiers (the gold's nodes.literal wrapper mechanism and repr() call are described only as behavior: 'canonical source representation'). Borderline point: Req 1.2 enumerates bool/int/string rendering (integer->decimal digits, string->single-quoted with surrounding quotes), which extends beyond the boolean-only public statement and loosely maps onto the hidden test's values (True/False, 0/1, 'abc'). However this is a faithful behavioral description of repr() over primitive constants — the natural generalization of the one-line gold edit — not a reconstruction of the specific test inputs; a reader cannot derive the exact parametrized case typing.Literal[0,1,'abc'] from it. Translating what the tests check into behavior is the intended purpose. Verdict: no semantic leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
