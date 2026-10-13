# P2 adversarial audit — django__django-12039

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

Counterexample / evidence:

```
Weak candidate 'naive_always_space_columns' rewrites only Columns.col_str to always insert a space via '{} {}'.format(...). It fixes the glued-token defect (probe_1 passes) but is rejected by probe_3 (plain column with empty suffix renders '"name" ' with a trailing space, violating R2.1/R2.3) and probe_5 (opclass code path untouched -> unrelated failure). Thus the suite discriminates this requirements-incomplete fix.
```

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
# R1.1 / R1.3: plain column with non-empty ordering suffix -> quoted name + one space + suffix
from django.db.backends.ddl_references import Columns
q = lambda c: '"%s"' % c
s = str(Columns("tbl", ["name"], q, col_suffixes=["DESC"]))
print("Columns desc:", repr(s))
assert s == '"name" DESC', s
print("OK")
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
# R1.2 / R1.4: opclass column with non-empty suffix -> name + sp + opclass + sp + suffix
from django.db.backends.ddl_references import IndexColumns
q = lambda c: '"%s"' % c
s = str(IndexColumns("tbl", ["name"], q, col_suffixes=["DESC"], opclasses=["text_pattern_ops"]))
print("IndexColumns desc:", repr(s))
assert s == '"name" text_pattern_ops DESC', s
print("OK")
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
# R2.1 / R2.3: plain column with empty-string suffix -> unchanged, no trailing space
from django.db.backends.ddl_references import Columns
q = lambda c: '"%s"' % c
s = str(Columns("tbl", ["name"], q, col_suffixes=[""]))
print("Columns empty suffix:", repr(s))
assert s == '"name"', s
print("OK")
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
# R2.2: no suffix at all (out of range) -> unchanged
from django.db.backends.ddl_references import Columns
q = lambda c: '"%s"' % c
s = str(Columns("tbl", ["name"], q, col_suffixes=[]))
print("Columns no suffix:", repr(s))
assert s == '"name"', s
print("OK")
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
# R2.4 / R3.2: opclass column with empty suffix -> name + sp + opclass, NO trailing space
from django.db.backends.ddl_references import IndexColumns
q = lambda c: '"%s"' % c
s = str(IndexColumns("tbl", ["name"], q, col_suffixes=[""], opclasses=["text_pattern_ops"]))
print("IndexColumns empty suffix:", repr(s))
assert s == '"name" text_pattern_ops', s
print("OK")
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
# R4.1 / R4.2: multi-column join with mixed suffixes, comma+space, each entry correct
from django.db.backends.ddl_references import Columns, IndexColumns
q = lambda c: '"%s"' % c
s = str(Columns("tbl", ["a", "b"], q, col_suffixes=["", "DESC"]))
print("Columns multi:", repr(s))
assert s == '"a", "b" DESC', s
s2 = str(IndexColumns("tbl", ["a", "b"], q, col_suffixes=["DESC", ""], opclasses=["op1", "op2"]))
print("IndexColumns multi:", repr(s2))
assert s2 == '"a" op1 DESC, "b" op2', s2
print("OK")
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
# R1.1 / R1.3: plain column with non-empty ordering suffix -> quoted name + one space + suffix
from django.db.backends.ddl_references import Columns
q = lambda c: '"%s"' % c
s = str(Columns("tbl", ["name"], q, col_suffixes=["DESC"]))
print("Columns desc:", repr(s))
assert s == '"name" DESC', s
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree: probe_1 R1.1/R1.3 (Columns desc -> '"name" DESC'); probe_2 R1.2/R1.4 (IndexColumns desc -> '"name" text_pattern_ops DESC'); probe_3 R2.1/R2.3 (Columns empty suffix -> '"name"' no trailing space); probe_4 R2.2 (out-of-range suffix -> '"name"'); probe_5 R2.4/R3.2 (IndexColumns empty suffix -> '"name" text_pattern_ops' no trailing space); probe_6 R4.1/R4.2 (multi-column comma+space join, each entry independently correct). Positive control probe_1: HOLDS patched, FAILS at base (base yields '"name"DESC' glued). probe_5 also discriminates base (base yields '"name" text_pattern_ops ' with stray trailing space). Weak candidate REJECTED by probes 3 and 5. Note: unrelated to G-EQ, meta.json records G-PANEL-3 (leakage) fail for Requirement 4 enumerating hidden test parametrization — outside this gate's scope.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 1/1 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 1 alternative candidate patch, claimed to satisfy every cited requirement, and ran the same suite against it. The suite rejected it: a probe encoding a cited requirement fails under it, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

Counterexample / evidence:

```
Weak candidate 'naive_always_space_columns' rewrites only Columns.col_str to always insert a space via '{} {}'.format(...). It fixes the glued-token defect (probe_1 passes) but is rejected by probe_3 (plain column with empty suffix renders '"name" ' with a trailing space, violating R2.1/R2.3) and probe_5 (opclass code path untouched -> unrelated failure). Thus the suite discriminates this requirements-incomplete fix.
```

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
# R1.1 / R1.3: plain column with non-empty ordering suffix -> quoted name + one space + suffix
from django.db.backends.ddl_references import Columns
q = lambda c: '"%s"' % c
s = str(Columns("tbl", ["name"], q, col_suffixes=["DESC"]))
print("Columns desc:", repr(s))
assert s == '"name" DESC', s
print("OK")
```

Prepatch bug re-encoded as an attack: `True`.

6 distinct probes, all HOLD on gold-patched tree: probe_1 R1.1/R1.3 (Columns desc -> '"name" DESC'); probe_2 R1.2/R1.4 (IndexColumns desc -> '"name" text_pattern_ops DESC'); probe_3 R2.1/R2.3 (Columns empty suffix -> '"name"' no trailing space); probe_4 R2.2 (out-of-range suffix -> '"name"'); probe_5 R2.4/R3.2 (IndexColumns empty suffix -> '"name" text_pattern_ops' no trailing space); probe_6 R4.1/R4.2 (multi-column comma+space join, each entry independently correct). Positive control probe_1: HOLDS patched, FAILS at base (base yields '"name"DESC' glued). probe_5 also discriminates base (base yields '"name" text_pattern_ops ' with stray trailing space). Weak candidate REJECTED by probes 3 and 5. Note: unrelated to G-EQ, meta.json records G-PANEL-3 (leakage) fail for Requirement 4 enumerating hidden test parametrization — outside this gate's scope.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Patch modifies both Columns.__str__ and IndexColumns.__str__ col_str helpers: append suffix with a single separating space only when suffix is truthy; empty string or IndexError -> unchanged. Requirements 1-4 map exactly to this, covering both changed classes (correct modeling boundary, not a narrow slice) and the multi-column join separator (unchanged). No forbidden/invented behavior; no mandated behavior the code lacks.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe the CREATE INDEX whitespace fix purely as behavior, drawing on the public problem_statement. Uses the problem_statement's identifier `"name"` throughout, never the hidden tests' `headline`. No test names/paths/class names (test_descending_columns_list_sql, SchemaIndexesTests, tests/indexes/tests.py) appear. Named modules/functions (ddl_references.py, Columns, col_suffixes, IndexColumns, Index.create_sql) are legitimate localization — Columns/col_suffixes/ddl_references.py are explicitly in the public statement; IndexColumns/create_sql are real API, not fix-invented (the gold introduces no new public identifiers). The four example renderings are the natural 2x2 product of {asc,desc}x{opclass,none}; three appear in the public statement and the fourth is a trivial implied combination — this is behavioral description, not a mirror of test parametrization (tests are separate hand-written methods, not parametrized). No verbatim gold-patch lines or test assertion code transmitted.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
