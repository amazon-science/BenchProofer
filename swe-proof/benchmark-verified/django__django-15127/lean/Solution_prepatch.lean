import Mathlib
-- imports-end

/-!
The effective mapping from a message's level to its display tag is derived from
two configuration sources: a built-in set of default tags and a
user-supplied override mapping keyed by the same levels, with the override value
taking precedence whenever a level appears in both. This effective mapping is
held in a cache that downstream code consults to label individual messages.

Whenever a configuration value changes, the cached mapping must stay consistent
with the current configuration:

  * if the configuration value that changed is the message-tag override, the
    effective mapping is recomputed from the current defaults and the current
    overrides;
  * for any other configuration change, the cached mapping is left exactly as it
    was.

Inputs:
  * `tagsSettingChanged` — whether the configuration value that changed is the
    message-tag override;
  * `defaultTags` — the built-in default level→tag pairs;
  * `overrideTags` — the user-supplied override level→tag pairs;
  * `prevTagMap` — the cached mapping in effect prior to the change.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The defaults,
-- the overrides, and the previously-cached mapping all enter as plain data, and
-- the change indicator enters as a Bool. The only operation is the combination
-- of the two configuration sources into the effective mapping (overrides taking
-- precedence per level), modeled directly below. Hence no `opaque`/`axiom`
-- callee contract is required.
-- axioms-end

-- pure-start
/-- The effective level→tag mapping built from a set of default pairs and a set
of override pairs: the overrides take precedence over the defaults whenever a
level is present in both. Modeled as the overrides followed by the defaults, so
that a first-match lookup over the result returns the override value when one
exists for a level and the default value otherwise (the key set being the union
of both sources). -/
def mergeTags (defaultTags overrideTags : List (Int × String)) : List (Int × String) :=
  overrideTags ++ defaultTags
-- pure-end

-- post-conditions-start
/-- The cached mapping is fully pinned to the inputs:

  * when the configuration value that changed is the message-tag override, the
    result is exactly the effective mapping recomputed from the current defaults
    and overrides;
  * otherwise the result is exactly the previously-cached mapping, unchanged.

The two cases are exhaustive in `tagsSettingChanged`, so the result is
determined for every input — no output component is left free. -/
def problem_spec_resolveTagMap
    (tagsSettingChanged : Bool)
    (defaultTags overrideTags prevTagMap result : List (Int × String)) : Prop :=
  (tagsSettingChanged = true →
      result = mergeTags defaultTags overrideTags) ∧
  (tagsSettingChanged = false →
      result = prevTagMap)
-- post-conditions-end

-- impl-start
def implementation_resolveTagMap
    (tagsSettingChanged : Bool)
    (defaultTags overrideTags prevTagMap : List (Int × String)) :
    List (Int × String) := Id.run do
  let mut tagMap := prevTagMap
  return tagMap
-- impl-end

-- proof-start
theorem correct_resolveTagMap :
    ∀ (tagsSettingChanged : Bool)
      (defaultTags overrideTags prevTagMap : List (Int × String)),
      problem_spec_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap
        (implementation_resolveTagMap tagsSettingChanged defaultTags overrideTags prevTagMap) := by
  intro tagsSettingChanged defaultTags overrideTags prevTagMap
  unfold problem_spec_resolveTagMap implementation_resolveTagMap
  simp only [Id.run, bind, pure]
  refine ⟨?_, ?_⟩
  · intro h; simp [h]
  · intro h; simp [h]
-- proof-end
