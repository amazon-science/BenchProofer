import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The credential tokens this decision compares are
--  produced by UNCHANGED machinery and are observed ONLY by equality; they enter
--  as the free inputs `currentCred` / `priorCreds`. The decision makes no
--  behavioural claim about how a token is computed and holds for EVERY value the
--  tokens could take, so there is nothing to check against a real callee — hence
--  no G-AX. The behaviour under spec — the acceptance policy — is modeled deeply
--  in the `pure`/`impl` regions, no outside contract consumed. See mapping.md §3
--  / refinement.md.)
-- axioms-end

-- pure-start
/- A credential token, identified abstractly: the policy observes only whether
   two tokens are EQUAL (a constant-time comparison), never a token's content,
   so a single opaque carrier with decidable equality suffices. -/
abbrev Cred := Nat

/- How the retained credential was classified by the decision:
   * `valid`         — it matches the principal's credential under the current
                       secret;
   * `acceptedPrior` — it does not match the current-secret credential but
                       matches one produced under a previously-valid secret;
   * `reject`        — it is absent or matches no known credential. -/
inductive SessionAction where
  | valid
  | acceptedPrior
  | reject
deriving DecidableEq, Inhabited, Repr

/- The two observables of the decision:
   * `principalKept` — whether the located principal survives (`true`) or is
                       dropped in favour of an anonymous one (`false`);
   * `action`        — how the retained credential was classified. -/
structure SessionVerify where
  principalKept : Bool
  action        : SessionAction
deriving DecidableEq, Inhabited, Repr

/- The desired acceptance policy for a located principal's session.

   `storedCred` is the credential retained on the session (absent ↔ `none`),
   `currentCred` is the principal's credential under the current secret, and
   `priorCreds` are its credentials under the previously-valid secrets.

   * If no credential is retained, the session cannot be trusted: drop the
     principal (`reject`).
   * If the retained credential matches the one under the current secret, accept
     the session (`valid`).
   * Otherwise, if the retained credential matches one produced under a prior
     secret, the session is still the principal's — it was merely established
     before a secret change. Keep the principal, accepting the credential under
     that prior secret (`acceptedPrior`).
   * Otherwise the credential is unrecognised: drop the principal (`reject`). -/
def verifyDecision (storedCred : Option Cred) (currentCred : Cred)
    (priorCreds : List Cred) : SessionVerify :=
  match storedCred with
  | none   => { principalKept := false, action := SessionAction.reject }
  | some h =>
    if h = currentCred then
      { principalKept := true, action := SessionAction.valid }
    else if priorCreds.contains h then
      { principalKept := true, action := SessionAction.acceptedPrior }
    else
      { principalKept := false, action := SessionAction.reject }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide the fate of a located principal's session.

   It is handed the credential retained on the session (`storedCred`: a present
   token `some h`, or `none` when nothing is retained), the principal's
   credential under the current secret (`currentCred`), and — as a read-only free
   input — the principal's credentials under the previously-valid secrets
   (`priorCreds`, possibly empty). All three are derived by UNCHANGED machinery
   and are observed only by equality; the decision claims nothing about how a
   token is computed.

   It returns a `SessionVerify` recording whether the principal is kept and how
   the retained credential was classified. The desired behaviour is
   `verifyDecision`: accept a session whose retained credential matches the
   current secret (`valid`); keep the principal for one that matches only a
   prior secret (`acceptedPrior`); otherwise drop the principal (`reject`).

   `storedCred`, `currentCred`, `priorCreds` are all read-only (none `mut`): the
   routine reads them and builds a fresh outcome, mutating nothing it is handed
   (directive 5). -/
method resolveSessionPrincipal (storedCred : Option Cred) (currentCred : Cred) (priorCreds : List Cred) return (out : SessionVerify)
  ensures out = verifyDecision storedCred currentCred priorCreds
  do
    -- impl-start
    -- Pre-image (buggy) skeleton: there is NO prior-secret acceptance path. The
    -- retained credential is checked against the current secret ONLY; any
    -- mismatch (including a credential that a prior secret would recognise)
    -- drops the principal. The frozen spec requires the `acceptedPrior` outcome
    -- (and `principalKept = true`) when the credential matches a prior — not
    -- the current — secret, so prove_correct MUST fail on exactly that clause.
    match storedCred with
    | none   => return { principalKept := false, action := SessionAction.reject }
    | some h =>
      if h = currentCred then
        return { principalKept := true, action := SessionAction.valid }
      else
        return { principalKept := false, action := SessionAction.reject }
    -- impl-end

prove_correct resolveSessionPrincipal by
  loom_solve <;> simp_all [verifyDecision]
