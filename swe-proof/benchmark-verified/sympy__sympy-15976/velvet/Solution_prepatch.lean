import Velvet.Std
-- imports-end

-- Total-correctness semantics: the node-assembly routine must COMPLETE (the
-- real routine is straight-line code — a match over which scripts are present
-- plus one attribute write — that always terminates), so the spec must also
-- rule out diverging implementations: under partial correctness a
-- non-terminating body would vacuously satisfy every ensures.
set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No axiomatized callees and no deep-model references. The decomposition of a
--  variable's printed name into its base name plus its lists of subscript and
--  superscript pieces, and the rendering of each such list into a single
--  presentation node, are unchanged upstream infrastructure: they are supplied
--  to this routine as the inputs `name`, `subs`, and `sups`. The only behavior
--  modeled here is the per-node decision of how those pieces are assembled into
--  the single node that represents the variable, which is modeled deeply in the
--  `pure` region. There is no `axiom` declaration. See mapping.md / refinement.md.)
-- axioms-end

-- pure-start
/- A presentation-markup node. Either a text node carrying a string value, or an
   element node carrying its tag name, a flag recording whether it bears the
   bold styling attribute, and its ordered children. Only the observables the
   acceptance tests inspect — the top element's tag, its bold flag, and its
   child structure — are represented. -/
inductive Node where
  | text (value : List Char)
  | elem (tag : List Char) (bold : Bool) (children : List Node)
  deriving Inhabited

/- The tag (node name) of a node; the text-node sentinel for text nodes. -/
def Node.tag : Node → List Char
  | .text _      => "#text".toList
  | .elem t _ _  => t

/- Whether a node carries the bold styling attribute (false for a text node). -/
def Node.isBold : Node → Bool
  | .text _      => false
  | .elem _ b _  => b

/- The identifier element wrapping a base name: an `mi` element whose single
   child is the name text. This is how the base name is presented (unchanged
   infrastructure, spelled out here so the assembled node is fully grounded in
   the inputs). -/
def mkMi (name : List Char) : Node :=
  .elem "mi".toList false [Node.text name]

/- Apply the bold styling to a node when requested: set the bold flag on the
   element; requesting no styling leaves the node unchanged. Applied to whichever
   node ends up representing the variable. -/
def setBold : Node → Bool → Node
  | .text v,        _ => .text v
  | .elem t b0 ch,  b => .elem t (b0 || b) ch

/- Assemble the single node that represents a variable, given its base name, its
   subscript node (present iff the variable has subscripts), its superscript node
   (present iff the variable has superscripts), and whether bold styling applies.

   The node that represents the variable is determined directly by which scripts
   are present:
     * no scripts          → the bare base-name identifier;
     * subscripts only      → a subscript container of the base name and the
                              subscript node;
     * superscripts only    → a superscript container of the base name and the
                              superscript node;
     * both                 → a sub-and-superscript container of the base name,
                              the subscript node, then the superscript node.
   Bold styling, when requested, is applied to that representing node itself. -/
def buildSymbol (name : List Char) (subs sups : Option Node) (bold : Bool) : Node :=
  let mname := mkMi name
  let core : Node :=
    match sups, subs with
    | none,     none     => mname
    | none,     some sub => .elem "msub".toList false [mname, sub]
    | some sup, none     => .elem "msup".toList false [mname, sup]
    | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
  setBold core bold

@[simp] lemma setBold_tag (n : Node) (b : Bool) : (setBold n b).tag = n.tag := by
  cases n <;> rfl

/- Applying bold styling to an element node sets its bold flag. (The representing
   node is always an element, so this is the only case the postcondition uses.) -/
@[simp] lemma setBold_elem_isBold (t : List Char) (b0 : Bool) (ch : List Node) :
    (setBold (.elem t b0 ch) true).isBold = true := by
  simp [setBold, Node.isBold]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Build the single presentation node that represents a printed variable.

   `name` is the variable's base name; `subs` is the subscript node (present iff
   the variable carries subscripts) and `sups` the superscript node (present iff
   it carries superscripts), each already rendered by unchanged infrastructure;
   `bold` requests bold styling. All four are read-only (none is `mut`): the
   routine consults them and produces a fresh node (directive 5).

   The desired behavior: the node the routine returns is the script container
   itself when the variable has scripts — a subscript container when it has only
   subscripts, a superscript container when it has only superscripts, and a
   sub-and-superscript container when it has both; a variable with no scripts is
   presented as the bare base-name identifier. Bold styling applies to that
   returned node. -/
method buildSymbolNode (name : List Char) (subs : Option Node) (sups : Option Node) (bold : Bool) return (out : Node)
  ensures out = buildSymbol name subs sups bold
  ensures (subs = none ∧ sups = none) → out.tag = "mi".toList
  ensures (subs ≠ none ∧ sups = none) → out.tag = "msub".toList
  ensures (subs = none ∧ sups ≠ none) → out.tag = "msup".toList
  ensures (subs ≠ none ∧ sups ≠ none) → out.tag = "msubsup".toList
  ensures bold = true → out.isBold = true
  do
    -- impl-start
    -- Pre-image skeleton: the representing node is created as a base identifier
    -- element up front (carrying the bold flag), and the chosen script container
    -- — or the bare name text when there are no scripts — is placed INSIDE it as
    -- a child. So when the variable has scripts the returned node is an
    -- identifier element wrapping the script container, whose top tag is `mi`.
    -- The frozen spec requires the script container itself to be the returned
    -- node, so prove_correct MUST fail on the scripted cases.
    let mname : Node := .elem "mi".toList false [Node.text name]
    let child : Node :=
      match sups, subs with
      | none,     none     => Node.text name
      | none,     some sub => .elem "msub".toList false [mname, sub]
      | some sup, none     => .elem "msup".toList false [mname, sup]
      | some sup, some sub => .elem "msubsup".toList false [mname, sub, sup]
    let x : Node := .elem "mi".toList bold [child]
    return x
    -- impl-end

prove_correct buildSymbolNode by
  loom_solve <;>
    cases sups <;> cases subs <;>
      simp_all [buildSymbol, mkMi, setBold, Node.tag, Node.isBold]
