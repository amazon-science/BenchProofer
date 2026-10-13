import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The gating decision is a closed function of the
--  output-format name and a project option, both modeled DEEPLY: the
--  format-name tests are ordinary equality/prefix checks over the name's
--  characters, and the option is a boolean input. The set of rendered pages the
--  unchanged emission body would produce is carried as an opaque input
--  `generated` — an unchanged concrete tail (tagged I in refinement.md), not a
--  callee with a contract — so nothing is consumed as an axiom. See
--  refinement.md §C and mapping.md §3.)
-- axioms-end

-- pure-start
/- One rendered output page: a builder-visible artifact identified by its page
   name (the only field the desired behaviour observes — whether such a page is
   emitted at all). -/
structure Page where
  name : List Char
deriving DecidableEq, Inhabited, Repr

/- Whether the active output format is the single combined-document web format:
   the whole build is rendered into one document, which hosts no separate
   companion source pages. Recognised by its exact name. -/
@[grind] def isCombinedFormat (fmt : List Char) : Bool :=
  fmt == "singlehtml".toList

/- Whether the active output format is the portable e-book family. Every member
   of that family shares the same leading name token, so a prefix test
   recognises the whole family (the plain member and its versioned variants). -/
@[grind] def isEbookFormat (fmt : List Char) : Bool :=
  "epub".toList.isPrefixOf fmt

/- Whether rendered source pages must be SUPPRESSED for this build. They are
   suppressed for the single combined-document format always, and for the
   portable e-book family unless the project has explicitly opted in to
   including them in e-book output. For every other format they are kept. -/
@[grind] def shouldSuppress (fmt : List Char) (ebookOptIn : Bool) : Bool :=
  isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn)

/- The pages actually emitted by the collection step. When no source modules
   were collected at all there is nothing to emit; otherwise the pages are
   suppressed for the formats above, and kept (exactly the pages the emission
   body produces) for all others. -/
@[grind] def collectedPages (fmt : List Char) (ebookOptIn hasModules : Bool)
    (generated : List Page) : List Page :=
  if !hasModules then []
  else if shouldSuppress fmt ebookOptIn then []
  else generated
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The collection step that emits one rendered output page per collected source
   module at the end of a build. The desired behaviour: emit nothing when no
   source modules were collected; otherwise SUPPRESS the rendered pages for the
   single combined-document format, and for the portable e-book family unless
   the project opted in to including them in e-book output — and for every
   other output format emit exactly the pages the unchanged emission body
   produces.

   `fmt` (the output-format name), `ebookOptIn` (the project option),
   `hasModules` (whether any source modules were collected) and `generated`
   (the pages the unchanged emission body yields) are all read-only inputs:
   the step only decides whether to emit `generated` or nothing, and mutates
   none of them (directive 5). The suppression set is pinned exactly by
   `shouldSuppress`, and the emitted page list by `collectedPages`. -/
method gatedPageEmission (fmt : List Char) (ebookOptIn : Bool) (hasModules : Bool)
    (generated : List Page) return (out : List Page)
  ensures out = collectedPages fmt ebookOptIn hasModules generated
  ensures shouldSuppress fmt ebookOptIn =
            (isCombinedFormat fmt || (isEbookFormat fmt && !ebookOptIn))
  do
    -- impl-start
    -- Nothing was collected: emit nothing.
    if !hasModules then
      return []
    else
      -- The single combined-document format hosts no separate companion pages.
      if isCombinedFormat fmt then
        return []
      else
        -- Suppress for the e-book family unless the project opted in.
        if isEbookFormat fmt && !ebookOptIn then
          return []
        else
          return generated
    -- impl-end

prove_correct gatedPageEmission by
  loom_solve
