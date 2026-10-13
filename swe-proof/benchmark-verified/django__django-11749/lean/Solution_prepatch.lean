import Mathlib
-- imports-end

-- axioms-start
-- No unchanged callee requires an axiomatized contract: selecting an action's
-- least option flag, consulting the value table at a destination, and the
-- string formatting used to render each forwarded option are modeled directly
-- below (identical concrete ops), so there is nothing to axiomatize here.
-- axioms-end

-- pure-start

/-- A single parser action. `id` carries object identity (membership in a group
is identity-based in the source), `optionStrings` are the option flags, `req`
marks an individually-required action, `dest` is the destination key. -/
structure ParserAction where
  id : Nat
  optionStrings : List String
  req : Bool
  dest : String
deriving DecidableEq, Repr

/-- A mutually-exclusive option group: whether the group as a whole is required,
and the actions it contains (which share identity with entries in the flat
action list). -/
structure ExclusiveGroup where
  required : Bool
  groupActions : List ParserAction
deriving DecidableEq, Repr

/-- The lexicographically least of an action's option flags. An action that
declares no flag at all has no least flag, so the selection is not defined
there and reports `none`. -/
def leastFlag? (xs : List String) : Option String :=
  match xs with
  | [] => none
  | x :: rest => some (rest.foldl (fun m s => if s < m then s else m) x)

/-- Whether an action belongs to some group that is itself required. -/
def inRequiredGroup (groups : List ExclusiveGroup) (opt : ParserAction) : Bool :=
  groups.any (fun g => g.required && g.groupActions.any (· == opt))

/-- Whether the caller named this action's destination. The keys the caller
named are their own input, carried separately from the value table below. -/
def destInOptions (optionKeys : List String) (opt : ParserAction) : Bool :=
  optionKeys.any (· = opt.dest)

/-- The keep predicate: a keyword-named action is forwarded to the parser iff
its destination was named AND it is required, either individually or by virtue
of belonging to a required mutually-exclusive group. -/
def keepAction (groups : List ExclusiveGroup) (optionKeys : List String)
    (opt : ParserAction) : Bool :=
  destInOptions optionKeys opt && (opt.req || inRequiredGroup groups opt)

/-- Render a forwarded action as the `"<flag>=<value>"` string built from its
least flag and from the value the value table carries at its destination. TWO
independent lookups can yield nothing, and the rendering is then not defined —
`none`: an action declaring no flag has no least flag, and the value table need
not carry a value at every destination the caller named, those being two
separate inputs. -/
def renderArg? (argOptions : List (String × String)) (opt : ParserAction) :
    Option String :=
  (leastFlag? opt.optionStrings).bind fun flag =>
    (argOptions.lookup opt.dest).map fun value => flag ++ "=" ++ value

/-- Render a whole run of forwarded actions, in order. Defined only when every
action in the run renders. -/
def renderAll (argOptions : List (String × String)) :
    List ParserAction → Option (List String)
  | [] => some []
  | opt :: rest =>
    (renderArg? argOptions opt).bind fun s =>
      (renderAll argOptions rest).map fun ss => s :: ss

-- pure-end

-- post-conditions-start
/-- The forwarded-argument list: the (frame-pinned) positional prefix followed,
in action order, by the rendered string for exactly those actions selected by
`keepAction`. Selection consults the destination keys the caller NAMED; each
selected action's value is read from the separate value table. The whole result
is defined exactly when every selected action renders, and is `none` otherwise. -/
def problem_spec_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (parseArgsPrefix : List String) (result : Option (List String)) : Prop :=
  result =
    (renderAll argOptions (actions.filter (keepAction groups optionKeys))).map
      (fun rendered => parseArgsPrefix ++ rendered)
-- post-conditions-end

-- impl-start
def implementation_requiredOptionArgs
    (actions : List ParserAction) (groups : List ExclusiveGroup)
    (optionKeys : List String) (argOptions : List (String × String))
    (parseArgsPrefix : List String) :
    Option (List String) := do
  let mut parseArgs := parseArgsPrefix
  for opt in actions do
    if destInOptions optionKeys opt && opt.req then
      parseArgs := parseArgs ++ [← renderArg? argOptions opt]
  return parseArgs
-- impl-end

-- proof-start
theorem correct_requiredOptionArgs :
    ∀ (actions : List ParserAction) (groups : List ExclusiveGroup)
      (optionKeys : List String) (argOptions : List (String × String))
      (parseArgsPrefix : List String),
    problem_spec_requiredOptionArgs actions groups optionKeys argOptions
      parseArgsPrefix
      (implementation_requiredOptionArgs actions groups optionKeys argOptions
        parseArgsPrefix) := by
  sorry
-- proof-end
