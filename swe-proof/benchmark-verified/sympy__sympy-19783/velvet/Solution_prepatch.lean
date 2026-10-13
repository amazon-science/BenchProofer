import Velvet.Std
-- imports-end

set_option loom.semantics.termination "total"
set_option loom.semantics.choice "demonic"

open TotalCorrectness DemonicChoice

-- axioms-start
/- No consumed axioms. The desired behaviour is a structural product-dispatch
   on symbolic quantum objects: it inspects WHICH kind each operand is and
   collapses certain products to one operand. The kind-membership tests it
   consults (is this object an operator? a Hermitian-conjugate object? the
   identity operator?) are an UNCHANGED inspection of the object hierarchy; they
   are modeled DEEPLY as the `isOperatorClass` / `isDaggerClass` /
   `isIdentityClass` predicates below (A-reference), validated == the real
   library's membership tests by axiom_check.py (G-AX) and by the end-to-end
   differential check (G-CONF). The operation under specification — the product
   dispatch itself — is modeled deeply as the `do` block, so it is never
   axiomatized. -/
-- axioms-end

-- pure-start
/- A finite carrier for the fragment of symbolic quantum expressions this
   product dispatch distinguishes. Each node is a concrete constructor referring
   to its sub-operands — there is no opaque "answer" node:

     • `op name`   — a plain (non-identity) operator, named by its label;
     • `ident`     — the identity operator;
     • `dag e`     — the Hermitian conjugate of `e` (a conjugate object);
     • `mul a b`   — the ordinary product of `a` and `b`. As a RESULT of the
                     dispatch this denotes exactly the value the real
                     product-construction routine returns for the two operands
                     (including any normalization that routine applies); as an
                     INPUT it stands for an already-built product object.

   The product builder used when no collapse applies is exactly the `mul`
   constructor (the ordinary product), so a dispatch that did not compute the
   collapse cannot echo an answer key: it would have to emit a different tree. -/
inductive QExpr where
  | op (name : String)
  | ident
  | dag (e : QExpr)
  | mul (a b : QExpr)
  deriving DecidableEq, Inhabited

/- Kind-membership tests, deep models of the object-hierarchy inspection
   (A-reference, validated against the real library by G-AX / G-CONF).

   `isOperatorClass` holds for a plain operator AND for the identity operator,
   because the identity operator is itself an operator (a subclass) — the
   membership test sees it as one. `isDaggerClass` holds for a conjugate object.
   `isIdentityClass` holds only for the identity operator. A product node and a
   conjugate object are not operators; only a conjugate object is a conjugate;
   only the identity is the identity. -/
def isOperatorClass : QExpr → Bool
  | .op _  => true
  | .ident => true
  | _      => false

def isDaggerClass : QExpr → Bool
  | .dag _ => true
  | _      => false

def isIdentityClass : QExpr → Bool
  | .ident => true
  | _      => false

/- The desired product of a Hermitian-conjugate object `self` with `other`:
   when `other` is the identity operator the product collapses to `self`;
   otherwise it is the ordinary product. Pinned operand-by-operand on the
   actual operands, so only the intended result — not a differently-shaped one —
   satisfies the contract. -/
def daggerProd (self other : QExpr) : QExpr :=
  if isIdentityClass other then self else .mul self other

/- The desired product of the identity operator `self` with `other`: when
   `other` is an operator OR a Hermitian-conjugate object the product collapses
   to `other`; otherwise it is the ordinary product. The conjugate-object case
   is the behaviour that must be covered as well as the operator case. -/
def identityProd (self other : QExpr) : QExpr :=
  if isOperatorClass other || isDaggerClass other then other else .mul self other
-- pure-end

-- pre-conditions-start
-- pre-conditions-end

-- post-conditions-start
-- post-conditions-end

/- Multiply a Hermitian-conjugate object on the left by `other`.

   Desired behaviour: a Hermitian-conjugate object times the identity operator
   simplifies to the conjugate object itself (the product is the conjugate
   object, NOT an ordinary product carrying a redundant identity factor);
   times anything else it is the ordinary product.

   `self` and `other` are read-only operands (neither is `mut`): the routine
   inspects them and mutates nothing (directive 5). `self` is a conjugate object
   (`require isDaggerClass self`), the dispatch precondition of this product. -/
method daggerProduct (self : QExpr) (other : QExpr) return (out : QExpr)
  require isDaggerClass self = true
  ensures out = daggerProd self other
  do
    -- impl-start
    -- Pre-image skeleton: a Hermitian-conjugate object provides no product
    -- dispatch of its own, so the product is ALWAYS the ordinary product —
    -- it never collapses against the identity operator. The frozen spec
    -- requires the collapse (daggerProd), so prove_correct MUST fail.
    return QExpr.mul self other
    -- impl-end

prove_correct daggerProduct by
  loom_solve <;> simp_all [daggerProd]

/- Multiply the identity operator on the left by `other`.

   Desired behaviour: the identity operator times an operator simplifies to that
   operator, and — the behaviour that must hold equally — the identity operator
   times a Hermitian-conjugate object simplifies to that conjugate object; times
   anything else it is the ordinary product.

   `self` and `other` are read-only operands (neither is `mut`); the routine
   inspects them and mutates nothing (directive 5). `self` is the identity
   operator (`require self = QExpr.ident`), the dispatch precondition of this
   product. -/
method identityProduct (self : QExpr) (other : QExpr) return (out : QExpr)
  require self = QExpr.ident
  ensures out = identityProd self other
  do
    -- impl-start
    -- When `other` is an operator or a Hermitian-conjugate object the product
    -- collapses to `other`; otherwise emit the ordinary product.
    if isOperatorClass other || isDaggerClass other then
      return other
    else
      return QExpr.mul self other
    -- impl-end

prove_correct identityProduct by
  loom_solve <;> simp_all [identityProd]
