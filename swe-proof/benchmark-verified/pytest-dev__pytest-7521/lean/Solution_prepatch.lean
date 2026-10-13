import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an opaque signature here. The operation under
-- specification — turning the raw character stream that was written into the
-- capture buffer back into the text handed to the caller — is modeled DEEPLY as
-- the single read pass below, rather than abstracted behind any callee. The
-- proof agent may add `_prop` axioms only if it gets stuck.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- The text read back out of a capture buffer must reproduce, character for
character, exactly the text that was written into it: nothing is dropped,
rewritten, merged, or inserted. The result is pinned entirely to the input
stream — the readback equals the written stream verbatim. -/
def problem_spec_readCaptured (written : List Char) (result : List Char) : Prop :=
  result = written
-- post-conditions-end

-- impl-start
/-- Pre-patch (buggy): the readback applies universal-newline translation. Every
carriage return is rewritten to a line feed, and a line feed that immediately
follows a carriage return is swallowed — so `\r\n` and a lone `\r` both collapse
to a single `\n`. Output that legitimately contained carriage returns is
corrupted. -/
def implementation_readCaptured (written : List Char) : List Char := Id.run do
  let mut out : Array Char := #[]
  let mut prevCR := false
  for c in written do
    if c = '\r' then
      out := out.push '\n'
      prevCR := true
    else if c = '\n' then
      if prevCR then
        prevCR := false
      else
        out := out.push '\n'
    else
      out := out.push c
      prevCR := false
  return out.toList
-- impl-end

-- proof-start
theorem correct_readCaptured :
    ∀ (written : List Char),
    problem_spec_readCaptured written (implementation_readCaptured written) := by
  sorry   -- carries the gold proof intent; UNCLOSABLE against the buggy impl (G-DIFF)
-- proof-end
