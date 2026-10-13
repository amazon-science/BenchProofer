import Mathlib
-- imports-end

/-!
Faithfully duplicating a structured value without copying any attached data.

The value space has three observable shapes:

  * a homogeneous **group** (an ordered collection) — duplicated by duplicating
    every element in place and rebuilding a group of the same kind;
  * a configurable **node** — a value that *exposes a configuration interface*
    (its keyed configuration can be read back) and is rebuilt from a fresh copy
    of that configuration;
  * everything else — an opaque leaf that exposes no configuration interface.

A node additionally carries a flag, `isBlueprint`, distinguishing a *blueprint*
(a template/recipe value) from a fully realized value. A blueprint nominally
advertises the configuration interface, yet that interface is bound to realized
values and cannot actually be queried on a blueprint; querying it on a blueprint
is invalid.

Duplication is parameterized by a `safe` flag. For any value that does NOT have
a usable configuration interface — because it exposes none at all, OR because it
is a blueprint (whose advertised interface is not usable) — duplication must NOT
attempt to read a configuration: when `safe = false` it returns the value
unchanged (a leaf duplicate that shares identity), and when `safe = true` it
reports a failure (the value is not a configurable node). Only a realized,
configuration-exposing node has its configuration read and each configuration
entry duplicated (unsafely) before the node is rebuilt.

The behavior to pin: the choice of whether to read a value's configuration
depends on whether that configuration is actually usable, NOT merely on whether
the value advertises the interface. A blueprint advertises it but is handled by
the no-configuration path, exactly like a leaf.
-/

-- axioms-start
-- No unchanged outside callee contributes a property the specification consumes.
-- Every routing decision — whether a value's configuration interface is usable,
-- and the consequent branch — is modeled structurally over the value's own
-- observable flags (`exposesConfig`, `isBlueprint`), and the rebuild is the
-- structural reconstruction `reproduce`. So no `opaque`/`axiom` callee is needed.
-- axioms-end

-- pure-start
/-- A structured value, restricted to the touched shape.

* `group kind elems` — an ordered collection of sub-values; `kind` records which
  collection variety it is (only equality of kinds is observed).
* `node isBlueprint exposesConfig tag config` — a value that may expose a keyed
  configuration. `exposesConfig` is whether the configuration-query interface is
  advertised; `isBlueprint` marks a template value whose advertised interface is
  not actually usable; `tag` is the value's class identity; `config` is the keyed
  configuration (each entry a `(key, sub-value)` pair). A leaf is a node with
  `exposesConfig = false`. -/
inductive PyVal where
  | group (kind : Nat) (elems : List PyVal)
  | node (isBlueprint : Bool) (exposesConfig : Bool) (tag : Nat) (config : List (Nat × PyVal))

/-- A value's configuration interface is usable for duplication iff the value
exposes the interface AND is not a blueprint. The no-configuration path is taken
in the complementary case: the value exposes nothing, OR it is a blueprint. -/
def configUnusable (isBlueprint exposesConfig : Bool) : Bool :=
  (!exposesConfig) || isBlueprint

/-- Structural duplication.

* A group is duplicated element-wise, preserving its kind and element order; if
  any element fails, the whole duplication fails.
* A value whose configuration interface is unusable (`configUnusable`) is on the
  no-configuration path: returned unchanged when `safe = false`, reported as a
  failure when `safe = true`.
* A realized, configuration-exposing node has each configuration entry
  duplicated (unsafely) and is then rebuilt with the duplicated configuration. -/
def reproduce (safe : Bool) : PyVal → Except Unit PyVal
  | .group kind es =>
      match es.attach.mapM (fun ⟨e, _⟩ => reproduce safe e) with
      | .error _ => .error ()
      | .ok es' => .ok (.group kind es')
  | .node isBlueprint exposesConfig tag cfg =>
      if configUnusable isBlueprint exposesConfig then
        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
      else
        -- Reached only for a realized configuration-exposing node; querying a
        -- blueprint's advertised interface here would be invalid.
        if isBlueprint then .error ()
        else
          match cfg.attach.mapM (fun ⟨kv, _⟩ => (reproduce false kv.2).map (fun v => (kv.1, v))) with
          | .error _ => .error ()
          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
termination_by v => sizeOf v
decreasing_by
  · have := List.sizeOf_lt_of_mem (by assumption : e ∈ es)
    simp_wf; omega
  · have h1 := List.sizeOf_lt_of_mem (by assumption : kv ∈ cfg)
    have h2 : sizeOf kv.2 < sizeOf kv := by cases kv; simp_wf
    simp_wf; omega
-- pure-end

-- post-conditions-start
/-- The duplicate is exactly the structural reproduction of the input under the
`safe` flag: groups duplicated element-wise, configuration-unusable values routed
to the no-configuration path (unchanged when unsafe, failure when safe), and only
realized configuration-exposing nodes rebuilt from a duplicated configuration. -/
def problem_spec_duplicate (safe : Bool) (v : PyVal) (result : Except Unit PyVal) : Prop :=
  result = reproduce safe v
-- post-conditions-end

-- impl-start
def implementation_duplicate (safe : Bool) : PyVal → Except Unit PyVal
  | .group kind es =>
      match es.attach.mapM (fun ⟨e, _⟩ => implementation_duplicate safe e) with
      | .error _ => .error ()
      | .ok es' => .ok (.group kind es')
  | .node isBlueprint exposesConfig tag cfg =>
      if !exposesConfig then
        if safe then .error () else .ok (.node isBlueprint exposesConfig tag cfg)
      else
        if isBlueprint then .error ()
        else
          match cfg.attach.mapM (fun ⟨kv, _⟩ => (implementation_duplicate false kv.2).map (fun v => (kv.1, v))) with
          | .error _ => .error ()
          | .ok cfg' => .ok (.node isBlueprint exposesConfig tag cfg')
termination_by v => sizeOf v
decreasing_by
  · have := List.sizeOf_lt_of_mem (by assumption : e ∈ es)
    simp_wf; omega
  · have h1 := List.sizeOf_lt_of_mem (by assumption : kv ∈ cfg)
    have h2 : sizeOf kv.2 < sizeOf kv := by cases kv; simp_wf
    simp_wf; omega
-- impl-end

-- proof-start
theorem correct_duplicate :
    ∀ (safe : Bool) (v : PyVal),
      problem_spec_duplicate safe v (implementation_duplicate safe v) := by
  sorry
-- proof-end
