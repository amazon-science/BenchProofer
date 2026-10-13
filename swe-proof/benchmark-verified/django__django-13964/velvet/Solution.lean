import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The decision modeled here observes, per stored
--  reference, only two values already supplied as inputs: the key currently
--  recorded on the referring object and the key now carried by the referenced
--  object. The "is this recorded key empty" test is modeled DEEPLY in the
--  `pure` region (`isEmpty`) and validated against the real notion of an empty
--  value by axiom_check.py (G-AX, an A-reference — see mapping.md §3 /
--  refinement.md). Nothing is consumed as an axiom, so there is no A-consumed
--  contract.)
-- axioms-end

-- pure-start
/- A stored value, modeled with just enough structure to decide whether it is
   "empty". A value is one of:
   * `pyNone`    — absent (the language's null);
   * `pyStr cs`  — a text value (empty exactly when it has no characters, e.g.
                   the empty string used for a non-numeric primary key);
   * `pyColl n`  — a collection value carrying `n` elements (empty when `n = 0`);
   * `pyInt k`   — a number (never empty).
   Emptiness is read off the structure, never stored as an answer. -/
inductive PyVal where
  | pyNone
  | pyStr  (cs : List Char)
  | pyColl (len : Nat)
  | pyInt  (k : Int)
  deriving DecidableEq, Inhabited

/- Whether a stored value counts as empty: absent, an empty text value, or an
   empty collection. A number is never empty. This is the structural notion of
   an "empty value" the desired behaviour keys off (problem statement: a
   primary key left as the empty string must be treated like an absent one). -/
def isEmpty : PyVal → Bool
  | .pyNone     => true
  | .pyStr  cs  => cs.isEmpty
  | .pyColl len => len == 0
  | .pyInt  _   => false

/- One reference held by the referring object:
   * `stored`    — the key value currently recorded for the reference;
   * `targetKey` — the key the referenced object now carries.
   `targetKey` is the value to adopt when the recorded key is still empty. -/
structure KeyRef where
  stored    : PyVal
  targetKey : PyVal
  deriving DecidableEq, Inhabited

/- The resolved stored key for one reference: when the recorded key is empty,
   adopt the referenced object's key; otherwise keep the recorded key. This is
   the per-reference decision the desired behaviour makes — an EMPTY recorded
   key (not merely an absent one) is the trigger to fill it in. -/
def resolvedKey (stored targetKey : PyVal) : PyVal :=
  if isEmpty stored then targetKey else stored

/- The resolved stored keys for a whole list of references: the per-reference
   resolution, element by element. Front-recursive so a single unfold is
   available per loop step (the backward-fold pattern, plan §5.4). -/
def resolvedKeys : List KeyRef → List PyVal
  | []      => []
  | r :: rs => resolvedKey r.stored r.targetKey :: resolvedKeys rs

@[grind] lemma resolvedKeys_nil : resolvedKeys [] = [] := rfl
@[grind] lemma resolvedKeys_cons (r : KeyRef) (rs : List KeyRef) :
    resolvedKeys (r :: rs) = resolvedKey r.stored r.targetKey :: resolvedKeys rs := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Reconcile the stored keys of an object's outgoing references against the
   keys their referenced objects now carry.

   For each reference, if the key recorded on the referring object is still
   EMPTY — absent, the empty string (as for a non-numeric primary key), or an
   empty collection — the referenced object's key is adopted; otherwise the
   recorded key is left as it stands. The result lists, in order, the resolved
   stored key for every reference.

   `refs` is read-only (not `mut`): the routine reads each reference and builds
   a fresh list of resolved keys, mutating nothing it is handed (directive 5).
   `require`: every referenced object already carries a key (its key is not
   absent) — the references reaching this reconciliation are exactly those whose
   referenced object is present and identified, the absent-key case having been
   handled beforehand. -/
method fillEmptyKeyRefs (refs : List KeyRef) return (out : List PyVal)
  require ∀ r ∈ refs, r.targetKey ≠ PyVal.pyNone
  ensures out = resolvedKeys refs
  do
    -- impl-start
    let mut result : List PyVal := []
    let mut i := refs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ refs.length
      invariant result = resolvedKeys (refs.drop i)
      done_with i = 0
      decreasing i
    do
      let r := refs[i - 1]!
      result := resolvedKey r.stored r.targetKey :: result
      i := i - 1
    return result
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `resolvedKeys` peels one `resolvedKey`. This is the
   single goal `loom_solve` leaves for the loop body. -/
lemma resolvedKeys_drop_step (refs : List KeyRef) (i : Nat)
    (hi : 0 < i) (hle : i ≤ refs.length) :
    resolvedKeys (refs.drop (i - 1))
      = resolvedKey (refs[i - 1]!).stored (refs[i - 1]!).targetKey
        :: resolvedKeys (refs.drop i) := by
  have hlt : i - 1 < refs.length := by omega
  have hcons : refs.drop (i - 1) = refs[i - 1]! :: refs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, resolvedKeys_cons]

prove_correct fillEmptyKeyRefs by
  loom_solve
  rw [resolvedKeys_drop_step refs i (by omega) (by omega)]
  simp_all
