# P2 adversarial audit — django__django-12143

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so no faithful refined patch could be materialized/resolve-run. The postcondition is an EXACT functional equality `out = editedPks pfx pkname items` under `loom.semantics.termination "total"`, and the `prove_correct` proof block is FROZEN OUTSIDE the editable impl region. Any impl that verifies must therefore be behaviorally identical to editedPks on the whole input domain, so its faithful patch is the gold behavior and resolves. verify⇒correct holds here.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,7 +137,9 @@
       decreasing i
     do
       let kv := items[i - 1]!
-      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
+      let matched : Bool :=
+        if pfx.contains '$' then false else matchesKey pfx pkname kv.1
+      result := (if matched then [kv.2] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -136,8 +136,7 @@
       done_with i = 0
       decreasing i
     do
-      let kv := items[i - 1]!
-      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
+      let _kv := items[i - 1]!
       i := i - 1
     return result
     -- impl-end
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,7 +130,7 @@
     -- impl-start
     let mut result : List (List Char) := []
     let mut i := items.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ items.length
       invariant result = editedPks pfx pkname (items.drop i)
       done_with i = 0
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,7 +137,7 @@
       decreasing i
     do
       let kv := items[i - 1]!
-      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
+      result := result ++ (if matchesKey pfx pkname kv.1 then [kv.2] else [])
       i := i - 1
     return result
     -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,18 +128,7 @@
   ensures out = editedPks pfx pkname items
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := items.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ items.length
-      invariant result = editedPks pfx pkname (items.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let kv := items[i - 1]!
-      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
-      i := i - 1
-    return result
+    return editedPks pfx pkname items
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the item at
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,7 +137,7 @@
       decreasing i
     do
       let kv := items[i - 1]!
-      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
+      result := [kv.2] ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -137,7 +137,7 @@
       decreasing i
     do
       let kv := items[i - 1]!
-      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
+      result := (if matchesKey pfx pkname kv.1 then [kv.1] else []) ++ result
       i := i - 1
     return result
     -- impl-end
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -128,18 +128,7 @@
   ensures out = editedPks pfx pkname items
   do
     -- impl-start
-    let mut result : List (List Char) := []
-    let mut i := items.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ items.length
-      invariant result = editedPks pfx pkname (items.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let kv := items[i - 1]!
-      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
-      i := i - 1
-    return result
+    return items.filterMap (fun kv => if matchesKey pfx pkname kv.1 then some kv.2 else none)
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the item at
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real selection over the request items always
   terminates (it is a single pass over a finite items list), so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the key-matching decision and the selection over the
--  request items are modeled deeply — see the `pure` region. The matcher's
--  fidelity to the real engine is checked mechanically by G-CONF, so there is
--  no opaque callee to over-approximate here.)
-- axioms-end

-- pure-start
/- The decimal-digit code points the key matcher's digit class accepts: the
   digits of every decimal number system (Unicode general category Nd, per the
   Unicode data the modeled engine ships), as inclusive (lo, hi) scalar-value
   bounds. The matcher's digit class is Unicode-aware, not restricted to the
   Latin digits. -/
def digitRanges : List (Nat × Nat) :=
  [ (0x30, 0x39), (0x660, 0x669), (0x6f0, 0x6f9), (0x7c0, 0x7c9),
    (0x966, 0x96f), (0x9e6, 0x9ef), (0xa66, 0xa6f), (0xae6, 0xaef),
    (0xb66, 0xb6f), (0xbe6, 0xbef), (0xc66, 0xc6f), (0xce6, 0xcef),
    (0xd66, 0xd6f), (0xde6, 0xdef), (0xe50, 0xe59), (0xed0, 0xed9),
    (0xf20, 0xf29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17e0, 0x17e9),
    (0x1810, 0x1819), (0x1946, 0x194f), (0x19d0, 0x19d9), (0x1a80, 0x1a89),
    (0x1a90, 0x1a99), (0x1b50, 0x1b59), (0x1bb0, 0x1bb9), (0x1c40, 0x1c49),
    (0x1c50, 0x1c59), (0xa620, 0xa629), (0xa8d0, 0xa8d9), (0xa900, 0xa909),
    (0xa9d0, 0xa9d9), (0xa9f0, 0xa9f9), (0xaa50, 0xaa59), (0xabf0, 0xabf9),
    (0xff10, 0xff19), (0x104a0, 0x104a9), (0x11066, 0x1106f),
    (0x110f0, 0x110f9), (0x11136, 0x1113f), (0x111d0, 0x111d9),
    (0x112f0, 0x112f9), (0x11450, 0x11459), (0x114d0, 0x114d9),
    (0x11650, 0x11659), (0x116c0, 0x116c9), (0x11730, 0x11739),
    (0x118e0, 0x118e9), (0x11c50, 0x11c59), (0x16a60, 0x16a69),
    (0x16b50, 0x16b59), (0x1d7ce, 0x1d7ff), (0x1e950, 0x1e959) ]

/- Whether a single code point is a decimal digit: a member of one of the
   decimal-digit runs above (any decimal number system's digits, not only
   '0'..'9'). -/
def isDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/- If `pat` is exactly the leading segment of `s`, return the trailing segment
   that follows it; otherwise report that `s` does not begin with `pat`. The
   comparison is code-point by code-point, so `pat` is matched as the exact
   sequence of characters it is — never as a pattern with distinguished
   characters. -/
def stripPrefix : List Char → List Char → Option (List Char)
  | [],      ys      => some ys
  | _ :: _,  []      => none
  | x :: xs, y :: ys => if x = y then stripPrefix xs ys else none

/- Split off the maximal leading run of decimal digits, returning the run and
   the remainder that follows it. -/
def takeDigits : List Char → (List Char × List Char)
  | []      => ([], [])
  | c :: cs =>
      if isDigit c then
        let p := takeDigits cs
        (c :: p.1, p.2)
      else ([], c :: cs)

/- The end-of-input position: nothing left, or a single trailing line
   terminator (the trailing-newline tolerance of the end-of-input position). -/
def atEnd (cs : List Char) : Bool := cs.isEmpty || cs == ['\n']

/- Whether a request key names one of the edited objects under `pfx`/`pkname`:
   the key must decompose as the exact characters of `pfx`, a separator '-', a
   nonempty run of decimal digits, a separator '-', and the exact characters of
   the identifier name `pkname`, ending the key (the trailing-newline tolerance
   aside). The prefix and the identifier name are matched as exact character
   sequences. -/
def matchesKey (pfx pkname key : List Char) : Bool :=
  match stripPrefix pfx key with
  | none    => false
  | some r1 =>
    match r1 with
    | '-' :: r2 =>
        let dp := takeDigits r2
        !dp.1.isEmpty &&
          (match dp.2 with
           | '-' :: r3 =>
               (match stripPrefix pkname r3 with
                | some tail => atEnd tail
                | none      => false)
           | _ => false)
    | _ => false

/- The selection over the request items (key, value pairs): keep the value of
   every item whose key matches. Front-recursive so a single unfold is available
   per loop step (the fold pattern). -/
def editedPks (pfx pkname : List Char) :
    List (List Char × List Char) → List (List Char)
  | []        => []
  | kv :: rest =>
      if matchesKey pfx pkname kv.1 then kv.2 :: editedPks pfx pkname rest
      else editedPks pfx pkname rest

@[grind] lemma editedPks_nil (pfx pkname : List Char) :
    editedPks pfx pkname [] = [] := rfl

@[grind] lemma editedPks_cons (pfx pkname : List Char)
    (kv : List Char × List Char) (rest : List (List Char × List Char)) :
    editedPks pfx pkname (kv :: rest)
      = (if matchesKey pfx pkname kv.1 then [kv.2] else [])
        ++ editedPks pfx pkname rest := by
  show (if matchesKey pfx pkname kv.1 then kv.2 :: editedPks pfx pkname rest
        else editedPks pfx pkname rest) = _
  split <;> rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The values of the request items whose key identifies an edited object under
   the given prefix and identifier name: the per-item selection over the items
   in order. -/
method editedObjectPks (pfx : List Char) (pkname : List Char) (items : List (List Char × List Char)) return (out : List (List Char))
  ensures out = editedPks pfx pkname items
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = editedPks pfx pkname (items.drop i)
      done_with i = 0
      decreasing i
    do
      let kv := items[i - 1]!
      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the item at
   `i-1` on the front, so `editedPks` peels one selection. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma editedPks_drop_step (pfx pkname : List Char)
    (items : List (List Char × List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ items.length) :
    editedPks pfx pkname (items.drop (i - 1))
      = (if matchesKey pfx pkname (items[i - 1]!).1 then [(items[i - 1]!).2] else [])
        ++ editedPks pfx pkname (items.drop i) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, editedPks_cons]

prove_correct editedObjectPks by
  loom_solve
  rw [editedPks_drop_step pfx pkname items i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

elan on PATH, PY=python, PYTHONPATH=src.

SPEC PIN (why hard to break): postcondition `ensures out = editedPks pfx pkname items` is an exact functional equality; `set_option loom.semantics.termination "total"` (rejects diverging impls, not vacuous); AND the entire `prove_correct editedObjectPks by loom_solve; rw [editedPks_drop_step ...]; simp_all` block sits OUTSIDE `-- impl-start/-- impl-end`, so it is byte-frozen and loom_solve's VC is tailored to the backward `while` fold. Editing only the impl must still discharge that exact frozen proof against the exact-equality post.

POSITIVE CONTROL: pos_control.lean = verbatim Solution.lean. Command: `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0 (verifies, no sorry). Same_spec vs Solution.lean = True.

SAME_SPEC: all 8 attacks checked via swebench_unified.markers.same_spec (velvet lang) => True for every one (impl region only edited).

### ATTACKS (all verified concurrently, <=4 background jobs; `bash scripts/lean_verify.sh .../atk_N.lean`):
  atk_1 (prepatch bug re-encode: `if pfx.contains '$' then false else matchesKey ...` -> drops $-bearing prefixes) : exit 1, `unsolved goals` at proof rw/simp_all (164:30). FAILS verify.
  atk_2 (partial-domain / empty: always return []) : exit 1, unsolved goals (161:30). FAILS.
  atk_3 (boundary/off-by-one: `while i > 1`, skips first item) : exit 1, unsolved goals (162:30). FAILS.
  atk_4 (control-flow-effect: reversed accumulation `result ++ [kv.2]`) : exit 1, unsolved goals (162:30). FAILS.
  atk_5 (ungrounded-oracle echo: `return editedPks pfx pkname items`, no loop) : exit 1, `No goals to be solved` (153:6) -- behaviorally CORRECT but cannot satisfy the frozen loop-tailored proof (correct-but-unverifiable false negative; does NOT break spec).
  atk_6 (matcher-weakening: keep every value, ignore matchesKey) : exit 1, unsolved goals (162:30). FAILS.
  atk_7 (wrong projection: emit kv.1 key instead of kv.2 value) : exit 1, unsolved goals (162:30). FAILS.
  atk_8 (forward reformulation: `items.filterMap ...`) : exit 1, frozen proof references `i` -> unknown identifier + unsolved goals (151/153) -- behaviorally CORRECT but frozen proof assumes the loop shape (false negative; does NOT break spec).

NO wrong impl VERIFIES => protocol step 2 (materialize+resolve faithful patch) is VACUOUS: there is no verifying-wrong-impl to resolve. patches={} accordingly. (Reported honestly, not skipped: a resolve run is only mandated for a verifying wrong impl; none exists.)

PREPATCH: shipped Solution_prepatch.lean copied to prepatch.lean, verified -> exit 1, unsolved goals (172:30). Prepatch bug reproduced (fails G-DIFF) as claimed. prepatch_reproduced=true.

REFINEMENT.MD LEG AUDIT (step 3): NO A-tagged (axiom/callee) legs -- bundle has no axioms (axiom_check.py is explicit no-op). Legs: A1/A2/A3/A6 = R (str<->List Char, order-preserving items, list result); A4 = I (comprehension = editedPks front-recursive selection); A5 = I (deep model) -- the changed op (re.escape literal match) modeled deeply as stripPrefix/takeDigits/atEnd, NOT behind an axiom. NO kind-3 (inexpressible) legs. Correspondence AUDITED: re-implemented the deep model (matchesKey/stripPrefix/takeDigits/atEnd/digitRanges) in Python and differentially compared to the REAL patched regex `re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkname))` on 16 discriminating cases: metachar prefixes ($, ., +, parens), empty prefix, trailing single \n (match) vs double \n (no match), Arabic-Indic digits U+0660s (match), superscript-2 non-Nd (no match), empty digit run, non-anchored key, trailing junk. Result: 0/16 mismatches. B2 (total-correctness repair) and B3 (Unicode \d digit-class repair) both independently corroborated by these cases.

CONCLUSION: verify=>correct holds on this bundle. Exact-equality post + total correctness + frozen loop-tailored proof leave no room for a verifying wrong impl; the only impls that fail-to-verify while being correct (atk_5, atk_8) are FALSE NEGATIVES (correct-but-unverifiable), which strengthen rather than break the spec. Deep-model<->real-regex correspondence holds on all discriminating inputs. >=5 distinct attack classes exercised (prepatch, partial-domain, boundary, control-flow-effect, matcher-weakening, wrong-projection, ungrounded-oracle echo, forward-reformulation); none breaks it. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None. No same-spec wrong implementation verifies, so no faithful refined patch could be materialized/resolve-run. The postcondition is an EXACT functional equality `out = editedPks pfx pkname items` under `loom.semantics.termination "total"`, and the `prove_correct` proof block is FROZEN OUTSIDE the editable impl region. Any impl that verifies must therefore be behaviorally identical to editedPks on the whole input domain, so its faithful patch is the gold behavior and resolves. verify⇒correct holds here.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

/- Total correctness: the real selection over the request items always
   terminates (it is a single pass over a finite items list), so a diverging
   implementation must NOT satisfy this spec. Partial correctness would let a
   non-terminating body discharge the postcondition vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees: the key-matching decision and the selection over the
--  request items are modeled deeply — see the `pure` region. The matcher's
--  fidelity to the real engine is checked mechanically by G-CONF, so there is
--  no opaque callee to over-approximate here.)
-- axioms-end

-- pure-start
/- The decimal-digit code points the key matcher's digit class accepts: the
   digits of every decimal number system (Unicode general category Nd, per the
   Unicode data the modeled engine ships), as inclusive (lo, hi) scalar-value
   bounds. The matcher's digit class is Unicode-aware, not restricted to the
   Latin digits. -/
def digitRanges : List (Nat × Nat) :=
  [ (0x30, 0x39), (0x660, 0x669), (0x6f0, 0x6f9), (0x7c0, 0x7c9),
    (0x966, 0x96f), (0x9e6, 0x9ef), (0xa66, 0xa6f), (0xae6, 0xaef),
    (0xb66, 0xb6f), (0xbe6, 0xbef), (0xc66, 0xc6f), (0xce6, 0xcef),
    (0xd66, 0xd6f), (0xde6, 0xdef), (0xe50, 0xe59), (0xed0, 0xed9),
    (0xf20, 0xf29), (0x1040, 0x1049), (0x1090, 0x1099), (0x17e0, 0x17e9),
    (0x1810, 0x1819), (0x1946, 0x194f), (0x19d0, 0x19d9), (0x1a80, 0x1a89),
    (0x1a90, 0x1a99), (0x1b50, 0x1b59), (0x1bb0, 0x1bb9), (0x1c40, 0x1c49),
    (0x1c50, 0x1c59), (0xa620, 0xa629), (0xa8d0, 0xa8d9), (0xa900, 0xa909),
    (0xa9d0, 0xa9d9), (0xa9f0, 0xa9f9), (0xaa50, 0xaa59), (0xabf0, 0xabf9),
    (0xff10, 0xff19), (0x104a0, 0x104a9), (0x11066, 0x1106f),
    (0x110f0, 0x110f9), (0x11136, 0x1113f), (0x111d0, 0x111d9),
    (0x112f0, 0x112f9), (0x11450, 0x11459), (0x114d0, 0x114d9),
    (0x11650, 0x11659), (0x116c0, 0x116c9), (0x11730, 0x11739),
    (0x118e0, 0x118e9), (0x11c50, 0x11c59), (0x16a60, 0x16a69),
    (0x16b50, 0x16b59), (0x1d7ce, 0x1d7ff), (0x1e950, 0x1e959) ]

/- Whether a single code point is a decimal digit: a member of one of the
   decimal-digit runs above (any decimal number system's digits, not only
   '0'..'9'). -/
def isDigit (c : Char) : Bool :=
  digitRanges.any (fun r => r.1 ≤ c.toNat && c.toNat ≤ r.2)

/- If `pat` is exactly the leading segment of `s`, return the trailing segment
   that follows it; otherwise report that `s` does not begin with `pat`. The
   comparison is code-point by code-point, so `pat` is matched as the exact
   sequence of characters it is — never as a pattern with distinguished
   characters. -/
def stripPrefix : List Char → List Char → Option (List Char)
  | [],      ys      => some ys
  | _ :: _,  []      => none
  | x :: xs, y :: ys => if x = y then stripPrefix xs ys else none

/- Split off the maximal leading run of decimal digits, returning the run and
   the remainder that follows it. -/
def takeDigits : List Char → (List Char × List Char)
  | []      => ([], [])
  | c :: cs =>
      if isDigit c then
        let p := takeDigits cs
        (c :: p.1, p.2)
      else ([], c :: cs)

/- The end-of-input position: nothing left, or a single trailing line
   terminator (the trailing-newline tolerance of the end-of-input position). -/
def atEnd (cs : List Char) : Bool := cs.isEmpty || cs == ['\n']

/- Whether a request key names one of the edited objects under `pfx`/`pkname`:
   the key must decompose as the exact characters of `pfx`, a separator '-', a
   nonempty run of decimal digits, a separator '-', and the exact characters of
   the identifier name `pkname`, ending the key (the trailing-newline tolerance
   aside). The prefix and the identifier name are matched as exact character
   sequences. -/
def matchesKey (pfx pkname key : List Char) : Bool :=
  match stripPrefix pfx key with
  | none    => false
  | some r1 =>
    match r1 with
    | '-' :: r2 =>
        let dp := takeDigits r2
        !dp.1.isEmpty &&
          (match dp.2 with
           | '-' :: r3 =>
               (match stripPrefix pkname r3 with
                | some tail => atEnd tail
                | none      => false)
           | _ => false)
    | _ => false

/- The selection over the request items (key, value pairs): keep the value of
   every item whose key matches. Front-recursive so a single unfold is available
   per loop step (the fold pattern). -/
def editedPks (pfx pkname : List Char) :
    List (List Char × List Char) → List (List Char)
  | []        => []
  | kv :: rest =>
      if matchesKey pfx pkname kv.1 then kv.2 :: editedPks pfx pkname rest
      else editedPks pfx pkname rest

@[grind] lemma editedPks_nil (pfx pkname : List Char) :
    editedPks pfx pkname [] = [] := rfl

@[grind] lemma editedPks_cons (pfx pkname : List Char)
    (kv : List Char × List Char) (rest : List (List Char × List Char)) :
    editedPks pfx pkname (kv :: rest)
      = (if matchesKey pfx pkname kv.1 then [kv.2] else [])
        ++ editedPks pfx pkname rest := by
  show (if matchesKey pfx pkname kv.1 then kv.2 :: editedPks pfx pkname rest
        else editedPks pfx pkname rest) = _
  split <;> rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The values of the request items whose key identifies an edited object under
   the given prefix and identifier name: the per-item selection over the items
   in order. -/
method editedObjectPks (pfx : List Char) (pkname : List Char) (items : List (List Char × List Char)) return (out : List (List Char))
  ensures out = editedPks pfx pkname items
  do
    -- impl-start
    let mut result : List (List Char) := []
    let mut i := items.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ items.length
      invariant result = editedPks pfx pkname (items.drop i)
      done_with i = 0
      decreasing i
    do
      let kv := items[i - 1]!
      result := (if matchesKey pfx pkname kv.1 then [kv.2] else []) ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the item at
   `i-1` on the front, so `editedPks` peels one selection. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma editedPks_drop_step (pfx pkname : List Char)
    (items : List (List Char × List Char)) (i : Nat)
    (hi : 0 < i) (hle : i ≤ items.length) :
    editedPks pfx pkname (items.drop (i - 1))
      = (if matchesKey pfx pkname (items[i - 1]!).1 then [(items[i - 1]!).2] else [])
        ++ editedPks pfx pkname (items.drop i) := by
  have hlt : i - 1 < items.length := by omega
  have hcons : items.drop (i - 1) = items[i - 1]! :: items.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, editedPks_cons]

prove_correct editedObjectPks by
  loom_solve
  rw [editedPks_drop_step pfx pkname items i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

elan on PATH, PY=python, PYTHONPATH=src.

SPEC PIN (why hard to break): postcondition `ensures out = editedPks pfx pkname items` is an exact functional equality; `set_option loom.semantics.termination "total"` (rejects diverging impls, not vacuous); AND the entire `prove_correct editedObjectPks by loom_solve; rw [editedPks_drop_step ...]; simp_all` block sits OUTSIDE `-- impl-start/-- impl-end`, so it is byte-frozen and loom_solve's VC is tailored to the backward `while` fold. Editing only the impl must still discharge that exact frozen proof against the exact-equality post.

POSITIVE CONTROL: pos_control.lean = verbatim Solution.lean. Command: `bash scripts/lean_verify.sh .../pos_control.lean` -> exit 0 (verifies, no sorry). Same_spec vs Solution.lean = True.

SAME_SPEC: all 8 attacks checked via swebench_unified.markers.same_spec (velvet lang) => True for every one (impl region only edited).

### ATTACKS (all verified concurrently, <=4 background jobs; `bash scripts/lean_verify.sh .../atk_N.lean`):
  atk_1 (prepatch bug re-encode: `if pfx.contains '$' then false else matchesKey ...` -> drops $-bearing prefixes) : exit 1, `unsolved goals` at proof rw/simp_all (164:30). FAILS verify.
  atk_2 (partial-domain / empty: always return []) : exit 1, unsolved goals (161:30). FAILS.
  atk_3 (boundary/off-by-one: `while i > 1`, skips first item) : exit 1, unsolved goals (162:30). FAILS.
  atk_4 (control-flow-effect: reversed accumulation `result ++ [kv.2]`) : exit 1, unsolved goals (162:30). FAILS.
  atk_5 (ungrounded-oracle echo: `return editedPks pfx pkname items`, no loop) : exit 1, `No goals to be solved` (153:6) -- behaviorally CORRECT but cannot satisfy the frozen loop-tailored proof (correct-but-unverifiable false negative; does NOT break spec).
  atk_6 (matcher-weakening: keep every value, ignore matchesKey) : exit 1, unsolved goals (162:30). FAILS.
  atk_7 (wrong projection: emit kv.1 key instead of kv.2 value) : exit 1, unsolved goals (162:30). FAILS.
  atk_8 (forward reformulation: `items.filterMap ...`) : exit 1, frozen proof references `i` -> unknown identifier + unsolved goals (151/153) -- behaviorally CORRECT but frozen proof assumes the loop shape (false negative; does NOT break spec).

NO wrong impl VERIFIES => protocol step 2 (materialize+resolve faithful patch) is VACUOUS: there is no verifying-wrong-impl to resolve. patches={} accordingly. (Reported honestly, not skipped: a resolve run is only mandated for a verifying wrong impl; none exists.)

PREPATCH: shipped Solution_prepatch.lean copied to prepatch.lean, verified -> exit 1, unsolved goals (172:30). Prepatch bug reproduced (fails G-DIFF) as claimed. prepatch_reproduced=true.

REFINEMENT.MD LEG AUDIT (step 3): NO A-tagged (axiom/callee) legs -- bundle has no axioms (axiom_check.py is explicit no-op). Legs: A1/A2/A3/A6 = R (str<->List Char, order-preserving items, list result); A4 = I (comprehension = editedPks front-recursive selection); A5 = I (deep model) -- the changed op (re.escape literal match) modeled deeply as stripPrefix/takeDigits/atEnd, NOT behind an axiom. NO kind-3 (inexpressible) legs. Correspondence AUDITED: re-implemented the deep model (matchesKey/stripPrefix/takeDigits/atEnd/digitRanges) in Python and differentially compared to the REAL patched regex `re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkname))` on 16 discriminating cases: metachar prefixes ($, ., +, parens), empty prefix, trailing single \n (match) vs double \n (no match), Arabic-Indic digits U+0660s (match), superscript-2 non-Nd (no match), empty digit run, non-anchored key, trailing junk. Result: 0/16 mismatches. B2 (total-correctness repair) and B3 (Unicode \d digit-class repair) both independently corroborated by these cases.

CONCLUSION: verify=>correct holds on this bundle. Exact-equality post + total correctness + frozen loop-tailored proof leave no room for a verifying wrong impl; the only impls that fail-to-verify while being correct (atk_5, atk_8) are FALSE NEGATIVES (correct-but-unverifiable), which strengthen rather than break the spec. Deep-model<->real-regex correspondence holds on all discriminating inputs. >=5 distinct attack classes exercised (prepatch, partial-domain, boundary, control-flow-effect, matcher-weakening, wrong-projection, ungrounded-oracle echo, forward-reformulation); none breaks it. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Independent verification, not a rubber-stamp: (1) same_spec(Solution, Solution_prepatch, velvet.language)=True — spec region byte-identical, only impl differs. (2) lean_verify.sh Solution.lean exit 0 — spec verifies (satisfiable, not vacuous). (3) Reconstructed the model semantics in Python from scratch and diffed against the REAL patched callee `[v for k,v in items if re.compile(r'{}-\d+-{}$'.format(re.escape(pfx),pkname)).match(k)]` run in the actual instance environment. Instance version=3.1 → Python 3.6 → unidata 9.0.0 (confirmed empirically in python:3.6-slim container). (4) digitRanges (580 code points) is BYTE-EXACT with Python 3.6 `\d` (table==host, 0 only_host / 0 only_table). The 100 Nd code points present in newer Unicode (≥10.0: Masaram Gondi, Rohingya, Dives Akuru, Kawi, Tangsa, Hmong, Wancho, Nag Mundari, Segmented) do NOT exist in Unicode 9.0.0 and are therefore not reachable — the version pinning is correct. (5) 400k randomized fuzz (metachar prefixes, astral digits, non-Latin digits, digit-lookalike near-misses, trailing \n/\r\n/\r) → 0 divergences. (6) Targeted edge cases in-container all agree: trailing \r\n/\r reject, single \n accept, \n\n reject (atEnd tolerance faithful); astral digits U+1D7CE/U+1E950/U+104A0 accept; U+1FBF0 (segmented, U13) correctly rejects. The escaped-prefix literal match (the gold fix) is faithfully modeled by stripPrefix. Termination='total' is the faithful semantics for a finite single-pass comprehension. Conclusion: the modeled function agrees with the real callee on every reachable input; the spec is FAITHFUL (not too strong, no drift).

Counterexample / evidence:

```
N/A — spec is faithful. (Out-of-domain only: pkname containing a metacharacter, which cannot occur since pk.name is always an identifier.)
```

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit = wrap prefix in re.escape() so the formset prefix is matched literally rather than as a regex pattern. The public problem_statement already discloses this fully: it quotes the exact vulnerable line pk_pattern = re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name)), names the discriminator (regex special chars in prefix -> data loss), and states the fix verbatim ('use re.escape()'). The spec view models the matcher as stripPrefix (exact code-point/literal match, 'never as a pattern with distinguished characters') + \d+ digit run + literal pkname + atEnd — i.e. the post-patch literal-prefix behavior, which is precisely what problem_statement already reveals; it adds no discriminating information beyond the public statement. same_spec(Solution.lean, Solution_prepatch.lean)=True (spec region byte-identical between twins; only impl/proof differ). The digitRanges/Unicode-aware \d modeling is a faithfulness detail of the unchanged \d class (present pre and post patch), not the gold discriminator, so no leak. Mechanical leakage.screen over the spec view passes with zero hard failures. NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
