import Mathlib
-- imports-end

/-!
Propagating an output-container choice through a composite transformer.

A composite transformer holds an ordered collection of contained
sub-transformers together with a fall-back transformer that handles the columns
not claimed by any of them. Each entry is either an actual estimator (which
carries its own output-container configuration) or one of the two reserved
sentinels meaning "pass the columns through unchanged" or "drop the columns".

Configuring the output container of the composite propagates the chosen
container to every contained estimator, and likewise to the fall-back
transformer whenever that fall-back is itself an estimator (i.e. not one of the
two reserved sentinels). A sentinel carries no configuration and is left as is.

So the result is: every contained sub-transformer with its output container set
to the chosen value (sentinels untouched), paired with the fall-back transformer
with its output container set to the chosen value (again, untouched if it is a
sentinel).
-/

-- axioms-start
-- No unchanged outside callee is consumed by this specification. Applying the
-- output-container choice to one transformer is modeled DEEPLY (the pure helper
-- `setOutput` below: an estimator records the new container, a sentinel is left
-- unchanged), so there is no `opaque`/`axiom` callee contract. The composite's
-- own container choice and the membership/fitted bookkeeping that produces the
-- contained collection are orthogonal to the modeled behavior and enter through
-- the grounded inputs.
-- axioms-end

-- pure-start
/-- A contained transformer entry: either an actual estimator carrying an
identity `id` and its current output-container configuration `output`, or one of
the two reserved sentinels (`passthrough` / `drop`) that carry no configuration.
(Faithful refinement of a Python transformer slot, which is either an estimator
object or one of the two reserved strings.) -/
inductive Transformer where
  | passthrough
  | drop
  | est (id : Nat) (output : String)
deriving DecidableEq, Repr

/-- Apply an output-container choice to one transformer: an estimator records the
new container value; a sentinel carries no configuration and is returned
unchanged. -/
def setOutput (transform : String) (t : Transformer) : Transformer :=
  match t with
  | .est id _ => .est id transform
  | other => other
-- pure-end

-- post-conditions-start
/-- The result pins both components to their inputs under the chosen container
`transform`: the first component is the contained collection with the container
applied to each entry (sentinels unchanged), and the second component is the
fall-back transformer with the container applied (again unchanged if it is a
sentinel). -/
def problem_spec_setOutput
    (transformers : List Transformer) (remainder : Transformer) (transform : String)
    (result : List Transformer × Transformer) : Prop :=
  result.1 = transformers.map (setOutput transform) ∧
  result.2 = setOutput transform remainder
-- post-conditions-end

-- impl-start
def implementation_setOutput
    (transformers : List Transformer) (remainder : Transformer) (transform : String) :
    List Transformer × Transformer := Id.run do
  let mut outTransformers : List Transformer := []
  for trans in transformers do
    outTransformers := outTransformers ++ [setOutput transform trans]
  -- Pre-patch bug: the fall-back transformer is returned unconfigured; the
  -- chosen output container is never propagated to it.
  let outRemainder := remainder
  return (outTransformers, outRemainder)
-- impl-end

-- proof-start
theorem correct_setOutput :
    ∀ (transformers : List Transformer) (remainder : Transformer) (transform : String),
      problem_spec_setOutput transformers remainder transform
        (implementation_setOutput transformers remainder transform) := by
  sorry   -- LEFT FOR THE PROOF AGENT — construction agent does NOT close this
-- proof-end
