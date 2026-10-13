# P2 adversarial audit — django__django-16145

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,7 @@
     if bracketed then
       return ['['] ++ host ++ [']']
     else
-      if host = "0".toList then
-        return "0.0.0.0".toList
-      else
-        return host
+      return host
     -- impl-end
 
 prove_correct formatHost by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,7 +65,7 @@
     if bracketed then
       return ['['] ++ host ++ [']']
     else
-      if host = "0".toList then
+      if host = "00".toList then
         return "0.0.0.0".toList
       else
         return host
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -62,13 +62,12 @@
   ensures (bracketed = false ∧ host ≠ "0".toList) → out = host
   do
     -- impl-start
-    if bracketed then
+    if host = "0".toList then
+      return "0.0.0.0".toList
+    else if bracketed then
       return ['['] ++ host ++ [']']
     else
-      if host = "0".toList then
-        return "0.0.0.0".toList
-      else
-        return host
+      return host
     -- impl-end
 
 prove_correct formatHost by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,7 +66,7 @@
       return ['['] ++ host ++ [']']
     else
       if host = "0".toList then
-        return "0.0.0.0".toList
+        return "0.0.0".toList
       else
         return host
     -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,13 +62,7 @@
   ensures (bracketed = false ∧ host ≠ "0".toList) → out = host
   do
     -- impl-start
-    if bracketed then
-      return ['['] ++ host ++ [']']
-    else
-      if host = "0".toList then
-        return "0.0.0.0".toList
-      else
-        return host
+    return displayAddress bracketed host
     -- impl-end
 
 prove_correct formatHost by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,7 +63,7 @@
   do
     -- impl-start
     if bracketed then
-      return ['['] ++ host ++ [']']
+      return ['['] ++ host
     else
       if host = "0".toList then
         return "0.0.0.0".toList
```

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,13 +62,10 @@
   ensures (bracketed = false ∧ host ≠ "0".toList) → out = host
   do
     -- impl-start
-    if bracketed then
-      return ['['] ++ host ++ [']']
-    else
-      if host = "0".toList then
-        return "0.0.0.0".toList
-      else
-        return host
+    match bracketed with
+    | true  => return ['['] ++ host ++ [']']
+    | false =>
+      if host = "0".toList then return "0.0.0.0".toList else return host
     -- impl-end
 
 prove_correct formatHost by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,10 +65,7 @@
     if bracketed then
       return ['['] ++ host ++ [']']
     else
-      if host = "0".toList then
-        return "0.0.0.0".toList
-      else
-        return host
+      return "0.0.0.0".toList
     -- impl-end
 
 prove_correct formatHost by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the modeled display computation is a straight-line
-- ladder that always terminates and produces the banner text, so an
-- implementation that diverges (e.g. loops forever instead of producing the
-- expanded address) must NOT verify. Partial correctness would vacuously admit
-- such non-terminating implementations.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no deep-model references. The operation is a
--  pure, total computation over a flag and a character sequence — square-bracket
--  wrapping, a single literal-equality test, and string literals — every step of
--  which is directly expressible. There is no unchanged callee whose behaviour
--  the proof must assume, so the `axioms` region is intentionally empty.)
-- axioms-end

-- pure-start
/- The display form of a network host shown in a server's startup banner.

   Three cases, decided in order:
     * a host flagged as already being in delimited (bracketed) literal form is
       wrapped in a pair of square brackets, so it reads back as a single host
       token in a URL;
     * otherwise, the unspecified-host shorthand "0" is expanded to its
       canonical dotted-quad form "0.0.0.0", so the printed address is one a
       browser can actually follow;
     * any other host is shown exactly as given.

   The middle case is the behaviour of interest: the bare "0" shorthand must be
   normalised to "0.0.0.0" for display, while every other (non-bracketed) host
   is passed through unchanged. -/
def displayAddress (bracketed : Bool) (host : List Char) : List Char :=
  if bracketed then ['['] ++ host ++ [']']
  else if host = "0".toList then "0.0.0.0".toList
  else host
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Format a host for display in a startup banner. The two inputs are read-only:
   neither the bracket flag nor the host sequence is mutated (none is `mut`;
   directive 5). The result is pinned exactly to `displayAddress`, so no
   implementation that disagrees on any (flag, host) pair can verify.

   Alongside the exact-equality postcondition, the three observable branches are
   each pinned to a witnessed input combination: a bracketed host is wrapped; a
   non-bracketed host equal to the "0" shorthand becomes "0.0.0.0"; any other
   non-bracketed host is returned verbatim. -/
method formatHost (bracketed : Bool) (host : List Char) return (out : List Char)
  ensures out = displayAddress bracketed host
  ensures bracketed = true → out = ['['] ++ host ++ [']']
  ensures (bracketed = false ∧ host = "0".toList) → out = "0.0.0.0".toList
  ensures (bracketed = false ∧ host ≠ "0".toList) → out = host
  do
    -- impl-start
    if bracketed then
      return ['['] ++ host ++ [']']
    else
      if host = "0".toList then
        return "0.0.0.0".toList
      else
        return host
    -- impl-end

prove_correct formatHost by
  loom_solve <;> simp_all [displayAddress]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition pins `out = displayAddress bracketed host` (exact equality, universally quantified over all (Bool, List Char) inputs, NO preconditions) plus three branch clauses — maximally tight. Same-spec confirmed True for all 8 attacks + positive control via swebench_unified.markers.same_spec (velvet).

### Results
- atk_1 (partial-domain / == prepatch bug: drops the "0"->"0.0.0.0" expansion, non-bracketed shown verbatim): exit 1 FAIL. Reproduces prepatch bug (prepatch_reproduced=true).
- atk_2 (boundary: expands "00" instead of "0"): exit 1 FAIL.
- atk_3 (control-flow-effect: reordered ladder, tests host="0" before bracketed, so bracketed "0" mis-handled): exit 1 FAIL.
- atk_4 (boundary off-by: expands "0"->"0.0.0" wrong literal): exit 1 FAIL.
- atk_6 (bracket-wrap wrong: '[' ++ host without closing ']'): exit 1 FAIL.
- atk_8 (ungrounded over-expansion: non-bracketed always -> "0.0.0.0"): exit 1 FAIL.
- atk_5 (ungrounded-oracle echo: `return displayAddress bracketed host`): exit 0 VERIFIES — behaviourally identical to gold.
- atk_7 (control-flow restructure via `match bracketed`): exit 0 VERIFIES — behaviourally identical to gold.
- pos_control (verbatim gold impl): exit 0 VERIFIES.

All 6 behaviourally-DISTINCT wrong impls (partial-domain, boundary x2, control-flow reorder, broken concat, over-expansion) FAIL verification. The ONLY verifying attacks (atk_5, atk_7) are semantically equal to the gold ladder; their faithful refined patches transliterate to the exact gold three-way `addr` ladder and are byte-identical to patch.diff (sha1 f0f5295...).

RESOLVE EXECUTED (protocol step 2): ran `run_resolve('django__django-16145', <faithful patch>, timeout=1800, retries=1)` via swebench_unified.harness (official harness under `docker`). Result: RESOLVED=True, completed=True, note='resolved', flaky=False. FAIL_TO_PASS test_zero_ip_addr (admin_scripts.tests.ManageRunserver) success; PASS_TO_PASS all green. Both atk_5 and atk_7 faithful patches are byte-identical to the run patch, so both resolve. => verify DOES imply correct here; no verifying wrong impl yields a non-resolving patch.

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], additional_change_sites=[]. refinement.md legs A1-A6 are all R / R+I / I (§B/§C explicitly state no kind-A and no kind-3). No A-legs exist, so no callee-correspondence can be wrong; model displayAddress structurally mirrors gold addr ladder verbatim. G-CONF passed 100030 inputs (seed 16145), 0 disagreements. No kind-3 inexpressible op. Model<->patch correspondence holds.

Verdict: SOUND — 6+ distinct wrong impls attacked, all behaviourally-wrong ones rejected by the tight equality spec, only gold-equivalent echoes verify and their patches resolve under the official harness.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 2 | `atk_5.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the modeled display computation is a straight-line
-- ladder that always terminates and produces the banner text, so an
-- implementation that diverges (e.g. loops forever instead of producing the
-- expanded address) must NOT verify. Partial correctness would vacuously admit
-- such non-terminating implementations.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts and no deep-model references. The operation is a
--  pure, total computation over a flag and a character sequence — square-bracket
--  wrapping, a single literal-equality test, and string literals — every step of
--  which is directly expressible. There is no unchanged callee whose behaviour
--  the proof must assume, so the `axioms` region is intentionally empty.)
-- axioms-end

-- pure-start
/- The display form of a network host shown in a server's startup banner.

   Three cases, decided in order:
     * a host flagged as already being in delimited (bracketed) literal form is
       wrapped in a pair of square brackets, so it reads back as a single host
       token in a URL;
     * otherwise, the unspecified-host shorthand "0" is expanded to its
       canonical dotted-quad form "0.0.0.0", so the printed address is one a
       browser can actually follow;
     * any other host is shown exactly as given.

   The middle case is the behaviour of interest: the bare "0" shorthand must be
   normalised to "0.0.0.0" for display, while every other (non-bracketed) host
   is passed through unchanged. -/
def displayAddress (bracketed : Bool) (host : List Char) : List Char :=
  if bracketed then ['['] ++ host ++ [']']
  else if host = "0".toList then "0.0.0.0".toList
  else host
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Format a host for display in a startup banner. The two inputs are read-only:
   neither the bracket flag nor the host sequence is mutated (none is `mut`;
   directive 5). The result is pinned exactly to `displayAddress`, so no
   implementation that disagrees on any (flag, host) pair can verify.

   Alongside the exact-equality postcondition, the three observable branches are
   each pinned to a witnessed input combination: a bracketed host is wrapped; a
   non-bracketed host equal to the "0" shorthand becomes "0.0.0.0"; any other
   non-bracketed host is returned verbatim. -/
method formatHost (bracketed : Bool) (host : List Char) return (out : List Char)
  ensures out = displayAddress bracketed host
  ensures bracketed = true → out = ['['] ++ host ++ [']']
  ensures (bracketed = false ∧ host = "0".toList) → out = "0.0.0.0".toList
  ensures (bracketed = false ∧ host ≠ "0".toList) → out = host
  do
    -- impl-start
    if bracketed then
      return ['['] ++ host ++ [']']
    else
      if host = "0".toList then
        return "0.0.0.0".toList
      else
        return host
    -- impl-end

prove_correct formatHost by
  loom_solve <;> simp_all [displayAddress]
```

Prepatch bug re-encoded as an attack: `True`.

SOUND. Spec postcondition pins `out = displayAddress bracketed host` (exact equality, universally quantified over all (Bool, List Char) inputs, NO preconditions) plus three branch clauses — maximally tight. Same-spec confirmed True for all 8 attacks + positive control via swebench_unified.markers.same_spec (velvet).

### Results
- atk_1 (partial-domain / == prepatch bug: drops the "0"->"0.0.0.0" expansion, non-bracketed shown verbatim): exit 1 FAIL. Reproduces prepatch bug (prepatch_reproduced=true).
- atk_2 (boundary: expands "00" instead of "0"): exit 1 FAIL.
- atk_3 (control-flow-effect: reordered ladder, tests host="0" before bracketed, so bracketed "0" mis-handled): exit 1 FAIL.
- atk_4 (boundary off-by: expands "0"->"0.0.0" wrong literal): exit 1 FAIL.
- atk_6 (bracket-wrap wrong: '[' ++ host without closing ']'): exit 1 FAIL.
- atk_8 (ungrounded over-expansion: non-bracketed always -> "0.0.0.0"): exit 1 FAIL.
- atk_5 (ungrounded-oracle echo: `return displayAddress bracketed host`): exit 0 VERIFIES — behaviourally identical to gold.
- atk_7 (control-flow restructure via `match bracketed`): exit 0 VERIFIES — behaviourally identical to gold.
- pos_control (verbatim gold impl): exit 0 VERIFIES.

All 6 behaviourally-DISTINCT wrong impls (partial-domain, boundary x2, control-flow reorder, broken concat, over-expansion) FAIL verification. The ONLY verifying attacks (atk_5, atk_7) are semantically equal to the gold ladder; their faithful refined patches transliterate to the exact gold three-way `addr` ladder and are byte-identical to patch.diff (sha1 f0f5295...).

RESOLVE EXECUTED (protocol step 2): ran `run_resolve('django__django-16145', <faithful patch>, timeout=1800, retries=1)` via swebench_unified.harness (official harness under `docker`). Result: RESOLVED=True, completed=True, note='resolved', flaky=False. FAIL_TO_PASS test_zero_ip_addr (admin_scripts.tests.ManageRunserver) success; PASS_TO_PASS all green. Both atk_5 and atk_7 faithful patches are byte-identical to the run patch, so both resolve. => verify DOES imply correct here; no verifying wrong impl yields a non-resolving patch.

REFINEMENT AUDIT: meta.json axioms=[], deep_model_references=[], additional_change_sites=[]. refinement.md legs A1-A6 are all R / R+I / I (§B/§C explicitly state no kind-A and no kind-3). No A-legs exist, so no callee-correspondence can be wrong; model displayAddress structurally mirrors gold addr ladder verbatim. G-CONF passed 100030 inputs (seed 16145), 0 disagreements. No kind-3 inexpressible op. Model<->patch correspondence holds.

Verdict: SOUND — 6+ distinct wrong impls attacked, all behaviourally-wrong ones rejected by the tight equality spec, only gold-equivalent echoes verify and their patches resolve under the official harness.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness attack (spec-too-strong / model-vs-callee drift) on django__django-16145 velvet bundle. FAITHFUL — no diverging input exists.

Mandate check (does the modeled function disagree with the real callee on any input?): NO.

Modeled displayAddress ladder:
  if bracketed -> '[' ++ host ++ ']'
  elif host = "0".toList -> "0.0.0.0".toList
  else -> host

Real post-patch callee (gold patch, django/core/management/commands/runserver.py:132-137, confirmed against base_commit 93d4c9ea worktree AND the dataset patch):
  if self._raw_ipv6: addr = f"[{self.addr}]"
  elif self.addr == "0": addr = "0.0.0.0"
  else: addr = self.addr

These are a 1:1 transliteration under the mapping.md bijection (str<->List Char, bool<->Bool, f"[{x}]"<->['['] ++ x ++ [']'], =="0"<->="0".toList). On every (bracketed, host) pair the model returns exactly what the real ladder returns. Searched adversarially for divergence: near-"0" strings ("00","0.0","10","0x0"," 0","0 "), empty string, expanded form "0.0.0.0", bracketed hosts, unicode — the two ladders compute identically for all. The spec is not over-constrained: the model domain (all List Char) is a superset of reachable repo inputs (self.addr after naiveip_re parsing / bracket-stripping) and agrees exactly on that subset; there is no case the real code produces that the exact-equality postcondition rejects.

Evidence:
- same_spec(Solution.lean, Solution_prepatch.lean, velvet) = True: spec region (imports/options/axioms/pure displayAddress/pre/post/method signature+ensures) is byte-identical; prepatch differs only in elided impl+proof (drops the "0"->"0.0.0.0" branch) and genuinely fails the frozen "0" clause => G-DIFF real.
- scripts/lean_verify.sh Solution.lean => exit 0 (verifies).
- conformance_check.py (G-CONF, seed 16145) => OK, 0 disagreements over 100030 inputs (boundary set + 1e5 fuzz), shadow==oracle where oracle is the patch ladder transliterated verbatim.
- F2P test test_zero_ip_addr asserts banner substring http://0.0.0.0:8000/ for addrport="0:8000", i.e. observes addr verbatim; the modeled A6 pass-through to the banner is content-preserving.

Conclusion: the spec faithfully models the real callee; no faithfulness break.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function). The account names `Solution.lean`, `conformance_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Mechanical G-LEAK screen passes (leakage.screen over spec_view returns passed=True, no hard failures): no diff markers, no gold-patch line reproduced, no patched file path (runserver.py) or dotted module path, no spec-view identifier or comment echoing a patched repo symbol (inner_run, self._raw_ipv6, self.addr), no bug/fix narration. same_spec(Solution.lean, Solution_prepatch.lean) = True — spec region byte-identical, prepatch differs only in impl/proof.

Semantic review beyond the lexical screen: the gold edit's discriminating behavior is `elif self.addr == "0": addr = "0.0.0.0"`, modeled as `else if host = "0".toList then "0.0.0.0".toList`. This exact behavior is ALREADY PUBLIC in the problem_statement, which states "Output should be 'Starting development server at http://0.0.0.0:8000/' when providing '0:8000'". So revealing the 0→0.0.0.0 expansion in the spec does not exceed the solver-visible task. The bracket-wrap branch (['['] ++ host ++ [']']) models PRE-EXISTING IPv6 behavior ("[%s]" % self.addr if self._raw_ipv6), which is unchanged by the gold patch and therefore not a leak of the edit. Spec uses invented names (formatHost/displayAddress), no repo path/symbols, and abstract behavioral comments. No content is smuggled from hints_text or the diff beyond what problem_statement already discloses.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
