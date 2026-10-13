import Mathlib
-- imports-end

/-!
Subscripting a documentation placeholder object.

A placeholder object stands in for an absent imported symbol that is unavailable
while building documentation. Indexing such a placeholder with a key (the `obj[key]`
operation) yields a fresh derived placeholder. The derived placeholder is
identified by a display name formed from the parent's display name and the key:
the parent display name, a separating dot, and the key rendered as text.

The key supplied to the subscript may be any object, not only a piece of text
(for example, a type parameter used when indexing a generic). Whatever the key
is, it is first rendered to its textual form, and the derived display name is the
parent display name followed by a dot and that textual form. The operation
always succeeds and yields that derived display name.

We model a key as `PyKey`: `PyKey.str s` is a key that is already text with code
points `s`; `PyKey.other r` is a non-text key whose textual rendering has code
points `r`. The outcome is `Except Unit (List Char)`: `Except.ok d` carries the
derived display name `d`, and `Except.error ()` marks a failure to form a display
name (which arises only when a display name is built from a non-text component).
-/

-- axioms-start
-- No `opaque` callees and no consumed axioms: every operation the subscript uses
-- (rendering the key to text; forming the derived display name) is modeled
-- directly in the `pure` region and validated against the real callees by G-AX.
-- axioms-end

-- pure-start
/-- A subscript key. `str s` is a textual key with code points `s`; `other r` is
a non-textual key whose textual rendering has code points `r`. -/
inductive PyKey where
  | str (s : List Char) : PyKey
  | other (r : List Char) : PyKey
  deriving DecidableEq

/-- The textual rendering of a key. A textual key renders to itself; a non-text
key renders to its carried textual form. -/
def strChars : PyKey → List Char
  | .str s => s
  | .other r => r

/-- Forming a derived display name by joining a parent display name to a key
component with a separating dot. The join requires the component to already be
text: a textual component yields `Except.ok (module ++ '.' :: s)`, while a
non-text component cannot be joined and yields `Except.error ()`. (This models
the unchanged display-name construction callee, an A-reference validated by
G-AX.) -/
def concatName (module : List Char) (name : PyKey) : Except Unit (List Char) :=
  match name with
  | .str s => Except.ok (module ++ '.' :: s)
  | .other _ => Except.error ()
-- pure-end

-- post-conditions-start
/-- Subscripting a placeholder with display name `displayName` by key `key`
yields the derived display name: the parent display name, a separating dot, and
the key's textual rendering. The operation always succeeds for every key. -/
def problem_spec_mockSubscript
    (displayName : List Char) (key : PyKey) (result : Except Unit (List Char)) : Prop :=
  result = Except.ok (displayName ++ '.' :: strChars key)
-- post-conditions-end

-- impl-start
def implementation_mockSubscript
    (displayName : List Char) (key : PyKey) : Except Unit (List Char) := Id.run do
  -- The key is forwarded to the display-name join without being rendered to
  -- text first.
  let name : PyKey := key
  return concatName displayName name
-- impl-end

-- proof-start
-- Gold proof body carried over from Solution.lean (SPEC_GUIDE §1.1). Against this
-- implementation it cannot close: for a non-text key (`PyKey.other r`) the
-- display-name join receives a non-text component and yields `Except.error ()`,
-- while the specification requires `Except.ok (displayName ++ '.' :: r)` — the
-- discriminating clause.
theorem correct_mockSubscript :
    ∀ (displayName : List Char) (key : PyKey),
      problem_spec_mockSubscript displayName key
        (implementation_mockSubscript displayName key) := by
  intro displayName key
  unfold problem_spec_mockSubscript implementation_mockSubscript concatName
  rfl
-- proof-end
