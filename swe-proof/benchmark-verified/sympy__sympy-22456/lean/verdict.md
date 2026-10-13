# P2 adversarial audit — sympy__sympy-22456

**Backend:** `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verify⇏correct witness found. 8 same-spec wrong/alternative impls closed `correct_reconstructString` with clean axioms (rc=0, 'does not depend on any axioms', zero axiom decls, zero sorry/admit); ALL 8 faithful patches were materialized and RESOLVED under the official harness (run_resolve, note=resolved). The nearest misses are atk_9/atk_11 (`not_in_args=['text']` dropped ⇒ `String('foobar').args == ('foobar',)`, which CONTRADICTS the spec's `stringArgs s = []`): both still RESOLVE, and both genuinely regress the ungraded `test_ast_replace` (passes at base, fails under them: AttributeError 'str' object has no attribute 'is_Relational'). That test is in NEITHER FAIL_TO_PASS nor PASS_TO_PASS, so the harness does not grade it — the spec is STRICTER than the oracle there, which is the safe direction for G-EQ (a task-list gap, not a spec defect).
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,18 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- PREPATCH BUG re-encoded: the value publishes its text under the keyword
+    -- convention, and the GENERIC constructor-callable rebuilds the value FROM
+    -- the data it is handed. Handed the EMPTY positional list it has no text to
+    -- rebuild from, so the positional round-trip fails.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
+    let kwargNames : List String := ["text"]
     let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
+      fun pos => match pos with
+        | (a :: _) => some a
+        | []       => none
     let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
+      fun kw => if kw.isEmpty then none else some s
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,15 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- POSITIONAL-ONLY (row 3 of refinement.md's table): the reconstruction
+    -- callable admits only the empty call, but the value STILL publishes a
+    -- keyword ("text"), so the keyword round-trip is refused.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
+    let kwargNames : List String := ["text"]
     let reconstructPositional : List StringObj → Option StringObj :=
       fun pos => if pos.isEmpty then some s else none
     let reconstructKeyword : List String → Option StringObj :=
       fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,14 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- PARTIAL DOMAIN: the positional round-trip is honoured only for a NON-EMPTY
+    -- text; the empty string is excluded from the guarantee.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
     let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
     let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
+      fun pos => if pos.isEmpty then (if s.text = "" then none else some s) else none
     let reconstructKeyword : List String → Option StringObj :=
       fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -54,21 +54,14 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- CONTROL-FLOW EFFECT: the positional round-trip SUCCEEDS but carries back a
+    -- MUTATED value (text with a marker appended) instead of the original.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
     let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
     let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
+      fun pos => if pos.isEmpty then some ⟨s.text ++ "!"⟩ else none
     let reconstructKeyword : List String → Option StringObj :=
       fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -53,25 +53,10 @@
 
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
-  fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
-    let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
-    let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
-    let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
-    match c with
-    | ReconCall.positional => reconstructPositional args
-    | ReconCall.keyword => reconstructKeyword kwargNames
+  -- UNGROUNDED-ORACLE ECHO: the impl simply ECHOES the postcondition — it asserts
+  -- the round-trip succeeds on every convention without modelling any
+  -- reconstruction data or callable at all.
+  fun _ => some s
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,24 +54,15 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
-    let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
-    let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
-    let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
-    match c with
-    | ReconCall.positional => reconstructPositional args
-    | ReconCall.keyword => reconstructKeyword kwargNames
+    -- INTRINSIC-TEXT SPELLING: the value's text is not a reconstruction slot at
+    -- all, so the value publishes NO data under EITHER convention (the positional
+    -- list and the keyword mapping are both empty because there is nothing to
+    -- report, not because a report was suppressed).
+    let published : ReconCall → List String := fun _ => []
+    -- The reconstruction callable consumes no reconstruction data and yields the
+    -- value itself.
+    let recon : List String → Option StringObj := fun _ => some s
+    recon (published c)
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,21 +54,13 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- RE-KEYED SELF-REPORT + TOLERANT CALLABLE: the value publishes a keyword
+    -- under a DIFFERENT name, and the reconstruction callable admits ANY data
+    -- whatsoever, so both round-trips still carry the value back.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
-    let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
-    let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
+    let kwargNames : List String := ["texte"]
+    let reconstructPositional : List StringObj → Option StringObj := fun _ => some s
+    let reconstructKeyword : List String → Option StringObj := fun _ => some s
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,21 +54,14 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- FRESH-VALUE CALLABLE: the callable does not return the value itself, it
+    -- CONSTRUCTS a new value carrying the same text.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
     let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
     let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
+      fun pos => if pos.isEmpty then some ⟨s.text⟩ else none
     let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
+      fun kw => if kw.isEmpty then some { text := s.text } else none
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,21 +54,18 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
-    let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
+    -- POSITIONAL PUBLICATION: the value reports its text as a POSITIONAL child
+    -- (it is not held back from the positional list), and the GENERIC
+    -- constructor-callable rebuilds the value from whatever data it is handed —
+    -- from the positional child on one convention, from the keyword on the other.
+    let args : List StringObj := [s]
+    let kwargNames : List String := ["text"]
     let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
+      fun pos => match pos with
+        | (a :: _) => some a
+        | []       => none
     let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
+      fun kw => if kw.isEmpty then none else some s
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,21 +54,13 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- MULTI-KEY SELF-REPORT + TOLERANT CALLABLE: the value publishes SEVERAL
+    -- reconstruction keywords, and the callable admits any data it is handed and
+    -- yields the value itself.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
-    let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
-    let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
+    let kwargNames : List String := ["text", "origin"]
+    let reconstructPositional : List StringObj → Option StringObj := fun _ => some s
+    let reconstructKeyword : List String → Option StringObj := fun _ => some s
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,21 +54,18 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
-    let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
+    -- DEFAULTED-SLOT CALLABLE: the value publishes its text as a positional child
+    -- AND under the keyword convention, and the reconstruction callable carries a
+    -- DEFAULT for the text, so it admits the empty call as well as the published
+    -- data. Every convention round-trips.
+    let args : List StringObj := [s]
+    let kwargNames : List String := ["text"]
     let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
+      fun pos => match pos with
+        | (a :: _) => some a
+        | []       => some ⟨""⟩          -- the default text
     let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
+      fun kw => if kw.isEmpty then some ⟨""⟩ else some s
     match c with
     | ReconCall.positional => reconstructPositional args
     | ReconCall.keyword => reconstructKeyword kwargNames
```

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -54,24 +54,17 @@
 -- impl-start
 def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
   fun c =>
-    -- The positional argument list the value reports about itself (empty for an
-    -- atomic value).
+    -- ROW-4 ALTERNATIVE (refinement.md's documented correct alternative): the
+    -- value still publishes its text under the keyword convention, but the
+    -- reconstruction callable is TOLERANT — it admits whatever data it is handed
+    -- and yields the value itself. Agreement is reached by widening the callable
+    -- rather than by emptying the self-report.
     let args := stringArgs s
-    -- The keyword argument names the value reports about itself. An atomic value
-    -- publishes no reconstruction keywords, so the mapping is empty too.
-    let kwargNames : List String := []
-    -- The value's reconstruction callable. It consumes NO reconstruction data at
-    -- all and yields the value itself, so it admits exactly the empty positional
-    -- list and the empty keyword mapping — which is precisely the data the value
-    -- publishes under each convention.
-    let reconstructPositional : List StringObj → Option StringObj :=
-      fun pos => if pos.isEmpty then some s else none
-    let reconstructKeyword : List String → Option StringObj :=
-      fun kw => if kw.isEmpty then some s else none
-    -- Apply the callable to the value's own self-reported data, per convention.
+    let kwargNames : List String := ["text"]
+    let reconstruct : List String → Option StringObj := fun _ => some s
     match c with
-    | ReconCall.positional => reconstructPositional args
-    | ReconCall.keyword => reconstructKeyword kwargNames
+    | ReconCall.positional => (fun _ => some s) args
+    | ReconCall.keyword => reconstruct kwargNames
 -- impl-end
 
 -- proof-start
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the reconstruction round-trip of
-- an atomic string value is modeled DEEPLY below (the impl spells out applying the
-- value's reconstruction callable to the argument data the value reports about
-- itself, under each argument-passing convention). No outside callee is invoked,
-- hence no consumed axiom and no A-reference. The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An atomic string value: it carries its text as intrinsic data. -/
structure StringObj where
  text : String
deriving DecidableEq, Repr

/-- The positional argument list of an atomic string value. An atomic value
exposes NO positional children — its text is intrinsic, not a positional
argument — so the list is empty. (This is the `args` in `expr.func(*expr.args)`.) -/
def stringArgs (_s : StringObj) : List StringObj := []

/-- The argument-passing conventions under which a value reports its own
reconstruction data: as a positional list (the `args` in
`expr.func(*expr.args)`) and as a keyword mapping (the `kwargs()` in
`expr.func(**expr.kwargs())`). Both are conventions the same value publishes
about itself, so both describe the same single reconstruction. -/
inductive ReconCall where
  | positional : ReconCall
  | keyword : ReconCall
deriving DecidableEq, Repr, Fintype
-- pure-end

-- post-conditions-start
/-- Argument-reconstruction invariance for an atomic string value, under EVERY
argument-passing convention that value publishes about itself. Handing the
value's reconstruction callable the value's OWN self-reported argument data
reproduces the original value: `expr.func(*expr.args) == expr` for the
positional list, and equally `expr.func(**expr.kwargs()) == expr` for the
keyword mapping. On each convention the round-trip SUCCEEDS and carries back
exactly the input value (`= some s`); the results are fully determined by the
input (frame: nothing is left unconstrained), and `none` — a call the callable
does not admit, or one that yields a different value — is excluded. The
quantifier is the substance of the clause: the two conventions describe one
value's single reconstruction, so honouring the data the value publishes under
one convention while refusing the data it publishes under the other does NOT
satisfy this. -/
def problem_spec_reconstructString (s : StringObj)
    (result : ReconCall → Option StringObj) : Prop :=
  ∀ c : ReconCall, result c = some s
-- post-conditions-end

-- impl-start
def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
  fun c =>
    -- The positional argument list the value reports about itself (empty for an
    -- atomic value).
    let args := stringArgs s
    -- The keyword argument names the value reports about itself. An atomic value
    -- publishes no reconstruction keywords, so the mapping is empty too.
    let kwargNames : List String := []
    -- The value's reconstruction callable. It consumes NO reconstruction data at
    -- all and yields the value itself, so it admits exactly the empty positional
    -- list and the empty keyword mapping — which is precisely the data the value
    -- publishes under each convention.
    let reconstructPositional : List StringObj → Option StringObj :=
      fun pos => if pos.isEmpty then some s else none
    let reconstructKeyword : List String → Option StringObj :=
      fun kw => if kw.isEmpty then some s else none
    -- Apply the callable to the value's own self-reported data, per convention.
    match c with
    | ReconCall.positional => reconstructPositional args
    | ReconCall.keyword => reconstructKeyword kwargNames
-- impl-end

-- proof-start
theorem correct_reconstructString : ∀ s : StringObj,
    problem_spec_reconstructString s (implementation_reconstructString s) := by
  intro s
  unfold problem_spec_reconstructString implementation_reconstructString
  intro c
  cases c <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-22456, backend lean. Attacks built by splicing ONLY the text between `-- impl-start`/`-- impl-end` of the bundle's Solution.lean, so axioms/pure/pre/post stay byte-identical. FINAL same_spec sweep after all edits: 13/13 files (atk_1..atk_12 + pos_control) = True, 0 mismatches, via markers.same_spec(Solution.lean, atk_N.lean, get_backend('lean').language).

### COMMANDS (from swe-proof):
  bash scripts/lean_verify.sh <S>/atk_N.lean
  bash scripts/lean_verify.sh <S>/ax_atk_N.lean      # same file + `#print axioms correct_reconstructString`
  bash scripts/lean_verify.sh <S>/neg_atk_N.lean     # machine-checked NEGATION theorem
  python3 <S>/resolve_one.py atk_N <S>/patch_atk_N.diff # swebench_unified.harness.run_resolve(instance, patch, timeout=1800)
Verifications and resolves were run 4-at-a-time as concurrent background jobs (schedule only; every attack fully verified).

### LEDGER (verify rc / axioms / resolve)
pos_control.lean (gold impl, byte-identical)   rc=0   clean ('does not depend on any axioms')  — POSITIVE CONTROL OK
gold patch.diff                                 —      —    graded-test control RESOLVED=True locally + F2P/P2P green
prepatch: reproduced. Real repo at base_commit (fresh worktree from the upstream repository @ a3475b3f9a) shows `String('foobar').func(*args)` raises TypeError('No value for text given and attribute has no default') while `func(**kwargs())` is True; graded rig gives F2P_ok=False (test_String fails), P2P_ok=True — exactly row 1 of refinement.md's table.

REJECTED BY THE SPEC (verify rc=1) — 4, each additionally shown GENUINELY FALSE (not merely rfl-shy) by a machine-checked negation theorem at exit 0:
  atk_1  PREPATCH BUG re-encoded (generic constructor-callable; kwargNames=["text"]; empty positional list ⇒ none)  rc=1; neg_atk_1.lean rc=0 proves ¬spec at c=positional for ⟨"foobar"⟩ (needed `simp [..., stringArgs]`).
  atk_2  positional-only / row-3 (callable admits only the empty call; value still publishes ["text"])              rc=1; neg_atk_2.lean rc=0 (¬spec at c=keyword) — fails on the OPPOSITE convention to atk_1, so the ∀ quantifier is load-bearing in BOTH directions.
  atk_3  PARTIAL DOMAIN (positional leg honoured only for non-empty text)                                           rc=1; neg_atk_3.lean rc=0 (¬spec at ⟨""⟩).
  atk_4  CONTROL-FLOW EFFECT (positional leg succeeds but returns ⟨s.text ++ "!"⟩)                                   rc=1; neg_atk_4.lean rc=0.

CLOSED WITH CLEAN AXIOMS (verify rc=0; `#print axioms` = 'does not depend on any axioms'; zero `axiom` decls; zero tactic sorry/admit) — 8, EVERY ONE with a MATERIALIZED faithful patch RUN through run_resolve:
  atk_5  UNGROUNDED-ORACLE ECHO (`fun _ => some s`; impl IS the postcondition)          → patch_atk_5.diff   RESOLVED=True note=resolved
  atk_6  publishes nothing on either convention; callable ignores all data              → patch_atk_6.diff   RESOLVED=True note=resolved
  atk_7  RE-KEYED self-report {'texte':...} + tolerant callable                          → patch_atk_7.diff   RESOLVED=True note=resolved
  atk_8  callable CONSTRUCTS a fresh equal value instead of returning self               → patch_atk_8.diff   RESOLVED=True note=resolved
  atk_9  POSITIONAL publication (not_in_args dropped), generic constructor-callable      → patch_atk_9.diff   RESOLVED=True note=resolved
  atk_10 multi-key self-report {'text','origin'} + tolerant callable                     → patch_atk_10.diff  RESOLVED=True note=resolved
  atk_11 DEFAULTED-slot callable + positional publication                                → patch_atk_11.diff  RESOLVED=True note=resolved
  atk_12 ROW-4 documented alternative (tolerant callable, kwargs() left as {'text':...})  → patch_atk_12.diff  RESOLVED=True note=resolved
So NO closing-clean-axiom impl has a non-resolving faithful patch ⇒ no verify⇏correct witness. NOT BROKEN.

MODEL↔PATCH CORRESPONDENCE MEASURED FOR EVERY CLOSER (fresh worktree @ base_commit + test_patch; observables String('foobar').args /.kwargs() keys / both round-trips / identity-of-result). Each patch reproduces its Lean model EXACTLY:
  atk_5 nargs=0 kwkeys=[] pos=T kw=T self=T | atk_6 nargs=0 kwkeys=[] pos=T kw=T self=T | atk_7 nargs=0 kwkeys=['texte'] pos=T kw=T | atk_8 nargs=0 kwkeys=[] pos=T kw=T self=FALSE (fresh instance, matches ⟨s.text⟩ spelling) | atk_9 nargs=1 kwkeys=['text'] pos=T kw=T | atk_10 nargs=0 kwkeys=['origin','text'] pos=T kw=T | atk_11 nargs=1 kwkeys=['text'] pos=T kw=T | atk_12 nargs=0 kwkeys=['text'] pos=T kw=T self=T.

### A-LEG AUDIT (my assigned focus; R/I legs are G-CONF's):
- axioms region declares NO opaque callee and NO `axiom` — consistent with reality: all 8 closers and the pos_control print 'does not depend on any axioms', so there is no consumed axiom to validate and nothing hidden behind an unproven assumption. Kind-3 (changed-inexpressible) legs: NONE.
- refinement.md legs: row 1 = R, row 2 = R, row 3 = A-reference. Every leg is R / A-reference; no A-consumed, no kind-3. Matches docs/architecture.md §5's requirement.
- A-reference (row 3) correspondence VERIFIED against the REAL patched callee: under the gold patch, over 3010 values (boundary catalogue: '', 'a', ' ', 500 chars, newline, unicode, 'text', 'None', '0' + 3000 seeded-random) I measured `obj.args == ()` (row 1), `list(obj.kwargs().keys()) == []` (row 2), and both `obj.func(*obj.args)` and `obj.func(**obj.kwargs())` returning a String equal to obj (row 3): 0 mismatches. So the deep model's claim 'the callable admits exactly what the value publishes, on both conventions' is what the real `String(Atom, Token)` does, and the A-reference is not a disguised assumption.
- mapping.md's claim that `kwargs() == {}` is deliberately NOT pinned is CORRECT and load-bearing: atk_12 (row 4) leaves kwargs()=={'text':...}, closes the proof, and resolves — confirming the spec pins the AGREEMENT between publication and admission rather than the gold spelling.

### ADDITIONAL FALSIFICATION PROBES (encoded + run locally against the graded F2P/P2P list; none yielded a witness, so not submitted as attacks):
- probeD (extra defaulted slot 'origin' in not_in_args): kwargs()={'text','origin'}, positional round-trip RAISES TypeError ⇒ does NOT resolve — but its Lean model is the already-REJECTED prepatch shape (none at c=positional), so it is not a witness.
- probeE (kwargs() with narrowed signature, dropping exclude/apply): resolves; same observables as atk_5.
- probeF (callable returns plain String(self.text), subclass-blind): resolves.
- probeG (modeled observables IDENTICAL to gold — args=(), kwargs={}, both round-trips → self — but the UNMODELED `is_Atom` flipped to False): does NOT resolve (F2P test_String fails on `assert st.is_Atom`). This is NOT a verify⇏correct witness: `is_Atom` is True ALREADY AT BASE_COMMIT and the gold patch does not touch it, so flipping it is an unrelated gratuitous regression outside the modeled delta, not a faithful refinement of any same-spec impl. Worth noting for the panel gates as the one graded assertion the Lean model is silent about.

OVER-STRENGTH / TASK-LIST GAP (for the panel gates, NOT a G-EQ break): the spec pins `stringArgs s = []` (row 1), yet atk_9 and atk_11 drop `not_in_args` so the real `args` becomes ('foobar',) — contradicting the model — and STILL resolve, while genuinely regressing the ungraded `test_ast_replace` (verified: passes at base, fails under atk_9 and atk_11 with AttributeError 'str' object has no attribute 'is_Relational'). The spec is stricter than the oracle here, which is the safe direction; the harness simply does not grade that test.

**VERDICT:** SOUND. 12 same-spec attacks encoded and fully run (4 correctly rejected, each with a machine-checked negation theorem including the reproduced prepatch bug; 8 closing with clean axioms). Every closing attack's faithful patch was materialized and EXECUTED through the official run_resolve, and all 8 RESOLVED — no verify⇏correct witness exists among them. Positive control verifies with clean axioms.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 12 admissible attacks re-run of 12 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 12 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 8 | `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean`, `atk_12.lean` |
| does not verify against this specification, so the specification excludes it | 4 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no verify⇏correct witness found. 8 same-spec wrong/alternative impls closed `correct_reconstructString` with clean axioms (rc=0, 'does not depend on any axioms', zero axiom decls, zero sorry/admit); ALL 8 faithful patches were materialized and RESOLVED under the official harness (run_resolve, note=resolved). The nearest misses are atk_9/atk_11 (`not_in_args=['text']` dropped ⇒ `String('foobar').args == ('foobar',)`, which CONTRADICTS the spec's `stringArgs s = []`): both still RESOLVE, and both genuinely regress the ungraded `test_ast_replace` (passes at base, fails under them: AttributeError 'str' object has no attribute 'is_Relational'). That test is in NEITHER FAIL_TO_PASS nor PASS_TO_PASS, so the harness does not grade it — the spec is STRICTER than the oracle there, which is the safe direction for G-EQ (a task-list gap, not a spec defect).
```

**Attacks re-run (12):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 12 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 9 — `atk_9.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 10 — `atk_10.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 11 — `atk_11.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 12 — `atk_12.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature: the reconstruction round-trip of
-- an atomic string value is modeled DEEPLY below (the impl spells out applying the
-- value's reconstruction callable to the argument data the value reports about
-- itself, under each argument-passing convention). No outside callee is invoked,
-- hence no consumed axiom and no A-reference. The proof agent may add `_prop`
-- axioms only if genuinely stuck.
-- axioms-end

-- pure-start
/-- An atomic string value: it carries its text as intrinsic data. -/
structure StringObj where
  text : String
deriving DecidableEq, Repr

/-- The positional argument list of an atomic string value. An atomic value
exposes NO positional children — its text is intrinsic, not a positional
argument — so the list is empty. (This is the `args` in `expr.func(*expr.args)`.) -/
def stringArgs (_s : StringObj) : List StringObj := []

/-- The argument-passing conventions under which a value reports its own
reconstruction data: as a positional list (the `args` in
`expr.func(*expr.args)`) and as a keyword mapping (the `kwargs()` in
`expr.func(**expr.kwargs())`). Both are conventions the same value publishes
about itself, so both describe the same single reconstruction. -/
inductive ReconCall where
  | positional : ReconCall
  | keyword : ReconCall
deriving DecidableEq, Repr, Fintype
-- pure-end

-- post-conditions-start
/-- Argument-reconstruction invariance for an atomic string value, under EVERY
argument-passing convention that value publishes about itself. Handing the
value's reconstruction callable the value's OWN self-reported argument data
reproduces the original value: `expr.func(*expr.args) == expr` for the
positional list, and equally `expr.func(**expr.kwargs()) == expr` for the
keyword mapping. On each convention the round-trip SUCCEEDS and carries back
exactly the input value (`= some s`); the results are fully determined by the
input (frame: nothing is left unconstrained), and `none` — a call the callable
does not admit, or one that yields a different value — is excluded. The
quantifier is the substance of the clause: the two conventions describe one
value's single reconstruction, so honouring the data the value publishes under
one convention while refusing the data it publishes under the other does NOT
satisfy this. -/
def problem_spec_reconstructString (s : StringObj)
    (result : ReconCall → Option StringObj) : Prop :=
  ∀ c : ReconCall, result c = some s
-- post-conditions-end

-- impl-start
def implementation_reconstructString (s : StringObj) : ReconCall → Option StringObj :=
  fun c =>
    -- The positional argument list the value reports about itself (empty for an
    -- atomic value).
    let args := stringArgs s
    -- The keyword argument names the value reports about itself. An atomic value
    -- publishes no reconstruction keywords, so the mapping is empty too.
    let kwargNames : List String := []
    -- The value's reconstruction callable. It consumes NO reconstruction data at
    -- all and yields the value itself, so it admits exactly the empty positional
    -- list and the empty keyword mapping — which is precisely the data the value
    -- publishes under each convention.
    let reconstructPositional : List StringObj → Option StringObj :=
      fun pos => if pos.isEmpty then some s else none
    let reconstructKeyword : List String → Option StringObj :=
      fun kw => if kw.isEmpty then some s else none
    -- Apply the callable to the value's own self-reported data, per convention.
    match c with
    | ReconCall.positional => reconstructPositional args
    | ReconCall.keyword => reconstructKeyword kwargNames
-- impl-end

-- proof-start
theorem correct_reconstructString : ∀ s : StringObj,
    problem_spec_reconstructString s (implementation_reconstructString s) := by
  intro s
  unfold problem_spec_reconstructString implementation_reconstructString
  intro c
  cases c <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

G-EQ (refinement fidelity) for sympy__sympy-22456, backend lean. Attacks built by splicing ONLY the text between `-- impl-start`/`-- impl-end` of the bundle's Solution.lean, so axioms/pure/pre/post stay byte-identical. FINAL same_spec sweep after all edits: 13/13 files (atk_1..atk_12 + pos_control) = True, 0 mismatches, via markers.same_spec(Solution.lean, atk_N.lean, get_backend('lean').language).

### COMMANDS (from swe-proof):
  bash scripts/lean_verify.sh <S>/atk_N.lean
  bash scripts/lean_verify.sh <S>/ax_atk_N.lean      # same file + `#print axioms correct_reconstructString`
  bash scripts/lean_verify.sh <S>/neg_atk_N.lean     # machine-checked NEGATION theorem
  python3 <S>/resolve_one.py atk_N <S>/patch_atk_N.diff # swebench_unified.harness.run_resolve(instance, patch, timeout=1800)
Verifications and resolves were run 4-at-a-time as concurrent background jobs (schedule only; every attack fully verified).

### LEDGER (verify rc / axioms / resolve)
pos_control.lean (gold impl, byte-identical)   rc=0   clean ('does not depend on any axioms')  — POSITIVE CONTROL OK
gold patch.diff                                 —      —    graded-test control RESOLVED=True locally + F2P/P2P green
prepatch: reproduced. Real repo at base_commit (fresh worktree from the upstream repository @ a3475b3f9a) shows `String('foobar').func(*args)` raises TypeError('No value for text given and attribute has no default') while `func(**kwargs())` is True; graded rig gives F2P_ok=False (test_String fails), P2P_ok=True — exactly row 1 of refinement.md's table.

REJECTED BY THE SPEC (verify rc=1) — 4, each additionally shown GENUINELY FALSE (not merely rfl-shy) by a machine-checked negation theorem at exit 0:
  atk_1  PREPATCH BUG re-encoded (generic constructor-callable; kwargNames=["text"]; empty positional list ⇒ none)  rc=1; neg_atk_1.lean rc=0 proves ¬spec at c=positional for ⟨"foobar"⟩ (needed `simp [..., stringArgs]`).
  atk_2  positional-only / row-3 (callable admits only the empty call; value still publishes ["text"])              rc=1; neg_atk_2.lean rc=0 (¬spec at c=keyword) — fails on the OPPOSITE convention to atk_1, so the ∀ quantifier is load-bearing in BOTH directions.
  atk_3  PARTIAL DOMAIN (positional leg honoured only for non-empty text)                                           rc=1; neg_atk_3.lean rc=0 (¬spec at ⟨""⟩).
  atk_4  CONTROL-FLOW EFFECT (positional leg succeeds but returns ⟨s.text ++ "!"⟩)                                   rc=1; neg_atk_4.lean rc=0.

CLOSED WITH CLEAN AXIOMS (verify rc=0; `#print axioms` = 'does not depend on any axioms'; zero `axiom` decls; zero tactic sorry/admit) — 8, EVERY ONE with a MATERIALIZED faithful patch RUN through run_resolve:
  atk_5  UNGROUNDED-ORACLE ECHO (`fun _ => some s`; impl IS the postcondition)          → patch_atk_5.diff   RESOLVED=True note=resolved
  atk_6  publishes nothing on either convention; callable ignores all data              → patch_atk_6.diff   RESOLVED=True note=resolved
  atk_7  RE-KEYED self-report {'texte':...} + tolerant callable                          → patch_atk_7.diff   RESOLVED=True note=resolved
  atk_8  callable CONSTRUCTS a fresh equal value instead of returning self               → patch_atk_8.diff   RESOLVED=True note=resolved
  atk_9  POSITIONAL publication (not_in_args dropped), generic constructor-callable      → patch_atk_9.diff   RESOLVED=True note=resolved
  atk_10 multi-key self-report {'text','origin'} + tolerant callable                     → patch_atk_10.diff  RESOLVED=True note=resolved
  atk_11 DEFAULTED-slot callable + positional publication                                → patch_atk_11.diff  RESOLVED=True note=resolved
  atk_12 ROW-4 documented alternative (tolerant callable, kwargs() left as {'text':...})  → patch_atk_12.diff  RESOLVED=True note=resolved
So NO closing-clean-axiom impl has a non-resolving faithful patch ⇒ no verify⇏correct witness. NOT BROKEN.

MODEL↔PATCH CORRESPONDENCE MEASURED FOR EVERY CLOSER (fresh worktree @ base_commit + test_patch; observables String('foobar').args /.kwargs() keys / both round-trips / identity-of-result). Each patch reproduces its Lean model EXACTLY:
  atk_5 nargs=0 kwkeys=[] pos=T kw=T self=T | atk_6 nargs=0 kwkeys=[] pos=T kw=T self=T | atk_7 nargs=0 kwkeys=['texte'] pos=T kw=T | atk_8 nargs=0 kwkeys=[] pos=T kw=T self=FALSE (fresh instance, matches ⟨s.text⟩ spelling) | atk_9 nargs=1 kwkeys=['text'] pos=T kw=T | atk_10 nargs=0 kwkeys=['origin','text'] pos=T kw=T | atk_11 nargs=1 kwkeys=['text'] pos=T kw=T | atk_12 nargs=0 kwkeys=['text'] pos=T kw=T self=T.

### A-LEG AUDIT (my assigned focus; R/I legs are G-CONF's):
- axioms region declares NO opaque callee and NO `axiom` — consistent with reality: all 8 closers and the pos_control print 'does not depend on any axioms', so there is no consumed axiom to validate and nothing hidden behind an unproven assumption. Kind-3 (changed-inexpressible) legs: NONE.
- refinement.md legs: row 1 = R, row 2 = R, row 3 = A-reference. Every leg is R / A-reference; no A-consumed, no kind-3. Matches docs/architecture.md §5's requirement.
- A-reference (row 3) correspondence VERIFIED against the REAL patched callee: under the gold patch, over 3010 values (boundary catalogue: '', 'a', ' ', 500 chars, newline, unicode, 'text', 'None', '0' + 3000 seeded-random) I measured `obj.args == ()` (row 1), `list(obj.kwargs().keys()) == []` (row 2), and both `obj.func(*obj.args)` and `obj.func(**obj.kwargs())` returning a String equal to obj (row 3): 0 mismatches. So the deep model's claim 'the callable admits exactly what the value publishes, on both conventions' is what the real `String(Atom, Token)` does, and the A-reference is not a disguised assumption.
- mapping.md's claim that `kwargs() == {}` is deliberately NOT pinned is CORRECT and load-bearing: atk_12 (row 4) leaves kwargs()=={'text':...}, closes the proof, and resolves — confirming the spec pins the AGREEMENT between publication and admission rather than the gold spelling.

### ADDITIONAL FALSIFICATION PROBES (encoded + run locally against the graded F2P/P2P list; none yielded a witness, so not submitted as attacks):
- probeD (extra defaulted slot 'origin' in not_in_args): kwargs()={'text','origin'}, positional round-trip RAISES TypeError ⇒ does NOT resolve — but its Lean model is the already-REJECTED prepatch shape (none at c=positional), so it is not a witness.
- probeE (kwargs() with narrowed signature, dropping exclude/apply): resolves; same observables as atk_5.
- probeF (callable returns plain String(self.text), subclass-blind): resolves.
- probeG (modeled observables IDENTICAL to gold — args=(), kwargs={}, both round-trips → self — but the UNMODELED `is_Atom` flipped to False): does NOT resolve (F2P test_String fails on `assert st.is_Atom`). This is NOT a verify⇏correct witness: `is_Atom` is True ALREADY AT BASE_COMMIT and the gold patch does not touch it, so flipping it is an unrelated gratuitous regression outside the modeled delta, not a faithful refinement of any same-spec impl. Worth noting for the panel gates as the one graded assertion the Lean model is silent about.

OVER-STRENGTH / TASK-LIST GAP (for the panel gates, NOT a G-EQ break): the spec pins `stringArgs s = []` (row 1), yet atk_9 and atk_11 drop `not_in_args` so the real `args` becomes ('foobar',) — contradicting the model — and STILL resolve, while genuinely regressing the ungraded `test_ast_replace` (verified: passes at base, fails under atk_9 and atk_11 with AttributeError 'str' object has no attribute 'is_Relational'). The spec is stricter than the oracle here, which is the safe direction; the harness simply does not grade that test.

**VERDICT:** SOUND. 12 same-spec attacks encoded and fully run (4 correctly rejected, each with a machine-checked negation theorem including the reproduced prepatch bug; 8 closing with clean axioms). Every closing attack's faithful patch was materialized and EXECUTED through the official run_resolve, and all 8 RESOLVED — no verify⇏correct witness exists among them. Positive control verifies with clean axioms.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL attacker (2) faithfulness-break for sympy__sympy-22456. Searched for an input where problem_spec_reconstructString / implementation_reconstructString disagrees with the REAL patched callee. Found none.

REFERENCE SETUP (per instructions): fresh worktree of sympy_sympy.git at base a3475b3f9ac662cd425157dd3bdb93ad7111c090 with patch.diff APPLIED = the modeled function's reference. A separate pristine base worktree was used only to confirm the pre-patch delta (not treated as the reference). mpmath supplied via PYTHONPATH.

### REAL POST-PATCH BEHAVIOR (measured):
- String('foo').args == (), String('foo').kwargs() == {}, String.func is the property returning `lambda: self`.
- obj.func(*obj.args) == obj -> True; obj.func(**obj.kwargs()) == obj -> True. Same for QuotedString and Comment, and for the test's Signifier(String) subclass (args=(), kwargs={}, both legs True).
- Construction paths all converge: String('foo'), String(text='foo'), String(String('foo')) all give args=(), kwargs={}, both round-trips True.
- Pre-patch (base, for the delta only): args=(), kwargs={'text':'foo'}, func = class String; positional leg raises TypeError("No value for 'text' given and attribute has no default"), keyword leg True. Exactly refinement.md row 1 / mapping.md 'Behavior: pre vs post'. I did NOT report this as a divergence.

SPEC-vs-REAL DIFFERENTIAL (attempted breaks, all failed to break):
1. conformance_check.py against the real patched String: G-CONF PASS, 0 disagreements over 240026 observations (120013 values x 2 conventions, seed=22456). Both conventions observed, matching the quantifier.
2. Independent heavy fuzz I wrote myself (not the bundled one): 20k random full-Unicode strings (codepoints 1..0x10FFFF) plus boundary catalogue (empty, NUL, '\x00abc', 100k-char, whitespace-only, 'text', 'self', 'args', 'func', 'kwargs', '%s', '{}', backslash, chr(0x10FFFF)) x {String, QuotedString, Comment}, checking construction, args == (), and BOTH round-trip legs. Violations: 0. No input makes the real callee return anything the spec models as `none`.
3. Over-strength probes on the two axes the spec pins:
   - Row 3 (positional-only): built a real variant worktree — String(Atom, Token) + func = `lambda: self` but kwargs() left slot-derived. Measured: args=(), kwargs={'text':'foo'}, positional True, keyword RAISES TypeError('unexpected keyword argument text'). Confirms the two conventions fail INDEPENDENTLY and in OPPOSITE directions from prepatch, so the ∀-over-ReconCall is load-bearing, not decorative padding.
   - Row 4 (keyword-tolerant alternative, the over-strength control): built a real variant — func = `lambda *a, **kw: self`, kwargs() left returning {'text':'foo'}. Measured: BOTH legs True and all F2P assertions pass on the real repo. The spec `∀ c, result c = some s` ACCEPTS this correct alternative — i.e. the spec pins agreement-between-published-data-and-callable, NOT the incidental `kwargs() == {}` of the gold spelling. This is the case that would have made the spec too strong, and it does not.
4. Domain-boundary probe: I hand-built a String subclass with an extra slot outside not_in_args (Tagged, `__slots__`=('text','tag')); it gets args=(String('t'),) and its positional leg raises. NOT a divergence — no such class exists anywhere in the real repo (grep for `class \w+\([^)]*String[^)]*\)` yields only QuotedString, Comment, and the test's Signifier, all with args=()); String.`__slots__`==('text',) with not_in_args==['text'] makes args==() for every real String instance, so this is outside the modeled domain (mapping.md binds StringObj to a codegen.ast.String instance). Reporting my own invented subclass as a counterexample would be fabricated.

### Artifact integrity
- markers.same_spec(Solution.lean, Solution_prepatch.lean, lean backend) == True: spec region (axioms/pure/pre/post) byte-identical, so the prepatch twin is a same-spec/different-impl pair and the delta is confined to the impl.
- scripts/lean_verify.sh Solution.lean -> exit 0 (compiles, no sorry).
- `#print axioms correct_reconstructString` -> "does not depend on any axioms". Clean: no sorryAx, no `_prop` axioms, so the proof is real, not fake.
- Non-vacuity control: I authored and compiled a DISPROOF against the prepatch impl — `¬ problem_spec_reconstructString {text:="foo"} (implementation_reconstructString...)` closes (exit 0) at c = positional. The spec genuinely rejects the buggy behavior rather than being satisfiable by anything.
- Regression: full sympy/codegen/tests/test_ast.py with the test_patch applied -> 31 passed, including F2P test_String with the new `st.func(*st.args) == st` line.

**MAPPING CHECK:** the Lean↔Python bijection holds on every point I could measure — stringArgs s = [] ↔ args == (); kwargNames = [] ↔ key set of kwargs() == {} (only the key set is modeled, which is what decides admissibility; the values are the text already carried by s.text — a sound abstraction, since kwargs(exclude=...)/kwargs(apply=...) also all return {} post-patch, measured); ReconCall.positional/keyword ↔ *args vs **kwargs(); some s ↔ equal rebuilt object, none ↔ raise/unequal.

**CONCLUSION:** no diverging input exists in the modeled domain. The spec is neither over-strong (accepts the measured correct alternative, row 4) nor drifted from the patched repo (0 disagreements over ~300k total observations across two independent fuzzers). Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** SCOPE: leakage / gold-reconstruction only, judged against the public problem_statement (instance.json hints_text is EMPTY for this row, so the public baseline is the problem_statement alone).

NO RELAXATION IN THIS BUNDLE — checked, not assumed. `json.load(meta.json).get('relaxed_leakage')` -> ABSENT (the only three occurrences of the string 'relaxed_leakage' anywhere in meta.json are inside a PRIOR G-PANEL-3 run's own note text, not a key), and `find benchmark-verified/sympy__sympy-22456 -iname '*RELAX*'` -> no hits (no RELAXED_LEAKAGE.md under lean/, velvet/, nagini/, ears/, or the instance root). So this is an ordinary strict leakage judgement with no disposition to inherit and no unavoidability argument to re-derive. I ran the load-bearing/strip test anyway (below), since it is the right check regardless.

SPEC VIEW I MEASURED (not eyeballed). markers.spec_view(Solution.lean, LeanBackend) -> sha256 302e8d90bbe860010997f113064ecf2fa08de7035bc128cfdbd60e41c6f12a8e. markers.same_spec(Solution.lean, Solution_prepatch.lean) = True; stronger, the two views are BYTE-identical (`.encode()` compare) and each of axioms/pure/pre-conditions/post-conditions region_text is byte-equal between twins (442/888/0/1079 bytes). impl and proof both collapse to the elision placeholders, so `kwargNames:= []` and the `reconstructPositional`/`reconstructKeyword` spellings — the only places the gold mechanism is echoed — are NOT in the solver-visible view. My region_hashes for all six entries reproduce meta.json's G-HYGIENE `data.region_hashes` block exactly.

**PUBLIC BASELINE.** problem_statement names verbatim: `codegen.ast`, the `String` class, `expr.func(*expr.args) == expr`, `expr.func(**expr.kwargs()) == expr`, and 'The former should hold for any `Basic` subclass, which `String` is.' So String/func/args/kwargs/Basic AND both round-trip identities AND 'both must hold' are public. The view's post-condition `∀ c: ReconCall, result c = some s` over `ReconCall = positional | keyword` is a transcription of exactly those two public identities plus a quantifier over them. The only spec-view identifiers colliding with patch-side symbols are `String`, `kwargs` (both verbatim in problem_statement) and `self` (English prose only: "about itself", "self-reported").

GOLD DISCRIMINATORS — THE VIEW NAMES NONE. patch.diff is four things: `from sympy.core.expr import Expr, Atom`; `class String(Atom, Token)`; new `kwargs()` returning `{}`; new `func` property returning `lambda: self`. Token-scanned the COMPUTED view for Atom, lambda, not_in_args, `__slots__`, property, MRO, inherit, Token, Expr, is_Atom, codegen, sympy, ast.py, 'return {}', 'kwargs() ==' -> zero hits ('Atom' matches only the English 'atomic'/'an atomic string value'; 'change' matches only '-- No UNCHANGED callee'). Normalized-whitespace compare of every added/removed gold line against the view: no line reproduced. leakage.`_NARRATION_RE` over the view -> empty set (no bug/fix/patch narration). The view never says the keyword mapping becomes empty, never says the class gains an atom base, never says the callable becomes nullary.

DECISIVE TEST — THE VIEW DOES NOT FINGERPRINT GOLD. On real sympy at base_commit a3475b3f9a (worktree; mpmath via) I built two alternative fixes and measured: ALT-B (tolerant `func` = `lambda *a, **k: self`, `kwargs()` LEFT returning `{'text':'foo'}`) -> args=(), kwargs={'text':'foo'}, pos=True kw=True — satisfies both public identities and the spec view indistinguishably from gold while leaving gold's key change (emptying the keyword mapping) UNDONE. ALT-A (`not_in_args = []`) -> args=('foo',), kwargs={'text':'foo'}, pos=True kw=True. Gold (worktree) -> args=(), kwargs={}, pos=True kw=True. Three distinct edits, one spec view: a solver reading the view cannot reconstruct which was made.

**PRE-PATCH OBSERVABILITY OF THE ONLY NON-PUBLIC-SOUNDING CLAIM.** The view asserts atomicity and `stringArgs s = []`. Both are facts of the UNPATCHED tree: at base_commit `String('foo').args == ()`, `is_Atom = True`, `__slots__=('text',)`, `not_in_args=['text']`, and ast.py:875 already reads 'Atomic object which is not an expression (as opposed to Symbol).' (all read/run directly in the base worktree). A solver learns nothing from them it cannot read off the unpatched file, and they do not point at gold (ALT-B shares args=(), ALT-A violates it).

LOAD-BEARING / STRIP TEST (run though nothing claims it). Mechanically stripped every /-- -/ docblock and -- comment, keeping only marker lines and formal declarations. (a) Stripped gold verifies: lean_verify.sh exit 0. (b) Stripped spec + PREPATCH impl + the gold tactic script fails to elaborate — residual goal is the positional leg reducing to `none = some s` ("case positional... = some s" in the log), exit 1. (c) I then PROVED the rejection instead of resting on a failed proof: `theorem prepatch_violates: ¬ (∀ s, problem_spec_reconstructString s (implementation_reconstructString s))` closes via `h ⟨"foo"⟩ ReconCall.positional`, exit 0. So the FORMAL content alone discriminates pre from post; the English prose is not doing the discriminating work — the shape a non-leaking spec should have.

**GATE SOUNDNESS I CONFIRMED FIRST-HAND.** lean_verify.sh Solution.lean -> exit 0; `#print axioms correct_reconstructString` -> 'does not depend on any axioms' (clean, no sorryAx — the proof is real). Re-ran the mechanical screen myself: leakage.screen(Solution.lean, LeanBackend, patch.diff, problem_statement, test_patch) -> LeakageReport(hard_failures=[], warnings=[]), passed=True, matching meta's recorded G-LEAK 'spec view clean'. Reproduced the real bug on the repo: pre-patch `func(*args)` raises TypeError("No value for 'text' given and attribute has no default") while `func(**kwargs())` returns an equal String — the two conventions genuinely disagree pre-patch and the fix is that they agree, exactly what the quantifier encodes.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as a finding in its own right, per instruction). leakage.reviewer_directed() over instance.json, patch.diff, and every lean/ file (Solution.lean, Solution_prepatch.lean, refinement.md, mapping.md, meta.json, verdict.md, axiom_check.py, conformance_check.py, properties.py) -> [] for all. Grepped the spec-side files for panel/attacker/reviewer/'you must'/'honest verdict'/'do not submit'/NO-LEAKAGE -> zero hits. TWO things worth naming, neither a directive: (1) mapping.md:11 asserts parenthetically that func/args/kwargs/String 'are public terms (not leakage)' — an authoring rationale about the problem_statement, which I independently verified is TRUE (all four appear verbatim), not an instruction about what to record. (2) verdict.md:2315-2347 contains a PRIOR G-PANEL-3 NO-LEAKAGE note. I did not inherit it; I re-derived the view hash, the screen, the three-fix separation, and the strip test from the artifacts and the real repo before reading it, and my numbers agree (spec_view 302e8d90..., prepatch TypeError, ALT-B pos/kw both True). Nothing in the bundle told me which verdict to submit.

TWO OUT-OF-LANE OBSERVATIONS, recorded so they are not lost; neither supports LEAKAGE.

(1) OVER-PINNING, OPPOSITE SIGN FROM LEAKAGE: ALT-A (not_in_args=[]) is a genuine fix satisfying both public identities, yet it violates the view's `stringArgs s = []`. That is strength/faithfulness territory (G-PANEL-1/2), and it points a solver AWAY from a correct alternative rather than toward gold, so it cannot ground a leakage finding.

(2) STALE ARTIFACT, not a leak and not leakage-gate-relevant: meta.json's TOP-LEVEL `region_hashes` (spec_view 9deb9988..., impl b002eef0...) disagrees with my recomputation AND with meta's own G-HYGIENE data block (spec_view 302e8d90..., impl 38e69eb6...) on all six entries. I traced the cause: those hashes are the spec_view of the 2026-07-29 revision of Solution.lean (git rev 1332b51f5), which had a non-quantified single-Option post-condition; the spec was revised at rev 77445e894 to the ∀-over-ReconCall form and the top-level block was not re-stamped. G-HYGIENE's recorded data matches the shipped file byte-for-byte, so the gate that consumes hashes is consistent with what ships; flagging the stale top-level copy as a bookkeeping defect for the integrity lane.

**CONCLUSION:** the spec view transcribes the two round-trip identities the problem_statement already names verbatim, adds a quantifier over them (the public ask), and adds only pre-patch-observable atomicity facts. It names no gold symbol or mechanism, reproduces no gold line, carries no fix narration, and is satisfied equally by gold and by a MEASURED alternative fix that leaves gold's key change undone. Nothing leaks beyond the public problem_statement. NO-LEAKAGE.

**SCOPE:** leakage / gold-reconstruction only, judged against the public problem_statement (instance.json hints_text is EMPTY for this row, so the public baseline is the problem_statement alone).

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `properties.py`, `conformance_check.py`, `axiom_check.py`, all of which ship in this bundle, so a reader can start there.
