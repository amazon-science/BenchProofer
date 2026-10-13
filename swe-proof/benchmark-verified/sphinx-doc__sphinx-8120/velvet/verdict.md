# P2 adversarial audit — sphinx-doc__sphinx-8120

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
None — no same-spec wrong impl verifies. The postcondition `out = sysNone :: (repoDirs ++ [packageLocale])` is an exact structural equality pinning the output for every input; any impl producing a different list leaves an 'unsolved goals' equality goal. There is therefore no verifying-but-wrong impl whose refined patch could fail to resolve.
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,9 +85,8 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
+    let mut localeDirs : List Dir := [sysNone, packageLocale]
     localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
     return localeDirs
     -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,7 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
-    localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
-    return localeDirs
+    return ((repoDirs ++ [packageLocale]) ++ [sysNone])
     -- impl-end
 
 prove_correct buildLocaleDirs by
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,7 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
-    localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
-    return localeDirs
+    return (sysNone :: (repoDirs.reverse ++ [packageLocale]))
     -- impl-end
 
 prove_correct buildLocaleDirs by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,7 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
-    localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
-    return localeDirs
+    return (sysNone :: repoDirs)
     -- impl-end
 
 prove_correct buildLocaleDirs by
```

Attack 5 — `atk_5.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,7 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
-    localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
-    return localeDirs
+    return (sysNone :: (repoDirs ++ [packageLocale, packageLocale]))
     -- impl-end
 
 prove_correct buildLocaleDirs by
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,7 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
-    localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
-    return localeDirs
+    return (sysNone :: (packageLocale :: repoDirs))
     -- impl-end
 
 prove_correct buildLocaleDirs by
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,10 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
-    localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
-    return localeDirs
+    if repoDirs = [] then
+      return (sysNone :: (repoDirs ++ [packageLocale]))
+    else
+      return (sysNone :: repoDirs)
     -- impl-end
 
 prove_correct buildLocaleDirs by
```

Attack 8 — `atk_8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -85,10 +85,7 @@
   ensures out = sysNone :: (repoDirs ++ [packageLocale])
   do
     -- impl-start
-    let mut localeDirs : List Dir := [sysNone]
-    localeDirs := localeDirs ++ repoDirs
-    localeDirs := localeDirs ++ [packageLocale]
-    return localeDirs
+    return (sysNone :: (repoDirs ++ [sysNone]))
     -- impl-end
 
 prove_correct buildLocaleDirs by
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Velvet.Std
-- imports-end

-- Total-correctness semantics: the operation under spec is straight-line
-- (three list appends; no loops or recursion — it always returns), so the
-- contract also demands termination. Under partial semantics a diverging
-- body would vacuously satisfy every postcondition.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no consumed axioms: the method's output is pinned structurally and the
--  search-order resolver below is a deep model validated against the real
--  message-catalog loader by axiom_check.py / G-AX.)
-- axioms-end

-- pure-start
/- A localization search entry is identified by its directory path. The
   system-default entry (a sentinel carrying no path) is just another entry in
   the ordered search list. -/
abbrev Dir := String

/- The message-catalog loader's lookup semantics: directories are searched in
   list order and the FIRST entry that defines a message supplies it; later
   entries only fill in messages no earlier entry defined. Front-recursive so a
   single unfold is available per step. `cat d k` is the translation directory
   `d` provides for message `k` (`none` if it provides none). Provenance +
   executable soundness check: mapping.md / axiom_check.py (G-AX). -/
def resolve (cat : Dir → String → Option String) : List Dir → String → Option String
  | [],      _ => none
  | d :: ds, k => (cat d k).orElse (fun _ => resolve cat ds k)

@[grind] lemma resolve_nil (cat : Dir → String → Option String) (k : String) :
    resolve cat [] k = none := rfl
@[grind] lemma resolve_cons (cat : Dir → String → Option String)
    (d : Dir) (ds : List Dir) (k : String) :
    resolve cat (d :: ds) k = (cat d k).orElse (fun _ => resolve cat ds k) := rfl

/- Searching a concatenation searches the prefix first; the suffix is consulted
   only when the prefix defines nothing. -/
lemma resolve_append (cat : Dir → String → Option String)
    (xs ys : List Dir) (k : String) :
    resolve cat (xs ++ ys) k
      = (resolve cat xs k).orElse (fun _ => resolve cat ys k) := by
  induction xs with
  | nil => simp [resolve]
  | cons d ds ih =>
    simp only [List.cons_append, resolve]
    cases h : cat d k with
    | none => simp [ih]
    | some v => simp

/- Behavioral consequence of the search order produced below: a message that any
   user-provided entry defines (and that the system-default entry does not) is
   resolved to that user value — the trailing package entry can never shadow it.
   This is the abstract property the issue demands (user overrides take effect);
   it is generic over the catalog contents and holds for the exact ordering the
   method returns. -/
lemma resolve_user_precedence
    (cat : Dir → String → Option String) (repoDirs : List Dir)
    (sysNone packageLocale : Dir) (k : String)
    (hsys : cat sysNone k = none)
    (huser : (resolve cat repoDirs k).isSome) :
    resolve cat (sysNone :: (repoDirs ++ [packageLocale])) k
      = resolve cat repoDirs k := by
  rw [resolve_cons, hsys, resolve_append]
  cases h : resolve cat repoDirs k with
  | none => rw [h] at huser; simp at huser
  | some v => simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the ordered localization search list from: the system-default entry,
   the user-provided entries, and the bundled package entry. The order is what
   determines precedence (earlier wins, per `resolve`). -/
method buildLocaleDirs (repoDirs : List Dir) (sysNone : Dir) (packageLocale : Dir)
    return (out : List Dir)
  ensures out = sysNone :: (repoDirs ++ [packageLocale])
  do
    -- impl-start
    let mut localeDirs : List Dir := [sysNone]
    localeDirs := localeDirs ++ repoDirs
    localeDirs := localeDirs ++ [packageLocale]
    return localeDirs
    -- impl-end

prove_correct buildLocaleDirs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT (velvet, sphinx-doc__sphinx-8120; root). Spec = pure exact-equality postcondition on buildLocaleDirs: ensures out = sysNone :: (repoDirs ++ [packageLocale]), which exactly matches gold patch's post-patch assembly [None] + list(repo.locale_dirs) + [path.join(package_dir,'locale')].

SAME-SPEC: verified True for all 9 files via swebench_unified.markers.same_spec (velvet) — only the impl region differs; axioms/pure/pre/post byte-identical.

### VERIFICATION (cmd `bash scripts/lean_verify.sh <f>`, run concurrently <=4 at a time):
- pos_control.lean (correct = gold order): EXIT 0, clean (no error/sorry/warning). POSITIVE CONTROL PASSES.
- atk_1.lean prepatch bug ([sysNone,packageLocale]++repoDirs, package before user): EXIT 1, unsolved goals. PREPATCH REPRODUCED (also confirmed with bundle's Solution_prepatch.lean -> EXIT 1).
- atk_2.lean ungrounded-oracle echo ((repoDirs++[packageLocale])++[sysNone], sysNone at end): EXIT 1, unsolved goals.
- atk_3.lean reversed user dirs (sysNone::(repoDirs.reverse++[packageLocale])): EXIT 1, unsolved goals.
- atk_4.lean partial/missing element (sysNone::repoDirs, drops packageLocale): EXIT 1, unsolved goals.
- atk_5.lean extra element (duplicate packageLocale): EXIT 1, unsolved goals.
- atk_6.lean boundary/order (sysNone::(packageLocale::repoDirs), package shadows user): EXIT 1, unsolved goals.
- atk_7.lean control-flow-effect partial-domain (if repoDirs=[] then correct else drops packageLocale): EXIT 1, unsolved goals.
- atk_8.lean wrong element (sysNone::(repoDirs++[sysNone]) instead of packageLocale): EXIT 1, unsolved goals (goal: sysNone::(repoDirs++[sysNone]) = sysNone::(repoDirs++[packageLocale])).

All 8 distinct wrong impls (spanning prepatch, ungrounded-oracle echo, boundary, partial-domain, control-flow-effect, extra/missing/wrong element) FAIL to verify with genuine 'unsolved goals' spec rejections — none is an infra/timeout artifact. Since NO verifying-but-wrong impl exists, there is no faithful refined patch to materialize/run through run_resolve; the verify=>correct route cannot be broken here. (patches={} for that reason — Protocol step 2 has no verifying wrong impl to trigger a resolve run.)

REFINEMENT.MD AUDIT: legs are A1=R, A2/A3/A4=I, A5=R+I, B1=A-reference, B2=A-reference+I. No kind-3 (inexpressible-changed-op) legs. The one changed operation (order of locale_dirs) is modeled by concrete I list-ops (A2-A4) and pinned by the exact-order postcondition (A5); the unchanged downstream loader is a DEEP MODEL (resolve) not a consumed axiom. Correspondence holds: postcondition order = gold order exactly. Crucially the A-reference `resolve` is NOT consumed by the method proof (verified: prove_correct uses only loom_solve over the equality postcondition), so verify=>resolve depends solely on the postcondition matching gold — which it does structurally and exactly. The resolve/resolve_user_precedence lemmas are narrative justification of WHY the order matters, not part of the discriminating obligation, so they cannot weaken the spec.

CONCLUSION: SOUND. 8 same-spec wrong impls attacked & verified-failed; positive control verifies; prepatch reproduced; refinement legs all R/A-reference/I with holding correspondence; no verifying wrong impl => verify=>correct not broken.

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
None — no same-spec wrong impl verifies. The postcondition `out = sysNone :: (repoDirs ++ [packageLocale])` is an exact structural equality pinning the output for every input; any impl producing a different list leaves an 'unsolved goals' equality goal. There is therefore no verifying-but-wrong impl whose refined patch could fail to resolve.
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

-- Total-correctness semantics: the operation under spec is straight-line
-- (three list appends; no loops or recursion — it always returns), so the
-- contract also demands termination. Under partial semantics a diverging
-- body would vacuously satisfy every postcondition.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (no consumed axioms: the method's output is pinned structurally and the
--  search-order resolver below is a deep model validated against the real
--  message-catalog loader by axiom_check.py / G-AX.)
-- axioms-end

-- pure-start
/- A localization search entry is identified by its directory path. The
   system-default entry (a sentinel carrying no path) is just another entry in
   the ordered search list. -/
abbrev Dir := String

/- The message-catalog loader's lookup semantics: directories are searched in
   list order and the FIRST entry that defines a message supplies it; later
   entries only fill in messages no earlier entry defined. Front-recursive so a
   single unfold is available per step. `cat d k` is the translation directory
   `d` provides for message `k` (`none` if it provides none). Provenance +
   executable soundness check: mapping.md / axiom_check.py (G-AX). -/
def resolve (cat : Dir → String → Option String) : List Dir → String → Option String
  | [],      _ => none
  | d :: ds, k => (cat d k).orElse (fun _ => resolve cat ds k)

@[grind] lemma resolve_nil (cat : Dir → String → Option String) (k : String) :
    resolve cat [] k = none := rfl
@[grind] lemma resolve_cons (cat : Dir → String → Option String)
    (d : Dir) (ds : List Dir) (k : String) :
    resolve cat (d :: ds) k = (cat d k).orElse (fun _ => resolve cat ds k) := rfl

/- Searching a concatenation searches the prefix first; the suffix is consulted
   only when the prefix defines nothing. -/
lemma resolve_append (cat : Dir → String → Option String)
    (xs ys : List Dir) (k : String) :
    resolve cat (xs ++ ys) k
      = (resolve cat xs k).orElse (fun _ => resolve cat ys k) := by
  induction xs with
  | nil => simp [resolve]
  | cons d ds ih =>
    simp only [List.cons_append, resolve]
    cases h : cat d k with
    | none => simp [ih]
    | some v => simp

/- Behavioral consequence of the search order produced below: a message that any
   user-provided entry defines (and that the system-default entry does not) is
   resolved to that user value — the trailing package entry can never shadow it.
   This is the abstract property the issue demands (user overrides take effect);
   it is generic over the catalog contents and holds for the exact ordering the
   method returns. -/
lemma resolve_user_precedence
    (cat : Dir → String → Option String) (repoDirs : List Dir)
    (sysNone packageLocale : Dir) (k : String)
    (hsys : cat sysNone k = none)
    (huser : (resolve cat repoDirs k).isSome) :
    resolve cat (sysNone :: (repoDirs ++ [packageLocale])) k
      = resolve cat repoDirs k := by
  rw [resolve_cons, hsys, resolve_append]
  cases h : resolve cat repoDirs k with
  | none => rw [h] at huser; simp at huser
  | some v => simp
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Assemble the ordered localization search list from: the system-default entry,
   the user-provided entries, and the bundled package entry. The order is what
   determines precedence (earlier wins, per `resolve`). -/
method buildLocaleDirs (repoDirs : List Dir) (sysNone : Dir) (packageLocale : Dir)
    return (out : List Dir)
  ensures out = sysNone :: (repoDirs ++ [packageLocale])
  do
    -- impl-start
    let mut localeDirs : List Dir := [sysNone]
    localeDirs := localeDirs ++ repoDirs
    localeDirs := localeDirs ++ [packageLocale]
    return localeDirs
    -- impl-end

prove_correct buildLocaleDirs by
  loom_solve
```

Prepatch bug re-encoded as an attack: `True`.

AUDIT (velvet, sphinx-doc__sphinx-8120; root). Spec = pure exact-equality postcondition on buildLocaleDirs: ensures out = sysNone :: (repoDirs ++ [packageLocale]), which exactly matches gold patch's post-patch assembly [None] + list(repo.locale_dirs) + [path.join(package_dir,'locale')].

SAME-SPEC: verified True for all 9 files via swebench_unified.markers.same_spec (velvet) — only the impl region differs; axioms/pure/pre/post byte-identical.

### VERIFICATION (cmd `bash scripts/lean_verify.sh <f>`, run concurrently <=4 at a time):
- pos_control.lean (correct = gold order): EXIT 0, clean (no error/sorry/warning). POSITIVE CONTROL PASSES.
- atk_1.lean prepatch bug ([sysNone,packageLocale]++repoDirs, package before user): EXIT 1, unsolved goals. PREPATCH REPRODUCED (also confirmed with bundle's Solution_prepatch.lean -> EXIT 1).
- atk_2.lean ungrounded-oracle echo ((repoDirs++[packageLocale])++[sysNone], sysNone at end): EXIT 1, unsolved goals.
- atk_3.lean reversed user dirs (sysNone::(repoDirs.reverse++[packageLocale])): EXIT 1, unsolved goals.
- atk_4.lean partial/missing element (sysNone::repoDirs, drops packageLocale): EXIT 1, unsolved goals.
- atk_5.lean extra element (duplicate packageLocale): EXIT 1, unsolved goals.
- atk_6.lean boundary/order (sysNone::(packageLocale::repoDirs), package shadows user): EXIT 1, unsolved goals.
- atk_7.lean control-flow-effect partial-domain (if repoDirs=[] then correct else drops packageLocale): EXIT 1, unsolved goals.
- atk_8.lean wrong element (sysNone::(repoDirs++[sysNone]) instead of packageLocale): EXIT 1, unsolved goals (goal: sysNone::(repoDirs++[sysNone]) = sysNone::(repoDirs++[packageLocale])).

All 8 distinct wrong impls (spanning prepatch, ungrounded-oracle echo, boundary, partial-domain, control-flow-effect, extra/missing/wrong element) FAIL to verify with genuine 'unsolved goals' spec rejections — none is an infra/timeout artifact. Since NO verifying-but-wrong impl exists, there is no faithful refined patch to materialize/run through run_resolve; the verify=>correct route cannot be broken here. (patches={} for that reason — Protocol step 2 has no verifying wrong impl to trigger a resolve run.)

REFINEMENT.MD AUDIT: legs are A1=R, A2/A3/A4=I, A5=R+I, B1=A-reference, B2=A-reference+I. No kind-3 (inexpressible-changed-op) legs. The one changed operation (order of locale_dirs) is modeled by concrete I list-ops (A2-A4) and pinned by the exact-order postcondition (A5); the unchanged downstream loader is a DEEP MODEL (resolve) not a consumed axiom. Correspondence holds: postcondition order = gold order exactly. Crucially the A-reference `resolve` is NOT consumed by the method proof (verified: prove_correct uses only loom_solve over the equality postcondition), so verify=>resolve depends solely on the postcondition matching gold — which it does structurally and exactly. The resolve/resolve_user_precedence lemmas are narrative justification of WHY the order matters, not part of the discriminating obligation, so they cannot weaken the spec.

CONCLUSION: SOUND. 8 same-spec wrong impls attacked & verified-failed; positive control verifies; prepatch reproduced; refinement legs all R/A-reference/I with holding correspondence; no verifying wrong impl => verify=>correct not broken.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Spec region (buildLocaleDirs ensures): out = sysNone :: (repoDirs ++ [packageLocale]). Verified against the real repo post-patch behavior.

FAITHFULNESS CHECK: The gold patch (patch.diff, confirmed byte-identical to the SWE-bench dataset gold patch and to base_commit 795747bdb6b8fb7d717d5bbfc2c3316869e66a73) rewrites _init_i18n's assembly to:
  locale_dirs = [None]
  locale_dirs += list(repo.locale_dirs)
  locale_dirs += [path.join(package_dir,'locale')]
which equals [None] + list(repo.locale_dirs) + [pkg] = None :: (repoDirs ++ [packageLocale]). Under the mapping.md type abstraction (None sentinel <-> sysNone, str dir <-> Dir, Python list <-> Lean List with order preserved), the modeled function buildLocaleDirs produces EXACTLY this ordered list on every input. The method is straight-line (three appends, no branching/recursion), so there is no input at which the modeled output diverges from the real post-patch _init_i18n assembly. No input makes the spec stronger or weaker than reality.

The ensures clause is not too strong: it pins precisely the discriminating behavioral change (user entries BEFORE the package entry). It is not too weak: prepatch order [sysNone, packageLocale] ++ repoDirs fails it (verified, unsolved goal at Solution_prepatch.lean:98), so the spec correctly excludes the buggy pre-patch behavior — G-DIFF holds.

### Evidence
- same_spec(Solution.lean, Solution_prepatch.lean) with velvet backend = True (spec region byte-identical; the SPEC_REGIONS axioms/pure/pre/post are equal — the resolve deep model + lemmas live in the pure region and match).
- Solution.lean verifies: lean_verify.sh exit 0.
- Solution_prepatch.lean fails the same ensures: exit 1, unsolved goal [sysNone, packageLocale] ++ repoDirs = sysNone :: (repoDirs ++ [packageLocale]) (unprovable whenever repoDirs != []).
- resolve is an A-reference (search-order model of the UNCHANGED sphinx.locale.init), out of the modeled-changed-function scope; it is audited by G-AX/axiom_check.py, not this gate. It does not weaken the buildLocaleDirs contract.

CONCLUSION: The modeled function agrees with the real callee on all inputs. No diverging input exists. Spec is faithful.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `axiom_check.py`, `mapping.md`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view confirmed byte-identical between Solution.lean and Solution_prepatch.lean via swebench_unified.markers.same_spec(get_backend('velvet')) = True; impl and prove_correct bodies are elided in the spec view. Leakage assessed against the PUBLIC problem_statement only (hints_text excluded).

Discriminating content in the spec view: (1) ensures clause `out = sysNone :: (repoDirs ++ [packageLocale])` on buildLocaleDirs, and (2) the `resolve_user_precedence` lemma (a user-defined message that the system default lacks resolves to the user value; the trailing package entry cannot shadow it).

Neither leaks the gold edit beyond the public issue. The problem_statement explicitly states the required behavior: a user-provided locale/<lang>/LC_MESSAGES/sphinx.po with updated entries SHOULD OVERRIDE the official built-in ('da') translation (the bug is that the built-in wins instead of the user's edits; Expected: user's edited caption labels take effect). 'User translation must override built-in' is logically equivalent to 'user dirs searched before the package/built-in dir', which is exactly what the ensures clause and resolve_user_precedence formalize. This is the legitimate behavioral postcondition any spec must pin so G-DIFF can separate gold from prepatch; it does not reveal gold-specific implementation detail beyond what the public issue already demands.

The remaining structural facts (the sysNone/None system-default first element, the packageLocale entry, the repoDirs user dirs) are pre-existing, non-secret facts present at base_commit: pre-patch code was `[None, path.join(package_dir,'locale')] + list(repo.locale_dirs)`, so the None-first element and all three participants already existed and are not the secret of the fix. The gold's actual secret — that the package entry must move to LAST (after the user dirs) — is the very thing the consumer must supply; it is NOT revealed as gold-diff text.

The spec view quotes no patch.diff text, no changed_files line, no hints_text/maintainer decision. Decisive corroboration: the prepatch encodes the WRONG order `[sysNone, packageLocale] ++ repoDirs` yet shares an IDENTICAL spec view and fails G-DIFF (lean_verify exit 1 on `[sysNone, packageLocale] ++ repoDirs = sysNone :: (repoDirs ++ [packageLocale])`), proving the ordering is genuinely the consumer's to derive and is not disclosed by the frozen spec text. The `resolve` deep-model lemmas describe the unchanged downstream loader's search semantics (public gettext/first-wins behavior), not the gold edit. Conclusion: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
