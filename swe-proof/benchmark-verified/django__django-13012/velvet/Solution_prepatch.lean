import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms and no deep-model reference to a library callee. The single
   unchanged step this operation delegates to — asking the wrapped inner
   expression for the columns it contributes to a grouping clause, in a requested
   grouping context — is modeled as a FREE input of the method (`innerCols`; and
   `innerColsDefaultContext` for the variant in which the context is not
   forwarded). The behaviour this bundle pins holds for EVERY value of those free
   inputs, so they are owed no contract: the spec is strictly weaker than any
   concrete implementation of that delegated step (directive 7). The behaviour
   actually pinned — that a transparent wrapping expression contributes exactly
   the columns of the expression it wraps, never standing in for them — is stated
   directly in the postcondition. There is no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- An opaque identity for an expression that may appear as a column of a grouping
   clause. Only identity matters here (whether two such columns are the same
   object); nothing about the internal content is constrained, because this
   operation neither inspects nor constructs grouping columns — it only decides
   WHICH columns a wrapping expression contributes. -/
structure GroupCol where
  ref : Nat
  deriving DecidableEq, Inhabited
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- The columns a wrapping expression contributes to a grouping clause. The
   delegated observation is read-only: `innerCols` is the list of columns the
   wrapped inner expression contributes for the requested grouping context, and
   `innerColsDefaultContext` is what it contributes when that context is not
   forwarded; `innerHasAggregate` flags whether the inner expression aggregates;
   `selfCol` is the wrapping expression's own identity. A wrapping expression is
   transparent for grouping: it provides extra context to the inner expression
   but is not itself a groupable column. Desired behaviour: the wrapping
   expression contributes EXACTLY the columns the wrapped inner expression
   contributes for the SAME grouping context — it never substitutes its own
   identity for them, regardless of whether the inner expression aggregates. -/
method groupingColumns (selfCol : GroupCol) (innerHasAggregate : Bool)
    (innerCols : List GroupCol) (innerColsDefaultContext : List GroupCol)
    return (out : List GroupCol)
  ensures out = innerCols
  do
    -- impl-start
    -- Pre-image skeleton: the generic grouping rule for an expression with no
    -- dedicated handling. A non-aggregating expression stands in for itself as a
    -- single grouping column; an aggregating one is replaced by the columns its
    -- sources contribute, queried WITHOUT forwarding the requested grouping
    -- context. The frozen spec requires the inner expression's columns for the
    -- SAME context, so prove_correct MUST fail.
    let result : List GroupCol :=
      if innerHasAggregate then innerColsDefaultContext
      else [selfCol]
    return result
    -- impl-end

prove_correct groupingColumns by
  loom_solve
