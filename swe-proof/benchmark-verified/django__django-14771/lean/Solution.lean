import Mathlib
-- imports-end

/-!
Building the argument vector used to relaunch the Python interpreter for the
development auto-reloader's child process.

When the auto-reloader spawns the reloaded server, it reconstructs the command
line the interpreter was originally invoked with. The vector starts with the
interpreter executable, followed by one `-W<opt>` entry for every active warning
option. On the CPython implementation it must additionally forward every active
interpreter `-X` option, so that settings such as `-Xutf8` survive across a
reload; each such option becomes either a bare `-X<key>` (for a flag-style option
whose value is the sentinel "on") or `-X<key>=<value>` (for a valued option).
Finally the original invocation arguments are appended unchanged.

The resulting vector is therefore, in order:

  * the executable,
  * the `-W` warning entries (one per warning option, in order),
  * on CPython only, the `-X` interpreter entries (one per option, in order),
  * the original invocation arguments.

On a non-CPython implementation the `-X` block is omitted entirely.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The way each warning
-- option and each interpreter option is rendered into a command-line token is
-- spelled out directly as the pure helpers below (string formatting only); there
-- is no opaque repo callee whose property the proof must assume.
-- axioms-end

-- pure-start
/-- The value carried by an interpreter `-X` option: either a flag-style option
whose value is the sentinel "on" (rendered as a bare `-X<key>`), or a valued
option carrying a string (rendered as `-X<key>=<value>`). -/
inductive XVal where
  | flag          -- value is the "on" sentinel
  | val (s : String)

/-- Render one warning option `o` as the command-line token `-W<o>`. -/
def warnArg (o : String) : String := "-W" ++ o

/-- Render one interpreter option `(key, v)` as a command-line token: a bare
`-X<key>` for a flag-style option, or `-X<key>=<value>` for a valued one. -/
def xoptArg (kv : String × XVal) : String :=
  match kv.2 with
  | XVal.flag   => "-X" ++ kv.1
  | XVal.val v  => "-X" ++ kv.1 ++ "=" ++ v
-- pure-end

-- post-conditions-start
/-- The relaunch argument vector is fully pinned to the inputs: it is the
executable, then the warning tokens (one per warning option, in order), then —
only on the CPython implementation — the interpreter `-X` tokens (one per option,
in order), then the original invocation arguments, all concatenated in that
order. Every output component is determined by an input; nothing is left free. -/
def problem_spec_reloaderArgv
    (executable : String) (warnoptions : List String) (isCpython : Bool)
    (xoptions : List (String × XVal)) (argv : List String)
    (result : List String) : Prop :=
  result =
    ([executable] ++ warnoptions.map warnArg)
      ++ (if isCpython then xoptions.map xoptArg else [])
      ++ argv
-- post-conditions-end

-- impl-start
def implementation_reloaderArgv
    (executable : String) (warnoptions : List String) (isCpython : Bool)
    (xoptions : List (String × XVal)) (argv : List String) : List String := Id.run do
  -- Start from the executable and append one `-W` token per warning option.
  let mut args := [executable]
  for o in warnoptions do
    args := args ++ [warnArg o]
  -- On the CPython implementation, forward every active `-X` interpreter option.
  if isCpython then
    for kv in xoptions do
      args := args ++ [xoptArg kv]
  -- On the common relaunch path the original invocation arguments are appended
  -- unchanged.
  args := args ++ argv
  return args
-- impl-end

-- proof-start
/-- A `for x in xs do acc := acc ++ [f x]` loop (over a `List`, in `Id`) builds
exactly `init ++ xs.map f`. Generalized over the accumulator so the induction
goes through. -/
theorem forIn_yield_append {α β : Type} (xs : List α) (init : List β) (f : α → β) :
    (forIn xs init (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β))
      = init ++ xs.map f := by
  induction xs generalizing init with
  | nil => simp only [List.forIn_nil, List.map_nil, List.append_nil]; rfl
  | cons a as ih =>
    rw [List.forIn_cons]
    show (forIn as (init ++ [f a]) (fun x r => ForInStep.yield (r ++ [f x])) : Id (List β)) = _
    rw [ih]
    simp [List.map_cons]

theorem correct_reloaderArgv :
    ∀ (executable : String) (warnoptions : List String) (isCpython : Bool)
      (xoptions : List (String × XVal)) (argv : List String),
      problem_spec_reloaderArgv executable warnoptions isCpython xoptions argv
        (implementation_reloaderArgv executable warnoptions isCpython xoptions argv) := by
  intro executable warnoptions isCpython xoptions argv
  unfold problem_spec_reloaderArgv implementation_reloaderArgv
  simp only [Id.run, bind, pure]
  cases isCpython <;>
    simp only [forIn_yield_append, Bool.false_eq_true, if_true, if_false,
      List.append_assoc, List.singleton_append, List.nil_append]
-- proof-end
