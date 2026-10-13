import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed axioms. The one unchanged callee this slice relies on — the
--  probability-estimation routine of a fitted classifier — is modeled DEEPLY
--  in the `pure` region (`probaMethodOf`) and validated == the real callee by
--  G-AX (an A-reference, mapping.md §3). It carries no module-level `axiom`.)
-- axioms-end

-- pure-start
/- The multiclass mode a classifier is asked to operate in. `ovr` fits one
   binary problem per label (one-vs-rest); `multinomial` fits the full
   cross-entropy / softmax model across all classes. These are the two modes a
   caller can request. -/
inductive MultiClass where
  | ovr
  | multinomial
  deriving DecidableEq, Inhabited

/- The probability-estimation method a fitted classifier applies to turn its
   decision scores into class probabilities. `ovrNormalize` runs the logistic
   function per class and normalizes those across classes (the one-vs-rest
   estimate); `softmax` applies the softmax across the decision scores (the
   multinomial estimate). For a multiclass problem the two yield DIFFERENT
   probabilities, so a probabilistic score (one computed from `predict_proba`)
   depends on which method is used. -/
inductive ProbaMethod where
  | ovrNormalize
  | softmax
  deriving DecidableEq, Inhabited

/- The probability-estimation method a classifier uses is determined by the
   multiclass mode it carries: `ovr` ⇒ the one-vs-rest normalization, anything
   else (here `multinomial`) ⇒ softmax. This is the behavior of the unchanged
   probability routine; it is modeled deeply here and validated == the real
   callee by axiom_check.py (G-AX, an A-reference — mapping.md §3). -/
def probaMethodOf : MultiClass → ProbaMethod
  | .ovr         => .ovrNormalize
  | .multinomial => .softmax
-- pure-end

-- pre-conditions-start
-- (No preconditions: every requested mode is admissible input.)
-- pre-conditions-end

-- post-conditions-start
-- (post-conditions are stated inline on the method below.)
-- post-conditions-end

/- The probability-estimation method that the classifier used to compute a
   probabilistic cross-validation score applies.

   Input: `requested` — the multiclass mode the caller asked the
   cross-validation routine to operate in.

   Guarantee: the probabilistic score is produced by the probability method
   that MATCHES the requested mode — softmax for a multinomial request, the
   one-vs-rest normalization for an ovr request. A multinomial request must NOT
   be scored with the one-vs-rest estimate (and vice-versa); the scoring
   classifier operates in the requested mode rather than in some mode-agnostic
   default. -/
method probabilityMethodForScoring (requested : MultiClass) return (out : ProbaMethod)
  ensures (requested = MultiClass.multinomial → out = ProbaMethod.softmax)
  ensures (requested = MultiClass.ovr → out = ProbaMethod.ovrNormalize)
  do
    -- invariants-start
    -- (no loops in this method.)
    -- invariants-end
    -- impl-start
    -- Pre-image skeleton: the scoring classifier is built without inheriting the
    -- requested mode, so it falls back to the fixed one-vs-rest default — its
    -- probability estimate is the one-vs-rest normalization regardless of what
    -- the caller requested. The frozen spec requires the method to MATCH the
    -- requested mode (softmax for a multinomial request), so prove_correct MUST
    -- fail at `requested = multinomial`.
    let out : ProbaMethod := ProbaMethod.ovrNormalize
    return out
    -- impl-end

prove_correct probabilityMethodForScoring by
  loom_solve
