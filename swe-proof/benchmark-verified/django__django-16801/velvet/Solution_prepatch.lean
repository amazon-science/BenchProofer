import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. Both modeled decisions are pure Boolean functions of
   observations of the field/instance configuration (whether the model is
   abstract, whether each optional companion dimension field is declared,
   whether the value is deferred, whether a file is present, whether the
   companion fields are already populated, and whether the refresh is forced).
   Every such observation is a free `Bool` input, universally quantified, so the
   spec covers every configuration and no callee contract is assumed. The
   reference behaviour of the underlying observations is differential-tested
   against the real code by conformance_check.py (G-CONF); see mapping.md. -/
-- axioms-end

-- pure-start
/- Whether the post-initialization dimension-synchronization handler should be
   registered for a model class.

   Desired behaviour: the handler is attached only when it can ever do useful
   work — i.e. for a concrete (non-abstract) model that actually declares at
   least one companion dimension field (a width field or a height field). For an
   abstract model, or for a model that declares no companion dimension field at
   all, no handler is registered, because such a handler could only ever be a
   no-op. -/
def shouldRegister (isAbstract hasWidthField hasHeightField : Bool) : Bool :=
  !isAbstract && (hasWidthField || hasHeightField)

/- Which companion dimension fields a single synchronization pass writes back to
   the instance. `writeWidth`/`writeHeight` record whether the width/height
   companion field (respectively) is assigned during the pass. -/
structure DimWrites where
  writeWidth : Bool
  writeHeight : Bool
deriving DecidableEq, Inhabited, Repr

/- The effect of one synchronization pass, as the set of companion fields it
   writes.

   A pass writes nothing at all unless it reaches the assignment stage, which
   requires all of: the value is not deferred; either a file is present or the
   pass is forced; and the companion fields are not already populated (unless the
   pass is forced). "Already populated" means every declared companion field
   currently holds a value. When the assignment stage is reached, a companion
   field is written exactly when it is declared: the width field is written iff a
   width field is declared, and likewise for height. Consequently a pass for a
   configuration that declares no companion field writes nothing — there is
   nothing to assign. -/
def dimUpdate
    (deferred force hasFile hasWidthField widthFilled hasHeightField heightFilled : Bool) :
    DimWrites :=
  let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))
  let proceed := !deferred && (hasFile || force) && (!dimFilled || force)
  { writeWidth := hasWidthField && proceed,
    writeHeight := hasHeightField && proceed }
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method registerInitHandler (isAbstract : Bool) (hasWidthField : Bool) (hasHeightField : Bool) return (out : Bool)
  ensures out = shouldRegister isAbstract hasWidthField hasHeightField
  do
    -- impl-start
    -- PRE-PATCH skeleton: the handler is registered for every concrete model,
    -- regardless of whether any companion dimension field is declared.
    let mut doRegister : Bool := false
    if !isAbstract then
      doRegister := true
    else
      doRegister := false
    return doRegister
    -- impl-end

prove_correct registerInitHandler by
  loom_solve <;> simp_all [shouldRegister]

method dimensionWrites
    (deferred : Bool) (force : Bool) (hasFile : Bool) (hasWidthField : Bool)
    (widthFilled : Bool) (hasHeightField : Bool) (heightFilled : Bool)
    return (out : DimWrites)
  ensures out = dimUpdate deferred force hasFile hasWidthField widthFilled hasHeightField heightFilled
  do
    -- impl-start
    -- PRE-PATCH skeleton: an extra leading guard short-circuits the pass when no
    -- companion dimension field is declared. This is observationally redundant
    -- (the per-field assignment guards already suppress every write in that
    -- case), so this skeleton still meets the spec.
    let mut proceed : Bool := true
    if (!hasWidthField && !hasHeightField) then
      proceed := false
    else
      proceed := proceed
    if deferred then
      proceed := false
    else
      proceed := proceed
    if (!hasFile && !force) then
      proceed := false
    else
      proceed := proceed
    let dimFilled := !((hasWidthField && !widthFilled) || (hasHeightField && !heightFilled))
    if (dimFilled && !force) then
      proceed := false
    else
      proceed := proceed
    return { writeWidth := hasWidthField && proceed,
             writeHeight := hasHeightField && proceed }
    -- impl-end

prove_correct dimensionWrites by
  loom_solve <;> simp_all [dimUpdate] <;> grind
