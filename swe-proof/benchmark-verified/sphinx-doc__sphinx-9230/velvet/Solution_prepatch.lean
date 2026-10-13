import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The way a parameter descriptor is separated into a type
   part and a name part — the only behaviour this operation depends on — is
   modeled DEEPLY in the `pure` region below (`severTail`) and validated against
   its real standard-library counterpart by axiom_check.py (G-AX) as an
   A-reference. Nothing is hidden behind a consumed `axiom`. -/
-- axioms-end

-- pure-start
/- The whitespace alphabet used when separating words: the Unicode code points
   the runtime treats as whitespace when separating on "any run of whitespace"
   (no explicit separator). This is the per-code-point classifier the separation
   below consults. Provenance + soundness check: mapping.md §3 / axiom_check.py. -/
def wsCodes : List Nat :=
  [0x9, 0xa, 0xb, 0xc, 0xd, 0x1c, 0x1d, 0x1e, 0x1f, 0x20, 0x85, 0xa0, 0x1680,
   0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008,
   0x2009, 0x200a, 0x2028, 0x2029, 0x202f, 0x205f, 0x3000]

def isWs (c : Char) : Bool := wsCodes.contains c.toNat

/- Drop a maximal run of trailing whitespace. -/
def rstripWs (s : List Char) : List Char :=
  (s.reverse.dropWhile isWs).reverse

/- The maximal whitespace-free suffix of `s` (its final word). -/
def tailWord (s : List Char) : List Char :=
  (s.reverse.takeWhile (fun c => !isWs c)).reverse

/- Everything strictly before the final whitespace-free suffix of `s`,
   including the whitespace run that precedes that suffix. -/
def beforeTailWord (s : List Char) : List Char :=
  (s.reverse.dropWhile (fun c => !isWs c)).reverse

/- Separate `s` into (everything-but-its-final-word, its-final-word) at the LAST
   run of whitespace, after first ignoring trailing whitespace. Leading and
   interior whitespace stays attached to the left part, so a left part that
   itself contains whitespace (e.g. a bracketed expression with internal spaces)
   is kept whole. `none` when, after ignoring outer whitespace, there is no
   whitespace separating two non-empty parts (a single word, or empty). The
   deep model of separating "on the last whitespace, at most once". -/
def severTail (s : List Char) : Option (List Char × List Char) :=
  let s' := rstripWs s
  let nm := tailWord s'
  let lead := rstripWs (beforeTailWord s')
  if lead.isEmpty then none else some (lead, nm)

/- The outcome of resolving one parameter descriptor. When the descriptor may
   carry an inline type and it separates into two parts at the last whitespace,
   the leading part is recorded as the type and the trailing word becomes the
   parameter name; otherwise the descriptor is left untouched and no type is
   recorded. This is the per-parameter result the operation produces. -/
structure ParsedParam where
  name     : List Char
  typeName : Option (List Char)
  deriving DecidableEq, Inhabited

def resolveParam (descriptor : List Char) (mayCarryType : Bool) : ParsedParam :=
  if mayCarryType then
    match severTail descriptor with
    | some (typ, nm) => { name := nm, typeName := some typ }
    | none           => { name := descriptor, typeName := none }
  else
    { name := descriptor, typeName := none }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Resolve one parameter descriptor into its name and (optional) inline type.
   Both inputs are read-only (not `mut`): the descriptor text and the
   may-carry-type flag are consulted, a fresh result is produced. When the
   descriptor may carry a type and its text separates at the last whitespace
   into a non-empty leading part and a trailing word, the leading part becomes
   the recorded type and the trailing word becomes the parameter name; in every
   other case the descriptor passes through unchanged with no recorded type
   (so a descriptor whose type expression itself contains spaces is kept whole
   as the type, and only its final word is taken as the name). -/
method resolveParamMethod (descriptor : List Char) (mayCarryType : Bool)
    return (out : ParsedParam)
  ensures out = resolveParam descriptor mayCarryType
  ensures mayCarryType = false → out = { name := descriptor, typeName := none }
  ensures out.typeName = none → out.name = descriptor
  ensures ∀ t a, severTail descriptor = some (t, a) → mayCarryType = true →
            out = { name := a, typeName := some t }
  do
    -- impl-start
    -- Pre-image skeleton: the descriptor is separated at the FIRST run of
    -- whitespace (its leading word becomes the type, everything after it the
    -- name). The frozen spec demands separation at the LAST whitespace
    -- (`severTail`/`resolveParam`), so on a descriptor whose type part itself
    -- contains whitespace the two disagree and `prove_correct` MUST fail.
    let out : ParsedParam :=
      if mayCarryType then
        let s' := descriptor.dropWhile isWs
        let head := s'.takeWhile (fun c => !isWs c)
        let rest := (s'.dropWhile (fun c => !isWs c)).dropWhile isWs
        if rest.isEmpty then { name := descriptor, typeName := none }
        else { name := rest, typeName := some head }
      else
        { name := descriptor, typeName := none }
    return out
    -- impl-end

prove_correct resolveParamMethod by
  loom_solve
  simp_all [resolveParam]
