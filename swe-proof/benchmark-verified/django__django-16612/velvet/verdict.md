# P2 adversarial audit — django__django-16612

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. The spec is a straight-line, precondition-free postcondition of EXACT equality (out = redirectTarget encodedPath encodedQuery) against a total pure function, so it pins the output uniquely for every (encodedPath, encodedQuery). Every attempted wrong impl leaves an unsolved goal, e.g. atk_1 (prepatch bug): ['/'] = (if encodedPath.getLast? = some '/' then [] else ['/']) ++ (if encodedQuery = [] then [] else '?' :: encodedQuery), false whenever a query is present or the path already ends in '/'.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -49,11 +49,7 @@
   ensures out = redirectTarget encodedPath encodedQuery
   do
     -- impl-start
-    let slash : List Char :=
-      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
-    let query : List Char :=
-      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
-    let result := encodedPath ++ slash ++ query
+    let result := encodedPath ++ ['/']
     return result
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -51,9 +51,7 @@
     -- impl-start
     let slash : List Char :=
       if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
-    let query : List Char :=
-      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
-    let result := encodedPath ++ slash ++ query
+    let result := encodedPath ++ slash
     return result
     -- impl-end
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -49,11 +49,9 @@
   ensures out = redirectTarget encodedPath encodedQuery
   do
     -- impl-start
-    let slash : List Char :=
-      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
     let query : List Char :=
       if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
-    let result := encodedPath ++ slash ++ query
+    let result := encodedPath ++ ['/'] ++ query
     return result
     -- impl-end
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -53,7 +53,7 @@
       if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
     let query : List Char :=
       if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
-    let result := encodedPath ++ slash ++ query
+    let result := encodedPath ++ query ++ slash
     return result
     -- impl-end
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -52,7 +52,7 @@
     let slash : List Char :=
       if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
     let query : List Char :=
-      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
+      if encodedQuery = [] then ([] : List Char) else ':' :: encodedQuery
     let result := encodedPath ++ slash ++ query
     return result
     -- impl-end
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -51,8 +51,7 @@
     -- impl-start
     let slash : List Char :=
       if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
-    let query : List Char :=
-      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
+    let query : List Char := '?' :: encodedQuery
     let result := encodedPath ++ slash ++ query
     return result
     -- impl-end
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -50,7 +50,7 @@
   do
     -- impl-start
     let slash : List Char :=
-      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
+      if encodedPath.head? = some '/' then ([] : List Char) else ['/']
     let query : List Char :=
       if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
     let result := encodedPath ++ slash ++ query
```

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

```diff
@@ -1,10 +1,10 @@
 import Velvet.Std
 -- imports-end
 
-set_option loom.semantics.termination "total"
+set_option loom.semantics.termination "partial"
 set_option loom.semantics.choice "demonic"
 
-open TotalCorrectness DemonicChoice
+open PartialCorrectness DemonicChoice
 
 -- axioms-start
 /- No consumed axioms. The two URL percent-encoders this construction relies on
@@ -49,11 +49,13 @@
   ensures out = redirectTarget encodedPath encodedQuery
   do
     -- impl-start
-    let slash : List Char :=
-      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
-    let query : List Char :=
-      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
-    let result := encodedPath ++ slash ++ query
+    let mut t : Nat := 1
+    while t > 0
+      invariant True
+      done_with (t = 0)
+    do
+      t := t + 1
+    let result := encodedPath ++ ['/']
     return result
     -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two URL percent-encoders this construction relies on
   are unchanged community helpers; rather than axiomatize them (they are not
   what this specification pins, and would not be code-generable inside the
   executable body), their outputs are refined directly into the input carrier
   (`encodedPath` / `encodedQuery` are the already-encoded character sequences).
   The bijection is stated in mapping.md §2 and validated executably by
   axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- The redirect destination that guarantees a trailing slash while preserving an
   existing query string, assembled from the encoded request path and the
   encoded query string:

     * the encoded path, then
     * a single '/' appended exactly when the path does not already end in one,
       then
     * when a query string is present, that query preserved after a '?'
       separator.

   This is a deep model of the standard request-destination builder (an
   unchanged community helper); `redirectTarget == that builder` is validated by
   axiom_check.py (G-AX), so it is an A-reference, not a consumed axiom. The
   preservation of the query-string component is the behaviour this
   specification pins. -/
def redirectTarget (encodedPath : List Char) (encodedQuery : List Char) : List Char :=
  encodedPath
    ++ (if encodedPath.getLast? = some '/' then ([] : List Char) else ['/'])
    ++ (if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method appendSlashRedirect (encodedPath : List Char) (encodedQuery : List Char)
    return (out : List Char)
  ensures out = redirectTarget encodedPath encodedQuery
  do
    -- impl-start
    let slash : List Char :=
      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
    let query : List Char :=
      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
    let result := encodedPath ++ slash ++ query
    return result
    -- impl-end

prove_correct appendSlashRedirect by
  loom_solve
  simp [redirectTarget]
```

Prepatch bug re-encoded as an attack: `True`.

Ran everything there. swebench_unified imported via python with PYTHONPATH=src; Lean via lean_verify.sh with,.

SAME_SPEC: all 8 attack files + positive_control return same_spec=True vs Solution.lean (only impl region edited; axioms/pure/pre/post byte-identical). Command per file: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SOLUTION).read(), open(ATK).read(), b.language))".

VERIFY (bash scripts/lean_verify.sh <file>), run concurrently in batches of 4:
- positive_control.lean -> exit 0 (VERIFIES). This is the exact gold impl.
- atk_1 PREPATCH BUG (encodedPath ++ ['/']; drops query, unconditional slash) -> exit 1 (unsolved goals; reproduces refinement.md G-DIFF: ['/'] = slash-comp ++ query-comp). prepatch_reproduced=true.
- atk_2 PARTIAL-DOMAIN (correct slash, drops query) -> exit 1.
- atk_3 BOUNDARY (unconditional slash even when path ends in '/', query kept) -> exit 1.
- atk_4 CONTROL-FLOW/ORDER (query ++ slash swapped) -> exit 1.
- atk_5 UNGROUNDED-ORACLE ECHO (wrong ':' separator instead of '?') -> exit 1.
- atk_6 DROPPED GUARD (always '?'::encodedQuery, emits '?' for empty query) -> exit 1.
- atk_7 WRONG PREDICATE (encodedPath.head? instead of getLast? for slash test) -> exit 1.
- atk_9 DIVERGING/PARTIAL-CORRECTNESS PROBE (infinite while-loop then returns wrong value encodedPath++['/']) -> exit 1. Velvet's done_with binds the loop-exit state into the postcondition obligation, so vacuous-post divergence does NOT slip through; the wrong return still leaves ['/'] = ... unsolved. The termination=partial setting does not open the classic verify-not-terminate hole here.
- atk_8 (correct-but-match-rewritten, intended positive) -> exit 1: fails ONLY because the FROZEN proof script `simp [redirectTarget]` cannot fold the match form; not counted as a verifying wrong impl. Confirms the proof script is rigid but the point stands: no WRONG impl verified.

RESOLVE (step 2): vacuously satisfied — ZERO same-spec wrong impls verify, so there is no faithful refined patch to materialize/run through run_resolve. patches={}.

G-AX / A-REFERENCE (deep-model correspondence, the only non-R/I trust point): ran axiom_check.py against the REAL repo worktree at base_commit 55bcbd8d172b689811fae17cde2f09218dd74e9c (verified git HEAD + sites.py:456 prepatch line). Command: python3 axiom_check.py -> exit 0, 'redirectTarget deep model (== real get_full_path(force_append_slash=True)) sound on 100 boundary + 20000 fuzz (path, query) pairs.' The deep model equals the real gold callee, so verify(assembly) => equals get_full_path(force_append_slash=True) => resolves.

REFINEMENT.MD LEG AUDIT: legs A1=R, A2=R, A3=I+R, A4=I+R, A5=A-reference+I. Every leg is R / A-reference / I; no kind-3 inexpressible-changed-op. The single A-reference (A5/§3.1) correspondence to the real callee get_full_path(force_append_slash=True) is validated by the G-AX run above. mapping.md §2 bijection (escape_uri_path/iri_to_uri outputs as carriers; endswith('/') <-> getLast?=some '/'; iri_to_uri('')=='') is consistent with the actual encoder safe-set and is exercised by both axiom_check.py and conformance_check.py.

CONCLUSION: The frozen spec is an exact functional equality with no preconditions and total domain; it admits a unique correct output per input, the gold impl verifies, all 8 distinct genuine wrong impls (partial-domain, boundary, control-flow/order, ungrounded-oracle echo, dropped-guard, wrong-predicate, prepatch, diverging) fail to verify, and the one non-R/I trust point (deep-model A-reference) is G-AX-sound against the real repo. No verify-but-not-resolve counterexample exists. Verdict SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 8 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_9.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no same-spec wrong impl verifies. The spec is a straight-line, precondition-free postcondition of EXACT equality (out = redirectTarget encodedPath encodedQuery) against a total pure function, so it pins the output uniquely for every (encodedPath, encodedQuery). Every attempted wrong impl leaves an unsolved goal, e.g. atk_1 (prepatch bug): ['/'] = (if encodedPath.getLast? = some '/' then [] else ['/']) ++ (if encodedQuery = [] then [] else '?' :: encodedQuery), false whenever a query is present or the path already ends in '/'.
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

Attack 8 — `atk_9.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The two URL percent-encoders this construction relies on
   are unchanged community helpers; rather than axiomatize them (they are not
   what this specification pins, and would not be code-generable inside the
   executable body), their outputs are refined directly into the input carrier
   (`encodedPath` / `encodedQuery` are the already-encoded character sequences).
   The bijection is stated in mapping.md §2 and validated executably by
   axiom_check.py (G-AX). -/
-- axioms-end

-- pure-start
/- The redirect destination that guarantees a trailing slash while preserving an
   existing query string, assembled from the encoded request path and the
   encoded query string:

     * the encoded path, then
     * a single '/' appended exactly when the path does not already end in one,
       then
     * when a query string is present, that query preserved after a '?'
       separator.

   This is a deep model of the standard request-destination builder (an
   unchanged community helper); `redirectTarget == that builder` is validated by
   axiom_check.py (G-AX), so it is an A-reference, not a consumed axiom. The
   preservation of the query-string component is the behaviour this
   specification pins. -/
def redirectTarget (encodedPath : List Char) (encodedQuery : List Char) : List Char :=
  encodedPath
    ++ (if encodedPath.getLast? = some '/' then ([] : List Char) else ['/'])
    ++ (if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method appendSlashRedirect (encodedPath : List Char) (encodedQuery : List Char)
    return (out : List Char)
  ensures out = redirectTarget encodedPath encodedQuery
  do
    -- impl-start
    let slash : List Char :=
      if encodedPath.getLast? = some '/' then ([] : List Char) else ['/']
    let query : List Char :=
      if encodedQuery = [] then ([] : List Char) else '?' :: encodedQuery
    let result := encodedPath ++ slash ++ query
    return result
    -- impl-end

prove_correct appendSlashRedirect by
  loom_solve
  simp [redirectTarget]
```

Prepatch bug re-encoded as an attack: `True`.

Ran everything there. swebench_unified imported via python with PYTHONPATH=src; Lean via lean_verify.sh with,.

SAME_SPEC: all 8 attack files + positive_control return same_spec=True vs Solution.lean (only impl region edited; axioms/pure/pre/post byte-identical). Command per file: python -c "from swebench_unified.markers import same_spec; from swebench_unified.backends import get_backend; b=get_backend('velvet'); print(same_spec(open(SOLUTION).read(), open(ATK).read(), b.language))".

VERIFY (bash scripts/lean_verify.sh <file>), run concurrently in batches of 4:
- positive_control.lean -> exit 0 (VERIFIES). This is the exact gold impl.
- atk_1 PREPATCH BUG (encodedPath ++ ['/']; drops query, unconditional slash) -> exit 1 (unsolved goals; reproduces refinement.md G-DIFF: ['/'] = slash-comp ++ query-comp). prepatch_reproduced=true.
- atk_2 PARTIAL-DOMAIN (correct slash, drops query) -> exit 1.
- atk_3 BOUNDARY (unconditional slash even when path ends in '/', query kept) -> exit 1.
- atk_4 CONTROL-FLOW/ORDER (query ++ slash swapped) -> exit 1.
- atk_5 UNGROUNDED-ORACLE ECHO (wrong ':' separator instead of '?') -> exit 1.
- atk_6 DROPPED GUARD (always '?'::encodedQuery, emits '?' for empty query) -> exit 1.
- atk_7 WRONG PREDICATE (encodedPath.head? instead of getLast? for slash test) -> exit 1.
- atk_9 DIVERGING/PARTIAL-CORRECTNESS PROBE (infinite while-loop then returns wrong value encodedPath++['/']) -> exit 1. Velvet's done_with binds the loop-exit state into the postcondition obligation, so vacuous-post divergence does NOT slip through; the wrong return still leaves ['/'] = ... unsolved. The termination=partial setting does not open the classic verify-not-terminate hole here.
- atk_8 (correct-but-match-rewritten, intended positive) -> exit 1: fails ONLY because the FROZEN proof script `simp [redirectTarget]` cannot fold the match form; not counted as a verifying wrong impl. Confirms the proof script is rigid but the point stands: no WRONG impl verified.

RESOLVE (step 2): vacuously satisfied — ZERO same-spec wrong impls verify, so there is no faithful refined patch to materialize/run through run_resolve. patches={}.

G-AX / A-REFERENCE (deep-model correspondence, the only non-R/I trust point): ran axiom_check.py against the REAL repo worktree at base_commit 55bcbd8d172b689811fae17cde2f09218dd74e9c (verified git HEAD + sites.py:456 prepatch line). Command: python3 axiom_check.py -> exit 0, 'redirectTarget deep model (== real get_full_path(force_append_slash=True)) sound on 100 boundary + 20000 fuzz (path, query) pairs.' The deep model equals the real gold callee, so verify(assembly) => equals get_full_path(force_append_slash=True) => resolves.

REFINEMENT.MD LEG AUDIT: legs A1=R, A2=R, A3=I+R, A4=I+R, A5=A-reference+I. Every leg is R / A-reference / I; no kind-3 inexpressible-changed-op. The single A-reference (A5/§3.1) correspondence to the real callee get_full_path(force_append_slash=True) is validated by the G-AX run above. mapping.md §2 bijection (escape_uri_path/iri_to_uri outputs as carriers; endswith('/') <-> getLast?=some '/'; iri_to_uri('')=='') is consistent with the actual encoder safe-set and is exercised by both axiom_check.py and conformance_check.py.

CONCLUSION: The frozen spec is an exact functional equality with no preconditions and total domain; it admits a unique correct output per input, the gold impl verifies, all 8 distinct genuine wrong impls (partial-domain, boundary, control-flow/order, ungrounded-oracle echo, dropped-guard, wrong-predicate, prepatch, diverging) fail to verify, and the one non-R/I trust point (deep-model A-reference) is G-AX-sound against the real repo. No verify-but-not-resolve counterexample exists. Verdict SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness-break attack on django__django-16612 (velvet). The modeled function redirectTarget(encodedPath, encodedQuery) := encodedPath ++ (if getLast? = some '/' then [] else ['/']) ++ (if encodedQuery = [] then [] else '?'::encodedQuery) is a deep model of the real callee HttpRequest.get_full_path(force_append_slash=True) -> _get_full_path(path, True) at django/http/request.py:183, which is `"%s%s%s" % (escape_uri_path(path), '/' if force and not path.endswith('/') else '', ('?'+iri_to_uri(qs)) if qs else '')`. Under the mapping.md §2 bijection encodedPath=escape_uri_path(path), encodedQuery=iri_to_uri(qs), the model agrees with the real callee on ALL tested inputs.

Verification performed against the real repo worktree (@ base_commit 55bcbd8d):
1. same_spec (swebench_unified.markers, VelvetBackend.language) Solution.lean vs Solution_prepatch.lean = True (spec region byte-identical).
2. Ran the bundle's axiom_check.py against the real django: G-AX OK on 100 boundary + 20000 fuzz pairs.
3. Independent aggressive fuzz (300,000 random (path,qs) pairs; alphabet incl. control chars, %, +, %2F, unicode, empty, ?, #, &, =) comparing real get_full_path(force=True) vs model composed with real escape_uri_path/iri_to_uri: 0 divergences.
4. Probed the two guard-equivalence risks that could break the abstraction: (a) query-suffix guard — real guards on truthy RAW qs then appends '?'+iri_to_uri(qs), model guards on encodedQuery==''. Confirmed Python quote() never maps a nonempty string to '' (quote is length-nondecreasing), so encodedQuery=='' ⇔ qs=='' exactly; no input where real emits a bare '?' while model omits it. (b) trailing-slash guard — escape_uri_path keeps '/' in its safe set and no character encodes to '/', so encodedPath ends in '/' iff raw path does, matching path.endswith('/').
5. Solution.lean elaborates cleanly (lean_verify.sh exit 0); Solution_prepatch.lean (drops query) correctly fails on the query-suffix clause.

No diverging input exists on the reachable domain. The spec is not too strong and does not drift from real repo behavior.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Verified same_spec(Solution.lean, Solution_prepatch.lean)=True (byte-identical spec regions; only the impl region differs). Mechanical leakage.screen over the spec view passes with zero hard_failures. The spec-view projection exposes: signatures + the axioms/pure comment blocks + `redirectTarget = encodedPath ++ (if getLast?=some '/' then [] else ['/']) ++ (if encodedQuery=[] then [] else '?'::encodedQuery)` + the `ensures out = redirectTarget ...` obligation; the impl and prove_correct bodies are elided. Assessed against the PUBLIC problem_statement only (not hints_text): the problem_statement already states the bug (query string dropped in append-slash redirect), quotes the exact broken line `HttpResponsePermanentRedirect("%s/" % request.path)`, gives the expected observable behavior (.../foo -> .../foo/?id=123 = path + trailing slash + preserved query after '?'), and even names request.META['QUERY_STRING'] as the source of the query. The spec view pins exactly that publicly-disclosed observable behavior (path, conditional slash, preserved query-after-'?') and nothing more. The gold-patch-SPECIFIC implementation identifier `request.get_full_path(force_append_slash=True)` appears ONLY in refinement.md/mapping.md (auditor docs, not the consumer spec view) and never in Solution.lean's spec regions. Encoding query-preservation in the spec is faithful specification of the issue's stated expected behavior, not reconstruction of the gold edit beyond the public statement. No spec-view line leaks the gold edit.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
