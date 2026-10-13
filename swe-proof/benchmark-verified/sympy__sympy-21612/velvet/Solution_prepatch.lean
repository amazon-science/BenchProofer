import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- The structural classification of the inner expression sitting underneath a
   denominator slot. When a quotient is rendered to its textual form, each
   denominator slot holds some inner expression; that inner expression has one of
   three shapes:

     • `product` — it is a product of two or more factors;
     • `power`   — it is itself a power (an exponentiation);
     • `simple`  — anything else (a single atom, a number, …).

   This is an OBSERVATION of an unchanged sub-object, not a computed value: the
   renderer already knows, for any sub-expression, both its rendered text and its
   top-level shape. Provenance + the executable soundness check that these
   observations match reality: mapping.md §3 / axiom_check.py (G-AX). -/
inductive DenomShape where
  | product
  | power
  | simple
deriving DecidableEq, Inhabited, Repr

/- One slot of the rendered denominator, described by the observations the
   bracketing decision needs:
     • `rendered`     — the already-rendered text of the slot's inner expression
                        (the result of the renderer's standard sub-rendering, an
                        unchanged callee taken here as a given value);
     • `shape`        — the inner expression's top-level shape (above);
     • `components`   — the number of top-level components of the inner
                        expression (e.g. the factor count of a product);
     • `isReciprocal` — whether this slot arose as the reciprocal of its inner
                        expression. Only reciprocal slots are ever considered for
                        protective brackets; the other denominator slots are
                        assembled from their text unchanged.
     • `innerKey`     — an identity code for the slot's inner expression: two
                        slots carry the SAME `innerKey` exactly when they hold
                        equal inner expressions. This is what lets a bracket
                        request be located by the expression it names rather than
                        by the position it was raised from. -/
structure DenomFactor where
  rendered     : List Char
  shape        : DenomShape
  components   : Nat
  isReciprocal : Bool
  innerKey     : Nat
deriving Inhabited
-- axioms-end

-- pure-start
/- A shape is *compound* when the inner expression is built from sub-parts that
   could be torn apart by a surrounding division — a product or a power. A simple
   atom is never compound. -/
def shapeIsCompound : DenomShape → Bool
  | DenomShape.product => true
  | DenomShape.power   => true
  | DenomShape.simple  => false

/- Whether a denominator slot raises a request for protective brackets. A
   reciprocal slot whose inner expression is COMPOUND (a product or a power) and
   has MORE THAN ONE top-level component raises one; otherwise the surrounding
   division would re-associate across the inner operator and change the meaning
   (the missing-brackets defect the issue describes: a denominator that is itself
   a fraction/quotient prints without the brackets it needs). A reciprocal of a
   single-component or simple inner expression, and any non-reciprocal slot,
   raises none. -/
def needsBrackets (f : DenomFactor) : Bool :=
  f.isReciprocal && (f.components != 1) && shapeIsCompound f.shape

/- Wrap one piece of text in a single bracket pair. -/
def wrapText (t : List Char) : List Char := "(".toList ++ t ++ ")".toList

/- The position of the FIRST denominator slot holding the given inner
   expression. A bracket request names an inner expression, and it is satisfied
   at the earliest slot carrying that expression — so requests raised by slots
   holding equal inner expressions all resolve to the same, earliest position.
   Past the end (no slot holds it) when there is no such slot. -/
def firstSlotWithKey (k : Nat) : List DenomFactor → Nat
  | []      => 0
  | f :: fs => if f.innerKey == k then 0 else 1 + firstSlotWithKey k fs

/- Wrap the text at one position in a bracket pair, leaving every other position
   alone. A position past the end wraps nothing. -/
def wrapAt : List (List Char) → Nat → List (List Char)
  | [],      _     => []
  | t :: ts, 0     => wrapText t :: ts
  | t :: ts, n + 1 => t :: wrapAt ts n

/- The positions the bracket requests resolve to, in slot order: walk the slots
   and, for each one that raises a request, record the position its inner
   expression is found at (`firstSlotWithKey` over the whole slot list `all`).
   One entry per raising slot, so several slots holding the same inner expression
   contribute several entries all naming the same position. -/
def bracketTargets (all : List DenomFactor) : List DenomFactor → List Nat
  | []      => []
  | f :: fs =>
      if needsBrackets f then firstSlotWithKey f.innerKey all :: bracketTargets all fs
      else bracketTargets all fs

/- Satisfy the bracket requests in order, each one wrapping the text at the
   position it named. Requests are applied one after another to the text produced
   so far, so two requests naming the same position wrap that text twice. -/
def applyWraps : List (List Char) → List Nat → List (List Char)
  | texts, []      => texts
  | texts, k :: ks => applyWraps (wrapAt texts k) ks

/- The denominator slots' texts before any bracket request is satisfied. -/
def slotTexts (slots : List DenomFactor) : List (List Char) :=
  slots.map (fun f => f.rendered)

/- The rendered text of every denominator slot: start from the slots' own texts
   and satisfy each bracket request at the position it names. -/
def renderDenomFactors (slots : List DenomFactor) : List (List Char) :=
  applyWraps (slotTexts slots) (bracketTargets slots slots)

@[grind] lemma applyWraps_nil (texts : List (List Char)) : applyWraps texts [] = texts := rfl
@[grind] lemma applyWraps_cons (texts : List (List Char)) (k : Nat) (ks : List Nat) :
    applyWraps texts (k :: ks) = applyWraps (wrapAt texts k) ks := rfl

/- Satisfying `ks` then `js` is satisfying their concatenation. -/
lemma applyWraps_append (texts : List (List Char)) (ks js : List Nat) :
    applyWraps texts (ks ++ js) = applyWraps (applyWraps texts ks) js := by
  induction ks generalizing texts with
  | nil => rfl
  | cons k ks ih => simp [applyWraps_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Render every denominator slot of a quotient, satisfying the protective-bracket
   requests raised by its reciprocal slots. `slots` is read-only (not `mut`); the
   step builds a fresh result list and mutates no input (directive 5).

   Desired behaviour: the result is the slots' rendered texts with each bracket
   request satisfied at the position its inner expression is found at — a request
   raised by a reciprocal of a compound inner expression, a reciprocal of a
   simple or single-component inner expression raising none. The defect this pins
   out is a reciprocal whose inner expression is itself a power (e.g. `1/y`)
   being rendered WITHOUT the brackets that a division around it requires, so the
   division re-associates and the printed expression means something else. -/
method bracketDenomFactors (slots : List DenomFactor) return (out : List (List Char))
  ensures out = renderDenomFactors slots
  do
    -- impl-start
    -- Pre-image skeleton: a bracket request is raised only by a slot whose inner
    -- expression is a `product` — a slot whose inner expression is a `power`
    -- raises none. So a reciprocal whose inner expression is itself a power is
    -- rendered without its protective brackets. The frozen spec requires
    -- `renderDenomFactors`, whose `needsBrackets` treats a `power` inner as
    -- compound too, so prove_correct MUST fail.
    let texts : List (List Char) := slotTexts slots
    let targets : List Nat :=
      (slots.filter (fun f =>
          f.isReciprocal && (f.components != 1) && (f.shape == DenomShape.product))).map
        (fun f => firstSlotWithKey f.innerKey slots)
    let mut result : List (List Char) := texts
    let mut k : Nat := 0
    while k < targets.length
      invariant k ≤ targets.length
      invariant result = applyWraps texts (targets.take k)
      done_with k = targets.length
      decreasing targets.length - k
    do
      result := wrapAt result targets[k]!
      k := k + 1
    return result
    -- impl-end

/- The forward step: taking one more bracket request appends it at the end, so
   satisfying the longer prefix is satisfying the shorter one and then wrapping
   at the new request's position. This is the single goal `loom_solve` leaves for
   the loop body. -/
lemma applyWraps_take_step (texts : List (List Char)) (ks : List Nat) (k : Nat)
    (hk : k < ks.length) :
    applyWraps texts (ks.take (k + 1)) = wrapAt (applyWraps texts (ks.take k)) ks[k]! := by
  have h : ks.take (k + 1) = ks.take k ++ [ks[k]!] := by
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hk, Option.getD_some]
    exact List.take_succ_eq_append_getElem hk
  rw [h, applyWraps_append]
  rfl

prove_correct bracketDenomFactors by
  loom_solve
  · rw [applyWraps_take_step (slotTexts slots)
      ((slots.filter (fun f =>
          f.isReciprocal && (f.components != 1) && (f.shape == DenomShape.product))).map
        (fun f => firstSlotWithKey f.innerKey slots)) k (by omega)]
    simp_all
  · simp_all [renderDenomFactors]
