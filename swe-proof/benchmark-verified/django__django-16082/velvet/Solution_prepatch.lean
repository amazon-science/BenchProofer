import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- No consumed axioms and no deep-model A-reference. The operation under
-- specification is a total function of the two operand numeric kinds; it calls
-- no unchanged repository callee that needs a contract. Its agreement with the
-- real result-kind resolver is checked executably by conformance_check.py
-- (G-CONF), which runs the resolver in its actual (post-change) configuration.
-- axioms-end

-- pure-start
/- The three numeric operand kinds an arithmetic combination can carry, in the
   abstract: an exact integer kind, a floating kind, and a fixed-precision
   decimal kind. (mapping.md §2 gives the bijection from the concrete operand
   field classes onto these kinds.) -/
inductive NumKind where
  | int
  | float
  | dec
  deriving DecidableEq, Inhabited

/- The desired result kind when combining a left operand of kind `l` with a
   right operand of kind `r` under the remainder operation.

   * like-with-like keeps the kind;
   * an integer mixed with a decimal widens to the decimal kind;
   * an integer mixed with a floating value widens to the floating kind;
   * a floating value mixed with a decimal has no common numeric kind
     (`none`), as does any pair this relation does not list.

   This is the abstract behaviour the issue asks for: combining mixed numeric
   kinds under remainder must resolve to the wider kind (e.g. integer with
   decimal resolves to decimal), exactly as the other arithmetic combinations
   already do. It is grounded purely in the two operand kinds, so only an
   implementation that actually performs the resolution can satisfy the
   postcondition. -/
def combinedNumeric : NumKind → NumKind → Option NumKind
  | .int,   .int   => some .int
  | .float, .float => some .float
  | .dec,   .dec   => some .dec
  | .int,   .dec   => some .dec
  | .dec,   .int   => some .dec
  | .int,   .float => some .float
  | .float, .int   => some .float
  | _,      _      => none

/- A single registered combination rule: (left kind, right kind, result kind). -/
abbrev Combinator := NumKind × NumKind × NumKind

/- First-match lookup over a list of registered combination rules: scan from the
   front and return the result of the first rule whose left/right kinds match the
   operands, otherwise `none`. Front-recursive so a single unfold is available
   per loop step (the backward-fold verification pattern). -/
def lookup : List Combinator → NumKind → NumKind → Option NumKind
  | [],                _, _ => none
  | (a, b, c) :: rest, l, r =>
      if l = a ∧ r = b then some c else lookup rest l r

/- The registered combination rules for the remainder operation: like-with-like
   for each numeric kind, plus the mixed integer/decimal and integer/floating
   widenings. First match wins (lowest index has the final say). -/
def modCombinators : List Combinator :=
  [ (NumKind.int,   NumKind.int,   NumKind.int),
    (NumKind.float, NumKind.float, NumKind.float),
    (NumKind.dec,   NumKind.dec,   NumKind.dec),
    (NumKind.int,   NumKind.dec,   NumKind.dec),
    (NumKind.dec,   NumKind.int,   NumKind.dec),
    (NumKind.int,   NumKind.float, NumKind.float),
    (NumKind.float, NumKind.int,   NumKind.float) ]

@[grind] lemma lookup_nil (l r : NumKind) : lookup [] l r = none := rfl

/- Cons unfold reading a rule by its projections (the loop body reads a rule as a
   triple via `.1 / .2.1 / .2.2` rather than by pattern syntax). -/
@[grind] lemma lookup_cons' (p : Combinator) (rest : List Combinator) (l r : NumKind) :
    lookup (p :: rest) l r =
      (if l = p.1 ∧ r = p.2.1 then some p.2.2 else lookup rest l r) := by
  obtain ⟨a, b, c⟩ := p; rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method resolveModType (lhs : NumKind) (rhs : NumKind) return (out : Option NumKind)
  ensures out = combinedNumeric lhs rhs
  do
    -- impl-start
    -- PRE-PATCH skeleton: the remainder operation is registered ONLY for
    -- like-with-like numeric kinds; the mixed integer/decimal and
    -- integer/floating rows are absent from the scanned list. So the scan
    -- returns `none` for mixed numeric operands instead of the widened kind —
    -- exactly the bug. `prove_correct` MUST fail: `out = combinedNumeric lhs rhs`
    -- is violated at e.g. lhs = .int, rhs = .dec (combinedNumeric gives `.dec`,
    -- this scan gives `none`).
    let combs : List Combinator :=
      [ (NumKind.int,   NumKind.int,   NumKind.int),
        (NumKind.float, NumKind.float, NumKind.float),
        (NumKind.dec,   NumKind.dec,   NumKind.dec) ]
    let mut res : Option NumKind := none
    let mut i := combs.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ combs.length
      invariant res = lookup (combs.drop i) lhs rhs
      done_with i = 0
      decreasing i
    do
      let p := combs[i - 1]!
      res := if lhs = p.1 ∧ rhs = p.2.1 then some p.2.2 else res
      i := i - 1
    return res
    -- impl-end

/- The backward-scan step: dropping one fewer rule exposes rule `i-1` on the
   front, so `lookup` peels exactly that rule. This is the single fold goal
   `loom_solve` leaves for the loop body. -/
lemma lookup_drop_step (combs : List Combinator) (i : Nat) (l r : NumKind)
    (hi : 0 < i) (hle : i ≤ combs.length) :
    lookup (combs.drop (i - 1)) l r =
      (if l = (combs[i - 1]!).1 ∧ r = (combs[i - 1]!).2.1 then some (combs[i - 1]!).2.2
       else lookup (combs.drop i) l r) := by
  have hlt : i - 1 < combs.length := by omega
  have hcons : combs.drop (i - 1) = combs[i - 1]! :: combs.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, lookup_cons']

/- Scanning the full rule list reproduces the abstract result-kind relation:
   the first-match lookup over `modCombinators` equals `combinedNumeric`. Closed
   by exhausting the nine operand-kind pairs. -/
@[grind] lemma lookup_modCombinators (l r : NumKind) :
    lookup modCombinators l r = combinedNumeric l r := by
  cases l <;> cases r <;> rfl

prove_correct resolveModType by
  loom_solve
  -- The loop body closes against the (buggy, like-with-like-only) scanned list,
  -- so the proof reaches the final obligation `lookup [int,int,int ; float,…;
  -- dec,…] lhs rhs = combinedNumeric lhs rhs`. That is FALSE — e.g. at
  -- lhs = .int, rhs = .dec the scan yields `none` but `combinedNumeric` yields
  -- `some .dec` — so `prove_correct` cannot close (G-DIFF: the spec sees the bug).
  rw [lookup_drop_step
        [ (NumKind.int,   NumKind.int,   NumKind.int),
          (NumKind.float, NumKind.float, NumKind.float),
          (NumKind.dec,   NumKind.dec,   NumKind.dec) ]
        i lhs rhs (by omega) (by omega)]
  simp_all
