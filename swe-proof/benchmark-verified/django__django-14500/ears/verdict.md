# P2 adversarial audit — django__django-14500

Backend: `ears`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

**Non-vacuity.** The positive control `probe_1.py` holds on the gold-patched tree and fails at base, so the suite separates the two trees rather than holding on either. It is one of the probes above, counted in the table there. The prepatch flag above records the defect this instance fixes as re-encoded among these probes; on this backend that is the same run at base, not a further check.

**Attacks re-run (6):** each is a standalone requirement probe rather than an alternative implementation: it runs on the gold-patched tree and exits 0 only if the behavior its cited requirement mandates holds there. The outcome after each arrow below is what that run recorded.

Attack 1 — `probe_1.py` → holds on the patched tree (good)

```python
from django.db.migrations.executor import MigrationExecutor

class Rec:
    def __init__(self): self.unapplied=[]
    def record_unapplied(self, app_label, name): self.unapplied.append((app_label,name))
    def record_applied(self, app_label, name): pass

class Mig:
    app_label="app"; name="0001_squash"; atomic=False
    replaces=[("app","0001"),("app","0002")]
    def unapply(self, state, se): return state

ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=None
ex.unapply_migration(None, Mig(), fake=True)
print("record_unapplied calls:", ex.recorder.unapplied)
own=("app","0001_squash")
ok = own in ex.recorder.unapplied
print("own identifier recorded:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 2 — `probe_2.py` → holds on the patched tree (good)

```python
from django.db.migrations.executor import MigrationExecutor
class Rec:
    def __init__(self): self.unapplied=[]
    def record_unapplied(self, a, n): self.unapplied.append((a,n))
    def record_applied(self, a, n): pass
class Mig:
    app_label="app"; name="0001_squash"; atomic=False
    replaces=[("app","0001"),("app","0002")]
    def unapply(self, state, se): return state
ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=None
ex.unapply_migration(None, Mig(), fake=True)
print("calls:", ex.recorder.unapplied)
need=[("app","0001"),("app","0002")]
ok=all(x in ex.recorder.unapplied for x in need)
print("all replaced identifiers recorded:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 3 — `probe_3.py` → holds on the patched tree (good)

```python
from django.db.migrations.executor import MigrationExecutor
class Rec:
    def __init__(self): self.unapplied=[]
    def record_unapplied(self, a, n): self.unapplied.append((a,n))
    def record_applied(self, a, n): pass
class Mig:
    app_label="app"; name="0005"; atomic=False
    replaces=[]   # ordinary
    def unapply(self, state, se): return state
ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=None
ex.unapply_migration(None, Mig(), fake=True)
print("calls:", ex.recorder.unapplied)
ok = ex.recorder.unapplied == [("app","0005")]
print("only own identifier recorded:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 4 — `probe_4.py` → holds on the patched tree (good)

```python
from django.db.migrations.executor import MigrationExecutor
class Rec:
    def __init__(self): self.unapplied=[]
    def record_unapplied(self, a, n): self.unapplied.append((a,n))
    def record_applied(self, a, n): pass
class Mig:
    app_label="app"; name="0001_squash"; atomic=False
    replaces=[("app","0001"),("app","0002"),("app","0003")]
    def unapply(self, state, se): return state
ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=None
ex.unapply_migration(None, Mig(), fake=True)
calls=ex.recorder.unapplied
print("calls:", calls)
own=("app","0001_squash")
cnt=calls.count(own)
own_idx=calls.index(own) if own in calls else -1
replaced_idx=[calls.index(x) for x in [("app","0001"),("app","0002"),("app","0003")] if x in calls]
ok = cnt==1 and own_idx!=-1 and len(replaced_idx)==3 and own_idx>max(replaced_idx)
print("own count:",cnt,"own_idx:",own_idx,"replaced_idx:",replaced_idx,"ok:",ok)
raise SystemExit(0 if ok else 1)
```

Attack 5 — `probe_5.py` → holds on the patched tree (good)

```python
from django.db.migrations.executor import MigrationExecutor
class Rec:
    def __init__(self): self.unapplied=[]
    def record_unapplied(self, a, n): self.unapplied.append((a,n))
    def record_applied(self, a, n): pass
class SE:
    def __enter__(self): return self
    def __exit__(self, *a): return False
class Conn:
    def schema_editor(self, atomic=True): return SE()
class Mig:
    app_label="app"; name="0001_squash"; atomic=False
    replaces=[("app","0001")]
    def unapply(self, state, se): return state
ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=Conn()
ex.unapply_migration(None, Mig(), fake=False)   # fake NOT set -> schema ops run
print("calls (fake=False):", ex.recorder.unapplied)
own=("app","0001_squash")
ok = own in ex.recorder.unapplied and ("app","0001") in ex.recorder.unapplied
print("own+replaced recorded regardless of fake:", ok)
raise SystemExit(0 if ok else 1)
```

Attack 6 — `probe_6.py` → holds on the patched tree (good)

```python
from django.db.migrations.executor import MigrationExecutor
class Rec:
    def __init__(self): self.applied=[]
    def record_applied(self, a, n): self.applied.append((a,n))
    def record_unapplied(self, a, n): pass
class Mig:
    def __init__(self, app, name, replaces):
        self.app_label=app; self.name=name; self.replaces=replaces; self.atomic=False
    def apply(self, state, se): return state
# replacement
ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=None
ex.apply_migration(None, Mig("app","0001_squash",[("app","0001"),("app","0002")]), fake=True)
repl=ex.recorder.applied
print("replacement apply calls:", repl)
# ordinary
ex2=object.__new__(MigrationExecutor)
ex2.recorder=Rec(); ex2.progress_callback=None; ex2.connection=None
ex2.apply_migration(None, Mig("app","0009",[]), fake=True)
ordn=ex2.recorder.applied
print("ordinary apply calls:", ordn)
ok = set(repl)=={("app","0001"),("app","0002")} and ("app","0001_squash") not in repl and ordn==[("app","0009")]
print("forward recording preserved:", ok)
raise SystemExit(0 if ok else 1)
```

**Positive control** (one of the probes above, and this role's discrimination witness: it holds on the gold-patched tree and FAILS at base, so the suite separates the two trees instead of holding on both): `probe_1.py`

```python
from django.db.migrations.executor import MigrationExecutor

class Rec:
    def __init__(self): self.unapplied=[]
    def record_unapplied(self, app_label, name): self.unapplied.append((app_label,name))
    def record_applied(self, app_label, name): pass

class Mig:
    app_label="app"; name="0001_squash"; atomic=False
    replaces=[("app","0001"),("app","0002")]
    def unapply(self, state, se): return state

ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=None
ex.unapply_migration(None, Mig(), fake=True)
print("record_unapplied calls:", ex.recorder.unapplied)
own=("app","0001_squash")
ok = own in ex.recorder.unapplied
print("own identifier recorded:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14500: gold fix makes unapply_migration record the migration's own identifier (app_label,name) as unapplied for ALL migrations, and for replacement migrations records the replaced identifiers too (previously an if/else recorded EITHER replaces OR own, so a rolled-back squash stayed in the applied set). Probes exercise MigrationExecutor.unapply_migration/apply_migration directly with stubbed recorder/connection (DB-free, robust across the image's django version), run in the official docker image.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/Req3, POSITIVE CONTROL): replacement + fake=True records own identifier. HOLDS patched, VIOLATED at base (base recorded only [0001,0002], no 0001_squash) => discriminates.
- probe_2 (Req1.2/1.4): replacement records every replaced identifier. HOLDS.
- probe_3 (Req2.1/2.2): ordinary (empty replaces) records ONLY its own identifier. HOLDS.
- probe_4 (Req1.5): every replaced recorded BEFORE own, own recorded exactly once. HOLDS.
- probe_5 (Req3.1/3.2): with fake=False (schema ops run via stub schema_editor), own+replaced still recorded. HOLDS.
- probe_6 (Req4.1/4.2): forward apply_migration unchanged — replacement records only its replaces (not own), ordinary records only own. HOLDS.

Candidate wrong-fixes (both REJECTED by the suite => discriminating):
- weak_order: records own BEFORE the replaces loop. Rejected by probe_4 (ordering, own_idx=0 < replaced) — passes 1,2,3,5,6.
- weak_partial: naive fix records ONLY own for every migration, dropping the replaced loop. Rejected by probe_2, probe_4, probe_5 — records neither replaced ids.

All 6 probes hold on patched; positive control fails at base and holds patched (prepatch_reproduced=true); >=1 candidate exercised and >=2 rejected. No requirements-conforming alternative found that would leave hidden tests unresolved. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 requirement probes hold on the patched tree; 2/2 weak-candidate(s) rejected by the probe suite; positive control discriminates base vs patched

**What was measured.** This backend has no verifier: the arbiter is a suite of executable probes, each a standalone script that encodes a behavior one cited requirement mandates and exits 0 only where the tree it runs against exhibits it. The harness re-ran 6 such probes against the gold-patched tree; a probe that FAILED there would mean the requirements mandate something the shipped patch does not do. The recorded outcomes were:

| probe outcome | probes | source |
| --- | ---: | --- |
| holds on the gold-patched tree, so the shipped patch exhibits the behavior that probe's cited requirement mandates | 6 | `probe_1.py`, `probe_2.py`, `probe_3.py`, `probe_4.py`, `probe_5.py`, `probe_6.py` |

**Discriminating power.** Probes that hold show conformance, not discriminating power, so the audit also submitted 2 alternative candidate patches, claimed to satisfy every cited requirement, and ran the same suite against them. The suite rejected all 2: a probe encoding a cited requirement fails under each of those, so the requirements as the probes read them exclude an implementation claimed to satisfy them. A candidate that conformed to every probe and yet did not resolve the instance would have shown the requirements admit an implementation that does not fix it, which is the refutation this half searches for; this role is recorded as passing only where none does.

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
from django.db.migrations.executor import MigrationExecutor

class Rec:
    def __init__(self): self.unapplied=[]
    def record_unapplied(self, app_label, name): self.unapplied.append((app_label,name))
    def record_applied(self, app_label, name): pass

class Mig:
    app_label="app"; name="0001_squash"; atomic=False
    replaces=[("app","0001"),("app","0002")]
    def unapply(self, state, se): return state

ex=object.__new__(MigrationExecutor)
ex.recorder=Rec(); ex.progress_callback=None; ex.connection=None
ex.unapply_migration(None, Mig(), fake=True)
print("record_unapplied calls:", ex.recorder.unapplied)
own=("app","0001_squash")
ok = own in ex.recorder.unapplied
print("own identifier recorded:", ok)
raise SystemExit(0 if ok else 1)
```

Prepatch bug re-encoded as an attack: `True`.

Instance django__django-14500: gold fix makes unapply_migration record the migration's own identifier (app_label,name) as unapplied for ALL migrations, and for replacement migrations records the replaced identifiers too (previously an if/else recorded EITHER replaces OR own, so a rolled-back squash stayed in the applied set). Probes exercise MigrationExecutor.unapply_migration/apply_migration directly with stubbed recorder/connection (DB-free, robust across the image's django version), run in the official docker image.

Probes (all HOLD on gold-patched tree):
- probe_1 (Req1.1/Req3, POSITIVE CONTROL): replacement + fake=True records own identifier. HOLDS patched, VIOLATED at base (base recorded only [0001,0002], no 0001_squash) => discriminates.
- probe_2 (Req1.2/1.4): replacement records every replaced identifier. HOLDS.
- probe_3 (Req2.1/2.2): ordinary (empty replaces) records ONLY its own identifier. HOLDS.
- probe_4 (Req1.5): every replaced recorded BEFORE own, own recorded exactly once. HOLDS.
- probe_5 (Req3.1/3.2): with fake=False (schema ops run via stub schema_editor), own+replaced still recorded. HOLDS.
- probe_6 (Req4.1/4.2): forward apply_migration unchanged — replacement records only its replaces (not own), ordinary records only own. HOLDS.

Candidate wrong-fixes (both REJECTED by the suite => discriminating):
- weak_order: records own BEFORE the replaces loop. Rejected by probe_4 (ordering, own_idx=0 < replaced) — passes 1,2,3,5,6.
- weak_partial: naive fix records ONLY own for every migration, dropping the replaced loop. Rejected by probe_2, probe_4, probe_5 — records neither replaced ids.

All 6 probes hold on patched; positive control fails at base and holds patched (prepatch_reproduced=true); >=1 candidate exercised and >=2 rejected. No requirements-conforming alternative found that would leave hidden tests unresolved. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Requirements pin the exact changed observable behavior — the boundary is the unconditional own-identifier record_unapplied after the replaces loop, which is precisely what the diff introduces (moving the call out of the else). Verified via inspect.getsource on both patched and base trees in the instance image. No wrong-boundary, over-strong, or invented behavior found.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Requirements describe unapply_migration behavior using only public/localizing identifiers (record_unapplied, migration.replaces, app_label/name) already implied by the problem_statement. No hidden-test artifacts leak: the F2P test name (test_migrate_marks_replacement_unapplied), the test file path (tests/migrations/test_executor.py), the migration module (migrations.test_migrations_squashed), and the parametrization id (0001_squashed_0002) never appear. No verbatim test or gold-patch code is quoted; no fix-invented identifiers (the gold patch invents none — it just removes an else branch). Requirement 5's 'replaced-before-own, exactly once' ordering matches the gold loop structure but is a behavioral/implementation spec, not a reconstruction of any test. Requirement 4.4 restates already-public 'squash from zero ignores replaced' behavior. Behavioral requirements are the intended translation, not a leak.


**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
