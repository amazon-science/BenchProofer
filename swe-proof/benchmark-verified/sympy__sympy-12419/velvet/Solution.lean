import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behaviour modeled is the choice of element value for a
   square diagonal-of-units operator at a symbolic position. The decision rests
   on two three-valued verdicts, each produced by a separate primitive and
   supplied to the method as an input: the verdict of comparing the two
   positions, and the coincidence indicator's OWN self-evaluation at those
   positions. Their agreement with the real primitives is exercised end-to-end by
   the conformance check (G-CONF); there is no module-level `axiom`. Provenance:
   mapping.md §3. -/
-- axioms-end

-- pure-start
/- A position into the operator: an opaque symbolic index. Two positions carry
   no decidable structure here — whether they coincide is decided by the
   three-valued verdicts that are passed in, NOT by inspecting the carrier — so
   this is just an abstract atom that the result may refer to. -/
structure Idx where
  id : Nat
deriving DecidableEq, Inhabited

/- The element value of a diagonal-of-units operator at one position. It is an
   honest symbolic-value carrier with NO opaque "answer" node:

     • `unit`        — the multiplicative unit,
     • `null`        — the additive zero,
     • `coincide a b`— the symbolic coincidence indicator of the two positions,
                       left UNEVALUATED: the value that becomes the unit or the
                       zero only once the coincidence of `a` and `b` is settled.

   The `coincide` node refers to the actual positions `a b`, so the result on the
   unsettled case is forced to be *produced by* the operands; a builder that did
   not consult them could not emit this node. -/
inductive MatEntry where
  | unit
  | null
  | coincide (a b : Idx)
deriving DecidableEq, Inhabited

/- Three-valued verdicts are modeled as `Option Bool`: `some true` = definitely
   coincident, `some false` = definitely distinct, `none` = unsettled (the
   question cannot be decided from what the primitive can see).

   TWO verdicts are consumed, because the operator's element value is selected in
   two stages and each stage has its OWN, DIFFERENT decision power:

     • `eq` — the verdict of the position-comparison primitive;
     • `kd` — the verdict of the coincidence indicator's own self-evaluation at
              the same two positions.

   These are NOT the same verdict. The indicator decides coincidence by its own
   rules, which see facts about the positions that the comparison primitive does
   not, so the indicator can settle a pair that the comparison leaves unsettled.
   `kd` is therefore an independent input, not a function of `eq`. -/

/- The value the coincidence indicator itself denotes at positions `i`, `j`,
   given its own three-valued self-evaluation `kd`:

     • definitely coincident (`some true`)  → the unit,
     • definitely distinct   (`some false`) → the zero,
     • unsettled             (`none`)       → the indicator, left unevaluated
                                              and referring to `i` and `j`.

   This is the indicator's contract: it is a value that COLLAPSES when its own
   rules settle the coincidence, and survives as a symbolic object only while
   they do not. -/
def coincideValue (i j : Idx) (kd : Option Bool) : MatEntry :=
  if kd = some true then MatEntry.unit
  else if kd = some false then MatEntry.null
  else MatEntry.coincide i j

/- The desired element value at positions `i`, `j` given the comparison verdict
   `eq` and the indicator's own verdict `kd`:

     • comparison definitely coincident (`some true`)  → the unit,
     • comparison definitely distinct   (`some false`) → the zero,
     • comparison UNSETTLED             (`none`)       → hand the pair to the
                                                        coincidence indicator and
                                                        take the value IT denotes.

   The second stage is itself a full three-way selection, not a single value:
   the indicator yields the unit or the zero where its own rules settle the pair,
   and remains the unevaluated indicator over the operands only where they do
   not. -/
def entryFor (i j : Idx) (eq : Option Bool) (kd : Option Bool) : MatEntry :=
  if eq = some true then MatEntry.unit
  else if eq = some false then MatEntry.null
  else coincideValue i j kd

@[grind] lemma entryFor_true (i j : Idx) (kd : Option Bool) :
    entryFor i j (some true) kd = MatEntry.unit := rfl
@[grind] lemma entryFor_false (i j : Idx) (kd : Option Bool) :
    entryFor i j (some false) kd = MatEntry.null := rfl
@[grind] lemma entryFor_none (i j : Idx) (kd : Option Bool) :
    entryFor i j none kd = coincideValue i j kd := rfl

@[grind] lemma coincideValue_true (i j : Idx) :
    coincideValue i j (some true) = MatEntry.unit := rfl
@[grind] lemma coincideValue_false (i j : Idx) :
    coincideValue i j (some false) = MatEntry.null := rfl
@[grind] lemma coincideValue_none (i j : Idx) :
    coincideValue i j none = MatEntry.coincide i j := rfl

/- When BOTH verdicts leave the coincidence unsettled the value is the
   unevaluated indicator over the two positions, which is a symbolic object
   distinct from the zero. Note the scope: the claim is made exactly where the
   indicator declines to collapse, NOT wherever the comparison declines to
   settle. Where the indicator's own rules DO settle the pair, its value is the
   unit or the zero, and the operator reports that. -/
@[grind] lemma entryFor_unsettled_ne_null (i j : Idx) :
    entryFor i j none none ≠ MatEntry.null := by
  simp [entryFor, coincideValue]

@[grind] lemma entryFor_unsettled_eq_coincide (i j : Idx) :
    entryFor i j none none = MatEntry.coincide i j := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Select the element value of a square diagonal-of-units operator at positions
   `i` and `j`, given the three-valued verdict `eq` of comparing the two
   positions and the three-valued verdict `kd` of the coincidence indicator's own
   self-evaluation at those same positions. Both verdicts are produced by
   separate primitives and both are read-only (neither is `mut`).

   Desired behaviour: a comparison that settles the pair yields the unit
   (coincident) or the zero (distinct). A comparison that leaves the pair
   UNSETTLED hands it to the coincidence indicator, and the result is the value
   the indicator denotes: the unit or the zero where the indicator's own rules
   settle it, and otherwise the indicator itself, unevaluated and referring to
   both operands. -/
method identityEntry (i : Idx) (j : Idx) (eq : Option Bool) (kd : Option Bool) return (out : MatEntry)
  ensures out = entryFor i j eq kd
  ensures eq = some true  → out = MatEntry.unit
  ensures eq = some false → out = MatEntry.null
  ensures eq = none → out = coincideValue i j kd
  ensures eq = none → kd = some true  → out = MatEntry.unit
  ensures eq = none → kd = some false → out = MatEntry.null
  ensures eq = none → kd = none → out = MatEntry.coincide i j
  ensures eq = none → kd = none → out ≠ MatEntry.null
  do
    -- impl-start
    if eq = some true then
      return MatEntry.unit
    else
      let e : MatEntry :=
        if eq = some false then MatEntry.null
        else
          if kd = some true then MatEntry.unit
          else if kd = some false then MatEntry.null
          else MatEntry.coincide i j
      return e
    -- impl-end

prove_correct identityEntry by
  loom_solve
  all_goals simp_all [entryFor, coincideValue]
