import Mathlib
-- imports-end

-- axioms-start
-- No UNCHANGED callee is axiomatized. The error-collection constructor used by
-- the modeled behavior (it records a CSS class string and an initial list of
-- messages) is modeled DEEPLY below (`mkErrorList`), so it is an A-reference
-- validated == the real callee by G-AX, not a consumed `_prop` axiom. There is
-- therefore no `opaque` declaration here.
-- axioms-end

-- pure-start
/-- An error collection that knows the CSS class it renders under and the list of
error messages it carries. -/
structure ErrorList where
  messages : List String
  cssClass : String
deriving DecidableEq, Repr

/-- Build an error collection from an initial list of messages and an optional
extra CSS class. With no extra class the collection renders under the base CSS
class `errorlist`; with an extra class `c` it renders under `errorlist c`
(the base class followed by a space and the extra class). -/
def mkErrorList (initlist : List String) (extraClass : Option String) : ErrorList :=
  { messages := initlist,
    cssClass := match extraClass with
                | none   => "errorlist"
                | some c => "errorlist " ++ c }

/-- Append one message to an error collection (the CSS class is unchanged). -/
def ErrorList.append (e : ErrorList) (msg : String) : ErrorList :=
  { e with messages := e.messages ++ [msg] }

/-- The messages the non-form error collection must carry, as a function of the
inputs that drive its production:
* if the data is unbound, processing stops immediately and the collection is empty;
* otherwise, if cross-collection validation reports errors, the collection holds
  exactly those reported messages;
* otherwise, if the management bookkeeping is invalid, the collection holds the
  single management error message;
* otherwise the collection is empty. -/
def expectedMessages (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : List String :=
  if !isBound then []
  else match raised with
       | some errs => errs
       | none => if !mgmtValid then [mgmtError] else []
-- pure-end

-- post-conditions-start
/-- The non-form error collection produced for a form-set always renders under
the CSS class `errorlist nonform`, and carries exactly the messages dictated by
the production path (`expectedMessages`). The non-form CSS class is present
regardless of which production path was taken (empty/unbound, management error,
or cross-collection validation error). -/
def problem_spec_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) (result : ErrorList) : Prop :=
  result.cssClass = "errorlist nonform" ∧
  result.messages = expectedMessages isBound mgmtValid mgmtError raised
-- post-conditions-end

-- impl-start
def implementation_nonFormErrors (isBound mgmtValid : Bool) (mgmtError : String)
    (raised : Option (List String)) : ErrorList := Id.run do
  -- pre-patch: the non-form error collection is built with no extra CSS class,
  -- so it renders under the bare base class rather than the non-form class.
  let mut nonForm := mkErrorList [] none
  if !isBound then
    return nonForm
  if !mgmtValid then
    nonForm := nonForm.append mgmtError
  if let some errs := raised then
    nonForm := mkErrorList errs none
  return nonForm
-- impl-end

-- proof-start
theorem correct_nonFormErrors :
    ∀ (isBound mgmtValid : Bool) (mgmtError : String) (raised : Option (List String)),
      problem_spec_nonFormErrors isBound mgmtValid mgmtError raised
        (implementation_nonFormErrors isBound mgmtValid mgmtError raised) := by
  intro isBound mgmtValid mgmtError raised
  -- carries the gold proof intent; UNCLOSABLE against the pre-patch impl: the
  -- produced collection's CSS class is `errorlist`, not `errorlist nonform`
  -- (G-DIFF: the discriminating clause cannot be discharged).
  refine ⟨?_, ?_⟩ <;> rfl
-- proof-end
