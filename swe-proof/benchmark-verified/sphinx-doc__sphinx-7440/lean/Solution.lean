import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee needs an `opaque` signature here. Both modeled procedures
-- derive their result strings directly from the term/reference text by
-- straight-line code; the node-id builder and surrounding bookkeeping are not
-- part of the modeled identifier behavior and are not referenced. The proof
-- agent may add `_prop` axioms only if a proof obligation needs one.
-- axioms-end

-- pure-start
-- (no shared pure helpers needed)
-- pure-end

-- post-conditions-start
/-- Specification of forming a glossary term's registration entry.

`termtext` is the term's text as a sequence of characters. The entry produced
for a term is a pair: the identifier under which the term is registered for
cross-referencing (`result.1`) and the term as it appears in its index entry
(`result.2`). Both components are the term text with its exact characters
preserved — including letter case — so two terms differing only in case have
different identifiers, and a term's identifier matches its index entry. -/
def problem_spec_glossaryTermEntry
    (termtext : List Char) (result : List Char × List Char) : Prop :=
  result.1 = termtext ∧ result.2 = termtext
-- post-conditions-end

-- impl-start
def implementation_glossaryTermEntry
    (termtext : List Char) : List Char × List Char := Id.run do
  let key := termtext
  let indexTerm := termtext
  return (key, indexTerm)
-- impl-end

-- proof-start
theorem correct_glossaryTermEntry : ∀ (termtext : List Char),
    problem_spec_glossaryTermEntry termtext
      (implementation_glossaryTermEntry termtext) := by
  intro
  exact ⟨rfl, rfl⟩
-- proof-end

-- post-conditions-start
/-- Specification of computing the lookup target for a glossary cross-reference.

`target` is the reference text as a sequence of characters. The resolved lookup
target is that text with its exact characters preserved — including letter case —
so a reference resolves to the term spelled with the same case. -/
def problem_spec_termXrefTarget
    (target : List Char) (result : List Char) : Prop :=
  result = target
-- post-conditions-end

-- impl-start
def implementation_termXrefTarget (target : List Char) : List Char := Id.run do
  return target
-- impl-end

-- proof-start
theorem correct_termXrefTarget : ∀ (target : List Char),
    problem_spec_termXrefTarget target (implementation_termXrefTarget target) := by
  intro
  rfl
-- proof-end
