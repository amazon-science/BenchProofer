import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The one unchanged callee this slice relies on — the
   subclass-construction operation that derives a child class from a name and a
   module — is modeled DEEPLY in the `pure` region (`buildSubclass`) and
   validated == the real callee by G-AX (an A-reference, mapping.md §3), so it
   carries no module-level `axiom`. -/
-- axioms-end

-- pure-start
/- The ways subclass construction can fail. A non-textual name has nothing to
   splice into the display name and cannot name a class (`typeError`). A textual
   name that the class machinery refuses — one carrying a NUL character, which
   cannot appear in a class name — fails differently (`valueError`). Success is
   the only other outcome the desired behaviour distinguishes. -/
inductive MockErr where
  | typeError
  | valueError
  deriving DecidableEq

/- A subscription key, in two observable shapes: a value that is already textual
   (`str s`), or a non-textual object that nonetheless carries a textual
   rendering (`obj s`, the rendering `s`). The behaviour distinguishes only
   whether the key was already textual and what its textual rendering is. -/
inductive Key where
  | str (s : String)
  | obj (s : String)
  deriving DecidableEq

/- The textual form of a key: a key that is already textual is unchanged; a
   non-textual object becomes its textual rendering. The result is ALWAYS a
   textual value — that is the whole point of taking the textual form. -/
def textForm : Key → Key
  | .str s => .str s
  | .obj s => .str s

/- A textual name the class machinery refuses: a name carrying a NUL character
   cannot name a class. (No other character is rejected — every other textual
   name, including empty, accented, or whitespace names, is accepted.) -/
def nameRejected (s : String) : Bool := s.contains (Char.ofNat 0)

/- The subclass-construction callee (unchanged by this change; A-reference, deep
   model of the real construction operation — mapping.md §3.1). Given a module
   and a name, it builds a child class whose display name is `module.name`. It
   succeeds only when the name is textual AND admissible as a class name; a
   non-textual name fails (`typeError` — the display name cannot be formed from,
   and the class cannot be named by, a non-textual value), and a textual name the
   class machinery refuses fails too (`valueError`). The value carried on success
   is that display name (the only observed field). -/
def buildSubclass (module : String) (name : Key) : Except MockErr String :=
  match name with
  | .str s => if nameRejected s then Except.error .valueError
              else Except.ok (module ++ "." ++ s)
  | .obj _ => Except.error .typeError

/- The intended result of subscription: construct a subclass named by the
   textual form of the key, under the owning module's display name. Because the
   textual form of any key is textual, construction SUCCEEDS for every key,
   textual or not, whose textual rendering is admissible as a class name — the
   display name is then the module name joined to that rendering. -/
def subscriptSpec (displayName : String) (key : Key) : Except MockErr String :=
  buildSubclass displayName (textForm key)

@[grind] lemma textForm_str (s : String) : textForm (.str s) = .str s := rfl
@[grind] lemma textForm_obj (s : String) : textForm (.obj s) = .str s := rfl
@[grind] lemma subscriptSpec_eq (displayName : String) (key : Key) :
    subscriptSpec displayName key = buildSubclass displayName (textForm key) := rfl
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

method subscriptMock (displayName : String) (key : Key) return (out : Except MockErr String)
  ensures out = subscriptSpec displayName key
  do
    -- impl-start
    -- Take the textual form of the key BEFORE handing it to construction, so
    -- the name passed in is always textual and construction never fails.
    let name := textForm key
    let out := buildSubclass displayName name
    return out
    -- impl-end

prove_correct subscriptMock by
  loom_solve
