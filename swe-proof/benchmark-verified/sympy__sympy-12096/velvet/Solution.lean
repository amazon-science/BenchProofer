import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- An opaque symbolic term — one argument carried into a numerical evaluation.
   Its internal structure is irrelevant here; only that each argument can be
   numerically evaluated to a requested working precision matters.
   Provenance + executable soundness check: mapping.md / axiom_check.py (G-AX). -/
axiom Term : Type

/- A canonical term value, so an out-of-range probe of an argument list has a
   harmless default. An UNCHANGED constructed value; left fully opaque (the
   weakest sufficient contract is none, directive 7). Provenance + soundness:
   mapping.md / axiom_check.py (G-AX). -/
axiom termDefault : Term

/- Numerically evaluate a single argument to a requested working precision. An
   UNCHANGED per-argument numerical evaluator; total (every argument has a
   numeric evaluation at any precision) and left fully opaque — the spec needs
   only that the SAME evaluator is applied to each argument, never any
   equational fact about the value it returns. Provenance + executable soundness
   check: mapping.md §3.2 / axiom_check.py (G-AX). -/
axiom numEval : Term → Nat → Term
-- axioms-end

-- pure-start
/- A term value is always available, so an out-of-range probe has a harmless
   default; derived from `termDefault` rather than postulated. -/
noncomputable instance : Inhabited Term := ⟨termDefault⟩

/- Numerically evaluate a whole argument sequence to a requested precision:
   apply the per-argument evaluation to each element, order preserved. This is
   the per-element rule the argument-sequence evaluation applies before the
   function's numerical implementation is invoked. Front-recursive so a single
   unfold is available per loop step (the fold pattern, plan §5.4). -/
noncomputable def numEvalSeq (prec : Nat) : List Term → List Term
  | []         => []
  | a :: rest  => numEval a prec :: numEvalSeq prec rest

@[grind] lemma numEvalSeq_nil (prec : Nat) : numEvalSeq prec [] = [] := rfl
@[grind] lemma numEvalSeq_cons (prec : Nat) (a : Term) (rest : List Term) :
    numEvalSeq prec (a :: rest) = numEval a prec :: numEvalSeq prec rest := rfl

/- Evaluating an argument sequence preserves its length and order: the result
   has exactly one evaluated element per input argument. -/
@[grind] lemma numEvalSeq_length (prec : Nat) (args : List Term) :
    (numEvalSeq prec args).length = args.length := by
  induction args with
  | nil => rfl
  | cons a rest ih => simp [numEvalSeq_cons, ih]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Numerically evaluate, to the requested working precision, the sequence of
   arguments that will be supplied to a function's numerical implementation.

   `prec` is the read-only target precision; `args` is the read-only sequence of
   arguments. Desired behaviour: every argument is itself numerically evaluated
   to the target precision, in order — so each element of the result is the
   precision-`prec` numeric evaluation of the corresponding argument, and the
   result has the same length and order as the input. -/
noncomputable section
method evaluateArgs (prec : Nat) (args : List Term) return (out : List Term)
  ensures out = numEvalSeq prec args
  ensures out.length = args.length
  do
    -- impl-start
    let mut result : List Term := []
    let mut i := args.length
    while i > 0
      invariant 0 ≤ i ∧ i ≤ args.length
      invariant result = numEvalSeq prec (args.drop i)
      done_with i = 0
      decreasing i
    do
      let a := args[i - 1]!
      result := numEval a prec :: result
      i := i - 1
    return result
    -- impl-end
end

/- The backward-fold step: dropping one fewer element exposes the element at
   `i-1` on the front, so `numEvalSeq` peels one `numEval`. This is the single
   goal `loom_solve` leaves for the loop body. -/
lemma numEvalSeq_drop_step (prec : Nat) (args : List Term) (i : Nat)
    (hi : 0 < i) (hle : i ≤ args.length) :
    numEvalSeq prec (args.drop (i - 1))
      = numEval args[i - 1]! prec :: numEvalSeq prec (args.drop i) := by
  have hlt : i - 1 < args.length := by omega
  have hcons : args.drop (i - 1) = args[i - 1]! :: args.drop i := by
    have h := List.drop_eq_getElem_cons hlt
    rw [List.getElem!_eq_getElem?_getD, List.getElem?_eq_getElem hlt, Option.getD_some]
    have hsucc : i - 1 + 1 = i := by omega
    rw [h, hsucc]
  rw [hcons, numEvalSeq_cons]

prove_correct evaluateArgs by
  loom_solve
  rw [numEvalSeq_drop_step prec args i (by omega) (by omega)]
  simp_all
