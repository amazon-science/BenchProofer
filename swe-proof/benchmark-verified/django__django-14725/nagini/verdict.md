# P2 adversarial audit — django__django-14725

Backend: `nagini`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

```diff
@@ -178,6 +178,6 @@
     if self.restrict_to_existing:
         result = persist_existing_objects(self, commit)
     else:
-        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
+        result = persist_new_objects(self, commit) + persist_existing_objects(self, commit)
     return result
     # impl-end
```

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,6 +176,7 @@
     # post-conditions-end
     # impl-start
     if self.restrict_to_existing:
+        _covert = persist_new_objects(self, commit)
         result = persist_existing_objects(self, commit)
     else:
         result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
```

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,9 +175,6 @@
                     self.get_new_runs() == Old(self.get_new_runs()) + 1))
     # post-conditions-end
     # impl-start
-    if self.restrict_to_existing:
-        result = persist_existing_objects(self, commit)
-    else:
-        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
+    result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
     return result
     # impl-end
```

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,7 +175,7 @@
                     self.get_new_runs() == Old(self.get_new_runs()) + 1))
     # post-conditions-end
     # impl-start
-    if self.restrict_to_existing:
+    if not self.restrict_to_existing:
         result = persist_existing_objects(self, commit)
     else:
         result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
```

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

```diff
@@ -175,9 +175,6 @@
                     self.get_new_runs() == Old(self.get_new_runs()) + 1))
     # post-conditions-end
     # impl-start
-    if self.restrict_to_existing:
-        result = persist_existing_objects(self, commit)
-    else:
-        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
+    result = persist_existing_objects(self, commit)
     return result
     # impl-end
```

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

```diff
@@ -176,8 +176,8 @@
     # post-conditions-end
     # impl-start
     if self.restrict_to_existing:
-        result = persist_existing_objects(self, commit)
+        result = persist_existing_objects(self, True)
     else:
-        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
+        result = persist_existing_objects(self, True) + persist_new_objects(self, True)
     return result
     # impl-end
```

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

```diff
@@ -177,7 +177,9 @@
     # impl-start
     if self.restrict_to_existing:
         result = persist_existing_objects(self, commit)
+    elif commit:
+        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
     else:
-        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
+        result = persist_existing_objects(self, commit)
     return result
     # impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14725.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection editor persists a batch of submitted forms and returns the list
  of records it persisted. It distinguishes two groups of records:

    * the records that already exist (drawn from the editor's bound set), and
    * the records that would be brought into existence from the remaining
      submitted forms.

  The editor carries a per-collection mode flag governing whether bringing new
  records into existence is permitted:

    (1) When the flag forbids new records, persisting returns ONLY the persisted
        already-existing records, in their order, and the new-record primitive
        is NEVER run — so no new record is brought into existence, regardless
        of how many new-record forms were submitted.

    (2) When the flag permits new records (the default), persisting returns the
        persisted already-existing records followed by the persisted new
        records, i.e. the concatenation of the two groups in that order, each
        primitive having run exactly once.

The editor is modelled as a minimal class carrying the touched field — the mode
flag (`restrict_to_existing: bool`) — plus, because persisting is an EFFECT
(each run of a primitive persists its whole group), one monotone invocation
count per primitive. The counts are held behind an abstraction predicate and
read only through pure accessors, so a count can advance ONLY by running its
primitive — it cannot be fabricated by writing the field directly. The two
unchanged persistence primitives are axiomatized: each reports a sequence of
record identifiers (carried as `PSeq[int]`) and advances its own count by
exactly one per run. The specification pins, per mode, both the returned
sequence AND the exact number of times each primitive ran, so an
implementation cannot run the new-record primitive for its effect while
discarding its report, nor run either primitive more often than once.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CollectionEditor:
    """Carries the mode flag and, behind an abstraction predicate, the two
    primitives' monotone invocation counts (observable but not directly
    writable by holders of the predicate)."""

    # pure-start
    @Predicate
    def run_counts_pred(self) -> bool:
        # Abstraction over the two primitives' invocation counts: a holder may
        # observe the counts (via the pure accessors below) but cannot write
        # them without going through the corresponding primitive, which is the
        # only operation permitted to advance its count.
        return Acc(self.existing_runs) and Acc(self.new_runs)

    @Pure
    def get_existing_runs(self) -> int:
        # Read the existing-group primitive's invocation count through the
        # abstraction (fractional, so the count can be observed in a
        # postcondition without granting the power to change it).
        Requires(Acc(self.run_counts_pred(), 1 / 2))
        return Unfolding(Acc(self.run_counts_pred(), 1 / 2), self.existing_runs)

    @Pure
    def get_new_runs(self) -> int:
        # Read the new-group primitive's invocation count through the
        # abstraction (fractional, read-only observation).
        Requires(Acc(self.run_counts_pred(), 1 / 2))
        return Unfolding(Acc(self.run_counts_pred(), 1 / 2), self.new_runs)
    # pure-end

    def __init__(self, restrict_to_existing: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.restrict_to_existing) and  # type: ignore
                self.restrict_to_existing == restrict_to_existing)  # type: ignore
        Ensures(self.run_counts_pred())  # type: ignore
        Ensures(self.get_existing_runs() == 0 and self.get_new_runs() == 0)  # type: ignore
        self.restrict_to_existing = restrict_to_existing
        self.existing_runs = 0  # type: int
        self.new_runs = 0  # type: int
        Fold(self.run_counts_pred())


# axioms-start
@Pure
@ContractOnly
def existing_report(commit: bool) -> PSeq[int]:
    """Identifiers reported by the unchanged primitive that persists the
    already-existing records of the collection, in order. It operates only on
    the bound (already-existing) records and never brings a new record into
    existence. Provenance + executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def new_report(commit: bool) -> PSeq[int]:
    """Identifiers reported by the unchanged primitive that persists the new
    records derived from the remaining submitted forms, in order — one per
    record it brings into existence (empty when none). Provenance + executable
    soundness: mapping.md / axiom_check.py.
    """


@ContractOnly
def persist_existing_objects(self: CollectionEditor, commit: bool) -> List[int]:
    """The unchanged callee that persists the already-existing records and
    returns them as a list; its content is exactly the reported sequence. Each
    run is an EFFECT: it advances the editor's existing-group invocation count
    by exactly one (and leaves the new-group count unchanged). It performs
    bounded work, so it promises termination to its callers."""
    Requires(MustTerminate(1))
    Requires(self.run_counts_pred())
    Ensures(self.run_counts_pred())
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()) + 1)
    Ensures(self.get_new_runs() == Old(self.get_new_runs()))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == existing_report(commit))


@ContractOnly
def persist_new_objects(self: CollectionEditor, commit: bool) -> List[int]:
    """The unchanged callee that persists the new records and returns them as a
    list; its content is exactly the reported sequence. Each run is an EFFECT:
    it brings the new group's records into existence and advances the editor's
    new-group invocation count by exactly one (leaving the existing-group count
    unchanged). It performs bounded work, so it promises termination to its
    callers."""
    Requires(MustTerminate(1))
    Requires(self.run_counts_pred())
    Ensures(self.run_counts_pred())
    Ensures(self.get_new_runs() == Old(self.get_new_runs()) + 1)
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == new_report(commit))
# axioms-end


def persist(self: CollectionEditor, commit: bool) -> List[int]:
    # pre-conditions-start
    # The mode flag is read-only for this operation: fractional permission,
    # required AND ensured, so the operation observes the flag without
    # altering it. The invocation counts ARE advanced -> full predicate.
    Requires(Acc(self.restrict_to_existing, 1 / 2))
    Requires(self.run_counts_pred())
    # Persisting is bounded work (at most one run of each primitive), so it
    # must TERMINATE: without this obligation the postconditions could be
    # discharged vacuously by a body that never returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.restrict_to_existing, 1 / 2))
    Ensures(self.run_counts_pred())
    Ensures(Acc(list_pred(Result())))
    # In BOTH modes the existing-group primitive runs exactly once (the counts
    # are observed through the abstraction, so these clauses are dischargeable
    # only by running the primitives, never by writing a count).
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()) + 1)
    # (1) When the flag forbids new records, the persisted list is EXACTLY the
    # already-existing group, in order — and the new-record primitive is NEVER
    # run, so no new record is brought into existence.
    Ensures(Implies(self.restrict_to_existing,
                    ToSeq(Result()) == existing_report(commit)))
    Ensures(Implies(self.restrict_to_existing,
                    self.get_new_runs() == Old(self.get_new_runs())))
    # (2) When the flag permits new records, the persisted list is the
    # already-existing group followed by the new group, in that order — the
    # new-record primitive having run exactly once.
    Ensures(Implies(not self.restrict_to_existing,
                    ToSeq(Result()) == existing_report(commit) + new_report(commit)))
    Ensures(Implies(not self.restrict_to_existing,
                    self.get_new_runs() == Old(self.get_new_runs()) + 1))
    # post-conditions-end
    # impl-start
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14725 (nagini). Ran ≥5 distinct same-spec wrong impls (impl region only; axioms/@Pure/Requires/Ensures byte-identical, confirmed by `same-spec` exit 0 for all 7). NO CANDIDATE emerged (every attack failed `weakness` with exit 2 = shares spec but does NOT verify), so no faithful refined patch needed materializing/resolving. Positive control (real model.py) verifies (nagini_verify.sh exit 0, 10.34s).

ENV: python, SBU_BENCHMARK_DIR=benchmark-verified, cwd.
CMD (per attack): python -m swebench_unified.adversary weakness nagini django__django-14725 <path>
Ran concurrently in 3 batches (≤3 JVMs at a time).

ATTACKS & OBSERVED WEAKNESS RESULTS (all same_spec=true, verifies=false → NOT-A-COUNTEREXAMPLE, exit 2):
- atk_1.py (control-flow-effect): default arm swaps order to new+existing. Rejected — violates clause (2) ToSeq(Result)==existing_report+new_report (PSeq concat is ordered).
- atk_2.py (ungrounded-oracle echo / covert effect): restrict arm runs persist_new_objects for its effect then discards report, returns existing. Rejected — clause (1e) get_new_runs()==Old(...) pins new_runs unchanged under restriction; the count advances via the primitive's contract, so the covert run is caught.
- atk_3.py (prepatch bug): always run both, ignore flag (== model_prepatch.py impl). Rejected — fails clause (1)/(1e) under restriction. prepatch_reproduced=true.
- atk_4.py (inverted flag / boundary): branch condition negated. Rejected — swaps the two modes' obligations, fails clause (1) and (2) counts.
- atk_5.py (boundary/partial): return existing only in both modes. Rejected — fails clause (2) content + (2e) new_runs+1 in default mode.
- atk_6.py (commit tampering): passes literal True to primitives instead of commit. Rejected — reports are existing_report(True)/new_report(True) != existing_report(commit)/new_report(commit); ToSeq equality fails.
- atk_7.py (partial-domain on commit): correct only when commit True; when commit False in default mode drops new group. Rejected — fails clause (2) content/(2e) count for commit=False.

REFINEMENT.MD LEG AUDIT (§4, A-legs focus): all legs are R / A-consumed / I — NO kind-3. A1(R bool↔bool), A2(I two-armed branch), A3(A-consumed persist_existing_objects↔save_existing_objects), A4(A-consumed+I: both primitives + concrete list `+`), A5(R instance-list↔List[int] identifiers), A6(R one invocation↔+1 count increment), B1(R factory plumbing↔restrict_to_existing field). A-legs' correspondence to real callees holds and is grounded by axiom_check.py: (i) inspect.getsource asserts neither save_existing_objects nor save_new_objects references edit_only (unchanged primitives); (iii) drives modelformset_factory/inlineformset_factory with edit_only=True/False through all FAIL_TO_PASS + default scenarios, asserting save()==existing under restriction (no rows created ↔ new_runs unchanged) and existing++new otherwise. The load-bearing discriminator (new-group primitive NEVER run under restriction) is pinned by the PAIRED content clause (1) AND effect clause (1e), with counts held behind abstraction predicate run_counts_pred advanceable only through the primitives' contracts — closing the covert-effect gap (verified by atk_2 rejection).

VERDICT: SOUND — spec is tight (per-mode content AND per-primitive invocation-count postconditions), rejected all 7 distinct wrong impls including the prepatch bug, positive control verifies, refinement legs are faithful. No verify⇏correct break found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.py`, `atk_2.py`, `atk_3.py`, `atk_4.py`, `atk_5.py`, `atk_6.py`, `atk_7.py` |

**Non-vacuity.** The positive control `positive_control.py` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.py` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.py` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.py` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.py` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.py` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.py` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.py` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.py`

```python
"""Twin-artifact model for django__django-14725.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A collection editor persists a batch of submitted forms and returns the list
  of records it persisted. It distinguishes two groups of records:

    * the records that already exist (drawn from the editor's bound set), and
    * the records that would be brought into existence from the remaining
      submitted forms.

  The editor carries a per-collection mode flag governing whether bringing new
  records into existence is permitted:

    (1) When the flag forbids new records, persisting returns ONLY the persisted
        already-existing records, in their order, and the new-record primitive
        is NEVER run — so no new record is brought into existence, regardless
        of how many new-record forms were submitted.

    (2) When the flag permits new records (the default), persisting returns the
        persisted already-existing records followed by the persisted new
        records, i.e. the concatenation of the two groups in that order, each
        primitive having run exactly once.

The editor is modelled as a minimal class carrying the touched field — the mode
flag (`restrict_to_existing: bool`) — plus, because persisting is an EFFECT
(each run of a primitive persists its whole group), one monotone invocation
count per primitive. The counts are held behind an abstraction predicate and
read only through pure accessors, so a count can advance ONLY by running its
primitive — it cannot be fabricated by writing the field directly. The two
unchanged persistence primitives are axiomatized: each reports a sequence of
record identifiers (carried as `PSeq[int]`) and advances its own count by
exactly one per run. The specification pins, per mode, both the returned
sequence AND the exact number of times each primitive ran, so an
implementation cannot run the new-record primitive for its effect while
discarding its report, nor run either primitive more often than once.

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *
from nagini_contracts.obligations import MustTerminate


class CollectionEditor:
    """Carries the mode flag and, behind an abstraction predicate, the two
    primitives' monotone invocation counts (observable but not directly
    writable by holders of the predicate)."""

    # pure-start
    @Predicate
    def run_counts_pred(self) -> bool:
        # Abstraction over the two primitives' invocation counts: a holder may
        # observe the counts (via the pure accessors below) but cannot write
        # them without going through the corresponding primitive, which is the
        # only operation permitted to advance its count.
        return Acc(self.existing_runs) and Acc(self.new_runs)

    @Pure
    def get_existing_runs(self) -> int:
        # Read the existing-group primitive's invocation count through the
        # abstraction (fractional, so the count can be observed in a
        # postcondition without granting the power to change it).
        Requires(Acc(self.run_counts_pred(), 1 / 2))
        return Unfolding(Acc(self.run_counts_pred(), 1 / 2), self.existing_runs)

    @Pure
    def get_new_runs(self) -> int:
        # Read the new-group primitive's invocation count through the
        # abstraction (fractional, read-only observation).
        Requires(Acc(self.run_counts_pred(), 1 / 2))
        return Unfolding(Acc(self.run_counts_pred(), 1 / 2), self.new_runs)
    # pure-end

    def __init__(self, restrict_to_existing: bool) -> None:
        Requires(MustTerminate(1))
        Ensures(Acc(self.restrict_to_existing) and  # type: ignore
                self.restrict_to_existing == restrict_to_existing)  # type: ignore
        Ensures(self.run_counts_pred())  # type: ignore
        Ensures(self.get_existing_runs() == 0 and self.get_new_runs() == 0)  # type: ignore
        self.restrict_to_existing = restrict_to_existing
        self.existing_runs = 0  # type: int
        self.new_runs = 0  # type: int
        Fold(self.run_counts_pred())


# axioms-start
@Pure
@ContractOnly
def existing_report(commit: bool) -> PSeq[int]:
    """Identifiers reported by the unchanged primitive that persists the
    already-existing records of the collection, in order. It operates only on
    the bound (already-existing) records and never brings a new record into
    existence. Provenance + executable soundness: mapping.md / axiom_check.py.
    """


@Pure
@ContractOnly
def new_report(commit: bool) -> PSeq[int]:
    """Identifiers reported by the unchanged primitive that persists the new
    records derived from the remaining submitted forms, in order — one per
    record it brings into existence (empty when none). Provenance + executable
    soundness: mapping.md / axiom_check.py.
    """


@ContractOnly
def persist_existing_objects(self: CollectionEditor, commit: bool) -> List[int]:
    """The unchanged callee that persists the already-existing records and
    returns them as a list; its content is exactly the reported sequence. Each
    run is an EFFECT: it advances the editor's existing-group invocation count
    by exactly one (and leaves the new-group count unchanged). It performs
    bounded work, so it promises termination to its callers."""
    Requires(MustTerminate(1))
    Requires(self.run_counts_pred())
    Ensures(self.run_counts_pred())
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()) + 1)
    Ensures(self.get_new_runs() == Old(self.get_new_runs()))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == existing_report(commit))


@ContractOnly
def persist_new_objects(self: CollectionEditor, commit: bool) -> List[int]:
    """The unchanged callee that persists the new records and returns them as a
    list; its content is exactly the reported sequence. Each run is an EFFECT:
    it brings the new group's records into existence and advances the editor's
    new-group invocation count by exactly one (leaving the existing-group count
    unchanged). It performs bounded work, so it promises termination to its
    callers."""
    Requires(MustTerminate(1))
    Requires(self.run_counts_pred())
    Ensures(self.run_counts_pred())
    Ensures(self.get_new_runs() == Old(self.get_new_runs()) + 1)
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()))
    Ensures(Acc(list_pred(Result())))
    Ensures(ToSeq(Result()) == new_report(commit))
# axioms-end


def persist(self: CollectionEditor, commit: bool) -> List[int]:
    # pre-conditions-start
    # The mode flag is read-only for this operation: fractional permission,
    # required AND ensured, so the operation observes the flag without
    # altering it. The invocation counts ARE advanced -> full predicate.
    Requires(Acc(self.restrict_to_existing, 1 / 2))
    Requires(self.run_counts_pred())
    # Persisting is bounded work (at most one run of each primitive), so it
    # must TERMINATE: without this obligation the postconditions could be
    # discharged vacuously by a body that never returns.
    Requires(MustTerminate(2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.restrict_to_existing, 1 / 2))
    Ensures(self.run_counts_pred())
    Ensures(Acc(list_pred(Result())))
    # In BOTH modes the existing-group primitive runs exactly once (the counts
    # are observed through the abstraction, so these clauses are dischargeable
    # only by running the primitives, never by writing a count).
    Ensures(self.get_existing_runs() == Old(self.get_existing_runs()) + 1)
    # (1) When the flag forbids new records, the persisted list is EXACTLY the
    # already-existing group, in order — and the new-record primitive is NEVER
    # run, so no new record is brought into existence.
    Ensures(Implies(self.restrict_to_existing,
                    ToSeq(Result()) == existing_report(commit)))
    Ensures(Implies(self.restrict_to_existing,
                    self.get_new_runs() == Old(self.get_new_runs())))
    # (2) When the flag permits new records, the persisted list is the
    # already-existing group followed by the new group, in that order — the
    # new-record primitive having run exactly once.
    Ensures(Implies(not self.restrict_to_existing,
                    ToSeq(Result()) == existing_report(commit) + new_report(commit)))
    Ensures(Implies(not self.restrict_to_existing,
                    self.get_new_runs() == Old(self.get_new_runs()) + 1))
    # post-conditions-end
    # impl-start
    if self.restrict_to_existing:
        result = persist_existing_objects(self, commit)
    else:
        result = persist_existing_objects(self, commit) + persist_new_objects(self, commit)
    return result
    # impl-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ refinement-fidelity audit for django__django-14725 (nagini). Ran ≥5 distinct same-spec wrong impls (impl region only; axioms/@Pure/Requires/Ensures byte-identical, confirmed by `same-spec` exit 0 for all 7). NO CANDIDATE emerged (every attack failed `weakness` with exit 2 = shares spec but does NOT verify), so no faithful refined patch needed materializing/resolving. Positive control (real model.py) verifies (nagini_verify.sh exit 0, 10.34s).

ENV: python, SBU_BENCHMARK_DIR=benchmark-verified, cwd.
CMD (per attack): python -m swebench_unified.adversary weakness nagini django__django-14725 <path>
Ran concurrently in 3 batches (≤3 JVMs at a time).

ATTACKS & OBSERVED WEAKNESS RESULTS (all same_spec=true, verifies=false → NOT-A-COUNTEREXAMPLE, exit 2):
- atk_1.py (control-flow-effect): default arm swaps order to new+existing. Rejected — violates clause (2) ToSeq(Result)==existing_report+new_report (PSeq concat is ordered).
- atk_2.py (ungrounded-oracle echo / covert effect): restrict arm runs persist_new_objects for its effect then discards report, returns existing. Rejected — clause (1e) get_new_runs()==Old(...) pins new_runs unchanged under restriction; the count advances via the primitive's contract, so the covert run is caught.
- atk_3.py (prepatch bug): always run both, ignore flag (== model_prepatch.py impl). Rejected — fails clause (1)/(1e) under restriction. prepatch_reproduced=true.
- atk_4.py (inverted flag / boundary): branch condition negated. Rejected — swaps the two modes' obligations, fails clause (1) and (2) counts.
- atk_5.py (boundary/partial): return existing only in both modes. Rejected — fails clause (2) content + (2e) new_runs+1 in default mode.
- atk_6.py (commit tampering): passes literal True to primitives instead of commit. Rejected — reports are existing_report(True)/new_report(True) != existing_report(commit)/new_report(commit); ToSeq equality fails.
- atk_7.py (partial-domain on commit): correct only when commit True; when commit False in default mode drops new group. Rejected — fails clause (2) content/(2e) count for commit=False.

REFINEMENT.MD LEG AUDIT (§4, A-legs focus): all legs are R / A-consumed / I — NO kind-3. A1(R bool↔bool), A2(I two-armed branch), A3(A-consumed persist_existing_objects↔save_existing_objects), A4(A-consumed+I: both primitives + concrete list `+`), A5(R instance-list↔List[int] identifiers), A6(R one invocation↔+1 count increment), B1(R factory plumbing↔restrict_to_existing field). A-legs' correspondence to real callees holds and is grounded by axiom_check.py: (i) inspect.getsource asserts neither save_existing_objects nor save_new_objects references edit_only (unchanged primitives); (iii) drives modelformset_factory/inlineformset_factory with edit_only=True/False through all FAIL_TO_PASS + default scenarios, asserting save()==existing under restriction (no rows created ↔ new_runs unchanged) and existing++new otherwise. The load-bearing discriminator (new-group primitive NEVER run under restriction) is pinned by the PAIRED content clause (1) AND effect clause (1e), with counts held behind abstraction predicate run_counts_pred advanceable only through the primitives' contracts — closing the covert-effect gap (verified by atk_2 rejection).

VERDICT: SOUND — spec is tight (per-mode content AND per-primitive invocation-count postconditions), rejected all 7 distinct wrong impls including the prepatch bug, positive control verifies, refinement legs are faithful. No verify⇏correct break found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness verdict: FAITHFUL (no divergence found). Instance django__django-14725 models the gold patch that adds an `edit_only` guard to BaseModelFormSet.save().

Spec integrity: the spec region (model.py lines 143-176) is byte-identical to model_prepatch.py (verified by diff and by swebench_unified.markers.same_spec / same-spec exit 0). The current model verifies with the pinned Nagini verifier (10.15 s, 'Verification successful'), and model_prepatch.py — which drops the branch and always concatenates both groups — correctly FAILS clause (1) `Implies(self.restrict_to_existing, ToSeq(Result()) == existing_report(commit))`. So the differential witness is real; the spec is not vacuous and not merely echoing the gold impl.

Modeled function vs real callee (BaseModelFormSet.save at base_commit 0af9a5fc):
- Return sequence: real save returns exactly `save_existing_objects(commit)` under edit_only, else `save_existing_objects(commit) + save_new_objects(commit)`. Model's content clauses (1)/(2) match under the instance<->identifier / list-`+`<->PSeq-`+` refinement (mapping.md §2; F2P tests compare by DB identity, faithfully abstracted).
- Invocation multiset: existing-group primitive runs exactly once in BOTH modes (unconditional clause `get_existing_runs()==Old+1`); new-group primitive never in restrict mode (clause 1e) and exactly once in default (clause 2e). Matches real save's call structure; the abstraction predicate makes counts advanceable only through the primitives, so these are not fabricated.
- Termination: both real primitives iterate bounded initial_forms/extra_forms; MustTerminate obligations are honorable, not too-strong.
- The `not commit` branch of real save additionally installs a save_m2m closure, but that alters neither the returned sequence nor the per-primitive invocation multiset — the only two observables the model pins — so abstracting it away is faithful (not drift).
- Opaqueness of existing_report/new_report and the unchanged-primitive claim are checked by G-AX/axiom_check.py against real Django (asserts neither primitive references edit_only and drives all FAIL_TO_PASS scenarios end-to-end), out of scope for this spec's strength.

I could not exhibit any input (restrict_to_existing True/False, any commit) where the modeled `persist` postconditions disagree with the real patched `save` under the stated refinement. The spec pins precisely the discriminating behaviour (whether the new-group primitive runs) and nothing the real callee does not exhibit. No too-strong clause and no drift found.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `model.py`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical screen (swebench_unified.leakage.screen for nagini) PASSES with zero hard failures. Gold edit adds `edit_only` flag gating BaseModelFormSet.save() (return save_existing_objects(commit) if edit_only else save_existing_objects(commit)+save_new_objects(commit)) plus edit_only=False plumbing in modelformset_factory/inlineformset_factory. Public problem_statement already discloses the full intent: 'Provide a way for model formsets to disallow new object creation' / 'edit only view of objects'. In the spec view every patched repo symbol is renamed/absent: edit_only->restrict_to_existing, save_existing_objects->persist_existing_objects/existing_report, save_new_objects->persist_new_objects/new_report, save->persist, BaseModelFormSet->CollectionEditor; the patched file path django/forms/models.py, module path, and factory names are all absent. No diff markers, no reproduced gold lines, no bug/fix narration. The behavior stated (a mode flag that forbids new records -> returns only existing; else existing followed by new) is exactly the 'edit only / disallow new object creation' behavior already public in problem_statement; the existing+new concatenation is the pre-existing unchanged behavior, not fix-specific localization. Nothing in the spec view enables reconstructing the gold edit beyond the public problem statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
