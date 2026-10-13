# P2 adversarial audit — django__django-11333

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,10 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 1: prepatch bug — present the RAW key, no None→default normalization.
 def implementation_cachedLookup
     (config : Option String) (defaultConfig : String) : Artifact := Id.run do
-  let mut key := config
-  if key = none then
-    key := some defaultConfig
+  let key := config
   return buildArtifact key
 -- impl-end
 
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,12 +56,14 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 2: partial-domain — correct only when config is explicit (some s);
+-- on the omitted lookup (none) it presents the raw none key (bug preserved
+-- only on that boundary).
 def implementation_cachedLookup
     (config : Option String) (defaultConfig : String) : Artifact := Id.run do
-  let mut key := config
-  if key = none then
-    key := some defaultConfig
-  return buildArtifact key
+  match config with
+  | some s => return buildArtifact (some s)
+  | none   => return buildArtifact none
 -- impl-end
 
 -- proof-start
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,12 +56,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 3: boundary/off-by-normalization — always normalize to default,
+-- ignoring the explicit config entirely (drops the some-s branch).
 def implementation_cachedLookup
     (config : Option String) (defaultConfig : String) : Artifact := Id.run do
-  let mut key := config
-  if key = none then
-    key := some defaultConfig
-  return buildArtifact key
+  let _ := config
+  return buildArtifact (some defaultConfig)
 -- impl-end
 
 -- proof-start
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,10 +56,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 4: control-flow-effect — wrong branch condition: normalize when
+-- config IS some (backwards), leaving none unnormalized.
 def implementation_cachedLookup
     (config : Option String) (defaultConfig : String) : Artifact := Id.run do
   let mut key := config
-  if key = none then
+  if key ≠ none then
     key := some defaultConfig
   return buildArtifact key
 -- impl-end
```

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -56,12 +56,12 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 5: ungrounded-oracle echo — return the spec's RHS literally,
+-- ignoring any executable normalization logic. Verifies trivially but the
+-- faithful patch (return the fixed constant) is not the real fix.
 def implementation_cachedLookup
-    (config : Option String) (defaultConfig : String) : Artifact := Id.run do
-  let mut key := config
-  if key = none then
-    key := some defaultConfig
-  return buildArtifact key
+    (config : Option String) (defaultConfig : String) : Artifact :=
+  buildArtifact (some (config.getD defaultConfig))
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,13 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 6: wrong-default — normalize the omitted lookup to a fixed constant
+-- ("") instead of the effective defaultConfig.
 def implementation_cachedLookup
     (config : Option String) (defaultConfig : String) : Artifact := Id.run do
   let mut key := config
   if key = none then
-    key := some defaultConfig
+    key := some ""
   return buildArtifact key
 -- impl-end
 
```

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -56,11 +56,15 @@
 -- post-conditions-end
 
 -- impl-start
+-- ATTACK 7: double-normalization / swapped — always wrap defaultConfig into
+-- the key but prefer config's inner string only when present via getD on the
+-- WRONG side (uses defaultConfig as the option content ignoring some s).
 def implementation_cachedLookup
     (config : Option String) (defaultConfig : String) : Artifact := Id.run do
-  let mut key := config
-  if key = none then
-    key := some defaultConfig
+  let mut key : Option String := some defaultConfig
+  match config with
+  | some _ => key := none
+  | none   => pure ()
   return buildArtifact key
 -- impl-end
 
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Looking up the artifact that is associated with a configuration.

A configuration may be supplied explicitly, or it may be omitted, in which case
a designated default configuration is meant instead. The artifact for a configuration
is produced by a memoized factory: the factory is keyed on the configuration it
is asked about, and asking it twice about the same configuration yields the very
same artifact — not merely an equivalent copy, but the identical one.

The desired behavior concerns this identity. Omitting the configuration must
denote *exactly* the default configuration: a lookup that leaves the
configuration unspecified and a lookup that names the default configuration
explicitly describe the same configuration, and so they must yield the identical
artifact. The artifact is therefore pinned to the factory applied to the
effective configuration — the explicit one when given, the default one when
omitted — so that the unspecified and explicit-default lookups coincide.
-/

-- axioms-start
/-- An opaque handle standing for a produced artifact. Equality on `Artifact`
models identity of the produced object in the host runtime: two lookups yield
the *same* artifact exactly when these handles are equal. -/
structure Artifact where
  handle : Nat
deriving Inhabited, DecidableEq

/-- The memoized factory that produces the artifact for a configuration key.

It is keyed on the configuration it is given (the key space includes the
"omitted" key, represented by `none`, as well as every explicit configuration
`some s`). Being an ordinary function, it is referentially transparent: asking
it about equal keys yields the identical artifact. It is consumed here as an
opaque carrier — the behavior modeled in this bundle is *which key* is presented
to it, not how it builds an artifact. -/
opaque buildArtifact : Option String → Artifact
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is selecting
-- the effective configuration key and presenting it to the memoized factory.
-- pure-end

-- post-conditions-start
/-- The produced artifact is fully pinned: it is the one the memoized factory
produces for the *effective* configuration — the explicitly supplied
configuration when one is given, and the default configuration when the
configuration is omitted. Because the effective configuration of an omitted
lookup equals that of an explicit default lookup, both yield the identical
artifact. No part of the result is left free. -/
def problem_spec_cachedLookup
    (config : Option String) (defaultConfig : String) (result : Artifact) : Prop :=
  result = buildArtifact (some (config.getD defaultConfig))
-- post-conditions-end

-- impl-start
def implementation_cachedLookup
    (config : Option String) (defaultConfig : String) : Artifact := Id.run do
  let mut key := config
  if key = none then
    key := some defaultConfig
  return buildArtifact key
-- impl-end

-- proof-start
theorem correct_cachedLookup :
    ∀ (config : Option String) (defaultConfig : String),
      problem_spec_cachedLookup config defaultConfig
        (implementation_cachedLookup config defaultConfig) := by
  intro config defaultConfig
  unfold problem_spec_cachedLookup implementation_cachedLookup
  cases config with
  | none => rfl
  | some s => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: total equation pinning result to opaque application `result = buildArtifact (some (config.getD defaultConfig))`. Because buildArtifact is opaque, any impl producing a different key k leaves an UNPROVABLE goal `buildArtifact k = buildArtifact (some (config.getD defaultConfig))`, so only behaviorally-correct impls can close. same_spec=True for all 7 attacks + positive control (verified via swebench_unified.markers.same_spec, lean backend).

Command per attack: `bash scripts/lean_verify.sh <path>` from repo root. Axioms via appended `#print axioms correct_cachedLookup`.

### Attack results
- atk_1 (prepatch bug / raw key, no None->default normalization): exit=1 (fails to close). Goal `(buildArtifact none).run = buildArtifact (some (none.getD defaultConfig))` unprovable. Correctly rejected.
- atk_2 (partial-domain: correct on some s, raw none on omitted): exit=1. Correctly rejected.
- atk_3 (ignore explicit config, always normalize to default): exit=1 (breaks the some-s branch). Correctly rejected.
- atk_4 (inverted branch condition: normalize when key != none): exit=1. Correctly rejected.
- atk_5 (ungrounded-oracle echo: returns spec RHS literally): exit=0, `#print axioms` => 'does not depend on any axioms' (CLEAN). This impl is BEHAVIORALLY IDENTICAL to gold (config.getD defaultConfig normalizes omitted->default and passes explicit through = the effective-config-before-memoization fix). Per protocol its faithful refined patch was materialized (= gold normalization patch, patch_equals_gold=True in meta) and RUN through the official harness: `SBU_BENCHMARK=swe_bench_verified run_resolve('django__django-11333', gold.patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. A resolving gold-equivalent echo is NOT a weakness (resolved G-PANEL-1/echo policy). Does not break the spec.
- atk_6 (wrong-default: normalize omitted to "" instead of defaultConfig): exit=1. Correctly rejected.
- atk_7 (swapped/degenerate key selection): exit=1. Correctly rejected.

POSITIVE CONTROL: pos_control.lean (= gold impl) exit=0, clean axioms.
PREPATCH: Solution_prepatch.lean (raw-key, omits None->default normalization) exit=1 — reproduces the FAIL_TO_PASS bug (get_resolver() vs get_resolver(ROOT_URLCONF) would be distinct cache slots). prepatch_reproduced=True.

refinement.md AUDIT: 3 legs, all tagged R (type-refinement), no kind-3. meta.json axioms=[], deep_model_references=[], conf_skip=False — consistent with refinement.md claim that buildArtifact is declared opaque only to carry the unchanged lru_cache factory into the executable impl, with NO axiom consumed (proof closes by case analysis + rfl). A-leg correspondence: buildArtifact <-> lru_cache-wrapped URLResolver(RegexPattern(r'^/'), key) construction, UNCHANGED by patch; the patch only changes which key reaches it (normalized effective config). Correspondence holds. No A-consumed / A-reference legs to falsify, so the A-leg attack surface reduces to: can any wrong key selection close? Answer NO (atk_1-4,6,7 all fail) — the total-equation pin is tight.

VERDICT: SOUND. >=6 distinct wrong impls attacked (prepatch + partial-domain + boundary + control-flow-effect + wrong-default + swapped + echo); every behaviorally-wrong impl fails to close; the sole closing impl (echo) is behaviorally gold-equivalent and its materialized faithful patch RESOLVES under the official harness. verify => correct holds.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 7 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 7 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 6 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_6.lean`, `atk_7.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk_5.lean` |

**Non-vacuity.** The positive control `pos_control.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

**Attacks re-run (7):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 7 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk_6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos_control.lean`

```lean
import Mathlib
-- imports-end

/-!
Looking up the artifact that is associated with a configuration.

A configuration may be supplied explicitly, or it may be omitted, in which case
a designated default configuration is meant instead. The artifact for a configuration
is produced by a memoized factory: the factory is keyed on the configuration it
is asked about, and asking it twice about the same configuration yields the very
same artifact — not merely an equivalent copy, but the identical one.

The desired behavior concerns this identity. Omitting the configuration must
denote *exactly* the default configuration: a lookup that leaves the
configuration unspecified and a lookup that names the default configuration
explicitly describe the same configuration, and so they must yield the identical
artifact. The artifact is therefore pinned to the factory applied to the
effective configuration — the explicit one when given, the default one when
omitted — so that the unspecified and explicit-default lookups coincide.
-/

-- axioms-start
/-- An opaque handle standing for a produced artifact. Equality on `Artifact`
models identity of the produced object in the host runtime: two lookups yield
the *same* artifact exactly when these handles are equal. -/
structure Artifact where
  handle : Nat
deriving Inhabited, DecidableEq

/-- The memoized factory that produces the artifact for a configuration key.

It is keyed on the configuration it is given (the key space includes the
"omitted" key, represented by `none`, as well as every explicit configuration
`some s`). Being an ordinary function, it is referentially transparent: asking
it about equal keys yields the identical artifact. It is consumed here as an
opaque carrier — the behavior modeled in this bundle is *which key* is presented
to it, not how it builds an artifact. -/
opaque buildArtifact : Option String → Artifact
-- axioms-end

-- pure-start
-- No additional pure helpers are required: the modeled behavior is selecting
-- the effective configuration key and presenting it to the memoized factory.
-- pure-end

-- post-conditions-start
/-- The produced artifact is fully pinned: it is the one the memoized factory
produces for the *effective* configuration — the explicitly supplied
configuration when one is given, and the default configuration when the
configuration is omitted. Because the effective configuration of an omitted
lookup equals that of an explicit default lookup, both yield the identical
artifact. No part of the result is left free. -/
def problem_spec_cachedLookup
    (config : Option String) (defaultConfig : String) (result : Artifact) : Prop :=
  result = buildArtifact (some (config.getD defaultConfig))
-- post-conditions-end

-- impl-start
def implementation_cachedLookup
    (config : Option String) (defaultConfig : String) : Artifact := Id.run do
  let mut key := config
  if key = none then
    key := some defaultConfig
  return buildArtifact key
-- impl-end

-- proof-start
theorem correct_cachedLookup :
    ∀ (config : Option String) (defaultConfig : String),
      problem_spec_cachedLookup config defaultConfig
        (implementation_cachedLookup config defaultConfig) := by
  intro config defaultConfig
  unfold problem_spec_cachedLookup implementation_cachedLookup
  cases config with
  | none => rfl
  | some s => rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

SPEC: total equation pinning result to opaque application `result = buildArtifact (some (config.getD defaultConfig))`. Because buildArtifact is opaque, any impl producing a different key k leaves an UNPROVABLE goal `buildArtifact k = buildArtifact (some (config.getD defaultConfig))`, so only behaviorally-correct impls can close. same_spec=True for all 7 attacks + positive control (verified via swebench_unified.markers.same_spec, lean backend).

Command per attack: `bash scripts/lean_verify.sh <path>` from repo root. Axioms via appended `#print axioms correct_cachedLookup`.

### Attack results
- atk_1 (prepatch bug / raw key, no None->default normalization): exit=1 (fails to close). Goal `(buildArtifact none).run = buildArtifact (some (none.getD defaultConfig))` unprovable. Correctly rejected.
- atk_2 (partial-domain: correct on some s, raw none on omitted): exit=1. Correctly rejected.
- atk_3 (ignore explicit config, always normalize to default): exit=1 (breaks the some-s branch). Correctly rejected.
- atk_4 (inverted branch condition: normalize when key != none): exit=1. Correctly rejected.
- atk_5 (ungrounded-oracle echo: returns spec RHS literally): exit=0, `#print axioms` => 'does not depend on any axioms' (CLEAN). This impl is BEHAVIORALLY IDENTICAL to gold (config.getD defaultConfig normalizes omitted->default and passes explicit through = the effective-config-before-memoization fix). Per protocol its faithful refined patch was materialized (= gold normalization patch, patch_equals_gold=True in meta) and RUN through the official harness: `SBU_BENCHMARK=swe_bench_verified run_resolve('django__django-11333', gold.patch, timeout=1800, retries=1)` => RESOLVED=True, COMPLETED=True, NOTE='resolved'. A resolving gold-equivalent echo is NOT a weakness (resolved G-PANEL-1/echo policy). Does not break the spec.
- atk_6 (wrong-default: normalize omitted to "" instead of defaultConfig): exit=1. Correctly rejected.
- atk_7 (swapped/degenerate key selection): exit=1. Correctly rejected.

POSITIVE CONTROL: pos_control.lean (= gold impl) exit=0, clean axioms.
PREPATCH: Solution_prepatch.lean (raw-key, omits None->default normalization) exit=1 — reproduces the FAIL_TO_PASS bug (get_resolver() vs get_resolver(ROOT_URLCONF) would be distinct cache slots). prepatch_reproduced=True.

refinement.md AUDIT: 3 legs, all tagged R (type-refinement), no kind-3. meta.json axioms=[], deep_model_references=[], conf_skip=False — consistent with refinement.md claim that buildArtifact is declared opaque only to carry the unchanged lru_cache factory into the executable impl, with NO axiom consumed (proof closes by case analysis + rfl). A-leg correspondence: buildArtifact <-> lru_cache-wrapped URLResolver(RegexPattern(r'^/'), key) construction, UNCHANGED by patch; the patch only changes which key reaches it (normalized effective config). Correspondence holds. No A-consumed / A-reference legs to falsify, so the A-leg attack surface reduces to: can any wrong key selection close? Answer NO (atk_1-4,6,7 all fail) — the total-equation pin is tight.

VERDICT: SOUND. >=6 distinct wrong impls attacked (prepatch + partial-domain + boundary + control-flow-effect + wrong-default + swapped + echo); every behaviorally-wrong impl fails to close; the sole closing impl (echo) is behaviorally gold-equivalent and its materialized faithful patch RESOLVES under the official harness. verify => correct holds.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) check for django__django-11333, modeled representative get_resolver in django/urls/resolvers.py.

### Verification performed
- same_spec(Solution.lean, Solution_prepatch.lean, LeanBackend.language) = True → post-conditions/axioms/pure spec regions are byte-identical between the pre- and post-patch bundles. Only impl differs (the fix adds the `if key = none then key := some defaultConfig` normalization before calling buildArtifact). Spec was NOT tightened to pass.
- scripts/lean_verify.sh Solution.lean → exit 0 (compiles, no sorry).
- `#print axioms correct_cachedLookup` → 'does not depend on any axioms' (no sorryAx; proof is real).

### SPEC vs REAL POST-PATCH CALLEE:
Spec: problem_spec_cachedLookup config defaultConfig result := result = buildArtifact (some (config.getD defaultConfig)).
Real get_resolver(urlconf): if urlconf is None: urlconf = settings.ROOT_URLCONF; return _get_cached_resolver(urlconf). Mapping: buildArtifact ↔ lru_cache-memoized _get_cached_resolver (referentially transparent, keyed on arg), config ↔ urlconf (str|None; none↔None, some s↔s), defaultConfig ↔ settings.ROOT_URLCONF, Artifact `=` ↔ CPython object identity `is`.

Case analysis (exhaustive over Option String):
- config=none: real returns _get_cached_resolver(ROOT_URLCONF); spec pins buildArtifact (some defaultConfig). Since (none).getD defaultConfig = defaultConfig, both denote key = defaultConfig. AGREE.
- config=some s: real returns _get_cached_resolver(s); spec pins buildArtifact (some s). AGREE.
Post-patch _get_cached_resolver is always invoked with a bare string, matching the always-`some` normalized key in the spec. No key ever reaches the factory as the raw None slot post-patch, consistent with the spec.

NOT OVER-STRONG: the postcondition asserts only the identity-collapse (`assertIs(get_resolver(), get_resolver(default))`), which is exactly the newly-added behavior. It does NOT assert distinctness for distinct configs (the pre-existing `assertIsNot` is not encoded), so the spec makes no claim stronger than the real callee guarantees. Cache-clear / cross-epoch behavior is a multi-call concern outside a single-call postcondition and introduces no divergence for any single input.

No input found where the modeled function disagrees with the real post-patch callee. Spec is FAITHFUL and appropriately scoped.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Spec view (Solution.lean, lean backend) judged against public problem_statement only (not hints_text). Mechanical leakage.screen passes (no hard failures); I confirm the semantic verdict too.

Gold edit: split get_resolver into a thin normalizer that resolves urlconf=None -> settings.ROOT_URLCONF BEFORE the lru_cache-memoized factory call, so the omitted call and explicit-default call share one cache slot and return the identical URLResolver (+ a behavior-preserving cache_clear rename to _get_cached_resolver).

The spec view encodes this abstractly: postcondition `result = buildArtifact (some (config.getD defaultConfig))` with generic names (buildArtifact/cachedLookup/Artifact/config/defaultConfig). Comments describe desired identity behavior in the abstract (omitted config denotes exactly the default; both must yield the identical artifact), with no bug/fix narration.

Nothing leaks BEYOND problem_statement:
- No patched repo symbols present (get_resolver, _get_cached_resolver, URLResolver, lru_cache, settings.ROOT_URLCONF).
- No patched file path/module path (django/urls/resolvers.py, django.urls.resolvers).
- No diff markers, no reproduced gold-patch line.
- Changed symbols {get_cached_resolver, reverse, repr}: none embedded in spec identifiers or comments.

Moreover, the public problem_statement itself already states the fix verbatim ('modify get_resolver to look up settings.ROOT_URLCONF before the memoized function call') and the failure mode (called with None first, ROOT_URLCONF later; multiple URLResolver._populate). So the spec's behavioral content (normalize omitted -> default before memoization) is already public; the abstract Lean spec adds no edit-localizing information beyond it. A spec necessarily encodes correct behavior, but that is not leakage when the behavior is public and the presentation is domain-generic.

Verdict: NO-LEAKAGE.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.
