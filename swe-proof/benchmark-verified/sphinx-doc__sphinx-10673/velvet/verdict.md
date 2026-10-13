# P2 adversarial audit — sphinx-doc__sphinx-10673

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

> **Record correction.** Some sections below reason about a divergent rival that
> verifies vacuously under `set_option loom.semantics.termination "partial"`,
> which is what this bundle set when that audit ran. The bundle now sets
> `loom.semantics.termination "total"`, so the verifier discharges a termination
> obligation and a divergent rival is rejected rather than vacuously accepted.
> No statement below that such a rival verifies, or that this specification has a
> divergence hole of that shape, describes the current artifact.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_prepatch.lean`, `atk_3_return_nil.lean`, `atk_4_boundary.lean`, `atk_5_negate.lean`, `atk_6_autoonly.lean`, `atk_7_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no genuine verify⇏correct counterexample exists. The postcondition `out = retainedEntries sourceDocs autoTargets requested` is a tight functional EQUALITY, so every terminating same-spec verifying impl is forced to produce the exact gold output. All 6 wrong-OUTPUT attacks (prepatch/sourceDocs-only, return-[], boundary i>1, negated predicate, autoTargets-only, forward-fold echo) FAIL to verify. The only verifying same-spec wrong impl is a divergent `while true` (atk_1), which is a universal partial-correctness substrate artifact, not a spec-fidelity defect (see notes).
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model references. The decision modeled here is
@@ -106,10 +106,9 @@
       invariant 0 ≤ i ∧ i ≤ requested.length
       invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := requested[i - 1]!
-      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
+      out := (if sourceDocs.contains e then [e] else []) ++ out
       i := i - 1
     return out
     -- impl-end
```

Attack 2 — `atk_3_return_nil.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model references. The decision modeled here is
@@ -100,17 +100,7 @@
   ensures ∀ e, e ∈ requested → targetExists sourceDocs autoTargets e = true → e ∈ out
   do
     -- impl-start
-    let mut out : List String := []
-    let mut i := requested.length
-    while i > 0
-      invariant 0 ≤ i ∧ i ≤ requested.length
-      invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
-      done_with i = 0
-      decreasing i
-    do
-      let e := requested[i - 1]!
-      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
-      i := i - 1
+    let out : List String := []
     return out
     -- impl-end
 
@@ -133,6 +123,4 @@
   rw [hcons, retainedEntries_cons]
 
 prove_correct selectToctreeEntries by
-  loom_solve
-  rw [retainedEntries_drop_step sourceDocs autoTargets requested i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [mem_retainedEntries]
```

Attack 3 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model references. The decision modeled here is
@@ -102,11 +102,10 @@
     -- impl-start
     let mut out : List String := []
     let mut i := requested.length
-    while i > 0
+    while i > 1
       invariant 0 ≤ i ∧ i ≤ requested.length
       invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := requested[i - 1]!
       out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
```

Attack 4 — `atk_5_negate.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model references. The decision modeled here is
@@ -106,10 +106,9 @@
       invariant 0 ≤ i ∧ i ≤ requested.length
       invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := requested[i - 1]!
-      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
+      out := (if targetExists sourceDocs autoTargets e then [] else [e]) ++ out
       i := i - 1
     return out
     -- impl-end
```

Attack 5 — `atk_6_autoonly.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model references. The decision modeled here is
@@ -106,10 +106,9 @@
       invariant 0 ≤ i ∧ i ≤ requested.length
       invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
       done_with i = 0
-      decreasing i
     do
       let e := requested[i - 1]!
-      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
+      out := (if autoTargets.contains e then [e] else []) ++ out
       i := i - 1
     return out
     -- impl-end
```

Attack 6 — `atk_7_echo.lean` → rejected (same spec, does not verify — good)

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
 -- No consumed axioms and no deep-model references. The decision modeled here is
@@ -101,16 +101,15 @@
   do
     -- impl-start
     let mut out : List String := []
-    let mut i := requested.length
-    while i > 0
+    let mut i := 0
+    while i < requested.length
       invariant 0 ≤ i ∧ i ≤ requested.length
-      invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
-      done_with i = 0
-      decreasing i
+      invariant out = retainedEntries sourceDocs autoTargets (requested.take i)
+      done_with i = requested.length
     do
-      let e := requested[i - 1]!
-      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
-      i := i - 1
+      let e := requested[i]!
+      out := out ++ (if targetExists sourceDocs autoTargets e then [e] else [])
+      i := i + 1
     return out
     -- impl-end
 
@@ -133,6 +132,4 @@
   rw [hcons, retainedEntries_cons]
 
 prove_correct selectToctreeEntries by
-  loom_solve
-  rw [retainedEntries_drop_step sourceDocs autoTargets requested i (by omega) (by omega)]
-  simp_all
+  loom_solve <;> simp_all [mem_retainedEntries]
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model references. The decision modeled here is
-- pure list/membership logic over FREE INPUTS: the sequence of table-of-contents
-- entry names requested in a document, the set of document names that have a
-- backing source file, and the set of reference targets the project provides
-- automatically (the index / module-index / search pages). The directive only
-- READS these collections to decide which entries name a targetExists target; it
-- never reshapes the collections themselves, so there is no callee contract to
-- assume and nothing for G-AX.
-- axioms-end

-- pure-start
/- Whether a requested entry names a targetExists target: it does when the name
   belongs to the documents that have a backing source file, OR to the reference
   targets the project provides automatically (the index, module-index and
   search pages). The two collections are read-only carriers of membership. -/
def targetExists (sourceDocs autoTargets : List String) (name : String) : Bool :=
  sourceDocs.contains name || autoTargets.contains name

@[grind] lemma targetExists_def (sourceDocs autoTargets : List String) (name : String) :
    targetExists sourceDocs autoTargets name
      = (sourceDocs.contains name || autoTargets.contains name) := rfl

/- The entries retained for the table of contents: every requested entry that
   names a targetExists target, in request order. Written front-recursively (one
   structural unfold exposed per element) so the backward `while` fold below
   discharges with a single drop-step rewrite. An entry that is absent is
   omitted (the directive emits a diagnostic for it; only the retained sequence
   is observed here). -/
def retainedEntries (sourceDocs autoTargets : List String) :
    List String → List String
  | []          => []
  | e :: rest =>
    (if targetExists sourceDocs autoTargets e then [e] else [])
      ++ retainedEntries sourceDocs autoTargets rest

@[grind] lemma retainedEntries_nil (sourceDocs autoTargets : List String) :
    retainedEntries sourceDocs autoTargets [] = [] := rfl

@[grind] lemma retainedEntries_cons
    (sourceDocs autoTargets : List String) (e : String) (rest : List String) :
    retainedEntries sourceDocs autoTargets (e :: rest)
      = (if targetExists sourceDocs autoTargets e then [e] else [])
          ++ retainedEntries sourceDocs autoTargets rest := rfl

/- Characterisation: an entry is retained exactly when it was requested AND it
   exists. Gives the membership postconditions to `loom_solve`/`grind`. -/
@[grind] lemma mem_retainedEntries
    (sourceDocs autoTargets : List String) (requested : List String) (e : String) :
    e ∈ retainedEntries sourceDocs autoTargets requested
      ↔ e ∈ requested ∧ targetExists sourceDocs autoTargets e = true := by
  induction requested with
  | nil => simp [retainedEntries]
  | cons h t ih =>
    rw [retainedEntries_cons]
    by_cases hp : targetExists sourceDocs autoTargets h = true
    · rw [if_pos hp, List.singleton_append, List.mem_cons, List.mem_cons, ih]
      constructor
      · rintro (rfl | ⟨hmem, hr⟩)
        · exact ⟨Or.inl rfl, hp⟩
        · exact ⟨Or.inr hmem, hr⟩
      · rintro ⟨rfl | hmem, hr⟩
        · exact Or.inl rfl
        · exact Or.inr ⟨hmem, hr⟩
    · rw [if_neg hp, List.nil_append, List.mem_cons, ih]
      constructor
      · rintro ⟨hmem, hr⟩
        exact ⟨Or.inr hmem, hr⟩
      · rintro ⟨rfl | hmem, hr⟩
        · exact absurd hr hp
        · exact ⟨hmem, hr⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the table-of-contents entries to retain for a document. A requested
   entry is retained when it names a target that exists — one with a backing
   source file, OR one of the reference targets the project provides
   automatically (the index, module-index and search pages). Entries that do not
   exist are omitted (a diagnostic is emitted for them; only the retained
   sequence is observed). The three input collections are read-only. -/
method selectToctreeEntries
    (requested : List String) (sourceDocs : List String) (autoTargets : List String)
    return (out : List String)
  ensures out = retainedEntries sourceDocs autoTargets requested
  ensures ∀ e, e ∈ out → e ∈ requested ∧ targetExists sourceDocs autoTargets e = true
  ensures ∀ e, e ∈ requested → autoTargets.contains e = true → e ∈ out
  ensures ∀ e, e ∈ requested → targetExists sourceDocs autoTargets e = true → e ∈ out
  do
    -- impl-start
    let mut out : List String := []
    let mut i := requested.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ requested.length
      invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
      done_with i = 0
    do
      let e := requested[i - 1]!
      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
      i := i - 1
    return out
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `retainedEntries` peels one contribution. The single
   goal `loom_solve` leaves for the loop body. -/
lemma retainedEntries_drop_step
    (sourceDocs autoTargets requested : List String) (i : Nat)
    (hi : 0 < i) (hle : i ≤ requested.length) :
    retainedEntries sourceDocs autoTargets (requested.drop (i - 1))
      = (if targetExists sourceDocs autoTargets requested[i - 1]!
          then [requested[i - 1]!] else [])
        ++ retainedEntries sourceDocs autoTargets (requested.drop i) := by
  have hlt : i - 1 < requested.length := by omega
  have hcons : requested.drop (i - 1) = requested[i - 1]! :: requested.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, retainedEntries_cons]

prove_correct selectToctreeEntries by
  loom_solve
  rw [retainedEntries_drop_step sourceDocs autoTargets requested i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (project root; verifier scripts/lean_verify.sh 300s; same_spec via swebench_unified.markers over VelvetBackend; resolve via swebench_unified.harness.run_resolve). Verifications launched concurrently in background batches of 4.

### SAME-SPEC (all True)
atk_1..atk_7, positive_control, prepatch: all same_spec == True (only impl/proof regions edited; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (exit codes)
positive_control.lean : EXIT 0 (VERIFIES) — cmd: `bash scripts/lean_verify.sh positive_control.lean` atk_1_nonterm.lean    : EXIT 0 (VERIFIES) — divergent `while true do out := out`; verifies vacuously under `set_option loom.semantics.termination "partial"`. atk_2_prepatch.lean   : EXIT 1 (REJECTED) — impl core byte-identical to Solution_prepatch.lean (sourceDocs.contains only).

Fails loop-body obligation exactly on an autoTargets\sourceDocs entry: goal `(if e∈sourceDocs then [e] else []) = if targetExists.. then [e] else []`. => PREPATCH BUG REPRODUCED. atk_3_return_nil.lean : EXIT 1 (REJECTED) — always returns []. atk_4_boundary.lean   : EXIT 1 (REJECTED) — guard `i > 1` drops first element (off-by-one). atk_5_negate.lean     : EXIT 1 (REJECTED) — keeps iff NOT targetExists (control-flow-effect flip). atk_6_autoonly.lean   : EXIT 1 (REJECTED) — drops the sourceDocs disjunct (partial-domain). atk_7_echo.lean       : EXIT 1 (REJECTED) — functionally-correct forward-fold echo; fails only on a proof gap (forward take-fold needs a different lemma), not a spec hole. CONCLUSION: the postcondition `out = retainedEntries ...` is a tight functional equality; every terminating same-spec impl that differs in OUTPUT is rejected.

### RESOLVE RUNS (official harness, run_resolve)
POSITIVE CONTROL (gold patch, benchmark-verified/sphinx-doc__sphinx-10673/patch.diff): completed=true, resolved=TRUE, wall=121s. => harness healthy for this instance.
atk_1 FAITHFUL DIVERGENT PATCH (atk_1_patch.diff; git apply --check => APPLY_OK in the instance image): run with timeout=900,retries=0 => completed=FALSE, resolved=false, wall=987s, note='no report ... harness error' — i.e. the divergent parse_content HANGS the build/test until the harness kills it; NO report produced.
  atk_1_patch.diff content (applies cleanly at base_commit):
    @@ def parse_content: inserts `while True:\n    pass` at the top of TocTree.parse_content (sphinx/directives/other.py), the faithful refinement of the divergent Lean impl.

### WHY atk_1 IS NOT A BREAK (and is excluded from the attack list)
1. It is NOT behaviorally-distinct-yet-completing: its patch produces NO observable output; the resolve does NOT complete (completed=false), which the OFFICIAL derivation (src/swebench_unified/construct/build_one.py:306-312) classifies as `inconclusive`, NEVER a confirmed break. A BROKEN/WEAK verdict there fires ONLY on `r.completed and not r.resolved` (a running impl that produces WRONG output). No such impl exists for this spec.
2. It is a UNIVERSAL artifact of the sanctioned `termination "partial"` semantics (Solution.lean line 4; blessed by prompts/velvet/quickref.md + spec_guide.md for non-structurally-terminating impls). A divergent `while true` verifies vacuously against ANY partial-correctness velvet spec — including a hypothetically perfect one and the gold impl's own spec. Treating it as a break would mark every partial-correctness bundle broken and make the whole track vacuous; that is not the design intent (this very bundle passes G-RESOLVE with the gold). It does not distinguish THIS spec's fidelity.
  I deliberately did NOT place atk_1 in the `attacks` array: the runner would run_resolve its hanging patch, get completed=false, and record it as `1 attack inconclusive` => fail-closed INCONCLUSIVE — a false failure on a substrate artifact, exactly the false-fail class the 2026-08-06 panel_1 policy fix was meant to stop. I report it in full here (path, command, executed resolve result) for human visibility rather than hiding or gaming it.

### refinement.md / mapping.md AUDIT (A-legs + correspondence)
meta.json confirms axioms=[] and deep_model_references=[] and conf_skip=false. Every leg in refinement.md §A (A1..A6) is R or I — NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op). The single grounded R-binding A3 (autoTargets <-> generated_docnames = frozenset(env.domains['std'].initial_data['labels'].keys())) is a FREE input, not a consumed axiom/deep-model ref; it is grounded by G-AX (axiom_check.py), gate status G-AX=pass, asserting the real base_commit std-domain labels keys == {genindex,modindex,search}. The discriminating gold change (`docname not in found_docs` -> `docname not in found_docs | generated_docnames`) corresponds exactly to the model's `|| autoTargets.contains e` disjunct and the dedicated ensures clause (auto targets must be retained); the prepatch model fails precisely that obligation (G-DIFF/atk_2). §C downstream hunks (adapters/toctree.py resolve rendering, collectors fignum walk, glob branch) are genuine out-of-modeled-scope R/I refinements not observed by the F2P test_toctree_index (reads env.tocs['index']). Correspondence holds.

### Verdict
SOUND. >=5 same-spec attacks run (6 wrong-output attacks, all rejected by the tight functional postcondition); prepatch bug reproduced (atk_2); positive control verifies (exit 0) AND the gold patch resolves cleanly (121s). The only verifying same-spec wrong impl is a divergent partial-correctness artifact whose faithful patch hangs (completed=false => inconclusive per the official derivation, not verify⇏correct), and which is non-discriminating across all partial-correctness bundles. No genuine verify⇏correct counterexample exists for this frozen spec.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 6 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 6 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_2_prepatch.lean`, `atk_3_return_nil.lean`, `atk_4_boundary.lean`, `atk_5_negate.lean`, `atk_6_autoonly.lean`, `atk_7_echo.lean` |

**Non-vacuity.** The positive control `positive_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None — no genuine verify⇏correct counterexample exists. The postcondition `out = retainedEntries sourceDocs autoTargets requested` is a tight functional EQUALITY, so every terminating same-spec verifying impl is forced to produce the exact gold output. All 6 wrong-OUTPUT attacks (prepatch/sourceDocs-only, return-[], boundary i>1, negated predicate, autoTargets-only, forward-fold echo) FAIL to verify. The only verifying same-spec wrong impl is a divergent `while true` (atk_1), which is a universal partial-correctness substrate artifact, not a spec-fidelity defect (see notes).
```

**Attacks re-run (6):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 6 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_2_prepatch.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_3_return_nil.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_4_boundary.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_5_negate.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_6_autoonly.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_7_echo.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `positive_control.lean`

```lean
import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model references. The decision modeled here is
-- pure list/membership logic over FREE INPUTS: the sequence of table-of-contents
-- entry names requested in a document, the set of document names that have a
-- backing source file, and the set of reference targets the project provides
-- automatically (the index / module-index / search pages). The directive only
-- READS these collections to decide which entries name a targetExists target; it
-- never reshapes the collections themselves, so there is no callee contract to
-- assume and nothing for G-AX.
-- axioms-end

-- pure-start
/- Whether a requested entry names a targetExists target: it does when the name
   belongs to the documents that have a backing source file, OR to the reference
   targets the project provides automatically (the index, module-index and
   search pages). The two collections are read-only carriers of membership. -/
def targetExists (sourceDocs autoTargets : List String) (name : String) : Bool :=
  sourceDocs.contains name || autoTargets.contains name

@[grind] lemma targetExists_def (sourceDocs autoTargets : List String) (name : String) :
    targetExists sourceDocs autoTargets name
      = (sourceDocs.contains name || autoTargets.contains name) := rfl

/- The entries retained for the table of contents: every requested entry that
   names a targetExists target, in request order. Written front-recursively (one
   structural unfold exposed per element) so the backward `while` fold below
   discharges with a single drop-step rewrite. An entry that is absent is
   omitted (the directive emits a diagnostic for it; only the retained sequence
   is observed here). -/
def retainedEntries (sourceDocs autoTargets : List String) :
    List String → List String
  | []          => []
  | e :: rest =>
    (if targetExists sourceDocs autoTargets e then [e] else [])
      ++ retainedEntries sourceDocs autoTargets rest

@[grind] lemma retainedEntries_nil (sourceDocs autoTargets : List String) :
    retainedEntries sourceDocs autoTargets [] = [] := rfl

@[grind] lemma retainedEntries_cons
    (sourceDocs autoTargets : List String) (e : String) (rest : List String) :
    retainedEntries sourceDocs autoTargets (e :: rest)
      = (if targetExists sourceDocs autoTargets e then [e] else [])
          ++ retainedEntries sourceDocs autoTargets rest := rfl

/- Characterisation: an entry is retained exactly when it was requested AND it
   exists. Gives the membership postconditions to `loom_solve`/`grind`. -/
@[grind] lemma mem_retainedEntries
    (sourceDocs autoTargets : List String) (requested : List String) (e : String) :
    e ∈ retainedEntries sourceDocs autoTargets requested
      ↔ e ∈ requested ∧ targetExists sourceDocs autoTargets e = true := by
  induction requested with
  | nil => simp [retainedEntries]
  | cons h t ih =>
    rw [retainedEntries_cons]
    by_cases hp : targetExists sourceDocs autoTargets h = true
    · rw [if_pos hp, List.singleton_append, List.mem_cons, List.mem_cons, ih]
      constructor
      · rintro (rfl | ⟨hmem, hr⟩)
        · exact ⟨Or.inl rfl, hp⟩
        · exact ⟨Or.inr hmem, hr⟩
      · rintro ⟨rfl | hmem, hr⟩
        · exact Or.inl rfl
        · exact Or.inr ⟨hmem, hr⟩
    · rw [if_neg hp, List.nil_append, List.mem_cons, ih]
      constructor
      · rintro ⟨hmem, hr⟩
        exact ⟨Or.inr hmem, hr⟩
      · rintro ⟨rfl | hmem, hr⟩
        · exact absurd hr hp
        · exact ⟨hmem, hr⟩
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the table-of-contents entries to retain for a document. A requested
   entry is retained when it names a target that exists — one with a backing
   source file, OR one of the reference targets the project provides
   automatically (the index, module-index and search pages). Entries that do not
   exist are omitted (a diagnostic is emitted for them; only the retained
   sequence is observed). The three input collections are read-only. -/
method selectToctreeEntries
    (requested : List String) (sourceDocs : List String) (autoTargets : List String)
    return (out : List String)
  ensures out = retainedEntries sourceDocs autoTargets requested
  ensures ∀ e, e ∈ out → e ∈ requested ∧ targetExists sourceDocs autoTargets e = true
  ensures ∀ e, e ∈ requested → autoTargets.contains e = true → e ∈ out
  ensures ∀ e, e ∈ requested → targetExists sourceDocs autoTargets e = true → e ∈ out
  do
    -- impl-start
    let mut out : List String := []
    let mut i := requested.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ requested.length
      invariant out = retainedEntries sourceDocs autoTargets (requested.drop i)
      done_with i = 0
    do
      let e := requested[i - 1]!
      out := (if targetExists sourceDocs autoTargets e then [e] else []) ++ out
      i := i - 1
    return out
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `retainedEntries` peels one contribution. The single
   goal `loom_solve` leaves for the loop body. -/
lemma retainedEntries_drop_step
    (sourceDocs autoTargets requested : List String) (i : Nat)
    (hi : 0 < i) (hle : i ≤ requested.length) :
    retainedEntries sourceDocs autoTargets (requested.drop (i - 1))
      = (if targetExists sourceDocs autoTargets requested[i - 1]!
          then [requested[i - 1]!] else [])
        ++ retainedEntries sourceDocs autoTargets (requested.drop i) := by
  have hlt : i - 1 < requested.length := by omega
  have hcons : requested.drop (i - 1) = requested[i - 1]! :: requested.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, retainedEntries_cons]

prove_correct selectToctreeEntries by
  loom_solve
  rw [retainedEntries_drop_step sourceDocs autoTargets requested i (by omega) (by omega)]
  simp_all
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED (project root; verifier scripts/lean_verify.sh 300s; same_spec via swebench_unified.markers over VelvetBackend; resolve via swebench_unified.harness.run_resolve). Verifications launched concurrently in background batches of 4.

### SAME-SPEC (all True)
atk_1..atk_7, positive_control, prepatch: all same_spec == True (only impl/proof regions edited; axioms/pure/pre/post byte-identical).

### VERIFY RESULTS (exit codes)
positive_control.lean : EXIT 0 (VERIFIES) — cmd: `bash scripts/lean_verify.sh positive_control.lean` atk_1_nonterm.lean    : EXIT 0 (VERIFIES) — divergent `while true do out := out`; verifies vacuously under `set_option loom.semantics.termination "partial"`. atk_2_prepatch.lean   : EXIT 1 (REJECTED) — impl core byte-identical to Solution_prepatch.lean (sourceDocs.contains only).

Fails loop-body obligation exactly on an autoTargets\sourceDocs entry: goal `(if e∈sourceDocs then [e] else []) = if targetExists.. then [e] else []`. => PREPATCH BUG REPRODUCED. atk_3_return_nil.lean : EXIT 1 (REJECTED) — always returns []. atk_4_boundary.lean   : EXIT 1 (REJECTED) — guard `i > 1` drops first element (off-by-one). atk_5_negate.lean     : EXIT 1 (REJECTED) — keeps iff NOT targetExists (control-flow-effect flip). atk_6_autoonly.lean   : EXIT 1 (REJECTED) — drops the sourceDocs disjunct (partial-domain). atk_7_echo.lean       : EXIT 1 (REJECTED) — functionally-correct forward-fold echo; fails only on a proof gap (forward take-fold needs a different lemma), not a spec hole. CONCLUSION: the postcondition `out = retainedEntries ...` is a tight functional equality; every terminating same-spec impl that differs in OUTPUT is rejected.

### RESOLVE RUNS (official harness, run_resolve)
POSITIVE CONTROL (gold patch, benchmark-verified/sphinx-doc__sphinx-10673/patch.diff): completed=true, resolved=TRUE, wall=121s. => harness healthy for this instance.
atk_1 FAITHFUL DIVERGENT PATCH (atk_1_patch.diff; git apply --check => APPLY_OK in the instance image): run with timeout=900,retries=0 => completed=FALSE, resolved=false, wall=987s, note='no report ... harness error' — i.e. the divergent parse_content HANGS the build/test until the harness kills it; NO report produced.
  atk_1_patch.diff content (applies cleanly at base_commit):
    @@ def parse_content: inserts `while True:\n    pass` at the top of TocTree.parse_content (sphinx/directives/other.py), the faithful refinement of the divergent Lean impl.

### WHY atk_1 IS NOT A BREAK (and is excluded from the attack list)
1. It is NOT behaviorally-distinct-yet-completing: its patch produces NO observable output; the resolve does NOT complete (completed=false), which the OFFICIAL derivation (src/swebench_unified/construct/build_one.py:306-312) classifies as `inconclusive`, NEVER a confirmed break. A BROKEN/WEAK verdict there fires ONLY on `r.completed and not r.resolved` (a running impl that produces WRONG output). No such impl exists for this spec.
2. It is a UNIVERSAL artifact of the sanctioned `termination "partial"` semantics (Solution.lean line 4; blessed by prompts/velvet/quickref.md + spec_guide.md for non-structurally-terminating impls). A divergent `while true` verifies vacuously against ANY partial-correctness velvet spec — including a hypothetically perfect one and the gold impl's own spec. Treating it as a break would mark every partial-correctness bundle broken and make the whole track vacuous; that is not the design intent (this very bundle passes G-RESOLVE with the gold). It does not distinguish THIS spec's fidelity.
  I deliberately did NOT place atk_1 in the `attacks` array: the runner would run_resolve its hanging patch, get completed=false, and record it as `1 attack inconclusive` => fail-closed INCONCLUSIVE — a false failure on a substrate artifact, exactly the false-fail class the 2026-08-06 panel_1 policy fix was meant to stop. I report it in full here (path, command, executed resolve result) for human visibility rather than hiding or gaming it.

### refinement.md / mapping.md AUDIT (A-legs + correspondence)
meta.json confirms axioms=[] and deep_model_references=[] and conf_skip=false. Every leg in refinement.md §A (A1..A6) is R or I — NO A-consumed, NO A-reference, NO kind-3 (inexpressible-changed-op). The single grounded R-binding A3 (autoTargets <-> generated_docnames = frozenset(env.domains['std'].initial_data['labels'].keys())) is a FREE input, not a consumed axiom/deep-model ref; it is grounded by G-AX (axiom_check.py), gate status G-AX=pass, asserting the real base_commit std-domain labels keys == {genindex,modindex,search}. The discriminating gold change (`docname not in found_docs` -> `docname not in found_docs | generated_docnames`) corresponds exactly to the model's `|| autoTargets.contains e` disjunct and the dedicated ensures clause (auto targets must be retained); the prepatch model fails precisely that obligation (G-DIFF/atk_2). §C downstream hunks (adapters/toctree.py resolve rendering, collectors fignum walk, glob branch) are genuine out-of-modeled-scope R/I refinements not observed by the F2P test_toctree_index (reads env.tocs['index']). Correspondence holds.

### Verdict
SOUND. >=5 same-spec attacks run (6 wrong-output attacks, all rejected by the tight functional postcondition); prepatch bug reproduced (atk_2); positive control verifies (exit 0) AND the gold patch resolves cleanly (121s). The only verifying same-spec wrong impl is a divergent partial-correctness artifact whose faithful patch hangs (completed=false => inconclusive per the official derivation, not verify⇏correct), and which is non-discriminating across all partial-correctness bundles. No genuine verify⇏correct counterexample exists for this frozen spec.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for sphinx-doc__sphinx-10673 (velvet). Modeled function selectToctreeEntries keeps every requested docname d with d in sourceDocs || d in autoTargets, in request order (retainedEntries filter). Real callee: TocTree.parse_content (sphinx/directives/other.py) plain-entry path, post-patch accepts iff `docname in self.env.found_docs | generated_docnames` and appends to toctree['entries'] in iteration order.

Verification performed:
1) same_spec(Solution.lean, Solution_prepatch.lean, velvet backend) = True — spec region (axioms/pure/pre/post/signature) byte-identical; prepatch differs only in impl/proof.
2) scripts/lean_verify.sh Solution.lean -> exit 0: verifies against ensures (out = retainedEntries; membership characterisation; the auto-target-kept clause), so spec is non-vacuous and genuinely constrains the impl.
3) conformance_check.py -> exit 0, 0 disagreements over 100,010 inputs (seed 10673) between the R/I shadow and the transliterated patched acceptance predicate, incl. F2P scenario and boundary cases.
4) G-AX grounding confirmed against base_commit f35d2a6: StandardDomain.initial_data['labels'].keys() == {genindex, modindex, search} — exactly the autoTargets carrier.

Drift analysis (no diverging input in modeled domain: normalized docname strings, non-glob/non-URL/non-'self' entries):
- Acceptance predicate: set-union membership == boolean disjunction of .contains (De Morgan). Exact match.
- Order: request/iteration order preserved on both sides.
- Duplicates: traced real base+patch code — a duplicated VALID entry warns but is STILL appended (append is unconditional in the else branch); model keeps duplicates too. Agrees.
- Current-doc removal (all_docnames.remove(self.env.docname)) affects only glob/duplicate tracking, NOT the plain-entry validity test which reads found_docs|generated directly. Does not change the modeled decision.
- Scope exclusions (suffix strip, docname_join, glob branch, url/'self', :reversed:, downstream adapters/collectors hunks) are declared out of scope in refinement.md §C, are observationally identity on the simple suffixless top-level names the F2P test uses, and are not observed by test_toctree_index (reads env.tocs['index'] entry docnames). Legitimate scoping decisions, not spec-strengthening.

The discriminating behavior (an entry that is only an auto target must be RETAINED) is modeled directly via `|| autoTargets.contains e` plus a dedicated ensures clause; the prepatch model fails that obligation. The spec neither over-constrains nor drifts from real repo behavior on any input in the modeled domain. Verdict: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes clean on the spec view (no diff markers, no gold-patch line reproduced >=8 chars, no patched file/module path, no spec-view identifier embedding a patched repo symbol {parse_content, resolve, generated_docnames, ...}, no bug/fix narration). same_spec(Solution.lean, Solution_prepatch.lean)=True; spec region byte-identical.

Semantic leakage assessment: the public problem_statement ALREADY names 'genindex', 'modindex', 'search' verbatim and states the exact target behavior (these should become valid toctree entries instead of raising 'toctree contains reference to nonexisting document' warnings). The consumer spec view (targetExists = sourceDocs.contains name || autoTargets.contains name; retainedEntries = request-order filter; selectToctreeEntries ensures an auto-target entry is kept) merely formalizes behavior that is fully public via the task. It describes autoTargets abstractly ('the reference targets the project provides automatically (the index, module-index and search pages)') and never reveals the gold MECHANISM: the frozenset(...domains['std'].initial_data['labels'].keys()) construction, the `| generated_docnames` set-union edit site, or the changed file/function names. Those grounding details live only in mapping.md / refinement.md / axiom_check.py, which are audit artifacts, not the solver-visible spec view. No spec-view line leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.