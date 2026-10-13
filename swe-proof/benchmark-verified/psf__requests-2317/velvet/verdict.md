# P2 adversarial audit — psf__requests-2317

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. The frozen spec pins the impl output to the token itself via three postconditions (out = nativeSeq token; out = token; out.length = token.length) under total-correctness termination. Every wrong behavior encoded is rejected on the out=token / out=nativeSeq token goal. The only same-spec candidate that verifies is the correct identity impl (atk_7 = `return token`), whose faithful refined patch is byte-identical to the gold patch and RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -60,7 +60,7 @@
       let c := token[i - 1]!
       result := nativeChar c ++ result
       i := i - 1
-    return result
+    return 'b' :: '\'' :: (result ++ ['\''])
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,7 @@
   ensures out.length = token.length
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := token.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ token.length
-      invariant result = nativeSeq (token.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := token[i - 1]!
-      result := nativeChar c ++ result
-      i := i - 1
-    return result
+    return []
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -78,6 +67,4 @@
   rw [hcons, nativeSeq_cons]
 
 prove_correct nativeToken by
-  loom_solve
-  rw [nativeSeq_drop_step token i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [nativeSeq_id]
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,7 @@
   ensures out.length = token.length
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := token.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ token.length
-      invariant result = nativeSeq (token.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := token[i - 1]!
-      result := nativeChar c ++ result
-      i := i - 1
-    return result
+    return token ++ token
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -78,6 +67,4 @@
   rw [hcons, nativeSeq_cons]
 
 prove_correct nativeToken by
-  loom_solve
-  rw [nativeSeq_drop_step token i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [nativeSeq_id]
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,7 @@
   ensures out.length = token.length
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := token.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ token.length
-      invariant result = nativeSeq (token.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := token[i - 1]!
-      result := nativeChar c ++ result
-      i := i - 1
-    return result
+    return token.drop 1
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -78,6 +67,4 @@
   rw [hcons, nativeSeq_cons]
 
 prove_correct nativeToken by
-  loom_solve
-  rw [nativeSeq_drop_step token i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [nativeSeq_id]
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,7 @@
   ensures out.length = token.length
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := token.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ token.length
-      invariant result = nativeSeq (token.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := token[i - 1]!
-      result := nativeChar c ++ result
-      i := i - 1
-    return result
+    return token ++ ['x']
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -78,6 +67,4 @@
   rw [hcons, nativeSeq_cons]
 
 prove_correct nativeToken by
-  loom_solve
-  rw [nativeSeq_drop_step token i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [nativeSeq_id]
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -49,18 +49,7 @@
   ensures out.length = token.length
   do
     -- impl-start
-    let mut result : List Char := []
-    let mut i := token.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ token.length
-      invariant result = nativeSeq (token.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let c := token[i - 1]!
-      result := nativeChar c ++ result
-      i := i - 1
-    return result
+    return token.reverse
     -- impl-end
 
 /- The backward-fold step: dropping one fewer element exposes the element at
@@ -78,6 +67,4 @@
   rw [hcons, nativeSeq_cons]
 
 prove_correct nativeToken by
-  loom_solve
-  rw [nativeSeq_drop_step token i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [nativeSeq_id]
```

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -51,7 +51,7 @@
     -- impl-start
     let mut result : List Char := []
     let mut i := token.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ token.length
       invariant result = nativeSeq (token.drop i)
       done_with i = 0
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The native text representation of a single token character: a token may
   arrive either as native text or as a byte string carrying the ASCII bytes
   of the token, and the representation keeps the character itself. Each
   carried character contributes exactly itself, with no surrounding marker or
   quoting wrapper. -/
def nativeChar (c : Char) : List Char := [c]

/- The native text representation of a whole token: the concatenation of the
   per-character representations. Front-recursive so a single unfold is
   available per loop step (the Velvet fold pattern). For an ASCII token this
   is the identity on the carried character sequence. -/
def nativeSeq : List Char → List Char
  | []      => []
  | c :: cs => nativeChar c ++ nativeSeq cs

@[grind] lemma nativeSeq_nil : nativeSeq [] = [] := rfl
@[grind] lemma nativeSeq_cons (c : Char) (cs : List Char) :
    nativeSeq (c :: cs) = nativeChar c ++ nativeSeq cs := rfl

/- The native representation preserves the carried character sequence exactly:
   it is the token's own characters, of the same length, regardless of whether
   the token arrived as native text or as a byte string. -/
@[grind] lemma nativeSeq_id : ∀ (cs : List Char), nativeSeq cs = cs
  | []      => rfl
  | c :: cs => by simp [nativeSeq_cons, nativeChar, nativeSeq_id cs]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method nativeToken (token : List Char) return (out : List Char)
  ensures out = nativeSeq token
  ensures out = token
  ensures out.length = token.length
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := token.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ token.length
      invariant result = nativeSeq (token.drop i)
      done_with i = 0
      decreasing i
    do
      let c := token[i - 1]!
      result := nativeChar c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `nativeSeq` peels one `nativeChar`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma nativeSeq_drop_step (token : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ token.length) :
    nativeSeq (token.drop (i - 1)) = nativeChar token[i - 1]! ++ nativeSeq (token.drop i) := by
  have hlt : i - 1 < token.length := by omega
  have hcons : token.drop (i - 1) = token[i - 1]! :: token.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, nativeSeq_cons]

prove_correct nativeToken by
  loom_solve
  rw [nativeSeq_drop_step token i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (project root; env, PATH incl elan). same_spec verified True for all 8 attack files via swebench_unified.markers.same_spec vs Solution.lean (velvet).

VERIFY (bash scripts/lean_verify.sh <file>), run concurrently in batches of 4:
- pos_control.lean (shipped Solution.lean identity loop): EXIT 0 (verifies).
- prepatch.lean (= Solution_prepatch.lean, b'...'-wrap len+3): EXIT 1, unsolved goals ensures_2 `out = token` / ensures_3 `out = nativeSeq token` => prepatch bug REPRODUCED.
- atk_1 (loop then 'b'::'\''::result++['\''], prepatch re-encoding): EXIT 1, fails out=token.
- atk_2 (return []): EXIT 1, fails out=token.
- atk_3 (return token++token): EXIT 1, fails out=token.
- atk_4 (return token.drop 1, partial-domain/boundary): EXIT 1, fails out=token.
- atk_5 (return token++['x'], length off-by-one/boundary): EXIT 1, fails out=token.
- atk_6 (return token.reverse, control-flow/ordering): EXIT 1, fails out=nativeSeq token.
- atk_8 (while i>1, loop off-by-one skipping first char): EXIT 1, fails out=token/out=nativeSeq token.
- atk_7 (return token, correct identity echo): EXIT 0 (verifies).

So the ONLY same-spec verifying impl is the CORRECT one (atk_7). No verifying wrong impl exists, so there is no candidate for a verify-not-resolve break; mandatory resolve was still run for the one verifying candidate.

RESOLVE (run_resolve('psf__requests-2317', atk_7.patch, timeout=1800, retries=1) via swebench_unified.harness): atk_7's faithful patch is byte-IDENTICAL to the frozen gold patch (confirmed: gold.strip()==mine.strip() True). Result: RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False (run_id sbu-resolve-...-psf__requests-2317-21aa7657dc-...). => verifying candidate maps to a RESOLVING patch. verify => correct holds here.

CAVEAT (not a spec defect): a pre-existing gold-patch resolve report (experiments/logs/run_evaluation/sbu-eq-gold/...) shows resolved:false with all FAIL_TO_PASS failing on `assert 503` from httpbin.org — the documented psf__requests live-internet drift (the audit protocol golden rule). My fresh atk_7/gold run resolved True, so the harness is working for this instance now; the historical false is network flakiness, not the spec.

A-LEG / refinement.md AUDIT: axioms region byte-empty (`-- axioms-start`/`-- axioms-end`); prove_correct consumes NO to_native_string axiom (only nativeSeq_drop_step + loom_solve). Legs: A1 param token<->method (R, str/bytes<->List Char, ASCII byte==code point); A2 copy loop out=nativeSeq token <-> to_native_string(method) (A-reference: deep model IS the computed value, validated == real callee by axiom_check.py over boundary + exhaustive 0..127 single-char + 20000 seeded fuzz, BOTH text and bytes forms, zero disagreements — checked domain == spec domain == ASCII); A3 import-list edit (I, no-op). No kind-3 legs; A-reference correspondence to the real callee (requests/utils.py:655 to_native_string) holds. A2b termination note is faithful: total correctness + decreasing i pins termination, closing the earlier partial-correctness while-true hole.

VERDICT: SOUND — >=5 distinct wrong impls (7 total: partial-domain atk_8, boundary atk_4/atk_5, control-flow-effect atk_3/atk_6, ungrounded echo atk_2, prepatch atk_1) all fail to verify; prepatch reproduced; positive control verifies; the sole verifying candidate's faithful patch resolves. No verify-not-resolve witness => verify does not fail to imply correct here.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_8.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. The frozen spec pins the impl output to the token itself via three postconditions (out = nativeSeq token; out = token; out.length = token.length) under total-correctness termination. Every wrong behavior encoded is rejected on the out=token / out=nativeSeq token goal. The only same-spec candidate that verifies is the correct identity impl (atk_7 = `return token`), whose faithful refined patch is byte-identical to the gold patch and RESOLVES.
```

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- axioms-end

-- pure-start
/- The native text representation of a single token character: a token may
   arrive either as native text or as a byte string carrying the ASCII bytes
   of the token, and the representation keeps the character itself. Each
   carried character contributes exactly itself, with no surrounding marker or
   quoting wrapper. -/
def nativeChar (c : Char) : List Char := [c]

/- The native text representation of a whole token: the concatenation of the
   per-character representations. Front-recursive so a single unfold is
   available per loop step (the Velvet fold pattern). For an ASCII token this
   is the identity on the carried character sequence. -/
def nativeSeq : List Char → List Char
  | []      => []
  | c :: cs => nativeChar c ++ nativeSeq cs

@[grind] lemma nativeSeq_nil : nativeSeq [] = [] := rfl
@[grind] lemma nativeSeq_cons (c : Char) (cs : List Char) :
    nativeSeq (c :: cs) = nativeChar c ++ nativeSeq cs := rfl

/- The native representation preserves the carried character sequence exactly:
   it is the token's own characters, of the same length, regardless of whether
   the token arrived as native text or as a byte string. -/
@[grind] lemma nativeSeq_id : ∀ (cs : List Char), nativeSeq cs = cs
  | []      => rfl
  | c :: cs => by simp [nativeSeq_cons, nativeChar, nativeSeq_id cs]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method nativeToken (token : List Char) return (out : List Char)
  ensures out = nativeSeq token
  ensures out = token
  ensures out.length = token.length
  do
    -- impl-start
    let mut result : List Char := []
    let mut i := token.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ token.length
      invariant result = nativeSeq (token.drop i)
      done_with i = 0
      decreasing i
    do
      let c := token[i - 1]!
      result := nativeChar c ++ result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `nativeSeq` peels one `nativeChar`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma nativeSeq_drop_step (token : List Char) (i : Nat)
    (hi : 0 < i) (hle : i ≤ token.length) :
    nativeSeq (token.drop (i - 1)) = nativeChar token[i - 1]! ++ nativeSeq (token.drop i) := by
  have hlt : i - 1 < token.length := by omega
  have hcons : token.drop (i - 1) = token[i - 1]! :: token.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, nativeSeq_cons]

prove_correct nativeToken by
  loom_solve
  rw [nativeSeq_drop_step token i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL & RESULTS (project root; env, PATH incl elan). same_spec verified True for all 8 attack files via swebench_unified.markers.same_spec vs Solution.lean (velvet).

VERIFY (bash scripts/lean_verify.sh <file>), run concurrently in batches of 4:
- pos_control.lean (shipped Solution.lean identity loop): EXIT 0 (verifies).
- prepatch.lean (= Solution_prepatch.lean, b'...'-wrap len+3): EXIT 1, unsolved goals ensures_2 `out = token` / ensures_3 `out = nativeSeq token` => prepatch bug REPRODUCED.
- atk_1 (loop then 'b'::'\''::result++['\''], prepatch re-encoding): EXIT 1, fails out=token.
- atk_2 (return []): EXIT 1, fails out=token.
- atk_3 (return token++token): EXIT 1, fails out=token.
- atk_4 (return token.drop 1, partial-domain/boundary): EXIT 1, fails out=token.
- atk_5 (return token++['x'], length off-by-one/boundary): EXIT 1, fails out=token.
- atk_6 (return token.reverse, control-flow/ordering): EXIT 1, fails out=nativeSeq token.
- atk_8 (while i>1, loop off-by-one skipping first char): EXIT 1, fails out=token/out=nativeSeq token.
- atk_7 (return token, correct identity echo): EXIT 0 (verifies).

So the ONLY same-spec verifying impl is the CORRECT one (atk_7). No verifying wrong impl exists, so there is no candidate for a verify-not-resolve break; mandatory resolve was still run for the one verifying candidate.

RESOLVE (run_resolve('psf__requests-2317', atk_7.patch, timeout=1800, retries=1) via swebench_unified.harness): atk_7's faithful patch is byte-IDENTICAL to the frozen gold patch (confirmed: gold.strip()==mine.strip() True). Result: RESOLVED=True, COMPLETED=True, NOTE='resolved', FLAKY=False (run_id sbu-resolve-...-psf__requests-2317-21aa7657dc-...). => verifying candidate maps to a RESOLVING patch. verify => correct holds here.

CAVEAT (not a spec defect): a pre-existing gold-patch resolve report (experiments/logs/run_evaluation/sbu-eq-gold/...) shows resolved:false with all FAIL_TO_PASS failing on `assert 503` from httpbin.org — the documented psf__requests live-internet drift (the audit protocol golden rule). My fresh atk_7/gold run resolved True, so the harness is working for this instance now; the historical false is network flakiness, not the spec.

A-LEG / refinement.md AUDIT: axioms region byte-empty (`-- axioms-start`/`-- axioms-end`); prove_correct consumes NO to_native_string axiom (only nativeSeq_drop_step + loom_solve). Legs: A1 param token<->method (R, str/bytes<->List Char, ASCII byte==code point); A2 copy loop out=nativeSeq token <-> to_native_string(method) (A-reference: deep model IS the computed value, validated == real callee by axiom_check.py over boundary + exhaustive 0..127 single-char + 20000 seeded fuzz, BOTH text and bytes forms, zero disagreements — checked domain == spec domain == ASCII); A3 import-list edit (I, no-op). No kind-3 legs; A-reference correspondence to the real callee (requests/utils.py:655 to_native_string) holds. A2b termination note is faithful: total correctness + decreasing i pins termination, closing the earlier partial-correctness while-true hole.

VERDICT: SOUND — >=5 distinct wrong impls (7 total: partial-domain atk_8, boundary atk_4/atk_5, control-flow-effect atk_3/atk_6, ungrounded echo atk_2, prepatch atk_1) all fail to verify; prepatch reproduced; positive control verifies; the sole verifying candidate's faithful patch resolves. No verify-not-resolve witness => verify does not fail to imply correct here.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness check for psf__requests-2317 (velvet). SPEC INTEGRITY: same_spec(Solution, Solution_prepatch)=True with the VelvetBackend LanguageTables — the frozen spec region is byte-identical. Solution.lean verifies (lean_verify exit 0); Solution_prepatch.lean (the b'...'-wrapping byte-render pre-image) fails the out=token / out=nativeSeq token / out.length=token.length postconditions (exit 1), so the spec senses the gold change (G-DIFF holds).

MODELED FN vs REAL CALLEE: The spec models nativeToken as the identity on the carried char sequence (out = nativeSeq token, nativeSeq_id: nativeSeq cs = cs), representing to_native_string(method) at requests/sessions.py:428 (deep-model A-reference of requests.utils.to_native_string, utils.py:655, Py3 path builtin_str=str/is_py2=False). I isolated the real callee (old requests won't import under py3.11 due to collections.Mapping, so I ran the exact function body verbatim) and swept the full declared domain:
  - str form, code points 0..127: 0 divergences (identity)
  - bytes form, code points 0..127: 0 divergences (bytes.decode('ascii') = carried code points)
  - boundary tokens GET/POST/'' as both str and bytes, plus empty: all match
  - str branch beyond ASCII (ü, €, naïve, ÿ): still identity — spec never over-restricts the str carrier
  - bytes beyond ASCII (b'\xff', b'\xc8'): real callee RAISES UnicodeDecodeError — but these are outside the declared ASCII domain (mapping.md §2 restricts the carrier to values <128) and are not valid HTTP method tokens, so they are not in scope.

CONCLUSION: The model agrees with the real callee on every input in the declared ASCII domain for both str and bytes carriers. The identity postcondition is not too strong — it exactly matches to_native_string over the modeled domain. No diverging input exists within scope. Spec is FAITHFUL (not too strong / no drift).

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec region is byte-identical between Solution.lean and Solution_prepatch.lean (same_spec=True, velvet backend). Mechanical G-LEAK screen passes clean (no diff markers, no reproduced gold line, patched file path requests/sessions.py absent, patched symbol 'request' absent). Judged manually against the SOLVER-VISIBLE problem_statement only.

The public problem_statement already discloses far more than the spec: it quotes the exact buggy line 'method = builtin_str(method)', names the file requests/sessions.py, and gives the exact defect (b'GET' rendered as the literal string "b'GET'" causing a 404), plus the desired behavior (requests should handle a binary-string method). So location + desired behavior are fully public.

The spec view (pure region docstrings + method ensures) states only behavior: the token's own characters are preserved with 'no surrounding marker or quoting wrapper', out = token, out = nativeSeq token, out.length = token.length. This is precisely the negation of the publicly-described bug (the b'...' wrapper). It does NOT name the gold callee to_native_string, nor builtin_str, nor .decode/.encode, nor any diff/path artifact.

Only attacker concern examined: the 'native' vocabulary (nativeToken/nativeSeq/nativeChar, 'native text representation'). The gold callee is to_native_string and 'native' is not in problem_statement (it appears in hints_text, which is correctly out of scope). But the spec names no gold symbol verbatim; 'native string' is standard Python domain terminology for the exact correct-behavior concept the problem statement already describes (a usable string rather than a b'...' literal). The solver implements the Lean impl/proof regions, not the Python edit, and the spec reveals only the publicly-derivable behavioral contract, not the specific gold edit (str-vs-bytes identity coercion). No spec-view line leaks the gold edit beyond problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
