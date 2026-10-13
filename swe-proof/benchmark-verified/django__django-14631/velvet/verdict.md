# P2 adversarial audit — django__django-14631

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,8 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := slotValue f :: result
+      let v : Stamp := if f.readOnly then f.stored else f.given
+      result := v :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,7 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := slotValue f :: result
+      result := f.given :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,8 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := slotValue f :: result
+      let v : Stamp := if f.readOnly then f.given else initialFor f
+      result := v :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -69,7 +69,7 @@
   do
     -- impl-start
     let mut result : List Stamp := []
-    let mut i := fields.length
+    let mut i := fields.length - 1
     while i > 0
       invariant 0 ≤ i ∧ i ≤ fields.length
       invariant result = cleanedSeq (fields.drop i)
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -79,7 +79,7 @@
       let f := fields[i - 1]!
       result := slotValue f :: result
       i := i - 1
-    return result
+    return result.reverse
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the slot at `i-1`
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -77,7 +77,8 @@
       decreasing i
     do
       let f := fields[i - 1]!
-      result := slotValue f :: result
+      let v : Stamp := if f.readOnly then { sec := f.stored.sec, sub := f.stored.sub } else f.given
+      result := v :: result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -68,18 +68,7 @@
   ensures out = cleanedSeq fields
   do
     -- impl-start
-    let mut result : List Stamp := []
-    let mut i := fields.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ fields.length
-      invariant result = cleanedSeq (fields.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let f := fields[i - 1]!
-      result := slotValue f :: result
-      i := i - 1
-    return result
+    return cleanedSeq fields
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the slot at `i-1`
@@ -98,5 +87,3 @@
 
 prove_correct cleanFields by
   loom_solve
-  rw [cleanedSeq_drop_step fields i (by omega) (by omega)]
-  simp_all
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. The field-cleaning step on the
   modeled inputs is the identity on the resolved value (a stored timestamp fed
   to a per-field cleaner that returns it unchanged), so it is transliterated as
   an identity op (refinement.md, tag I) rather than axiomatized. The behaviour
   that actually changes — how a read-only slot's value is resolved — is modeled
   directly in the `pure` region below. -/
-- axioms-end

-- pure-start
/- A timestamp's observable components: a primary count and a finer sub-count.
   (Models the value a per-field cleaner produces; the finer sub-count is the
   part a coarse presentation cannot represent.) -/
structure Stamp where
  sec : Int
  sub : Int
deriving Inhabited, DecidableEq

/- A single field slot the cleaner walks over.
   * `readOnly` — the slot's value is held internally, not taken from supplied data.
   * `coarse`   — the slot's presentation cannot carry the finer sub-count, so
                  the resolved stored value drops it to 0 (standardized handling).
   * `stored`   — the slot's resolved stored value (evaluated once).
   * `given`    — the value supplied for the slot through ordinary data. -/
structure FieldSlot where
  readOnly : Bool
  coarse   : Bool
  stored   : Stamp
  given    : Stamp
deriving Inhabited, DecidableEq

/- The stored value as a slot actually exposes it: a coarse slot zeroes the
   finer sub-count; otherwise the stored value passes through unchanged. -/
def initialFor (f : FieldSlot) : Stamp :=
  if f.coarse then { f.stored with sub := 0 } else f.stored

/- The value used to clean one slot: a read-only slot uses its exposed stored
   value; any other slot uses the value supplied through data. -/
def slotValue (f : FieldSlot) : Stamp :=
  if f.readOnly then initialFor f else f.given

/- The per-slot cleaned values across the whole field list. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def cleanedSeq : List FieldSlot → List Stamp
  | []      => []
  | f :: fs => slotValue f :: cleanedSeq fs

@[grind] lemma cleanedSeq_nil : cleanedSeq [] = [] := rfl
@[grind] lemma cleanedSeq_cons (f : FieldSlot) (fs : List FieldSlot) :
    cleanedSeq (f :: fs) = slotValue f :: cleanedSeq fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method cleanFields (fields : List FieldSlot) return (out : List Stamp)
  ensures out = cleanedSeq fields
  do
    -- impl-start
    let mut result : List Stamp := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant result = cleanedSeq (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      result := slotValue f :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the slot at `i-1`
   on the front, so `cleanedSeq` peels one `slotValue`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma cleanedSeq_drop_step (fields : List FieldSlot) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    cleanedSeq (fields.drop (i - 1)) = slotValue fields[i - 1]! :: cleanedSeq (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, cleanedSeq_cons]

prove_correct cleanFields by
  loom_solve
  rw [cleanedSeq_drop_step fields i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition `ensures out = cleanedSeq fields` is an UNCONDITIONAL full functional equality that completely pins the output to the deep-modeled `cleanedSeq` (built from `slotValue`/`initialFor`). Any verifying impl must compute exactly that value; there is no room for a genuinely-wrong-but-verifying impl.

PROTOCOL: All files built by copying Solution.lean and editing ONLY the impl region (+ prove_correct body for the echo). same_spec(velvet)=True confirmed for all 8 attack/control files AND the shipped Solution_prepatch.lean. Verified via scripts/lean_verify.sh (cap 300s), run concurrently in two batches of 4.

### Attacks
- atk_1.lean (prepatch bug / control-flow: readOnly branch uses raw f.stored, dropping coarse `sub:=0` normalization) -> exit 1. Fails on discriminating goal `(if readOnly then stored else given) = slotValue f` (false on coarse read-only slot). This IS the prepatch defect; shipped prepatch.lean also same_spec=True and exit 1 => prepatch_reproduced=true.
- atk_2.lean (partial-domain: ignore readOnly, always f.given) -> exit 1.
- atk_3.lean (swapped branches: readOnly=>given, else=>initialFor) -> exit 1.
- atk_4.lean (boundary/off-by-one: i starts at fields.length-1, drops front slot) -> exit 1 (invariant init goal unsolved).
- atk_5.lean (control-flow-effect: correct fold then return result.reverse) -> exit 1 (`result.reverse = cleanedSeq fields`).
- atk_6.lean (boundary: readOnly uses reconstructed {sec,sub} keeping sub, ignoring coarse) -> exit 1, same discriminating goal as atk_1.
- atk_7.lean (ungrounded-oracle ECHO: `return cleanedSeq fields`, prove_correct = loom_solve) -> exit 0 VERIFIES.
- pos_control.lean (original impl) -> exit 0 VERIFIES.

MANDATORY RESOLVE OF VERIFYING WRONG-IMPL: The only verifying attack besides the positive control is atk_7 (echo of the spec's pinned output). Its faithful refined patch = the gold patch (echo returns exactly cleanedSeq fields, the spec's own output; faithful Python refinement is patch.diff verbatim). Materialized as atk_7.faithful.patch and RUN through the official harness:
  cmd: run_resolve('django__django-14631', <faithful patch>, run_id='sbu-audit-atk7-03rpbcad', timeout=1800, retries=1)
  RESULT: RESOLVED=True, NOTE='resolved'.
Per G-PANEL-1/G-EQ policy (the audit protocol), a same-spec verifying echo whose faithful patch RESOLVES is NOT a weakness. No verifying wrong impl produced a non-resolving faithful patch => spec is not BROKEN.

REFINEMENT.MD AUDIT (A-legs focus): axioms region EMPTY (no consumed axioms). Legs: A1=R (dict-order<->list-order), A2=R (Bool identity on disabled), A3=A-reference+I (initialFor == BoundField.initial microsecond-normalization #22502; the fold/if are I), A4=R (bf.data<->given), A5=I (field.clean identity on resolved datetime), B1/B2=I (behaviour-preserving companion refactors). No kind-3 (inexpressible-changed-op) legs. The single trust point is the A-reference `initialFor == BoundField.initial`, validated by G-AX (axiom_check.py exercises the REAL callee BoundField.initial on real Django forms over coarse DateTimeInput + microsecond-supporting TextInput, 6 boundary + 4000 fuzz timestamps, plus field.clean identity) — prior audit records PASS against base-commit worktree 84400d2e. The A-reference correspondence is genuine and matches the real callee. mapping.md bijection (Stamp<->datetime sec/microsecond, FieldSlot<->(name,BoundField)) is consistent. (Note: could not re-run axiom_check.py locally — this env has no importable real Django; G-AX runs in-container/worktree. R/I legs are G-CONF's domain, covered by G-CONF as noted in the task.)

CONCLUSION: 6 distinct genuinely-wrong impls (partial-domain, boundary/off-by-one, control-flow-effect, swapped-branch, coarse-ignoring) ALL fail to verify against the tight postcondition; the prepatch bug is reproduced; the only extra verifying impl is the echo, whose faithful patch RESOLVES. verify => correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No unchanged callee needs an axiom here. The field-cleaning step on the
   modeled inputs is the identity on the resolved value (a stored timestamp fed
   to a per-field cleaner that returns it unchanged), so it is transliterated as
   an identity op (refinement.md, tag I) rather than axiomatized. The behaviour
   that actually changes — how a read-only slot's value is resolved — is modeled
   directly in the `pure` region below. -/
-- axioms-end

-- pure-start
/- A timestamp's observable components: a primary count and a finer sub-count.
   (Models the value a per-field cleaner produces; the finer sub-count is the
   part a coarse presentation cannot represent.) -/
structure Stamp where
  sec : Int
  sub : Int
deriving Inhabited, DecidableEq

/- A single field slot the cleaner walks over.
   * `readOnly` — the slot's value is held internally, not taken from supplied data.
   * `coarse`   — the slot's presentation cannot carry the finer sub-count, so
                  the resolved stored value drops it to 0 (standardized handling).
   * `stored`   — the slot's resolved stored value (evaluated once).
   * `given`    — the value supplied for the slot through ordinary data. -/
structure FieldSlot where
  readOnly : Bool
  coarse   : Bool
  stored   : Stamp
  given    : Stamp
deriving Inhabited, DecidableEq

/- The stored value as a slot actually exposes it: a coarse slot zeroes the
   finer sub-count; otherwise the stored value passes through unchanged. -/
def initialFor (f : FieldSlot) : Stamp :=
  if f.coarse then { f.stored with sub := 0 } else f.stored

/- The value used to clean one slot: a read-only slot uses its exposed stored
   value; any other slot uses the value supplied through data. -/
def slotValue (f : FieldSlot) : Stamp :=
  if f.readOnly then initialFor f else f.given

/- The per-slot cleaned values across the whole field list. Front-recursive so a
   single unfold is available per loop step (the fold pattern, plan §5.4). -/
def cleanedSeq : List FieldSlot → List Stamp
  | []      => []
  | f :: fs => slotValue f :: cleanedSeq fs

@[grind] lemma cleanedSeq_nil : cleanedSeq [] = [] := rfl
@[grind] lemma cleanedSeq_cons (f : FieldSlot) (fs : List FieldSlot) :
    cleanedSeq (f :: fs) = slotValue f :: cleanedSeq fs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method cleanFields (fields : List FieldSlot) return (out : List Stamp)
  ensures out = cleanedSeq fields
  do
    -- impl-start
    let mut result : List Stamp := []
    let mut i := fields.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ fields.length
      invariant result = cleanedSeq (fields.drop i)
      done_with i = 0
      decreasing i
    do
      let f := fields[i - 1]!
      result := slotValue f :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the slot at `i-1`
   on the front, so `cleanedSeq` peels one `slotValue`. The single goal
   `loom_solve` leaves for the loop body. -/
lemma cleanedSeq_drop_step (fields : List FieldSlot) (i : Nat)
    (hi : 0 < i) (hle : i ≤ fields.length) :
    cleanedSeq (fields.drop (i - 1)) = slotValue fields[i - 1]! :: cleanedSeq (fields.drop i) := by
  have hlt : i - 1 < fields.length := by omega
  have hcons : fields.drop (i - 1) = fields[i - 1]! :: fields.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, cleanedSeq_cons]

prove_correct cleanFields by
  loom_solve
  rw [cleanedSeq_drop_step fields i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

VERDICT: SOUND. The frozen spec's postcondition `ensures out = cleanedSeq fields` is an UNCONDITIONAL full functional equality that completely pins the output to the deep-modeled `cleanedSeq` (built from `slotValue`/`initialFor`). Any verifying impl must compute exactly that value; there is no room for a genuinely-wrong-but-verifying impl.

PROTOCOL: All files built by copying Solution.lean and editing ONLY the impl region (+ prove_correct body for the echo). same_spec(velvet)=True confirmed for all 8 attack/control files AND the shipped Solution_prepatch.lean. Verified via scripts/lean_verify.sh (cap 300s), run concurrently in two batches of 4.

### Attacks
- atk_1.lean (prepatch bug / control-flow: readOnly branch uses raw f.stored, dropping coarse `sub:=0` normalization) -> exit 1. Fails on discriminating goal `(if readOnly then stored else given) = slotValue f` (false on coarse read-only slot). This IS the prepatch defect; shipped prepatch.lean also same_spec=True and exit 1 => prepatch_reproduced=true.
- atk_2.lean (partial-domain: ignore readOnly, always f.given) -> exit 1.
- atk_3.lean (swapped branches: readOnly=>given, else=>initialFor) -> exit 1.
- atk_4.lean (boundary/off-by-one: i starts at fields.length-1, drops front slot) -> exit 1 (invariant init goal unsolved).
- atk_5.lean (control-flow-effect: correct fold then return result.reverse) -> exit 1 (`result.reverse = cleanedSeq fields`).
- atk_6.lean (boundary: readOnly uses reconstructed {sec,sub} keeping sub, ignoring coarse) -> exit 1, same discriminating goal as atk_1.
- atk_7.lean (ungrounded-oracle ECHO: `return cleanedSeq fields`, prove_correct = loom_solve) -> exit 0 VERIFIES.
- pos_control.lean (original impl) -> exit 0 VERIFIES.

MANDATORY RESOLVE OF VERIFYING WRONG-IMPL: The only verifying attack besides the positive control is atk_7 (echo of the spec's pinned output). Its faithful refined patch = the gold patch (echo returns exactly cleanedSeq fields, the spec's own output; faithful Python refinement is patch.diff verbatim). Materialized as atk_7.faithful.patch and RUN through the official harness:
  cmd: run_resolve('django__django-14631', <faithful patch>, run_id='sbu-audit-atk7-03rpbcad', timeout=1800, retries=1)
  RESULT: RESOLVED=True, NOTE='resolved'.
Per G-PANEL-1/G-EQ policy (the audit protocol), a same-spec verifying echo whose faithful patch RESOLVES is NOT a weakness. No verifying wrong impl produced a non-resolving faithful patch => spec is not BROKEN.

REFINEMENT.MD AUDIT (A-legs focus): axioms region EMPTY (no consumed axioms). Legs: A1=R (dict-order<->list-order), A2=R (Bool identity on disabled), A3=A-reference+I (initialFor == BoundField.initial microsecond-normalization #22502; the fold/if are I), A4=R (bf.data<->given), A5=I (field.clean identity on resolved datetime), B1/B2=I (behaviour-preserving companion refactors). No kind-3 (inexpressible-changed-op) legs. The single trust point is the A-reference `initialFor == BoundField.initial`, validated by G-AX (axiom_check.py exercises the REAL callee BoundField.initial on real Django forms over coarse DateTimeInput + microsecond-supporting TextInput, 6 boundary + 4000 fuzz timestamps, plus field.clean identity) — prior audit records PASS against base-commit worktree 84400d2e. The A-reference correspondence is genuine and matches the real callee. mapping.md bijection (Stamp<->datetime sec/microsecond, FieldSlot<->(name,BoundField)) is consistent. (Note: could not re-run axiom_check.py locally — this env has no importable real Django; G-AX runs in-container/worktree. R/I legs are G-CONF's domain, covered by G-CONF as noted in the task.)

CONCLUSION: 6 distinct genuinely-wrong impls (partial-domain, boundary/off-by-one, control-flow-effect, swapped-branch, coarse-ignoring) ALL fail to verify against the tight postcondition; the prepatch bug is reproduced; the only extra verifying impl is the echo, whose faithful patch RESOLVES. verify => correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-14631 velvet.

SPEC INTEGRITY: same_spec(Solution.lean, Solution_prepatch.lean) = True under the velvet backend (impl region elided → identical spec views). Spec regions (axioms empty, pure: Stamp/FieldSlot/initialFor/slotValue/cleanedSeq, ensures out = cleanedSeq fields) are frozen and byte-identical. Solution.lean verifies (lean_verify exit 0, non-vacuous); Solution_prepatch.lean fails at exactly the coarse read-only slot (`if f.readOnly then f.stored` ≠ slotValue), so the spec is discriminating.

FAITHFULNESS vs REAL REPO (gold patch applied @ 84400d2e9d, BaseForm._clean_fields + BoundField.initial): the modeled function cleanedSeq was fuzzed against real Django cleaned_data.
  - disabled + coarse widget (default DateTimeInput, supports_microseconds=False): model initialFor drops microseconds; real BoundField.initial applies data.replace(microsecond=0) (#22502). 20k fuzz over sec∈[0,59],sub∈[0,999999]: 0 divergences.
  - disabled + micro-supporting widget (TextInput): model passes stored through; real matches. ✓
  - enabled path: model returns given; real returns clean(bf.data). ✓ (incl. arbitrary microseconds via %Y-%m-%d %H:%M:%S.%f, 20k fuzz, 0 divergences).
  - multi-slot ordered mixed form (disabled-coarse / enabled / disabled-noncoarse): element-wise equality, list/insertion order preserved. ✓
  The two audited legs hold empirically: initialFor == BoundField.initial, and field.clean is the identity on the resolved datetime (DateTimeField.to_python returns it unchanged).

WITHIN the declared abstraction domain (mapping.md: values are datetimes carried by Stamp{sec,sub}; date/non-datetime initials are out of domain), NO input was found where cleanedSeq disagrees with the real patched callee. The unconditional microsecond-zeroing of initialFor for coarse slots is only applied to datetime carriers, matching Django's isinstance(datetime/time) guard — no drift within domain.

OBSERVED WEAKNESS (not a faithfulness/too-strong defect): conformance_check.py's coverage note claims the enabled path 'carries no sub-second precision' and fuzzes enabled slots with sub=0. This is false — the default DATETIME_INPUT_FORMATS include '%Y-%m-%d %H:%M:%S.%f', which round-trips microseconds (verified). This is a G-CONF completeness/spec-too-WEAK coverage gap, not the spec asserting something the repo contradicts; it does not make the modeled function too strong. Out of scope for this gate; flagging for the record.

Conclusion: the modeled function does not disagree with the real callee on any in-domain input. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Consumer spec view (impl + prove_correct bodies elided) verified via swebench_unified.markers.spec_view for the velvet backend. All pass-through regions use abstract, backend-neutral vocabulary (Stamp/FieldSlot/readOnly/coarse/stored/given/initialFor/slotValue/cleanedSeq) and name NONE of the gold-patch identifiers (BoundField, bf.initial, _bound_items, field.disabled, _clean_fields, supports_microseconds, DateTimeField, microsecond, datetime). The abstract behavior modeled (a coarse read-only slot resolves to its normalized stored value with sub:=0) coincides with what the public problem_statement already discloses in the clear: that _clean_fields() should access values via BoundField and that form._clean_fields() should equal form[name].initial for disabled fields. Thus the spec view reveals nothing about the gold edit beyond problem_statement; the Django/patch specifics are confined to refinement.md/mapping.md (auditor docs, not the consumer spec view). same_spec(Solution, Solution_prepatch)=True (spec frozen; delta only in elided impl region). Lexical G-LEAK screen passes with zero hard_failures. Not a relaxed bundle. Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
