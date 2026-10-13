# P2 adversarial audit — sphinx-doc__sphinx-7440

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,7 @@
 -- impl-start
 def implementation_glossaryTermEntry
     (termtext : List Char) : List Char × List Char := Id.run do
-  let key := termtext
+  let key := termtext.map Char.toLower
   let indexTerm := termtext
   return (key, indexTerm)
 -- impl-end
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
 
 -- impl-start
 def implementation_termXrefTarget (target : List Char) : List Char := Id.run do
-  return target
+  return target.map Char.toLower
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,7 @@
 -- impl-start
 def implementation_glossaryTermEntry
     (termtext : List Char) : List Char × List Char := Id.run do
-  let key := termtext
+  let key := termtext.map Char.toUpper
   let indexTerm := termtext
   return (key, indexTerm)
 -- impl-end
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -30,7 +30,7 @@
 -- impl-start
 def implementation_glossaryTermEntry
     (termtext : List Char) : List Char × List Char := Id.run do
-  let key := termtext
+  let key := if termtext = [] then termtext else termtext.map Char.toLower
   let indexTerm := termtext
   return (key, indexTerm)
 -- impl-end
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
 
 -- impl-start
 def implementation_termXrefTarget (target : List Char) : List Char := Id.run do
-  return target
+  return target.dropLast
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,7 +56,7 @@
 
 -- impl-start
 def implementation_termXrefTarget (target : List Char) : List Char := Id.run do
-  return target
+  return target.reverse
 -- impl-end
 
 -- proof-start
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -31,7 +31,7 @@
 def implementation_glossaryTermEntry
     (termtext : List Char) : List Char × List Char := Id.run do
   let key := termtext
-  let indexTerm := termtext
+  let indexTerm := termtext.map Char.toLower
   return (key, indexTerm)
 -- impl-end
 
```

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -30,7 +30,7 @@
 -- impl-start
 def implementation_glossaryTermEntry
     (termtext : List Char) : List Char × List Char := Id.run do
-  let key := termtext
+  let key := termtext.reverse.reverse
   let indexTerm := termtext
   return (key, indexTerm)
 -- impl-end
@@ -39,8 +39,9 @@
 theorem correct_glossaryTermEntry : ∀ (termtext : List Char),
     problem_spec_glossaryTermEntry termtext
       (implementation_glossaryTermEntry termtext) := by
-  intro
-  exact ⟨rfl, rfl⟩
+  intro termtext
+  refine ⟨?_, rfl⟩
+  simp [implementation_glossaryTermEntry, problem_spec_glossaryTermEntry]
 -- proof-end
 
 -- post-conditions-start
@@ -56,12 +57,12 @@
 
 -- impl-start
 def implementation_termXrefTarget (target : List Char) : List Char := Id.run do
-  return target
+  return (target ++ [])
 -- impl-end
 
 -- proof-start
 theorem correct_termXrefTarget : ∀ (target : List Char),
     problem_spec_termXrefTarget target (implementation_termXrefTarget target) := by
-  intro
-  rfl
+  intro target
+  simp [implementation_termXrefTarget, problem_spec_termXrefTarget]
 -- proof-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. Both modeled procedures
-- derive their result strings directly from the term/reference text by
-- straight-line code; the node-id builder and surrounding bookkeeping are not
-- part of the modeled identifier behavior and are not referenced. The proof
-- agent may add `_prop` axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Specification of forming a glossary term's registration entry.

`termtext` is the term's text as a sequence of characters. The entry produced
for a term is a pair: the identifier under which the term is registered for
cross-referencing (`result.1`) and the term as it appears in its index entry
(`result.2`). Both components are the term text with its exact characters
preserved — including letter case — so two terms differing only in case have
different identifiers, and a term's identifier matches its index entry. -/
def problem_spec_glossaryTermEntry
    (termtext : List Char) (result : List Char × List Char) : Prop :=
  result.1 = termtext ∧ result.2 = termtext
-- post-conditions-end

-- impl-start
def implementation_glossaryTermEntry
    (termtext : List Char) : List Char × List Char := Id.run do
  let key := termtext
  let indexTerm := termtext
  return (key, indexTerm)
-- impl-end

-- proof-start
theorem correct_glossaryTermEntry : ∀ (termtext : List Char),
    problem_spec_glossaryTermEntry termtext
      (implementation_glossaryTermEntry termtext) := by
  intro
  exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Specification of computing the lookup target for a glossary cross-reference.

`target` is the reference text as a sequence of characters. The resolved lookup
target is that text with its exact characters preserved — including letter case —
so a reference resolves to the term spelled with the same case. -/
def problem_spec_termXrefTarget
    (target : List Char) (result : List Char) : Prop :=
  result = target
-- post-conditions-end

-- impl-start
def implementation_termXrefTarget (target : List Char) : List Char := Id.run do
  return target
-- impl-end

-- proof-start
theorem correct_termXrefTarget : ∀ (target : List Char),
    problem_spec_termXrefTarget target (implementation_termXrefTarget target) := by
  intro
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A TIGHT FUNCTIONAL EQUALITY. problem_spec_glossaryTermEntry pins BOTH outputs: result.1 = termtext AND result.2 = termtext. problem_spec_termXrefTarget pins result = target. Any same-spec impl that verifies must be extensionally equal to identity, so verify=>correct.

PROTOCOL / same_spec: all 8 attacks + positive control return same_spec=True vs gold Solution.lean (checked with swebench_unified.markers.same_spec, lean backend). Only impl regions (and proofs) edited; axioms/pure/pre/post byte-identical.

COMMANDS: bash scripts/lean_verify.sh <atk>.lean ; axioms via appended #print axioms correct_glossaryTermEntry / correct_termXrefTarget ; resolve via SBU_BENCHMARK=swe_bench_verified run_resolve('sphinx-doc__sphinx-7440', <patch>, timeout=1800, retries=1).

### ATTACK RESULTS (all same-spec):
- atk_1 (prepatch bug1: glossary key := termtext.map Char.toLower): lean_verify EXIT=1 (does NOT close). Reproduces prepatch G-DIFF bug (Solution_prepatch.lean).
- atk_2 (prepatch bug2: return target.map Char.toLower): EXIT=1 (does NOT close). Reproduces Solution_prepatch_2.lean.
- atk_3 (glossary key := termtext.map Char.toUpper): EXIT=1.
- atk_4 (control-flow-effect: key := if termtext=[] then termtext else termtext.map Char.toLower): EXIT=1.
- atk_5 (boundary: return target.dropLast): EXIT=1.
- atk_6 (order-effect: return target.reverse): EXIT=1.
- atk_7 (ungrounded/frame: indexTerm := termtext.map Char.toLower, breaks result.2=termtext): EXIT=1.
- atk_8 (EXTENSIONAL-IDENTITY echo: key := termtext.reverse.reverse ; return (target ++ [])): lean_verify EXIT=0, closes with a genuine simp proof, no sorry. #print axioms => both correct_* depend on axioms: [propext] only (CLEAN core axiom; not sorry/unsound). Because reverse.reverse=id and (++[])=id, this is behaviorally identity = the gold behavior. Materialized faithful patch (== gold patch byte-wise) and RAN official harness: run_resolve => RESOLVED=True, COMPLETED=True, note='resolved'. A resolving echo is NOT a spec weakness (per 2026-08-06 G-PANEL-1/eq policy).

Positive control pc.lean (gold impl): lean_verify EXIT=0; #print axioms => 'does not depend on any axioms'.

prepatch_reproduced=true: atk_1 and atk_2 encode the two prepatch bugs (both fail to close against the tight spec), matching Solution_prepatch{,_2}.lean.

REFINEMENT AUDIT (A-legs focus): refinement.md declares NO A-consumed and NO A-reference legs; every leg is R (Python str per-code-point <-> List Char identity) or I. Solution.lean axioms block is empty; no opaque/axiom declared; no _prop axioms. No kind-3 legs. Correspondence to real callees holds: patch.diff hunk1 changes note_object key arg termtext.lower()->termtext (R, was the bug); index entry uses un-folded termtext (I, unchanged); hunk2 drops lowercase=True on the 'term' XRefRole so create_xref_node leaves target unfolded (R). mapping.md symbol bindings (sphinx/domains/std.py:307,309-310,567; sphinx/roles.py:146-147) are consistent. Frame discipline is correct: pinning result.2=termtext is what forces the key to match the index term, defeating any lowercase-key impl (confirmed empirically by atk_1/atk_7 failing).

CONCLUSION: 7 distinct genuinely-wrong impls (partial-domain/boundary/control-flow-effect/frame/ungrounded) all FAIL to verify; the one verifying same-spec impl is provably identity and its faithful patch RESOLVES. No verifying impl with a clean-axiom proof has a non-resolving faithful patch. verify=>correct holds. SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_8.lean` |

**Non-vacuity.** The positive control `pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → correct echo (verifies AND its patch resolves — not a weakness)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pc.lean`

```lean
import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. Both modeled procedures
-- derive their result strings directly from the term/reference text by
-- straight-line code; the node-id builder and surrounding bookkeeping are not
-- part of the modeled identifier behavior and are not referenced. The proof
-- agent may add `_prop` axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Specification of forming a glossary term's registration entry.

`termtext` is the term's text as a sequence of characters. The entry produced
for a term is a pair: the identifier under which the term is registered for
cross-referencing (`result.1`) and the term as it appears in its index entry
(`result.2`). Both components are the term text with its exact characters
preserved — including letter case — so two terms differing only in case have
different identifiers, and a term's identifier matches its index entry. -/
def problem_spec_glossaryTermEntry
    (termtext : List Char) (result : List Char × List Char) : Prop :=
  result.1 = termtext ∧ result.2 = termtext
-- post-conditions-end

-- impl-start
def implementation_glossaryTermEntry
    (termtext : List Char) : List Char × List Char := Id.run do
  let key := termtext
  let indexTerm := termtext
  return (key, indexTerm)
-- impl-end

-- proof-start
theorem correct_glossaryTermEntry : ∀ (termtext : List Char),
    problem_spec_glossaryTermEntry termtext
      (implementation_glossaryTermEntry termtext) := by
  intro
  exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Specification of computing the lookup target for a glossary cross-reference.

`target` is the reference text as a sequence of characters. The resolved lookup
target is that text with its exact characters preserved — including letter case —
so a reference resolves to the term spelled with the same case. -/
def problem_spec_termXrefTarget
    (target : List Char) (result : List Char) : Prop :=
  result = target
-- post-conditions-end

-- impl-start
def implementation_termXrefTarget (target : List Char) : List Char := Id.run do
  return target
-- impl-end

-- proof-start
theorem correct_termXrefTarget : ∀ (target : List Char),
    problem_spec_termXrefTarget target (implementation_termXrefTarget target) := by
  intro
  rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC IS A TIGHT FUNCTIONAL EQUALITY. problem_spec_glossaryTermEntry pins BOTH outputs: result.1 = termtext AND result.2 = termtext. problem_spec_termXrefTarget pins result = target. Any same-spec impl that verifies must be extensionally equal to identity, so verify=>correct.

PROTOCOL / same_spec: all 8 attacks + positive control return same_spec=True vs gold Solution.lean (checked with swebench_unified.markers.same_spec, lean backend). Only impl regions (and proofs) edited; axioms/pure/pre/post byte-identical.

COMMANDS: bash scripts/lean_verify.sh <atk>.lean ; axioms via appended #print axioms correct_glossaryTermEntry / correct_termXrefTarget ; resolve via SBU_BENCHMARK=swe_bench_verified run_resolve('sphinx-doc__sphinx-7440', <patch>, timeout=1800, retries=1).

### ATTACK RESULTS (all same-spec):
- atk_1 (prepatch bug1: glossary key := termtext.map Char.toLower): lean_verify EXIT=1 (does NOT close). Reproduces prepatch G-DIFF bug (Solution_prepatch.lean).
- atk_2 (prepatch bug2: return target.map Char.toLower): EXIT=1 (does NOT close). Reproduces Solution_prepatch_2.lean.
- atk_3 (glossary key := termtext.map Char.toUpper): EXIT=1.
- atk_4 (control-flow-effect: key := if termtext=[] then termtext else termtext.map Char.toLower): EXIT=1.
- atk_5 (boundary: return target.dropLast): EXIT=1.
- atk_6 (order-effect: return target.reverse): EXIT=1.
- atk_7 (ungrounded/frame: indexTerm := termtext.map Char.toLower, breaks result.2=termtext): EXIT=1.
- atk_8 (EXTENSIONAL-IDENTITY echo: key := termtext.reverse.reverse ; return (target ++ [])): lean_verify EXIT=0, closes with a genuine simp proof, no sorry. #print axioms => both correct_* depend on axioms: [propext] only (CLEAN core axiom; not sorry/unsound). Because reverse.reverse=id and (++[])=id, this is behaviorally identity = the gold behavior. Materialized faithful patch (== gold patch byte-wise) and RAN official harness: run_resolve => RESOLVED=True, COMPLETED=True, note='resolved'. A resolving echo is NOT a spec weakness (per 2026-08-06 G-PANEL-1/eq policy).

Positive control pc.lean (gold impl): lean_verify EXIT=0; #print axioms => 'does not depend on any axioms'.

prepatch_reproduced=true: atk_1 and atk_2 encode the two prepatch bugs (both fail to close against the tight spec), matching Solution_prepatch{,_2}.lean.

REFINEMENT AUDIT (A-legs focus): refinement.md declares NO A-consumed and NO A-reference legs; every leg is R (Python str per-code-point <-> List Char identity) or I. Solution.lean axioms block is empty; no opaque/axiom declared; no _prop axioms. No kind-3 legs. Correspondence to real callees holds: patch.diff hunk1 changes note_object key arg termtext.lower()->termtext (R, was the bug); index entry uses un-folded termtext (I, unchanged); hunk2 drops lowercase=True on the 'term' XRefRole so create_xref_node leaves target unfolded (R). mapping.md symbol bindings (sphinx/domains/std.py:307,309-310,567; sphinx/roles.py:146-147) are consistent. Frame discipline is correct: pinning result.2=termtext is what forces the key to match the index term, defeating any lowercase-key impl (confirmed empirically by atk_1/atk_7 failing).

CONCLUSION: 7 distinct genuinely-wrong impls (partial-domain/boundary/control-flow-effect/frame/ungrounded) all FAIL to verify; the one verifying same-spec impl is provably identity and its faithful patch RESOLVES. No verifying impl with a clean-axiom proof has a non-resolving faithful patch. verify=>correct holds. SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** G-PANEL-2 faithfulness-break: no divergence found. Both modeled functions are exact identity pass-throughs matching the real post-patch behavior on ALL inputs.

Verification: Solution.lean compiles (exit 0), no sorry; #print axioms clean for correct_glossaryTermEntry and correct_termXrefTarget ('does not depend on any axioms'). Spec region byte-identical to both prepatch variants via swebench_unified.markers.same_spec (lean backend).

Site 1 — problem_spec_glossaryTermEntry (result.1 = termtext ∧ result.2 = termtext): real post-patch sphinx/domains/std.py make_glossary_term registers key = termtext (patch: termtext.lower() -> termtext; note_object stores name verbatim at std.py:659) and builds index entry term = termtext ('single', termtext, node_id,...) unchanged. Both are the exact term text; there is no transform between termtext = term.astext() and either use. Model identity == real identity for every input.

Site 2 — problem_spec_termXrefTarget (result = target): real post-patch 'term' role = XRefRole(innernodeclass=..., warn_dangling=True); patch dropped lowercase=True so XRefRole.lowercase defaults False, and fix_parens defaults False, so create_xref_node (roles.py:143-149) leaves target as written — no lower(), no paren strip. Model identity == real identity for every input.

Because post-patch code applies no case fold or other transformation, the spec's identity constraint agrees with the real callee on all inputs (incl. Unicode and mixed-case such as the F2P witness TERM2). The extra result.2 = termtext conjunct is faithfully justified by the unchanged index-entry frame component and is not over-strong. No input where spec disagrees with the real repo.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (no hard failures): no gold-diff lines, no diff markers, no patched file path (sphinx/domains/std.py), no spec-view identifier embedding a patched repo symbol (make_glossary_term/StandardDomain), no narration keywords. Semantic review: the public problem_statement ('glossary duplicate term with a different case', 'MySQL != mysql term right ?') already discloses the required behavior — glossary terms differing only in letter case must remain distinct, i.e. term identifiers preserve exact case. The spec view models exactly that behavior: problem_spec_glossaryTermEntry pins result.1 = termtext AND result.2 = termtext (registration key = index-entry term, case preserved) and problem_spec_termXrefTarget pins result = target (lookup target case-preserved). This is a faithful behavioral spec derivable from the public statement; it does NOT reveal the gold-edit mechanism (removal of termtext.lower() / dropping XRefRole(lowercase=True)). No lowercase/.lower()/note_object/XRefRole references, no bug/fix/previously narration, docstrings describe behavior abstractly. Leakage judged against problem_statement only, not hints_text. Nothing leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
