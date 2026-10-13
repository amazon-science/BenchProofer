import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees. The component-wise version ordering is modeled
--  DEEPLY by `verGt` in the `pure` region — it is the operation under spec, so
--  it is spelled out, NOT hidden behind an axiom (SPEC_GUIDE directive 7). The
--  deep model's equality to the real numeric version comparator is validated by
--  axiom_check.py (G-AX) as an A-reference, on the numeric-version domain the
--  `require` clause pins. Nothing is consumed as an axiom.)
-- axioms-end

-- pure-start
/- A version string in the modeled domain: a dotted sequence of decimal
   components. `verGt` is exact only on this domain; the `require` clause below
   pins it, and the G-CONF / G-AX fuzzers stay inside it. -/

/- The numeric value of one decimal digit. -/
def digitVal (c : Char) : Nat := c.toNat - '0'.toNat

/- The numeric value of one dotted component (a run of decimal digits), read
   most-significant first. Leading zeros are absorbed (value-preserving), which
   is exactly how the numeric comparator treats them. -/
def parseComp (cs : List Char) : Nat :=
  cs.foldl (fun acc c => acc * 10 + digitVal c) 0

/- Split a version string into its dotted components, front-recursively so a
   single unfold is available per step. Always yields at least one component. -/
def splitDots : List Char → List (List Char)
  | []      => [[]]
  | c :: cs =>
    let rest := splitDots cs
    if c = '.' then [] :: rest
    else (c :: rest.headD []) :: rest.tail

/- One component is well formed iff it is a non-empty run of decimal digits. -/
def compOk (cs : List Char) : Bool := cs ≠ [] && cs.all Char.isDigit

/- A version string is in the modeled (numeric) domain iff every dotted
   component is a non-empty digit run. -/
def numericVer (s : List Char) : Bool := (splitDots s).all compOk

/- Strict numeric ordering of two component lists, most-significant first.
   When one list is exhausted the remaining components of the other are compared
   against an implicit zero — so trailing-zero components do not change the
   order (`[1,0] = [1,0,0]`), matching the numeric version comparator. -/
def relGt : List Nat → List Nat → Bool
  | [],        []        => false
  | [],        (y :: ys) => if 0 < y then false else relGt [] ys
  | (x :: xs), []        => if x > 0 then true else relGt xs []
  | (x :: xs), (y :: ys) =>
    if x > y then true else if x < y then false else relGt xs ys

/- The component-wise numeric "strictly greater than" on version strings: parse
   each into its component list and compare numerically. This is the desired
   ordering the issue asks for — `verGt "0.10" "0.6" = true` even though the
   purely textual ordering disagrees. -/
def verGt (a b : List Char) : Bool :=
  relGt ((splitDots a).map parseComp) ((splitDots b).map parseComp)

/- A loaded software component carrying a version requirement:
   `required`  — the minimum version the project demands;
   `present`   — the version actually available (meaningful only when present
                 and known);
   `isPresent` — whether the component is available at all;
   `isKnown`   — whether the available version is determinate. -/
structure Requirement where
  required  : List Char
  present   : List Char
  isPresent : Bool
  isKnown   : Bool
  deriving Inhabited

/- A single requirement is UNMET iff the component is present and either its
   version is indeterminate, or its available version is strictly below the
   demanded minimum under the numeric ordering. An absent component imposes no
   obligation here (it is reported elsewhere, not failed). -/
def unmet (r : Requirement) : Bool :=
  if !r.isPresent then false
  else if !r.isKnown then true
  else verGt r.required r.present

/- Whether ANY requirement in the list is unmet — the disjunction of the
   per-requirement test. Front-recursive so a single unfold is available per
   loop step (the backward-fold pattern, plan §5.4). -/
def anyUnmet : List Requirement → Bool
  | []      => false
  | r :: rs => unmet r || anyUnmet rs

@[grind] lemma anyUnmet_nil : anyUnmet [] = false := rfl
@[grind] lemma anyUnmet_cons (r : Requirement) (rs : List Requirement) :
    anyUnmet (r :: rs) = (unmet r || anyUnmet rs) := rfl

/- A requirement is in the modeled domain iff its demanded version is numeric,
   and (when present with a determinate version) its available version is too. -/
def reqWellFormed (r : Requirement) : Bool :=
  numericVer r.required && (!(r.isPresent && r.isKnown) || numericVer r.present)
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The version-requirement scan: returns whether at least one loaded component
   fails its minimum-version requirement (the signal a caller turns into an
   abort). It folds the per-requirement test `unmet` over the requested list.
   `reqs` is read-only (not `mut`); the scan mutates nothing it is handed
   (directive 5). The `require` pins the modeled numeric-version domain on which
   the component-wise ordering is exact (mapping.md §3.1). -/
method anyRequirementUnmet (reqs : List Requirement) return (raised : Bool)
  require reqs.all reqWellFormed = true
  ensures raised = anyUnmet reqs
  do
    -- impl-start
    let mut acc : Bool := false
    let mut i := reqs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ reqs.length
      invariant acc = anyUnmet (reqs.drop i)
      done_with i = 0
      decreasing i
    do
      let r := reqs[i - 1]!
      acc := unmet r || acc
      i := i - 1
    return acc
    -- impl-end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `anyUnmet` peels one disjunct. This is the single goal
   `loom_solve` leaves for the loop body. -/
lemma anyUnmet_drop_step (reqs : List Requirement) (i : Nat)
    (hi : 0 < i) (hle : i ≤ reqs.length) :
    anyUnmet (reqs.drop (i - 1)) = (unmet reqs[i - 1]! || anyUnmet (reqs.drop i)) := by
  have hlt : i - 1 < reqs.length := by omega
  have hcons : reqs.drop (i - 1) = reqs[i - 1]! :: reqs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, anyUnmet_cons]

prove_correct anyRequirementUnmet by
  loom_solve
  rw [anyUnmet_drop_step reqs i (by omega) (by omega)]
  simp_all
