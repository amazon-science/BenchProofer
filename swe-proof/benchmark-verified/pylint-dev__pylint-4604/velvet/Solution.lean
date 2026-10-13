import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
-- (No consumed callee contracts. The walk's only library call is the unchanged
--  structural collection of every bare reference inside a sub-expression's
--  subtree; that is modeled DEEPLY below as `collectNames` and validated
--  == the real structural traversal by axiom_check.py (G-AX, A-reference). The
--  behavior under specification — the whole walk, `storedNames` — is itself
--  modeled deeply as the do block, so it is never axiomatized.)
-- axioms-end

-- pure-start
/- A node of an annotation expression that is PRESENT — an actual expression that
   can be inspected and traversed — carrying only the structure the walk
   observes:
     * `.name`      — a bare reference (exposes the referenced identifier);
     * `.attribute` — an attribute access taken on a sub-expression (exposes
                      that sub-expression — the thing to the left of the dot);
     * `.subscript` — an indexing form (exposes the indexed expression and the
                      index expression);
     * `.other`     — any other expression shape, exposing the immediate
                      sub-expressions it is built from (in source order). A
                      compound shape such as a grouping of several expressions
                      still CONTAINS references, so its parts are carried
                      rather than discarded; a leaf shape has no parts. -/
inductive Node where
  | name (n : String)
  | attribute (expr : Node)
  | subscript (value : Node) (index : Node)
  | other (parts : List Node)

/- What occupies ONE annotation position, which is what the routine is handed:
   either an expression is present there, or the annotation is ABSENT — the
   position holds no expression at all. Absent positions genuinely arrive here:
   the surrounding walk hands over the annotation of each parameter position one
   at a time without filtering, and a position whose type is not spelled out
   individually yields nothing.

   An absent annotation is NOT an expression that merely happens to hold no
   references. There is no expression there, so NONE of the observations `Node`
   exposes are available on it: its shape cannot be examined and the references
   inside it cannot be collected, because there is no subtree to walk. Only a
   present expression supports those observations. Keeping the two apart is what
   makes "the routine collected references out of this annotation" a statement
   with a truth value. -/
abbrev Annotation := Option Node

/- Every bare reference occurring anywhere inside a PRESENT expression, in the
   order a left-to-right pre-order traversal meets them: a reference yields
   itself, an attribute access yields the references of the expression it is
   taken on, an indexing form yields the references of the indexed expression
   followed by those of the index, and any other shape yields the references of
   its parts in order. The traversal descends through EVERY shape — a reference
   nested inside a compound shape is still met.

   This traversal is an operation ON AN EXPRESSION: it is available exactly when
   there is an expression to walk, and so it is not defined on an absent
   annotation. -/
mutual
def collectNames : Node → List String
  | .name n        => [n]
  | .attribute e   => collectNames e
  | .subscript v i => collectNames v ++ collectNames i
  | .other ps      => collectNamesOf ps
/- The references of a list of expressions, concatenated in order. -/
def collectNamesOf : List Node → List String
  | []      => []
  | p :: ps => collectNames p ++ collectNamesOf ps
end

/- Whether an indexed expression is headed by an attribute access taken directly
   on the standard typing namespace (a `typing.<x>[…]` form). Such a form is
   accounted for by the namespace reference alone. -/
def isTypingHead : Node → Bool
  | .attribute (.name m) => m = "typing"
  | _                    => false

/- The references a PRESENT annotation expression contributes to the recorded
   set:

     * a bare reference contributes itself;
     * an attribute access contributes whatever its sub-expression contributes —
       i.e. the access reaches through to the expression it is taken on, so a
       dotted reference is credited to the name it is rooted at;
     * an indexing form headed by the typing namespace contributes only that
       namespace; any other indexing form contributes every reference inside it,
       however deeply nested — the whole indexing form is traversed;
     * any other expression shape contributes nothing, EVEN IF it has parts that
       contain references: the walk stops at such a shape instead of descending.

   Note the asymmetry between the last two clauses, which is deliberate: a
   compound shape reached as an INDEX (or as the indexed expression) of an
   indexing form does have its references collected, because the traversal
   covers the whole indexing form; the same shape reached as the WHOLE
   annotation contributes nothing. -/
def storedNamesOf : Node → List String
  | .name n        => [n]
  | .attribute e   => storedNamesOf e
  | .subscript v i => if isTypingHead v then ["typing"] else collectNames v ++ collectNames i
  | .other _       => []

/- The references the annotation occupying one position contributes to the
   recorded set.

   An ABSENT annotation contributes nothing, and it does so WITHOUT any
   expression having been inspected or traversed — there is no expression there
   to inspect, so reaching this outcome cannot involve collecting references out
   of the annotation. A present expression contributes exactly what its shape
   says (above).

   This is the full behavior under specification, modeled deeply (no opaque
   oracle): the result is determined structurally by the input. -/
def storedNames : Annotation → List String
  | none   => []
  | some e => storedNamesOf e

/- Reaching through one attribute layer leaves the recorded references
   unchanged — the single structural fact the peeling loop relies on. -/
@[grind] lemma storedNames_attribute (e : Node) :
    storedNames (some (.attribute e)) = storedNames (some e) := rfl

/- Whether the annotation present at this position is an attribute access (the
   shape the walk reaches through). An absent annotation is not. -/
def isAttr : Annotation → Bool
  | some (.attribute _) => true
  | _                   => false

/- Reach through one attribute layer, exposing the expression the access was
   taken on; anything else (including an absent annotation) is left as is. -/
def peelAttr : Annotation → Annotation
  | some (.attribute e) => some e
  | a                   => a

/- Reaching through one attribute layer preserves the contributed references:
   the loop invariant survives each peel step. -/
@[grind] lemma peel_preserves (a : Annotation) (h : isAttr a = true) :
    storedNames a = storedNames (peelAttr a) := by
  cases a with
  | none   => simp [isAttr] at h
  | some e => cases e <;> simp_all [isAttr, peelAttr, storedNames, storedNamesOf]

/- How many attribute layers a present expression is wrapped in. -/
def attrDepthOf : Node → Nat
  | .attribute e => attrDepthOf e + 1
  | _            => 0

/- How many attribute layers the annotation at this position is wrapped in —
   equivalently, how many times `peelAttr` can still reach through it. An absent
   annotation is at zero. This is the size measure the peeling walk consumes. -/
def attrDepth : Annotation → Nat
  | none   => 0
  | some e => attrDepthOf e

/- Reaching through one attribute layer strictly lowers the layer count. Paired
   with `peel_preserves` (the invariant survives a peel) this is what makes the
   peeling walk a finite descent rather than an unbounded one. -/
@[grind] lemma attrDepth_peel (a : Annotation) (h : isAttr a = true) :
    attrDepth (peelAttr a) < attrDepth a := by
  cases a with
  | none   => simp [isAttr] at h
  | some e => cases e <;> simp_all [isAttr, peelAttr, attrDepth, attrDepthOf]
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Given the annotation occupying one position, report the bare references it
   contributes to the recorded set of referenced identifiers (so an import named
   only inside an annotation is not mistaken for unused).

   If the position holds NO annotation at all, nothing is contributed, and
   nothing about an expression is read on the way there — there is no expression
   at that position to read, so no reference collection happens.

   Otherwise the contribution is determined by the structure of the expression:
     * a bare reference contributes itself;
     * an attribute access reaches through to the expression it is taken on and
       contributes that expression's references — so a dotted reference such as
       `m.<x>` (or `m.<x>.<y>…`) is credited to the name `m` it is rooted at;
     * an indexing form headed by the typing namespace contributes only that
       namespace; any other indexing form contributes every reference inside it,
       at any depth;
     * any other expression shape contributes nothing, even when it has parts
       holding references.

   `annot` is a read-only handle on the annotation position (not `mut`): the
   routine inspects it and mutates nothing it is given (directive 5). -/
method storeAnnotationNames (annot : Annotation) return (out : List String)
  ensures out = storedNames annot
  do
    -- impl-start
    -- implementation elided — supplied by the consumer
    -- impl-end

prove_correct storeAnnotationNames by
  -- proof elided — supplied by the consumer
