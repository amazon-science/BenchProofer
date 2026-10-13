import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The downstream credential lookup chain — locate a
--  principal for an identifier and validate the supplied secret against it — is
--  UNCHANGED, and its result is observed only through the free input
--  `backendOutcome : Option Principal`. The spec makes no behavioural claim
--  about that chain and holds for EVERY value it could take, so there is nothing
--  to check against a real callee, hence no G-AX. The behaviour under spec — the
--  admissibility short-circuit — is modeled deeply in the `pure`/`impl` regions,
--  no outside contract consumed. See mapping.md §3 / refinement.md.)
-- axioms-end

-- pure-start
/- An identifier, identified abstractly: the admissibility decision observes only
   whether one is PRESENT, never its concrete spelling, so a single opaque
   carrier suffices. -/
abbrev Name := Nat

/- A secret credential, identified abstractly: only its PRESENCE is observed
   here (its content flows untouched into the unchanged downstream chain). -/
abbrev Secret := Nat

/- A located principal, identified abstractly. -/
abbrev Principal := Nat

/- What the entry routine produces, recording BOTH observables that distinguish
   the desired behaviour:
   * `queried`  — whether the expensive downstream work was performed: the
                  identifier lookup against the store and the credential-strength
                  computation. `false` means neither was run.
   * `principal` — the authenticated principal handed back, if any. -/
structure AuthOutcome where
  queried   : Bool
  principal : Option Principal
  deriving DecidableEq, Inhabited

/- The identifier actually used downstream: the directly-supplied one when
   present, otherwise the one recovered from the surrounding extra arguments. -/
def effectiveName (supplied recovered : Option Name) : Option Name :=
  match supplied with
  | some u => some u
  | none   => recovered

/- The desired behaviour of the entry routine.

   The routine is only entitled to perform the expensive downstream work — an
   identifier lookup against the store and a credential-strength computation —
   when it has BOTH an identifier to look up and a secret to check. If either is
   absent, it must do NEITHER (perform no lookup, run no credential computation)
   and yield no principal: a request carrying incomplete credentials is simply
   not this routine's to serve. When both are present, the downstream chain runs
   and its outcome (`backendOutcome`) is returned verbatim. -/
def authDecision (supplied recovered : Option Name) (password : Option Secret)
    (backendOutcome : Option Principal) : AuthOutcome :=
  if (effectiveName supplied recovered).isNone || password.isNone then
    { queried := false, principal := none }
  else
    { queried := true, principal := backendOutcome }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The model-store credential entry routine. It is handed a directly-supplied
   identifier (`suppliedName`), an identifier recovered from the surrounding
   extra arguments used when the direct one is absent (`recoveredName`), a secret
   (`password`), and — as a read-only free input — the outcome the UNCHANGED
   downstream chain would yield were it run (`backendOutcome`: the principal
   located and validated, or none).

   It returns an `AuthOutcome` whose `queried` flag records whether the expensive
   downstream work (store lookup + credential-strength computation) was performed
   and whose `principal` is the principal handed back. The desired behaviour is
   `authDecision`: perform the downstream work, and hand back its outcome, only
   when an effective identifier AND a secret are both present; otherwise perform
   no work and hand back nothing.

   `suppliedName`, `recoveredName`, `password`, `backendOutcome` are all
   read-only (none `mut`): the routine reads them and builds a fresh outcome,
   mutating nothing it is handed (directive 5). -/
method authGuard (suppliedName : Option Name) (recoveredName : Option Name) (password : Option Secret) (backendOutcome : Option Principal) return (out : AuthOutcome)
  ensures out = authDecision suppliedName recoveredName password backendOutcome
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: NO admissibility short-circuit. The routine
    -- always proceeds into the expensive downstream path — performing the store
    -- lookup and credential-strength computation (`queried := true`) and handing
    -- back whatever that chain yields — even when no effective identifier or no
    -- secret was supplied. The frozen spec requires `queried = false` (and no
    -- principal) in that incomplete-credentials case, so prove_correct MUST
    -- fail on exactly that clause.
    let _effective := effectiveName suppliedName recoveredName
    return { queried := true, principal := backendOutcome }
    -- impl-end

prove_correct authGuard by
  loom_solve <;> simp_all [authDecision, effectiveName]
