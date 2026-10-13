import Mathlib
-- imports-end

/-!
Reading object signatures from the leading text of a documentation comment.

A documentation comment is a list of *blocks*, and each block is a list of text
lines. A line is recognised as a signature line by a given extended-signature
matcher; a recognised line yields a *thing name*, an argument string and an
optional return annotation. A recognised line is accepted only when its thing
name is one of the object's candidate names.

The desired behavior collects **every** signature offered at the start of a
block, in order, rather than only the first one. Within a block the lines are
read top to bottom and stop at the first empty line. A signature line that ends
in a backslash is a *continuation*: another signature follows it on the next
line (the trailing backslash and trailing whitespace are dropped before
matching), so reading proceeds to the next line. A signature line that does NOT
end in a backslash is the last one of the run, so reading of that block stops
there.
Lines that are not recognised, or whose thing name is not a candidate, are
skipped without stopping. Across the list of blocks, the first block that yields
at least one signature provides the whole result (the first such signature is
the primary one and the rest follow it, all in order); later blocks are then
ignored. If no block yields a signature the result is empty.
-/

-- axioms-start
/-- The outcome of matching one line against the extended-signature matcher: the
thing name, the argument string, and the (possibly empty) return annotation. -/
structure SigMatch where
  base : String
  args : String
  retann : String
deriving DecidableEq, Repr

/-- One collected signature: an argument string and a (possibly empty) return
annotation. -/
structure Sig where
  args : String
  retann : String
deriving DecidableEq, Repr

/-- The given extended-signature matcher applied to a single line. It returns
`none` when the line is not a signature line, otherwise the parsed thing name /
arguments / return annotation. This matcher is UNCHANGED by the modeled behavior
and is invoked identically wherever a line must be classified; the modeled
behavior consumes no property of it beyond "it is a deterministic function of
the line". The proof agent may add a `_prop` axiom only if a proof obligation
later needs one. -/
opaque matchSig : String → Option SigMatch
-- axioms-end

-- pure-start
/-- The whitespace codepoints Python's `str.rstrip()` (with no argument)
removes — exactly the characters `str.isspace()` accepts: tab, LF, VT, FF, CR,
FS/GS/RS/US, space, NEL, NBSP, Ogham space mark, the Unicode space separators
U+2000–U+200A, LS, PS, NNBSP, MMSP, and ideographic space. Note this is WIDER
than Lean's `Char.isWhitespace` (which is only space/tab/CR/LF). -/
def pyWhitespaceCodes : List UInt32 :=
  [0x9, 0xA, 0xB, 0xC, 0xD, 0x1C, 0x1D, 0x1E, 0x1F, 0x20, 0x85, 0xA0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000]

/-- `str.isspace()` / the character class `str.rstrip()` strips. -/
def isPyWhitespace (c : Char) : Bool :=
  pyWhitespaceCodes.contains c.val

/-- Drop a continuation marker from the end of a line: remove trailing
backslashes, then any trailing whitespace exposed underneath them
(`line.rstrip('\\').rstrip()` — Python's whitespace set). -/
def stripContinuation (s : String) : String :=
  String.mk
    (((s.toList.reverse.dropWhile (· = '\\')).dropWhile isPyWhitespace).reverse)

/-- Read the leading signature run of a single block.

The lines are walked front to back. An empty line ends the run. A line ending in
a backslash is a continuation (matched against its stripped form, then reading
proceeds); any other line is the last candidate of the run. A line that the
matcher rejects, or whose thing name is not among `validNames`, is skipped. The
accepted signatures are returned in order. -/
def scanDoc (validNames : List String) : List String → List Sig
  | [] => []
  | line0 :: rest =>
    if line0 = "" then []
    else
      let multiline := line0.endsWith "\\"
      let line := if multiline then stripContinuation line0 else line0
      match matchSig line with
      | none => scanDoc validNames rest
      | some m =>
        if validNames.contains m.base then
          let s : Sig := ⟨m.args, m.retann⟩
          if multiline then s :: scanDoc validNames rest else [s]
        else
          scanDoc validNames rest

/-- The collected signatures: the first block whose leading run is non-empty
supplies the entire result; otherwise the result is empty. -/
def collectSpec (validNames : List String) : List (List String) → List Sig
  | [] => []
  | doc :: docs =>
    let sigs := scanDoc validNames doc
    if sigs = [] then collectSpec validNames docs else sigs
-- pure-end

-- post-conditions-start
/-- The result is exactly the ordered list of signatures collected from the
documentation comment. This pins every component: the result's length, the order
of the signatures, and each signature's argument string and return annotation
are all determined by the input blocks and the candidate names. A correct result
must come from the first block that offers any signature, must include every
signature of that block's leading run (continuations included), and must stop at
the first non-continuation signature line; no signature may be dropped, added,
reordered, or sourced from a later block. -/
def problem_spec_collectSignatures
    (docstrings : List (List String)) (validNames : List String)
    (result : List Sig) : Prop :=
  result = collectSpec validNames docstrings
-- post-conditions-end

-- impl-start
/-- PRE-FIX skeleton: only the FIRST line of each block is inspected (raw, with
no continuation handling), and at most ONE signature is ever returned. The first
block whose first line is an accepted signature line supplies that single
signature; all other lines and any further signatures are ignored. -/
def implementation_collectSignatures
    (docstrings : List (List String)) (validNames : List String) : List Sig := Id.run do
  let mut result : Option Sig := none
  for doclines in docstrings do
    match doclines with
    | [] => continue
    | line0 :: _ =>
      match matchSig line0 with
      | none => continue
      | some m =>
        if validNames.contains m.base then
          result := some ⟨m.args, m.retann⟩
          break
        else
          continue
  match result with
  | none => return []
  | some r => return [r]
-- impl-end

-- proof-start
theorem correct_collectSignatures :
    ∀ (docstrings : List (List String)) (validNames : List String),
      problem_spec_collectSignatures docstrings validNames
        (implementation_collectSignatures docstrings validNames) := by
  sorry   -- carried-over placeholder: against this PRE-FIX impl no proof of the
          -- spec can close. On a block whose leading run is a backslash-
          -- continued pair of signature lines, the spec requires the full
          -- ordered list (two signatures, the first with its continuation
          -- marker stripped), whereas this impl returns a single signature
          -- carrying the raw, unstripped line — so the equality in
          -- `problem_spec` is unprovable, and G-VERIFY/G-DIFF fail here.
-- proof-end
