import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An opaque, distinguished marker value standing for one compiled exclusion
   pattern. Its internal structure is irrelevant to this decision; only whether
   it accepts a given character sequence matters (see `matchesPattern`). -/
axiom Pat : Type

/- The canonical form of a filesystem path: redundant separators collapsed and
   same-directory / parent references resolved, yielding the path's normalized
   spelling. An UNCHANGED standard-library path utility; it is total (every
   character sequence has a canonical form) and is left fully opaque — the
   weakest sufficient contract is none (directive 7). Provenance + executable
   soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom canonicalize : List Char → List Char

/- The trailing component of a path (everything after the final separator). An
   UNCHANGED standard-library path utility; total and left fully opaque.
   Provenance + soundness: mapping.md / axiom_check.py (G-AX). -/
axiom baseComponent : List Char → List Char

/- Whether one compiled exclusion pattern accepts a character sequence at its
   start. An UNCHANGED standard-library matcher; total (it either accepts or
   does not) and left fully opaque. Provenance + soundness: mapping.md /
   axiom_check.py (G-AX). -/
axiom matchesPattern : Pat → List Char → Bool
-- axioms-end

-- pure-start
/- Whether ANY pattern in a list accepts the given sequence — the existential
   fold over `matchesPattern`. This is the spelled-out deep model of the
   unchanged "matched by some pattern in this list" helper; its equality to that
   real helper is validated by axiom_check.py (G-AX, an A-reference). Written as
   a direct `List.any` so the decision below reduces definitionally. -/
noncomputable def anyMatch (ps : List Pat) (s : List Char) : Bool :=
  ps.any (fun p => matchesPattern p s)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decide whether a discovered filesystem path must be excluded from processing.

   `path` and the three exclusion configurations are read-only inputs (none is
   `mut`). The configurations are:
     * `ignoredNames`  — trailing-component names excluded verbatim;
     * `namePatterns`  — patterns tested against the trailing component;
     * `pathPatterns`  — patterns tested against the path itself.

   Desired behaviour: a path discovered during traversal may be spelled
   non-canonically (e.g. carrying same-directory references). The exclusion
   decision must be made against the path in its CANONICAL form, so that a
   pattern written against the canonical spelling governs the path regardless of
   how traversal happened to spell it. The path is therefore reduced to its
   canonical form first; the trailing component is taken from that canonical
   path; and the path-pattern test consults the canonical path — never the raw
   spelling. The result is the disjunction of the three exclusion tests over
   those canonical values. -/
noncomputable section
method shouldExclude (path : List Char) (ignoredNames : List (List Char))
    (namePatterns : List Pat) (pathPatterns : List Pat) return (out : Bool)
  ensures out = (ignoredNames.contains (baseComponent (canonicalize path))
                 || anyMatch namePatterns (baseComponent (canonicalize path))
                 || anyMatch pathPatterns (canonicalize path))
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct shouldExclude by
  -- proof elided — supplied by the consumer
