import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No unchanged opaque callee is consumed. The modeled behaviour is the
--  per-axis carry-over of a shared coordinate's display-conversion setting,
--  modeled deeply below as a plain value copy. There is no consumed axiom and
--  no A-reference deep model of an unchanged callee. See refinement.md §C and
--  mapping.md §3.)
-- axioms-end

-- pure-start
/- The display-conversion setting that an axis may carry for the quantity
   plotted along it. It is either absent (`none` — no conversion configured) or
   a present setting identified up to object identity by an opaque tag
   (`some t`). When a quantity has already been plotted along an axis, that axis
   carries a present setting; a freshly created axis carries `none`.

   The behaviour under spec turns only on whether two axes carry the SAME
   setting (the identical present object, or both absent), so the setting is
   modeled as `Option Int`: `none` ↔ absent, `some t` ↔ a present setting whose
   integer tag is its object identity. Equality of the modeled value is exactly
   identity of the underlying setting (mapping.md §2). -/
abbrev ConvSetting := Option Int

/- Whether an axis carries a present (non-absent) conversion setting. The public
   reproduction observes that, after a quantity has been plotted, the shared
   axis carries a present setting on BOTH the original and the newly created
   companion axes. -/
@[grind, simp]
def isPresent (s : ConvSetting) : Bool := s.isSome
-- pure-end

-- pre-conditions-start
-- (inheritSharedConvA: the source axis's conversion setting for the shared
--  coordinate.)
-- pre-conditions-end

-- post-conditions-start
-- (inheritSharedConvA: the companion axis's setting for the shared coordinate
--  equals the source's — the same present object, or both absent.)
-- post-conditions-end

/- First companion-creation site. A new companion view is created that shares
   one coordinate with the source view. The companion's axis for that SHARED
   coordinate must carry exactly the source axis's conversion setting for it:
   the identical setting object when one is present, and absent when the source
   has none. Two guarantees pin the behavior the issue's tested scenario
   demands:

   - the companion's shared-axis setting equals the source's (`out = source`);
     so when the source already carries a present setting the companion carries
     that very same one, and the companion never silently starts from absent.
   - consequently the companion's shared axis reports a present setting exactly
     when the source does (`isPresent out = isPresent source`).

   `source` is the read-only setting carried by the source view's shared axis;
   the step constructs the companion's setting and never alters the source
   (directive 5). -/
method inheritSharedConvA (source : ConvSetting) return (out : ConvSetting)
  ensures out = source
  ensures isPresent out = isPresent source
  do
    -- impl-start
    let out := source
    return out
    -- impl-end

prove_correct inheritSharedConvA by
  loom_solve

-- pre-conditions-start
-- (inheritSharedConvB: the source axis's conversion setting for the shared
--  coordinate, at the second independent companion-creation site.)
-- pre-conditions-end

-- post-conditions-start
-- (inheritSharedConvB: same carry-over guarantee as inheritSharedConvA, at the
--  second independent site.)
-- post-conditions-end

/- Second, independent companion-creation site with the same obligation: a new
   companion view shares the OTHER coordinate with the source, and its axis for
   that shared coordinate must carry exactly the source axis's conversion
   setting. Modeled separately because it is observed independently of the first
   site (the issue's tested scenario exercises each coordinate on its own). -/
method inheritSharedConvB (source : ConvSetting) return (out : ConvSetting)
  ensures out = source
  ensures isPresent out = isPresent source
  do
    -- impl-start
    -- Pre-image skeleton: at the second site the companion axis is likewise
    -- created with no conversion setting for the shared coordinate (the
    -- freshly-initialised absent default) rather than carrying over the
    -- source axis's setting. The frozen spec demands `out = source`, so this
    -- diverges whenever the source carries a present setting and prove_correct
    -- MUST fail here.
    let out : ConvSetting := none
    return out
    -- impl-end

prove_correct inheritSharedConvB by
  loom_solve
