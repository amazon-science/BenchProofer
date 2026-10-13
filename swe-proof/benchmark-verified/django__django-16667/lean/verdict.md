# P2 adversarial audit — django__django-16667

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
   match c with
   | DateEntry.valid => return some rendered
   | DateEntry.malformed => return some (pseudoIso y m d)
-  | DateEntry.unrepresentable => return some "0-0-0"
+  | DateEntry.unrepresentable => return none
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,7 @@
 -- impl-start
 def implementation_coerceDateEntry
     (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
-  match c with
-  | DateEntry.valid => return some rendered
-  | DateEntry.malformed => return some (pseudoIso y m d)
-  | DateEntry.unrepresentable => return some "0-0-0"
+  return some rendered
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,8 +85,8 @@
     (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
   match c with
   | DateEntry.valid => return some rendered
-  | DateEntry.malformed => return some (pseudoIso y m d)
-  | DateEntry.unrepresentable => return some "0-0-0"
+  | DateEntry.malformed => return some "0-0-0"
+  | DateEntry.unrepresentable => return some (pseudoIso y m d)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -86,7 +86,7 @@
   match c with
   | DateEntry.valid => return some rendered
   | DateEntry.malformed => return some (pseudoIso y m d)
-  | DateEntry.unrepresentable => return some "0-0-0"
+  | DateEntry.unrepresentable => return some (pseudoIso y m d)
 -- impl-end
 
 -- proof-start
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -83,10 +83,7 @@
 -- impl-start
 def implementation_coerceDateEntry
     (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
-  match c with
-  | DateEntry.valid => return some rendered
-  | DateEntry.malformed => return some (pseudoIso y m d)
-  | DateEntry.unrepresentable => return some "0-0-0"
+  return some "0-0-0"
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,7 +85,7 @@
     (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
   match c with
   | DateEntry.valid => return some rendered
-  | DateEntry.malformed => return some (pseudoIso y m d)
+  | DateEntry.malformed => return some rendered
   | DateEntry.unrepresentable => return some "0-0-0"
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -84,7 +84,7 @@
 def implementation_coerceDateEntry
     (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
   match c with
-  | DateEntry.valid => return some rendered
+  | DateEntry.valid => return some "canonical"
   | DateEntry.malformed => return some (pseudoIso y m d)
   | DateEntry.unrepresentable => return some "0-0-0"
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Coercing a tripartite date entry into the string a date field will later parse.

A date entry collected from three separate components — a year, a month and a
day, each arriving as text — is reduced to a single textual value before any
field-level parsing happens. The reduction attempts to read the three components
as a calendar date. Three situations can arise from that attempt, and in EVERY
one of them the reduction must successfully hand on a value (it is total — it
never fails to produce an outcome):

  * the three components denote a representable calendar date — the value handed
    on is that date rendered in the field's canonical input format;
  * the three components are well-formed text but do NOT denote a representable
    calendar date (an impossible month or day, an out-of-range year, or
    non-numeric text) — the value handed on is a pseudo-ISO string built from the
    raw components, each empty component shown as a single zero
    (`"<y>-<m>-<d>"`, e.g. `"2017-0-23"`);
  * a component, though syntactically a number, is so large that it cannot be
    accommodated as a calendar component at all — the value handed on is the
    all-zero sentinel `"0-0-0"`.

A value being handed on is modeled as `some s`; the totality requirement is that
the outcome is `some …` in every situation (never `none`). The all-zero sentinel
is itself not a representable calendar date, so a field parsing it afterwards
rejects the entry as invalid rather than accepting it. The canonical rendering of
a representable date and the pseudo-ISO fallback for a non-representable-but-well-
formed entry are unchanged across all of this.
-/

-- axioms-start
-- No unchanged outside callee contract is consumed by this specification. The
-- classification of the entry (representable / well-formed-but-not-a-date /
-- out-of-range magnitude) and the canonical rendering of a representable date
-- are produced by surrounding machinery and enter this computation as arbitrary
-- inputs (`c`, `rendered`); this computation only dispatches on them. No
-- `opaque`/`axiom` callee declaration is therefore needed.
-- axioms-end

-- pure-start
/-- The outcome of attempting to read the three textual components as a calendar
date.
* `valid`          — the components denote a representable calendar date;
* `malformed`      — the components are well-formed text but do not denote a
                     representable calendar date;
* `unrepresentable`— a component's numeric magnitude is too large to be
                     accommodated as a calendar component. -/
inductive DateEntry where
  | valid
  | malformed
  | unrepresentable
  deriving DecidableEq, Repr

/-- The pseudo-ISO fallback `"<y>-<m>-<d>"`, where an empty component is shown as
a single `"0"` (modeling `"%s-%s-%s" % (y or 0, m or 0, d or 0)`). -/
def pseudoIso (y m d : String) : String :=
  (if y = "" then "0" else y) ++ "-" ++
  (if m = "" then "0" else m) ++ "-" ++
  (if d = "" then "0" else d)
-- pure-end

-- post-conditions-start
/-- The value handed on is pinned in every outcome (directive 5 frame: no case
left unconstrained). `c` is the entry classification; `rendered` is the canonical
rendering produced when the entry is a representable date; `y`/`m`/`d` are the raw
textual components. The result is modeled as `Option String`: `some s` means the
value `s` is handed on, `none` means no value is produced. The reduction is TOTAL
— a value is handed on in every situation: a representable date is rendered
canonically (`some rendered`); a well-formed but non-representable entry yields
the pseudo-ISO fallback (`some (pseudoIso y m d)`); an entry whose magnitude
cannot be accommodated yields the all-zero sentinel (`some "0-0-0"`). The
totality of the third case is the discriminating clause: the value must be
produced (not absent) AND equal `"0-0-0"`. -/
def problem_spec_coerceDateEntry
    (c : DateEntry) (rendered y m d : String) (result : Option String) : Prop :=
  (c = DateEntry.valid → result = some rendered) ∧
  (c = DateEntry.malformed → result = some (pseudoIso y m d)) ∧
  (c = DateEntry.unrepresentable → result = some "0-0-0")
-- post-conditions-end

-- impl-start
def implementation_coerceDateEntry
    (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
  match c with
  | DateEntry.valid => return some rendered
  | DateEntry.malformed => return some (pseudoIso y m d)
  | DateEntry.unrepresentable => return some "0-0-0"
-- impl-end

-- proof-start
theorem correct_coerceDateEntry :
    ∀ (c : DateEntry) (rendered y m d : String),
      problem_spec_coerceDateEntry c rendered y m d
        (implementation_coerceDateEntry c rendered y m d) := by
  intro c rendered y m d
  cases c <;>
    refine ⟨?_, ?_, ?_⟩ <;>
    intro h <;>
    simp_all [implementation_coerceDateEntry]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 same-spec wrong impls (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec/get_backend('lean')). All 7 FAIL to verify (lean_verify.sh exit 1, genuine 'unsolved goals' on the discriminating clauses); positive control (exact gold impl) verifies (exit 0) with clean axioms (#print axioms correct_coerceDateEntry => depends on axioms: [propext] only; no sorryAx/custom axiom). Because NO wrong impl closes with a clean-axiom proof, no faithful-patch resolve run was required (nothing to materialize).

Commands:
  same_spec: python -c 'from swebench_unified.markers import same_spec; ...' => atk_1..7 all True, pos_control True
  verify each: bash scripts/lean_verify.sh <file> (run concurrently, 4 at a time)

Results:
  atk_1 (prepatch bug: unrepresentable->none) exit=1, goal 'False' on unrepresentable.refine_3 => PREPATCH REPRODUCED (prepatch faithfully fails).
  atk_2 (partial-domain: always some rendered) exit=1, unsolved 'rendered = pseudoIso y m d', 'rendered = "0-0-0"'.
  atk_3 (boundary/branch swap: malformed<->unrepresentable outputs) exit=1.
  atk_4 (control-flow-effect: unrepresentable->pseudoIso y m d instead of sentinel) exit=1.
  atk_5 (ungrounded-oracle echo: collapse all to some "0-0-0") exit=1, unsolved '"0-0-0" = rendered', '"0-0-0" = pseudoIso y m d'.
  atk_6 (wrong fallback: malformed->rendered) exit=1.
  atk_7 (valid->fixed literal "canonical" instead of rendered) exit=1.
  pos_control exit=0.

Spec analysis: DateEntry has exactly {valid, malformed, unrepresentable}; problem_spec pins the output uniquely and totally in every case (some rendered / some (pseudoIso y m d) / some "0-0-0"), so the impl is fully forced with no free/underspecified region. Every deviation (drop totality, ignore classification, swap branches, wrong fallback, echo sentinel, literal for rendered) is caught.

refinement.md audit: 5 legs, tags R/R/R/I/R. axioms region empty (G-AX skips) => no A-consumed and no A-reference legs, hence no kind-3 leg. The single deep-model leg (#4, the added 'except OverflowError: return "0-0-0"' fix) is modeled as DateEntry.unrepresentable -> some "0-0-0", grounded in the real literal; correspondence to the changed callee/patch holds. Only I/R legs; A-leg correspondence obligation is vacuous here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Coercing a tripartite date entry into the string a date field will later parse.

A date entry collected from three separate components — a year, a month and a
day, each arriving as text — is reduced to a single textual value before any
field-level parsing happens. The reduction attempts to read the three components
as a calendar date. Three situations can arise from that attempt, and in EVERY
one of them the reduction must successfully hand on a value (it is total — it
never fails to produce an outcome):

  * the three components denote a representable calendar date — the value handed
    on is that date rendered in the field's canonical input format;
  * the three components are well-formed text but do NOT denote a representable
    calendar date (an impossible month or day, an out-of-range year, or
    non-numeric text) — the value handed on is a pseudo-ISO string built from the
    raw components, each empty component shown as a single zero
    (`"<y>-<m>-<d>"`, e.g. `"2017-0-23"`);
  * a component, though syntactically a number, is so large that it cannot be
    accommodated as a calendar component at all — the value handed on is the
    all-zero sentinel `"0-0-0"`.

A value being handed on is modeled as `some s`; the totality requirement is that
the outcome is `some …` in every situation (never `none`). The all-zero sentinel
is itself not a representable calendar date, so a field parsing it afterwards
rejects the entry as invalid rather than accepting it. The canonical rendering of
a representable date and the pseudo-ISO fallback for a non-representable-but-well-
formed entry are unchanged across all of this.
-/

-- axioms-start
-- No unchanged outside callee contract is consumed by this specification. The
-- classification of the entry (representable / well-formed-but-not-a-date /
-- out-of-range magnitude) and the canonical rendering of a representable date
-- are produced by surrounding machinery and enter this computation as arbitrary
-- inputs (`c`, `rendered`); this computation only dispatches on them. No
-- `opaque`/`axiom` callee declaration is therefore needed.
-- axioms-end

-- pure-start
/-- The outcome of attempting to read the three textual components as a calendar
date.
* `valid`          — the components denote a representable calendar date;
* `malformed`      — the components are well-formed text but do not denote a
                     representable calendar date;
* `unrepresentable`— a component's numeric magnitude is too large to be
                     accommodated as a calendar component. -/
inductive DateEntry where
  | valid
  | malformed
  | unrepresentable
  deriving DecidableEq, Repr

/-- The pseudo-ISO fallback `"<y>-<m>-<d>"`, where an empty component is shown as
a single `"0"` (modeling `"%s-%s-%s" % (y or 0, m or 0, d or 0)`). -/
def pseudoIso (y m d : String) : String :=
  (if y = "" then "0" else y) ++ "-" ++
  (if m = "" then "0" else m) ++ "-" ++
  (if d = "" then "0" else d)
-- pure-end

-- post-conditions-start
/-- The value handed on is pinned in every outcome (directive 5 frame: no case
left unconstrained). `c` is the entry classification; `rendered` is the canonical
rendering produced when the entry is a representable date; `y`/`m`/`d` are the raw
textual components. The result is modeled as `Option String`: `some s` means the
value `s` is handed on, `none` means no value is produced. The reduction is TOTAL
— a value is handed on in every situation: a representable date is rendered
canonically (`some rendered`); a well-formed but non-representable entry yields
the pseudo-ISO fallback (`some (pseudoIso y m d)`); an entry whose magnitude
cannot be accommodated yields the all-zero sentinel (`some "0-0-0"`). The
totality of the third case is the discriminating clause: the value must be
produced (not absent) AND equal `"0-0-0"`. -/
def problem_spec_coerceDateEntry
    (c : DateEntry) (rendered y m d : String) (result : Option String) : Prop :=
  (c = DateEntry.valid → result = some rendered) ∧
  (c = DateEntry.malformed → result = some (pseudoIso y m d)) ∧
  (c = DateEntry.unrepresentable → result = some "0-0-0")
-- post-conditions-end

-- impl-start
def implementation_coerceDateEntry
    (c : DateEntry) (rendered y m d : String) : Option String := Id.run do
  match c with
  | DateEntry.valid => return some rendered
  | DateEntry.malformed => return some (pseudoIso y m d)
  | DateEntry.unrepresentable => return some "0-0-0"
-- impl-end

-- proof-start
theorem correct_coerceDateEntry :
    ∀ (c : DateEntry) (rendered y m d : String),
      problem_spec_coerceDateEntry c rendered y m d
        (implementation_coerceDateEntry c rendered y m d) := by
  intro c rendered y m d
  cases c <;>
    refine ⟨?_, ?_, ?_⟩ <;>
    intro h <;>
    simp_all [implementation_coerceDateEntry]
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. 7 same-spec wrong impls (all same_spec=True vs Solution.lean, verified via swebench_unified.markers.same_spec/get_backend('lean')). All 7 FAIL to verify (lean_verify.sh exit 1, genuine 'unsolved goals' on the discriminating clauses); positive control (exact gold impl) verifies (exit 0) with clean axioms (#print axioms correct_coerceDateEntry => depends on axioms: [propext] only; no sorryAx/custom axiom). Because NO wrong impl closes with a clean-axiom proof, no faithful-patch resolve run was required (nothing to materialize).

Commands:
  same_spec: python -c 'from swebench_unified.markers import same_spec; ...' => atk_1..7 all True, pos_control True
  verify each: bash scripts/lean_verify.sh <file> (run concurrently, 4 at a time)

Results:
  atk_1 (prepatch bug: unrepresentable->none) exit=1, goal 'False' on unrepresentable.refine_3 => PREPATCH REPRODUCED (prepatch faithfully fails).
  atk_2 (partial-domain: always some rendered) exit=1, unsolved 'rendered = pseudoIso y m d', 'rendered = "0-0-0"'.
  atk_3 (boundary/branch swap: malformed<->unrepresentable outputs) exit=1.
  atk_4 (control-flow-effect: unrepresentable->pseudoIso y m d instead of sentinel) exit=1.
  atk_5 (ungrounded-oracle echo: collapse all to some "0-0-0") exit=1, unsolved '"0-0-0" = rendered', '"0-0-0" = pseudoIso y m d'.
  atk_6 (wrong fallback: malformed->rendered) exit=1.
  atk_7 (valid->fixed literal "canonical" instead of rendered) exit=1.
  pos_control exit=0.

Spec analysis: DateEntry has exactly {valid, malformed, unrepresentable}; problem_spec pins the output uniquely and totally in every case (some rendered / some (pseudoIso y m d) / some "0-0-0"), so the impl is fully forced with no free/underspecified region. Every deviation (drop totality, ignore classification, swap branches, wrong fallback, echo sentinel, literal for rendered) is caught.

refinement.md audit: 5 legs, tags R/R/R/I/R. axioms region empty (G-AX skips) => no A-consumed and no A-reference legs, hence no kind-3 leg. The single deep-model leg (#4, the added 'except OverflowError: return "0-0-0"' fix) is modeled as DateEntry.unrepresentable -> some "0-0-0", grounded in the real literal; correspondence to the changed callee/patch holds. Only I/R legs; A-leg correspondence obligation is vacuous here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attacker: found NO input where the modeled function disagrees with the real post-patch callee; verdict FAITHFUL (spec is not too strong / does not drift).

Modeled function = date-coercion try/except block in SelectDateWidget.value_from_datadict (widgets.py:1158-1164, post-patch, patch.diff adds `except OverflowError: return "0-0-0"`).

Evidence:
1. same_spec(Solution.lean, Solution_prepatch.lean)=True (LeanBackend.language tables): the post-conditions/pure/axioms regions are byte-identical across patched and prepatch. Spec is fixed, not tuned to the impl.
2. lean_verify.sh exit 0; `#print axioms correct_coerceDateEntry` = [propext] only — no sorryAx, proof is real.
3. Model faithfully mirrors the three real outcomes: valid -> some rendered (=strftime); ValueError -> some (pseudoIso y m d) where pseudoIso (empty->"0", else verbatim, joined by '-') exactly reproduces Python `"%s-%s-%s" % (y or 0, m or 0, d or 0)` string truthiness; OverflowError -> some "0-0-0".
4. Trichotomy exhaustive: brute-forced 35,937 string triples (empties, non-numeric, whitespace, unicode digit, negatives, str(sys.maxsize+1), 5000-digit ints) — the real block raises ONLY ValueError/OverflowError, never a third exception type. So the Option String result is `some ...` in every reachable case, matching post-patch totality; the third-conjunct totality clause (unrepresentable -> some "0-0-0") is not too strong.
5. G-CONF conformance_check.py passes: 120,016 differential checks (16 edges + 120k fuzz, seed 16667), 0 disagreements between R/I shadow and in-process replica of the patched block. Note: huge-digit strings hit Python's int-string digit limit and classify as `malformed` in BOTH the oracle and shadow legs, so they agree — not a divergence.

No diverging input exists; spec matches real repo behavior at the modeled boundary.


**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.
## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Bundle: django__django-16667/lean. Gold edit = `except OverflowError: return "0-0-0"` in SelectDateWidget.value_from_datadict (widgets.py).

Mechanical G-LEAK screen: PASS (leakage.screen over spec view, lean backend) — hard_failures=[], warnings=[]. No diff markers, no patched file path (widgets.py), no patched symbol (value_from_datadict / SelectDateWidget), no bug/fix narration tokens in the spec view.

Spec integrity: same_spec(Solution.lean, Solution_prepatch.lean, lean)=True — spec region is byte-identical (spec-signature equal), so the consumer spec view is fixed and untampered. Not a relaxed bundle (relaxed_leakage=None, no RELAXED_LEAKAGE.md); meta records G-LEAK=pass.

Semantic gold-reconstruction judgment: The public problem_statement already fully discloses the bug — it names OverflowError by name, states y/m/d are user-controlled, and that magnitudes > sys.maxsize crash datetime.date(int(y),int(m),int(d)). The only thing beyond that in the spec view is the SPECIFIED CORRECT OUTPUT for the too-large-magnitude case: the all-zero sentinel "0-0-0". Pinning the intended output is intrinsic to any functional spec (a spec that failed to constrain the output would be a G-PANEL weakness, not a leak) and is not equivalent to revealing the gold edit's location/syntax. The spec view is fully abstracted from the patch form: no `except`, no `OverflowError`, no `datetime.date`, no Python, no file path, no diff. The solver must still supply the implementation and proof. Nothing localizes the edit to a file/symbol/exception-handler beyond what problem_statement already says, and nothing trivializes reconstruction beyond the public statement.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
