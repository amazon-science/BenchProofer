# P2 adversarial audit — django__django-16255

Backend: `lean`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is an exact closed-form equation: result = some (if hasM=false then none else if callM then vals.max? else constM), pinning result as a total function of all inputs. By function extensionality every impl that closes correct_ must return the identical Option (Option Int) on every input tuple, so no spec-closing impl can map to a non-resolving patch. The one attack that verifies (atk5) is a literal echo of the spec RHS, extensionally identical to the reference; its faithful patch is the gold patch and RESOLVES (run_resolve: RESOLVED=True, completed=True, note='resolved').
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -65,12 +65,7 @@
     Option (Option Int) := Id.run do
   if hasM = false then
     return some none
-  if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
-    return some vals.max?
-  else
-    return some constM
+  return some constM
 -- impl-end
 
 -- proof-start
```

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,9 +66,7 @@
   if hasM = false then
     return some none
   if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
-    return some vals.max?
+    return some vals.head?
   else
     return some constM
 -- impl-end
```

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -63,11 +63,9 @@
 def implementation_latestLastmod
     (hasM callM : Bool) (vals : List Int) (constM : Option Int) :
     Option (Option Int) := Id.run do
-  if hasM = false then
+  if hasM = true then
     return some none
   if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
     return some vals.max?
   else
     return some constM
```

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,9 +66,9 @@
   if hasM = false then
     return some none
   if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
-    return some vals.max?
+    match vals.max? with
+    | some d => return some (some d)
+    | none   => return none
   else
     return some constM
 -- impl-end
```

Attack 5 — `atk5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

```diff
@@ -62,15 +62,10 @@
 -- impl-start
 def implementation_latestLastmod
     (hasM callM : Bool) (vals : List Int) (constM : Option Int) :
-    Option (Option Int) := Id.run do
-  if hasM = false then
-    return some none
-  if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
-    return some vals.max?
-  else
-    return some constM
+    Option (Option Int) :=
+  some (if hasM = false then none
+        else if callM then vals.max?
+        else constM)
 -- impl-end
 
 -- proof-start
```

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,9 +66,7 @@
   if hasM = false then
     return some none
   if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
-    return some vals.max?
+    return some vals.getLast?
   else
     return some constM
 -- impl-end
```

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,11 +66,9 @@
   if hasM = false then
     return some none
   if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
+    return some constM
+  else
     return some vals.max?
-  else
-    return some constM
 -- impl-end
 
 -- proof-start
```

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

```diff
@@ -66,9 +66,7 @@
   if hasM = false then
     return some none
   if callM then
-    -- greatest of the per-item timestamps; an empty collection has no greatest
-    -- element, so the report is "no latest timestamp".
-    return some vals.max?
+    return some none
   else
     return some constM
 -- impl-end
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the single "latest timestamp" of a collection of items.

The collection knows two configuration facts:

  * whether a timestamp source is defined at all, and
  * whether the timestamp is computed PER ITEM (a function applied to each item)
    rather than being one constant value for the whole collection.

When the timestamp is computed per item, the report is the greatest of the
per-item timestamps. The collection may be EMPTY, in which case there is no
greatest element and the report is "no latest timestamp". When the timestamp is a
single constant value, the report is exactly that value (which may itself be absent).
When no timestamp source is defined, the report is "no latest timestamp".

The report is TOTAL: it always produces an answer, for every configuration —
including a per-item timestamp over an empty collection. Its value is an optional
timestamp: present (a timestamp) or absent ("no latest timestamp").
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The report is a pure
-- decision over the two configuration booleans, the list of per-item timestamps,
-- and the single constant timestamp. Producing the per-item timestamp list (applying
-- the per-item function across the collection) is abstracted to its result — the
-- list of timestamps — supplied as an input carrier. A timestamp is modeled as a
-- comparable ordinal (the only operation performed on it is the order comparison
-- that selects the greatest), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no extra pure helpers needed: the greatest-of-a-list operation is `List.max?`,
-- which is `none` for the empty list and `some` of the maximum otherwise.)
-- pure-end

-- post-conditions-start
/-- The report is TOTAL and fully pinned to the inputs.

  * `result = some v` always (the report never fails to produce an answer — in
    particular it is defined when the per-item timestamps are taken over an empty
    collection); there is no failing outcome.
  * the reported optional timestamp `v` is:
      - "no latest timestamp" (`none`) when no timestamp source is defined;
      - the greatest of the per-item timestamps (`vals.max?` — `none` exactly when
        the collection is empty) when the timestamp is computed per item;
      - the single constant timestamp otherwise.

No output component is left free: the outcome is `some` of the exact case split
over the inputs. -/
def problem_spec_latestLastmod
    (hasM callM : Bool) (vals : List Int) (constM : Option Int)
    (result : Option (Option Int)) : Prop :=
  result =
    some (if hasM = false then none
          else if callM then vals.max?
          else constM)
-- post-conditions-end

-- impl-start
def implementation_latestLastmod
    (hasM callM : Bool) (vals : List Int) (constM : Option Int) :
    Option (Option Int) := Id.run do
  if hasM = false then
    return some none
  if callM then
    -- greatest of the per-item timestamps; an empty collection has no greatest
    -- element, so the report is "no latest timestamp".
    return some vals.max?
  else
    return some constM
-- impl-end

-- proof-start
theorem correct_latestLastmod :
    ∀ (hasM callM : Bool) (vals : List Int) (constM : Option Int),
      problem_spec_latestLastmod hasM callM vals constM
        (implementation_latestLastmod hasM callM vals constM) := by
  intro hasM callM vals constM
  unfold problem_spec_latestLastmod implementation_latestLastmod
  cases hasM <;> cases callM <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED in fresh scratch dir. same_spec=True confirmed for all 9 files (atk_pc + atk1-8) via swebench_unified.markers.same_spec against Solution.lean. Verified concurrently in background batches of <=4 with: bash scripts/lean_verify.sh <path>.

### RESULTS (lean_verify exit codes):
- atk_pc (positive control, identical correct impl): exit 0; #print axioms -> 'does not depend on any axioms' (clean).
- atk1 partial-domain (drop callM branch, always constM): exit 1 (rfl failed).
- atk2 boundary (vals.head? instead of vals.max?): exit 1 (rfl failed).
- atk3 control-flow-effect (negate hasM guard: if hasM=true then some none): exit 1 (rfl failed).
- atk4 PREPATCH BUG (return outer none on empty per-item collection, modeling the ValueError raise): exit 1 (rfl failed) => prepatch reproduced as spec-violating.
- atk5 ungrounded-oracle echo (return spec RHS literally): exit 0; #print axioms -> 'does not depend on any axioms' (clean).
- atk6 boundary (vals.getLast?): exit 1 (rfl failed).
- atk7 branch swap (callM->constM, else->vals.max?): exit 1 (rfl failed).
- atk8 ungrounded (callM branch always some none, ignoring vals): exit 1 (rfl failed).

Every genuinely-wrong impl fails with 'rfl failed' (elaboration ERROR, not sorry). The ONLY closing impl besides the reference is atk5, the extensional echo of the exact-equation spec RHS, hence behaviorally identical to the reference. Per protocol its faithful refined patch (= gold: add ', default=None') was MATERIALIZED and RUN through the official harness: run_resolve('django__django-16255', atk5.patch, timeout=1200) => RESOLVED=True, completed=True, note='resolved'. So NO impl with a closing clean-axiom proof maps to a non-resolving patch.

A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=False. refinement.md legs are all R (ops 3,4: List.max?/Option Int type refinements) or I (ops 1,2,5: hasattr/callable guards + total-outcome framing). No kind-3 leg. No A-consumed / A-reference legs exist (get_latest_lastmod calls no unchanged callee needing an axiom; items()/lastmod(item) abstracted to the vals carrier). Correspondence to the real patched callee holds. R/I legs mechanically covered by G-CONF.

The exact-equation spec shape makes verify=>correct hold by function extensionality; >=5 distinct wrong impls (partial-domain, boundary x2, control-flow-effect, prepatch bug, branch-swap, ungrounded-oracle echo) attempted, none broke it. VERDICT: SOUND.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 8 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 8 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 7 | `atk1.lean`, `atk2.lean`, `atk3.lean`, `atk4.lean`, `atk6.lean`, `atk7.lean`, `atk8.lean` |
| verifies, and its patch resolves the instance, so it is a correct implementation and not a counterexample | 1 | `atk5.lean` |

**Non-vacuity.** The positive control `atk_pc.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is an exact closed-form equation: result = some (if hasM=false then none else if callM then vals.max? else constM), pinning result as a total function of all inputs. By function extensionality every impl that closes correct_ must return the identical Option (Option Int) on every input tuple, so no spec-closing impl can map to a non-resolving patch. The one attack that verifies (atk5) is a literal echo of the spec RHS, extensionally identical to the reference; its faithful patch is the gold patch and RESOLVES (run_resolve: RESOLVED=True, completed=True, note='resolved').
```

**Attacks re-run (8):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 8 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk5.lean` → correct echo (verifies AND its patch resolves — not a weakness)

Attack 6 — `atk6.lean` → rejected (same spec, does not verify — good)

Attack 7 — `atk7.lean` → rejected (same spec, does not verify — good)

Attack 8 — `atk8.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `atk_pc.lean`

```lean
import Mathlib
-- imports-end

/-!
Reporting the single "latest timestamp" of a collection of items.

The collection knows two configuration facts:

  * whether a timestamp source is defined at all, and
  * whether the timestamp is computed PER ITEM (a function applied to each item)
    rather than being one constant value for the whole collection.

When the timestamp is computed per item, the report is the greatest of the
per-item timestamps. The collection may be EMPTY, in which case there is no
greatest element and the report is "no latest timestamp". When the timestamp is a
single constant value, the report is exactly that value (which may itself be absent).
When no timestamp source is defined, the report is "no latest timestamp".

The report is TOTAL: it always produces an answer, for every configuration —
including a per-item timestamp over an empty collection. Its value is an optional
timestamp: present (a timestamp) or absent ("no latest timestamp").
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The report is a pure
-- decision over the two configuration booleans, the list of per-item timestamps,
-- and the single constant timestamp. Producing the per-item timestamp list (applying
-- the per-item function across the collection) is abstracted to its result — the
-- list of timestamps — supplied as an input carrier. A timestamp is modeled as a
-- comparable ordinal (the only operation performed on it is the order comparison
-- that selects the greatest), so no `opaque`/`axiom` callee contract is needed.
-- axioms-end

-- pure-start
-- (no extra pure helpers needed: the greatest-of-a-list operation is `List.max?`,
-- which is `none` for the empty list and `some` of the maximum otherwise.)
-- pure-end

-- post-conditions-start
/-- The report is TOTAL and fully pinned to the inputs.

  * `result = some v` always (the report never fails to produce an answer — in
    particular it is defined when the per-item timestamps are taken over an empty
    collection); there is no failing outcome.
  * the reported optional timestamp `v` is:
      - "no latest timestamp" (`none`) when no timestamp source is defined;
      - the greatest of the per-item timestamps (`vals.max?` — `none` exactly when
        the collection is empty) when the timestamp is computed per item;
      - the single constant timestamp otherwise.

No output component is left free: the outcome is `some` of the exact case split
over the inputs. -/
def problem_spec_latestLastmod
    (hasM callM : Bool) (vals : List Int) (constM : Option Int)
    (result : Option (Option Int)) : Prop :=
  result =
    some (if hasM = false then none
          else if callM then vals.max?
          else constM)
-- post-conditions-end

-- impl-start
def implementation_latestLastmod
    (hasM callM : Bool) (vals : List Int) (constM : Option Int) :
    Option (Option Int) := Id.run do
  if hasM = false then
    return some none
  if callM then
    -- greatest of the per-item timestamps; an empty collection has no greatest
    -- element, so the report is "no latest timestamp".
    return some vals.max?
  else
    return some constM
-- impl-end

-- proof-start
theorem correct_latestLastmod :
    ∀ (hasM callM : Bool) (vals : List Int) (constM : Option Int),
      problem_spec_latestLastmod hasM callM vals constM
        (implementation_latestLastmod hasM callM vals constM) := by
  intro hasM callM vals constM
  unfold problem_spec_latestLastmod implementation_latestLastmod
  cases hasM <;> cases callM <;> rfl
-- proof-end
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL EXECUTED in fresh scratch dir. same_spec=True confirmed for all 9 files (atk_pc + atk1-8) via swebench_unified.markers.same_spec against Solution.lean. Verified concurrently in background batches of <=4 with: bash scripts/lean_verify.sh <path>.

### RESULTS (lean_verify exit codes):
- atk_pc (positive control, identical correct impl): exit 0; #print axioms -> 'does not depend on any axioms' (clean).
- atk1 partial-domain (drop callM branch, always constM): exit 1 (rfl failed).
- atk2 boundary (vals.head? instead of vals.max?): exit 1 (rfl failed).
- atk3 control-flow-effect (negate hasM guard: if hasM=true then some none): exit 1 (rfl failed).
- atk4 PREPATCH BUG (return outer none on empty per-item collection, modeling the ValueError raise): exit 1 (rfl failed) => prepatch reproduced as spec-violating.
- atk5 ungrounded-oracle echo (return spec RHS literally): exit 0; #print axioms -> 'does not depend on any axioms' (clean).
- atk6 boundary (vals.getLast?): exit 1 (rfl failed).
- atk7 branch swap (callM->constM, else->vals.max?): exit 1 (rfl failed).
- atk8 ungrounded (callM branch always some none, ignoring vals): exit 1 (rfl failed).

Every genuinely-wrong impl fails with 'rfl failed' (elaboration ERROR, not sorry). The ONLY closing impl besides the reference is atk5, the extensional echo of the exact-equation spec RHS, hence behaviorally identical to the reference. Per protocol its faithful refined patch (= gold: add ', default=None') was MATERIALIZED and RUN through the official harness: run_resolve('django__django-16255', atk5.patch, timeout=1200) => RESOLVED=True, completed=True, note='resolved'. So NO impl with a closing clean-axiom proof maps to a non-resolving patch.

A-LEG AUDIT: meta.json axioms=[], deep_model_references=[], conf_skip=False. refinement.md legs are all R (ops 3,4: List.max?/Option Int type refinements) or I (ops 1,2,5: hasattr/callable guards + total-outcome framing). No kind-3 leg. No A-consumed / A-reference legs exist (get_latest_lastmod calls no unchanged callee needing an axiom; items()/lastmod(item) abstracted to the vals carrier). Correspondence to the real patched callee holds. R/I legs mechanically covered by G-CONF.

The exact-equation spec shape makes verify=>correct hold by function extensionality; >=5 distinct wrong impls (partial-domain, boundary x2, control-flow-effect, prepatch bug, branch-swap, ungrounded-oracle echo) attempted, none broke it. VERDICT: SOUND.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Callee: Sitemap.get_latest_lastmod (django/contrib/sitemaps/__init__.py:165) at base_commit 444b6da7 (worktree, HEAD 2c7846d). Patch is byte-identical to gold: add `, default=None` to `max([self.lastmod(item) for item in self.items()])`.

Mechanical preflight (all pass):
- Solution.lean compiles, exit 0 (lean_verify.sh).
- `#print axioms correct_latestLastmod` => 'does not depend on any axioms' (clean, no sorryAx).
- swebench_unified.markers.same_spec(Solution, Solution_prepatch, lean tables) = True: spec region byte-identical; the two files differ only in impl/proof (prepatch models the ValueError raise as outer `none`).

Faithfulness of spec `result = some (if hasM=false then none else if callM then vals.max? else constM)` vs. real patched method (model: outer none=raised, some v=returned v; date<->Int order-isomorphic ordinal; vals = [self.lastmod(item) for item in self.items()]):
- not hasattr => None  <->  hasM=false => some none. OK
- callable + nonempty => max([...], default=None) = greatest  <->  callM=true, vals nonempty => some vals.max? = some(some greatest). OK
- callable + empty => max([], default=None) = None (the fix)  <->  vals=[] => some vals.max? = some none. OK (List.max? []=none, nonempty=some max, exactly max(_,default=None)).
- not callable => self.lastmod  <->  else => some constM. OK

Domain: the unchanged `except TypeError` path (heterogeneous/incomparable timestamps, e.g. None mixed with dates) is genuinely unreachable for homogeneous totally-ordered vals: List Int, is untouched by the patch, and so excluding it does not narrow the modeled change or over-strengthen the spec. Searched for an in-domain diverging input and found none: List.max? and max(·,default=None) agree on all lists; hasM=false short-circuits identically; constM read iff not callable in both. Spec neither over- nor under-constrains the real callee on the modeled domain. VERDICT: FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, which ships in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Gold edit: `max([...])` -> `max([...], default=None)` in Sitemap.get_latest_lastmod, i.e. an empty per-item-callable collection returns None ('no latest timestamp') instead of raising ValueError. The PUBLIC problem_statement already fully discloses this: its title is 'Sitemaps without items raise ValueError on callable lastmod', its traceback pins `return max([self.lastmod(item) for item in self.items()])` / 'max() arg is an empty sequence', and it even proposes returning None for the empty case. The spec view models the report as TOTAL (never fails) with the empty per-item collection yielding `none` (vals.max? = none) — precisely the publicly-described corrected behavior, no more. The hasM/callM/constM branches are faithful full-method framing unrelated to the edit; no line names `default=None` or reveals the specific gold token beyond the problem statement. Mechanical G-LEAK screen (leakage.screen, lean backend) passes: passed=True, hard_failures=[] — no diff markers, no reproduced gold line, no patched file path, no patched-symbol echo (get_latest_lastmod/lastmod appear nowhere in spec-view identifiers/comments), no bug/fix narration. Meta G-LEAK not relaxed; not applicable. Nothing in the spec view leaks the gold edit beyond the public problem_statement.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view).
