import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axioms: this operation selects which field-building callback a form
--  should use, from facts already read off the form's configuration and its
--  ancestry. There is no unchanged callee whose contract the proof consumes.)
-- axioms-end

-- pure-start
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Choose the field-building callback for a model-backed form.

   A callback is an opaque function identified here by a tag (`some n`), with
   `none` meaning "no callback". A form has three callback sources that are
   observable when its fields are built:

   * `configCallback`  — the callback the form's OWN configuration resolves to
                         (its configuration block directly, or one inherited
                         through that block's ancestry); already resolved here;
   * `declaredCallback` — what, if anything, is named directly on the form class
                         body. The outer `Option` is presence (`none` = nothing
                         named there), the inner is the named value (`some none`
                         = explicitly "no callback" named on the body);
   * `inheritedCallback` — the callback a parent form offers as a default.

   The desired behavior is that the callback the form is built with is exactly
   the one its own configuration resolves to (`configCallback`), independently
   of what is named on the class body or offered by a parent. All three are
   read-only inputs (no `mut`): the result is a pure selection. -/
method selectFieldCallback
    (configCallback : Option Nat)
    (declaredCallback : Option (Option Nat))
    (inheritedCallback : Option Nat)
    return (out : Option Nat)
  ensures out = configCallback
  do
    -- impl-start
    return configCallback
    -- impl-end

prove_correct selectFieldCallback by
  loom_solve
