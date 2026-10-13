import Mathlib
-- imports-end

/-!
Rendering a single type-annotation token as a documentation cross-reference.

When a type annotation in an API signature is turned into documentation, each
bare token of the annotation (a name such as `int`, `List`, or `None`) becomes a
clickable cross-reference into the documentation set. Such a reference carries
four pieces of data:

  * the documentation DOMAIN it resolves in (here always the Python domain,
    `"py"`);
  * the reference KIND, which selects what sort of documented entity the token
    names;
  * the TARGET, the name that is looked up — the token text itself;
  * the visible LABEL shown to the reader — again the token text.

Most tokens name a class-like entity, so their reference kind is the class kind
(`"class"`). The single exception is the token `None`: it does not name a class
but the unique `None` object, so its reference kind is the object kind
(`"obj"`). Both `None` and every other token must yield a cross-reference (so a
`None` annotation is just as clickable as any other) — they differ only in which
kind that reference carries.

So for the token `None` the result is the object-kind reference targeting and
labelled `None`; for any other token `t` the result is the class-kind reference
targeting and labelled `t`. The domain, target, and label are determined by the
token alone; only the kind branches on whether the token is `None`.
-/

-- axioms-start
-- No unchanged outside callee is consumed as an axiom. Building the
-- cross-reference for a token is spelled out directly below: the four
-- components (domain, kind, target, label) are computed from the token by
-- pure structural data, so there is no opaque repo callee whose behavior the
-- proof must assume.
-- axioms-end

-- pure-start
/-- A documentation cross-reference for a single annotation token: the domain it
resolves in, the kind of entity it names, the lookup target, and the visible
label. -/
structure TypeRef where
  domain : String
  kind   : String
  target : List Char
  label  : List Char
deriving Repr, DecidableEq
-- pure-end

-- post-conditions-start
/-- The cross-reference is fully pinned to the input token `text`:

  * the domain is always the Python domain `"py"`;
  * the target and the visible label are both exactly the token `text`;
  * the kind is the object kind `"obj"` when the token is `None`, and the class
    kind `"class"` for every other token.

No output component is left free: each of the four components is determined by
`text`, and the kind is forced by whether `text` is the `None` token. -/
def problem_spec_annotationRef (text : List Char) (result : TypeRef) : Prop :=
  result.domain = "py"
    ∧ result.target = text
    ∧ result.label = text
    ∧ result.kind = (if text = "None".toList then "obj" else "class")
-- post-conditions-end

-- impl-start
def implementation_annotationRef (text : List Char) : TypeRef := Id.run do
  let mut kind := "class"
  if text = "None".toList then
    kind := "obj"
  else
    kind := "class"
  return { domain := "py", kind := kind, target := text, label := text }
-- impl-end

-- proof-start
theorem correct_annotationRef :
    ∀ (text : List Char),
      problem_spec_annotationRef text (implementation_annotationRef text) := by
  intro text
  unfold problem_spec_annotationRef implementation_annotationRef
  by_cases h : text = "None".toList <;>
    simp only [h, Id.run, if_pos, pure] <;>
    exact ⟨rfl, rfl, rfl, rfl⟩
-- proof-end
