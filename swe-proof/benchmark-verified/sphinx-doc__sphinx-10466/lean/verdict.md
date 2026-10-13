# P2 adversarial audit — sphinx-doc__sphinx-10466

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass

- **status (recorded):** `pass`
- **machine verdict:** eq: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return pairs
 -- impl-end
 
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return pairs.dedup
 -- impl-end
 
 
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return pairs.mergeSort lexLe
 -- impl-end
 
 
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return (pairs.dedup.mergeSort lexLe).reverse
 -- impl-end
 
 
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return pairs.dedup.mergeSort (fun a b => decide (a.2 ≤ b.2))
 -- impl-end
 
 
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return (pairs.dedup.mergeSort lexLe).dropLast
 -- impl-end
 
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return (("", (-1 : Int)) :: pairs.dedup.mergeSort lexLe)
 -- impl-end
 
 
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,7 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  return (pairs.map (fun p => (p.1, (0 : Int)))).dedup.mergeSort lexLe
 -- impl-end
 
 
```

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,8 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  let s := pairs.dedup.mergeSort lexLe
+  return if s.length ≤ 2 then s else s.take 2
 -- impl-end
 
 
```

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -63,10 +63,13 @@
 -- impl-start
 def implementation_dedupSort
     (triples : List (String × Int × String)) : List (String × Int) := Id.run do
+  let mut seen : List String := []
   let mut pairs : List (String × Int) := []
   for t in triples do
-    pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+    if !(seen.contains t.1) then
+      seen := seen ++ [t.1]
+      pairs := pairs ++ [(t.1, t.2.1)]
+  return pairs.mergeSort lexLe
 -- impl-end
 
 
```

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good) (shown as a diff against the cell's spec file, which it is otherwise identical to -- that is what makes it a same-spec attack)

```diff
@@ -66,7 +66,13 @@
   let mut pairs : List (String × Int) := []
   for t in triples do
     pairs := pairs ++ [(t.1, t.2.1)]
-  return pairs.dedup.mergeSort lexLe
+  if pairs.length = 4 then
+    return [("/path/to/filename", (1 : Int)), ("/path/to/filename", (2 : Int)),
+            ("/path/to/yetanother", (1 : Int))]
+  else if pairs.length = 1 then
+    return pairs
+  else
+    return []
 -- impl-end
 
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**G-EQ SOUND.** 11 same-spec wrong impls, all same_spec=True and admissible=True (unsound_evasions=[]); positive_control is byte-identical to Solution.lean, verifies exit 0, `#print axioms correct_dedupSort` = [propext, Classical.choice, Quot.sound] (standard only, no sorryAx).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`; all exit 1 = does not verify):
atk_1 prepatch bug (return pairs; no dedup, no sort) -> 1. atk_2 dedup only -> 1. atk_3 sort only -> 1. atk_4 descending (.reverse) -> 1. atk_5 line-only comparator -> 1. atk_6 .dropLast (boundary, drops max) -> 1. atk_7 phantom minimal element (("",-1) prepended, keeps result SORTED so it attacks only the membership clause) -> 1. atk_8 line collapsed to 0 (boundary value from the bug report) -> 1. atk_9 partial-domain (correct for <=2 distinct positions, truncates beyond) -> 1. atk_10 control-flow-effect (dedup on SOURCE only via a guarded accumulator, first line per source wins) -> 1. atk_11 ungrounded-oracle echo (hardcodes the F2P test's expected locations by length) -> 1.

Official primitive `adversary.check_attack('lean', ...)` re-run on all 11: same_spec=True, admissible=True, verifies=False, verify_completed=True for each. verify_completed=True everywhere matters: no rejection is a host-saturation timeout being misread as a rejection.

WHY THE REJECTIONS ARE SEMANTIC, NOT TACTIC BRITTLENESS (the key check): every attack's raw failure is an error inside the gold's `loop_eq_map` helper (rfl/rewrite), which by itself is worthless evidence -- it could be mere tactic fragility. Two machine-checked artifacts close that gap:

(a) refute.lean (exit 0) proves `spec_functional`: any two lists satisfying problem_spec_dedupSort for the same input are EQUAL (Sorted lexLt => Nodup, membership iff => Perm, then eq_of_perm_of_sorted). The postcondition is FUNCTIONAL, so it admits exactly one output per input and no impl differing from gold anywhere can satisfy it.

(b) refute_all.lean (exit 0) proves, for all 11, both `i_n <witness> != gold <witness>` (native_decide) AND the direct refutation `¬ problem_spec_dedupSort <witness> (i_n <witness>)` -- r1..r11. So the spec is provably FALSE of each attack's output, not merely unproven. Witness W = the F2P case (4 records, 3 distinct positions); V/V5 for the order-only legs (V5=[("b",1),("a",2)] is needed because line-order and lex-order agree on V -- my first V witness let atk_5 match gold and native_decide caught it).
Also proved in refute_all.lean: gold W = [("/path/to/filename",1),("/path/to/filename",2),("/path/to/yetanother",1)], exactly the locations tests/test_build_gettext.py::test_Catalog_duplicated_message asserts.

No attack verified, so per the G-EQ rule no resolve run is MANDATED (verify=>correct is not threatened). patches={} for that reason. But "nothing verified" can also mean a dead oracle, so I materialized faithful patches for all 10 non-trivial attacks (atk_1's faithful patch is a no-op: the impl IS the prepatch source), verified all 10 with `git apply --check` in a base_commit worktree ( @ cab2d93) -- all APPLY -- and ran run_resolve as a liveness/discrimination control:
  gold.diff  -> resolved=True,  completed=True
  atk_5.diff -> resolved=False, completed=True
  atk_11.diff-> resolved=True,  completed=True
The oracle is live and discriminating (gold passes, a wrong impl fails). Notable and reported rather than buried: atk_11 (the hardcoded echo) RESOLVES the F2P test yet the Lean spec REJECTS it -- the spec is strictly STRONGER than the test suite there, which is the safe direction for verify=>correct.

**A-LEG AUDIT:** refinement.md claims no A rows and all-R/I. Confirmed: `grep -nE '^\s*(axiom|opaque)'` on Solution.lean = NONE, no native_decide/sorry/admit in the bundle, so axiom_check.py being a skip stub is correct and there is no deep-model reference whose correspondence could drift. Every one of the 5 rows is R or I -- no kind-3 leg. R-leg correspondence checked directly, not taken on trust: (i) Lean `String` `<` vs Python `str` `<` agree on all 8 probes including prefix cases ("ab"<"b"), empty string, case ("Z"<"a"), punctuation ("a/b" vs "a.b" both False), and non-ASCII ("é"<"z" False in BOTH) -- strord.lean; (ii) 40-case differential fuzz of the Lean model against Python `sorted(set(...))` at the pinned seed 1046620250630, 0 mismatches (fuzz.lean exit 0 vs fuzz_expected.txt). Row 3's claim that dedup order is irrelevant because row 4 re-sorts is sound given spec_functional.

ONE RESIDUAL, non-blocking and NOT a G-EQ weakness (recorded for the faithfulness panel): mapping.md types line as Int, but `origin.line` can be None in docutils (real Python then raises TypeError comparing int to None inside `sorted`, whereas the Lean model is total). This makes the model total where the real code can throw -- it does not admit a wrong impl, so verify=>correct holds; it is a domain-totalization note for G-PANEL-2, and mapping.md already flags Int as a deliberate superset.

All evidence is  (atk_*.lean, atk_*.log/.code, pos_control.*, ax_check.lean, refute.lean, refute_all.lean, strord.lean, fuzz.lean, fuzz_expected.txt, patches/*.diff, res_*.json, repo/).

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 11 admissible attacks re-run of 11 submitted, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 11 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 11 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_5.lean`, `atk_6.lean`, `atk_7.lean`, `atk_8.lean`, `atk_9.lean`, `atk_10.lean`, `atk_11.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (11):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 11 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

Attack 9 — `atk_9.lean` → rejected (same spec, does not verify — good)

Attack 10 — `atk_10.lean` → rejected (same spec, does not verify — good)

Attack 11 — `atk_11.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean` (identical to the cell's spec file: the unmodified correct implementation, which is what a non-vacuity control has to be, so there is no diff to show)

Prepatch bug re-encoded as an attack: `True`.

**G-EQ SOUND.** 11 same-spec wrong impls, all same_spec=True and admissible=True (unsound_evasions=[]); positive_control is byte-identical to Solution.lean, verifies exit 0, `#print axioms correct_dedupSort` = [propext, Classical.choice, Quot.sound] (standard only, no sorryAx).

### ATTACKS (cmd: `bash scripts/lean_verify.sh <path>`; all exit 1 = does not verify):
atk_1 prepatch bug (return pairs; no dedup, no sort) -> 1. atk_2 dedup only -> 1. atk_3 sort only -> 1. atk_4 descending (.reverse) -> 1. atk_5 line-only comparator -> 1. atk_6 .dropLast (boundary, drops max) -> 1. atk_7 phantom minimal element (("",-1) prepended, keeps result SORTED so it attacks only the membership clause) -> 1. atk_8 line collapsed to 0 (boundary value from the bug report) -> 1. atk_9 partial-domain (correct for <=2 distinct positions, truncates beyond) -> 1. atk_10 control-flow-effect (dedup on SOURCE only via a guarded accumulator, first line per source wins) -> 1. atk_11 ungrounded-oracle echo (hardcodes the F2P test's expected locations by length) -> 1.

Official primitive `adversary.check_attack('lean', ...)` re-run on all 11: same_spec=True, admissible=True, verifies=False, verify_completed=True for each. verify_completed=True everywhere matters: no rejection is a host-saturation timeout being misread as a rejection.

WHY THE REJECTIONS ARE SEMANTIC, NOT TACTIC BRITTLENESS (the key check): every attack's raw failure is an error inside the gold's `loop_eq_map` helper (rfl/rewrite), which by itself is worthless evidence -- it could be mere tactic fragility. Two machine-checked artifacts close that gap:

(a) refute.lean (exit 0) proves `spec_functional`: any two lists satisfying problem_spec_dedupSort for the same input are EQUAL (Sorted lexLt => Nodup, membership iff => Perm, then eq_of_perm_of_sorted). The postcondition is FUNCTIONAL, so it admits exactly one output per input and no impl differing from gold anywhere can satisfy it.

(b) refute_all.lean (exit 0) proves, for all 11, both `i_n <witness> != gold <witness>` (native_decide) AND the direct refutation `¬ problem_spec_dedupSort <witness> (i_n <witness>)` -- r1..r11. So the spec is provably FALSE of each attack's output, not merely unproven. Witness W = the F2P case (4 records, 3 distinct positions); V/V5 for the order-only legs (V5=[("b",1),("a",2)] is needed because line-order and lex-order agree on V -- my first V witness let atk_5 match gold and native_decide caught it).
Also proved in refute_all.lean: gold W = [("/path/to/filename",1),("/path/to/filename",2),("/path/to/yetanother",1)], exactly the locations tests/test_build_gettext.py::test_Catalog_duplicated_message asserts.

No attack verified, so per the G-EQ rule no resolve run is MANDATED (verify=>correct is not threatened). patches={} for that reason. But "nothing verified" can also mean a dead oracle, so I materialized faithful patches for all 10 non-trivial attacks (atk_1's faithful patch is a no-op: the impl IS the prepatch source), verified all 10 with `git apply --check` in a base_commit worktree ( @ cab2d93) -- all APPLY -- and ran run_resolve as a liveness/discrimination control:
  gold.diff  -> resolved=True,  completed=True
  atk_5.diff -> resolved=False, completed=True
  atk_11.diff-> resolved=True,  completed=True
The oracle is live and discriminating (gold passes, a wrong impl fails). Notable and reported rather than buried: atk_11 (the hardcoded echo) RESOLVES the F2P test yet the Lean spec REJECTS it -- the spec is strictly STRONGER than the test suite there, which is the safe direction for verify=>correct.

**A-LEG AUDIT:** refinement.md claims no A rows and all-R/I. Confirmed: `grep -nE '^\s*(axiom|opaque)'` on Solution.lean = NONE, no native_decide/sorry/admit in the bundle, so axiom_check.py being a skip stub is correct and there is no deep-model reference whose correspondence could drift. Every one of the 5 rows is R or I -- no kind-3 leg. R-leg correspondence checked directly, not taken on trust: (i) Lean `String` `<` vs Python `str` `<` agree on all 8 probes including prefix cases ("ab"<"b"), empty string, case ("Z"<"a"), punctuation ("a/b" vs "a.b" both False), and non-ASCII ("é"<"z" False in BOTH) -- strord.lean; (ii) 40-case differential fuzz of the Lean model against Python `sorted(set(...))` at the pinned seed 1046620250630, 0 mismatches (fuzz.lean exit 0 vs fuzz_expected.txt). Row 3's claim that dedup order is irrelevant because row 4 re-sorts is sound given spec_functional.

ONE RESIDUAL, non-blocking and NOT a G-EQ weakness (recorded for the faithfulness panel): mapping.md types line as Int, but `origin.line` can be None in docutils (real Python then raises TypeError comparing int to None inside `sorted`, whereas the Lean model is total). This makes the model total where the real code can throw -- it does not admit a wrong impl, so verify=>correct holds; it is a domain-totalization note for G-PANEL-2, and mapping.md already flags Int as a deliberate superset.

All evidence is  (atk_*.lean, atk_*.log/.code, pos_control.*, ax_check.lean, refute.lean, refute_all.lean, strord.lean, fuzz.lean, fuzz_expected.txt, patches/*.diff, res_*.json, repo/).

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`

**Machine verdict**

Faithfulness/drift audit of the lean bundle for sphinx-doc__sphinx-10466. Reference = base worktree cab2d930 (fresh mktemp worktree from the upstream repository) with patch.diff APPLIED, i.e. `positions = sorted(set((source, line) for source, line, uuid in self.metadata[message]))` at sphinx/builders/gettext.py:60-61. Modeled function: implementation_dedupSort = project each (source,line,uuid) triple to (source,line) in order, List.dedup, List.mergeSort lexLe. Spec problem_spec_dedupSort = List.Sorted lexLt result AND (p in result <-> exists u, (p.1,p.2,u) in triples).

### CHECKS PERFORMED (all first-hand, nothing trusted from verdict.md):
(1) markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend().language) = True -> spec region byte-identical; spec_view sha256 77e722bd454a3139310cf70f7792c443aac963df218d4723506dc567a09f2fb5 matches the meta.json G-HYGIENE region hash. Confirmed the prepatch impl really is the buggy `return pairs` (no dedup, no sort), so the frozen spec is not tailored to the gold impl.

(2) scripts/lean_verify.sh Solution.lean -> exit 0. `#print axioms correct_dedupSort` = [propext, Classical.choice, Quot.sound]; implementation_dedupSort = [propext, Quot.sound]; problem_spec_dedupSort = [propext]. NO sorryAx anywhere -> the proof is genuine, not fake.

(3) The real faithfulness risk here is that G-CONF only exercises lexLe through a PYTHON str< proxy and never runs Lean's actual String.<. I closed that hole two ways. (a) Hand-built 11 adversarial Lean #eval batches vs patched-Python on identical inputs: prefix-vs-longer (a<ab<aba<abc<abcd<abd), case boundaries (A,Z<_,`<a), punctuation codepoints around '/' ('.','/','~','_','`','0'), empty string sorts first, negative Int lines (-1,-3,-1000000) and +1000000, multibyte ('e' vs 'é', 'ss'/'SS'/'ß', 'i'/'Istanbul-I'/dotless-i, U+FB00), astral plane vs BMP (U+D7FF, U+FFFD, U+FFFF, U+10000 -- checks Lean does NOT sort by UTF-16 surrogate order), whitespace-in-source, empty input, 6x-repeated identical triple. All 11 byte-identical. (b) Generated a 400-case randomized Lean file (codepoints emitted via String.mk [Char.ofNat n] to avoid escape ambiguity) over the same adversarial alphabet -> 400/400 identical to sorted(set(...)).

(4) Strongest check: rather than re-typing the expression, I exec'd the REAL patched Message/Catalog/MsgOrigin class text sliced verbatim out of the patched worktree file (asserting 'sorted(set((source, line)' is present in the sliced region) and drove the actual Catalog.`__iter__` over 200,000 randomized metadata lists. 0 mismatches vs the Lean model's semantics. The F2P case test_Catalog_duplicated_message reproduces exactly: [('/path/to/filename',1),('/path/to/filename',2),('/path/to/yetanother',1)].

DOMAIN / TOO-STRONG ANALYSIS. The one thing that looked like a live drift: upstream commits bca9e4834 ('Ensure positions always sort', changing to `line or -1`) and 34a829685 (warn + coerce None to -1 in Catalog.add) show that AFTER this patch, real docutils Elements can carry line=None, and I confirmed the real patched callee then raises TypeError: '<' not supported between 'int' and 'NoneType'. The Lean model types line as a total Int and cannot represent None, so it has no counterpart to that crash.

This is NOT a faithfulness defect of this bundle: (i) the repo's own declared type at the modeled read site is `self.metadata: Dict[str, List[Tuple[str, int, str]]]` -- int, not Optional[int], so None is outside the annotated input domain the model refines; (ii) those are LATER upstream commits, not this instance's gold patch, and the base-commit reference plus patch.diff is the sole authority here; (iii) the model is not too STRONG on this -- a spec that omits an out-of-domain crash is weaker/silent there, not stronger, and it cannot make a wrong impl verify.

Also checked the frame: the sibling `uuids = [uuid for ...]` on line 61 is untouched by the patch and is correctly declared unmodeled in refinement.md/mapping.md, and the modeled function's sole output is positions, so nothing else needed pinning. Int is a sound superset of Python int (arbitrary precision, matches on negatives; verified at +/-1000000). Lean String.< is codepoint-lexicographic exactly like Python str, including across the astral boundary.

**CONCLUSION:** no diverging input exists between the modeled function and the real post-patch repo behavior on the modeled domain. The spec is an exact characterization of sorted(set(...)) -- the strict-ascending clause pins BOTH sorted order and set-dedup, and the membership-iff pins exactly the projected (source,line) pairs with uuid correctly irrelevant. Neither too strong nor drifted. Worktree removed and pruned after the run.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`

**Machine verdict**

RELAXED_LEAKAGE.md checked as a CLAIM, not inherited. Facet re-confirmed: the ORDER of reported positions (the `List.Sorted lexLt` conjunct, the `lexLe`/`lexLt` pure helpers, and the module docstring phrase "in ascending order"). Verdict NO-LEAKAGE: the relaxation argument holds on my own measurements and the spec view leaks nothing beyond that one facet.

### WHAT I RAN (first-hand):

(1) Spec view + lexical screen. markers.spec_view(Solution.lean, lean) printed in full; sha256 77e722bd454a3139310cf70f7792c443aac963df218d4723506dc567a09f2fb5. impl and proof regions are properly elided, so `pairs.dedup.mergeSort lexLe` is NOT consumer-visible. leakage.screen(...) -> passed=True, hard_failures=[] (so this is a purely SEMANTIC relaxation, exactly the case leak.py's docstring says the flag exists for). Zero repo symbols in the spec view: no `positions`, `metadata`, `Catalog`, `Message`, `sorted`, `set`, `uuid`; the model uses neutral names (triples/source/line/identifier). No narration of the bug->fix mechanism, no test/assertion values, no file:line references.

(2) same_spec byte-identity. markers.same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend().language) = True; spec_signature equal. Confirmed the prepatch impl is genuinely the buggy `return pairs` (no dedup, no sort), so the frozen spec is not tailored to gold.

(3) Token scan re-run from the frozen row's problem_statement ONLY (hints_text excluded). sort 0, sorted 0, order 0, ordering 0, ascending 0, descending 0, alphabet 0, lexicograph 0, arrange 0, reorder 0, canonical 0, stable 0, position 0. Dedup vocabulary by contrast IS public: duplicat x3, unique x2, `set(` x1, loc_set x2. hints_text has sort x8/sorted x1/order x3 -- i.e. ordering is reachable only via out-of-scope hints or the gold diff. Two public-side confirmations: the reporter's own quoted fix is `loc_set = set(locations); return list(loc_set)`, which is order-arbitrary; and the statement's sample .pot block is itself NOT ascending (vector_rotate.rst:38 precedes modeling/hair.rst:0), so ascending order cannot be inferred from the displayed expected output either. So there is NO problem_statement-only derivation of the ordering discriminator.

(4) UNAVOIDABILITY re-derived myself, and this is where I DISAGREE with the earlier G-PANEL-3 LEAKAGE record in meta.json. That record applied the strip-the-narration test ("does the spec still reject the PRE-patch impl?"), found the de-leaked Nodup spec still rejects prepatch, and concluded the ordering clause is not load-bearing. That test is NECESSARY BUT NOT SUFFICIENT here: prepatch-rejection is the G-DIFF obligation, whereas the corpus standard is verify => correct. I wrote p3_10466_deleak.lean from scratch (de-leaked spec = ordering conjunct replaced by `result.Nodup`, membership biconditional unchanged) and scripts/lean_verify.sh returned EXIT=0 with four theorems closed:
  * deleaked_admits_rival : forall triples, problem_spec_deleaked triples ((triples.map fun t => (t.1,t.2.1)).dedup.reverse) -- axioms [propext, Classical.choice, Quot.sound], no sorryAx. The unsorted rival satisfies the de-leaked spec at EVERY input.
  * shipped_rejects_rival : NOT problem_spec_dedupSort W (rival W) for W = [("a",1,"u1"),("a",2,"u2")] -- the shipped ordering conjunct is exactly what excludes it.
  * rival_on_F2P_differs_from_graded : rival F2P != the graded list. #eval gives [("/path/to/yetanother",1), ("/path/to/filename",2), ("/path/to/filename",1)].
  * shipped_functional : two results satisfying problem_spec_dedupSort are EQUAL (via List.perm_ext_iff_of_nodup + List.eq_of_perm_of_sorted, with lexLt irrefl/trans/antisymm instances I proved). So the shipped spec pins the output to one list => every satisfying impl returns what gold returns => resolves.

(5) HARNESS half re-run on the real repo, not taken on faith. Fresh mktemp worktree at base_commit cab2d930 from the upstream repository; confirmed the pre-patch line 60 is the list comprehension. Applied the instance test_patch, then the descending candidate `positions = sorted(set(...), reverse=True)` -- which SATISFIES the de-leaked spec (nodup + same set) -- and pytest tests/test_build_gettext.py::test_Catalog_duplicated_message FAILED: "At index 0 diff: ('/path/to/yetanother', 1) != ('/path/to/filename', 1)", the exact list my Lean rival_on_F2P computes. Restored the gold expression and the same test PASSED (1 passed; the other 7 in the file error on missing sphinx test roots in my bare worktree, unrelated to the patch -- they are P2P and the recorded G-RESOLVE pass covers them). The graded assertion is list EQUALITY, so it grades order. Conclusion: an implementation verified against the de-leaked spec FAILS the graded test => verify => correct breaks without the ordering conjunct => a faithful sound spec cannot avoid naming order. Unavoidability CONFIRMED by my own measurement; the earlier LEAKAGE finding is refuted on its own test's insufficiency.

(6) Core gates the disposition leans on. Re-ran the two that matter and spot-checked the record: scripts/lean_verify.sh Solution.lean EXIT=0; `#print axioms correct_dedupSort` = [propext, Classical.choice, Quot.sound] -- NO sorryAx, proof is genuine; problem_spec_dedupSort = [propext]. Solution_prepatch.lean EXIT=3 (fails to verify), so the spec still sees the bug. meta.json: G-VERIFY/G-DIFF/G-GOLD/G-CONF (120007 cases, 0 mismatches)/G-MUT (10/10)/G-PBT/G-EQ (11/11)/G-RESOLVE/G-HYGIENE/G-INTEGRITY all pass, G-AX skip. G-LEAK sources digests in meta.json match current bytes exactly (RELAXED_LEAKAGE.md b10a874f..., Solution.lean c35b4161...), so the stamp describes the artifact that ships. No core gate is unsound.

(7) Scope. Nothing in the spec view leaks beyond the ordering facet. The dedup half is public vocabulary. The doc's own scope section correctly disclaims coverage of anything else, and I found nothing else to cover.

BUNDLE-ADDRESSES-REVIEWER CHECK (reported as a finding in its own right, per my instructions): CLEAN. leakage.reviewer_directed(RELAXED_LEAKAGE.md) = [] (empty), and I independently grepped RELAXED_LEAKAGE.md, mapping.md, refinement.md and Solution.lean for reviewer address / verdict prescription ("panel", "reviewer", "auditor", "you should/must", "the honest verdict", "record NO-LEAKAGE", "submit ... only if", "recording convention") -- zero hits. The file states its mismatch, gives reproducible measurements, and explicitly invites refutation ("a reader who measures something different has found something this file gets wrong") without telling me what to submit. No file in the bundle attempts to steer this verdict. Note that leak.py hard-FAILS a relaxation that directs its reviewer, so this is the intended shape.

G-PANEL-3 in meta.json currently records fail/LEAKAGE from the pre-repair run; per the rollup convention a failing G-PANEL means re-audit, and this run is that re-audit. My verdict supersedes it: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere. This cell separately records G-LEAK as `relaxed`, which is a disclosure a reviewer accepted rather than the absence of one.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `relaxed` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, `RELAXED_LEAKAGE.md`, all of which ship in this bundle, so a reader can start there.