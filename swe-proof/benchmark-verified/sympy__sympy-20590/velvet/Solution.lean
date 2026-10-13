import Velvet.Std
-- imports-end

/- Total correctness: every modeled operation is a straight-line pure
   computation over the closed-layout flag chain and always terminates, so a
   diverging implementation must NOT satisfy this spec. Partial correctness
   would let a non-terminating body discharge the exact-pin postconditions
   vacuously. -/
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The behavior under specification — whether an instance of
   a value type carries an open per-instance namespace, and the consequence for
   binding an undeclared attribute name — is modeled DEEPLY in the `pure` region
   (`allClosedLayout`, `instanceAdmitsNamespace`, `bindUndeclared`). The rule
   relating a type's layout declarations to the presence of an open namespace is
   a property of the host runtime's object model, validated against the real
   interpreter out of band (mapping.md §3, axiom_check.py / G-AX); it is NOT
   axiomatized as a callee. -/
-- axioms-end

-- pure-start
/- The single way binding an undeclared attribute name can be refused: the
   instance carries no open namespace to absorb it, so the binding is rejected
   rather than silently stored. This is the only outcome the desired behavior
   distinguishes from success. -/
inductive AttrError where
  | bindingRefused
  deriving DecidableEq

/- An instance is built from a CHAIN of contributing types (its resolution
   order, with the universal root — which never contributes a namespace —
   excluded). Each entry is a flag: `true` iff that type pins a closed instance
   layout (declares a closed set of attribute slots and so contributes no
   open per-instance namespace of its own); `false` iff it leaves its layout
   open.

   `allClosedLayout` is `true` iff EVERY type in the chain pins a closed layout.
   Front-recursive over the chain so a single unfold is available per step (the
   Velvet fold pattern): the head must pin a closed layout and so must the
   tail. -/
def allClosedLayout : List Bool → Bool
  | []      => true
  | f :: fs => f && allClosedLayout fs

@[grind] lemma allClosedLayout_nil : allClosedLayout [] = true := rfl
@[grind] lemma allClosedLayout_cons (f : Bool) (fs : List Bool) :
    allClosedLayout (f :: fs) = (f && allClosedLayout fs) := rfl
@[grind] lemma allClosedLayout_append (xs ys : List Bool) :
    allClosedLayout (xs ++ ys) = (allClosedLayout xs && allClosedLayout ys) := by
  induction xs with
  | nil => simp [allClosedLayout]
  | cons f fs ih => simp [allClosedLayout, ih, Bool.and_assoc]

/- An instance carries an open per-instance namespace iff AT LEAST ONE type in
   its chain leaves its layout open — equivalently, iff NOT every type pins a
   closed layout. -/
def instanceAdmitsNamespace (chain : List Bool) : Bool :=
  !allClosedLayout chain

/- The outcome of binding an attribute name that none of the contributing types
   pre-declared, as `Except AttrError Bool`:

     * if the instance carries an open namespace (some type leaves its layout
       open) the binding is ABSORBED and succeeds (`ok true`);
     * otherwise — every type in the chain pins a closed layout — there is no
       namespace to hold it, so the binding is REFUSED (`error bindingRefused`).

   This is the deep model of the runtime rule; G-AX validates it against the
   real interpreter (mapping.md §3, A-reference). -/
def bindUndeclared (chain : List Bool) : Except AttrError Bool :=
  if allClosedLayout chain then Except.error AttrError.bindingRefused
  else Except.ok true
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Each type contributing to the value type's chain must pin a closed instance
   layout — declare a closed set of attribute slots and so contribute no
   open per-instance namespace of its own — so that combining it with the other
   contributing types does not re-open the layout of the types that use it. The
   desired behavior requires this flag to be `true`: every contributing type,
   INCLUDING the shared mixin contributor, pins a closed layout. -/
method mixinPinsClosedLayout return (out : Bool)
  ensures out = true
  do
    -- impl-start
    -- The shared contributing type pins a closed instance layout (declares an
    -- empty closed slot set, adding no named slots and no open namespace).
    return true
    -- impl-end

/- Whether an instance of the value type carries an open per-instance
   namespace, as a function of the OTHER contributing types' closed-layout
   flags. `others` is the value type's chain WITHOUT the shared mixin
   contributor (resolution order, most-derived first, universal root excluded);
   the full chain appends the shared contributor's flag, which the desired
   behavior pins to `true` (`mixinPinsClosedLayout`). The result must follow
   the runtime rule on that full chain — in particular, when every other
   contributing type pins a closed layout (the value type's actual shape, whose
   own flags are all `true`), the instance carries NO open namespace. -/
method coreInstanceAdmitsNamespace (others : List Bool) return (out : Bool)
  ensures out = instanceAdmitsNamespace (others ++ [true])
  ensures allClosedLayout others = true → out = false
  do
    -- impl-start
    let trait := true
    let chain : List Bool := others ++ [trait]
    return instanceAdmitsNamespace chain
    -- impl-end

/- The outcome of binding an attribute name the value type did not pre-declare,
   on an instance of the value type, as a function of the OTHER contributing
   types' closed-layout flags (`others`, as above; the full chain appends the
   shared contributor's flag, pinned `true` by the desired behavior). The
   outcome must follow the runtime rule on that full chain — in particular,
   when every other contributing type pins a closed layout (the value type's
   actual shape), the binding is REFUSED with the binding-refused outcome. -/
method coreBindUndeclared (others : List Bool) return (out : Except AttrError Bool)
  ensures out = bindUndeclared (others ++ [true])
  ensures allClosedLayout others = true → out = Except.error AttrError.bindingRefused
  do
    -- impl-start
    let trait := true
    let chain : List Bool := others ++ [trait]
    return bindUndeclared chain
    -- impl-end

prove_correct mixinPinsClosedLayout by
  loom_solve

prove_correct coreInstanceAdmitsNamespace by
  loom_solve
  all_goals simp_all [instanceAdmitsNamespace, allClosedLayout_append, allClosedLayout]

prove_correct coreBindUndeclared by
  loom_solve
  all_goals simp_all [bindUndeclared, allClosedLayout_append, allClosedLayout]
