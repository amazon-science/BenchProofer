# P2 adversarial audit — sympy__sympy-19783

Backend: `velvet`. One section per audit role below. Each role's status/note is the MACHINE-derived verdict (the runner re-runs the submitted attacks); the agent's own verdict and notes are advisory context, not the source of truth for green.

## Role 1 — G-EQ (refinement fidelity): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** eq: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a TOTAL functional pin: daggerProduct.ensures = (out = daggerProd self other) and identityProduct.ensures = (out = identityProd self other), where daggerProd/identityProd are total pure functions over the whole QExpr carrier. Any verifying impl must compute exactly those functions, so there is no verifying-but-wrong impl to materialize a non-resolving patch from. All 5 genuinely-wrong same-spec impls FAIL to verify (exit 1).
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,12 +103,9 @@
   ensures out = daggerProd self other
   do
     -- impl-start
-    -- When `other` is the identity operator the product collapses to `self`;
-    -- otherwise emit the ordinary product of the two operands.
-    if isIdentityClass other then
-      return self
-    else
-      return QExpr.mul self other
+    -- ATTACK (partial-domain): always collapse to self, dropping the
+    -- fall-through product. Wrong whenever other is not the identity.
+    return self
     -- impl-end
 
 prove_correct daggerProduct by
```

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,9 +130,10 @@
   ensures out = identityProd self other
   do
     -- impl-start
-    -- When `other` is an operator or a Hermitian-conjugate object the product
-    -- collapses to `other`; otherwise emit the ordinary product.
-    if isOperatorClass other || isDaggerClass other then
+    -- ATTACK (prepatch bug for method B / boundary): pre-patch test used the
+    -- Operator arm only, so a Dagger `other` is NOT collapsed. This is exactly
+    -- the bug the gold patch fixes; must fail the spec on isDaggerClass other.
+    if isOperatorClass other then
       return other
     else
       return QExpr.mul self other
```

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

```diff
@@ -103,12 +103,12 @@
   ensures out = daggerProd self other
   do
     -- impl-start
-    -- When `other` is the identity operator the product collapses to `self`;
-    -- otherwise emit the ordinary product of the two operands.
+    -- ATTACK (control-flow-effect / inverted branch): collapse in the wrong
+    -- case. Return the mul when other IS the identity, self otherwise.
     if isIdentityClass other then
+      return QExpr.mul self other
+    else
       return self
-    else
-      return QExpr.mul self other
     -- impl-end
 
 prove_correct daggerProduct by
```

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,12 +130,9 @@
   ensures out = identityProd self other
   do
     -- impl-start
-    -- When `other` is an operator or a Hermitian-conjugate object the product
-    -- collapses to `other`; otherwise emit the ordinary product.
-    if isOperatorClass other || isDaggerClass other then
-      return other
-    else
-      return QExpr.mul self other
+    -- ATTACK (ungrounded over-collapse): always collapse to `other`, even for a
+    -- product node. Wrong when other is a mul (should stay ordinary product).
+    return other
     -- impl-end
 
 prove_correct identityProduct by
```

Attack 5 — `atk_7.lean` → rejected (same spec, does not verify — good)

```diff
@@ -130,9 +130,9 @@
   ensures out = identityProd self other
   do
     -- impl-start
-    -- When `other` is an operator or a Hermitian-conjugate object the product
-    -- collapses to `other`; otherwise emit the ordinary product.
-    if isOperatorClass other || isDaggerClass other then
+    -- ATTACK (partial-domain / dropped arm): collapse only for a conjugate
+    -- object, dropping the operator arm. Wrong on a plain operator `other`.
+    if isDaggerClass other then
       return other
     else
       return QExpr.mul self other
```

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
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
    -- When `other` is the identity operator the product collapses to `self`;
    -- otherwise emit the ordinary product of the two operands.
    if isIdentityClass other then
      return self
    else
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
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec(velvet) True for all 8 files (pos + atk_1..7). Verify cmd: `bash scripts/lean_verify.sh <f>`.

### RESULTS (exit: 0=verifies, 1=error):
- pos.lean (correct impl) EXIT=0 -> positive control verifies.
- atk_1.lean (partial-domain: daggerProduct always `return self`) EXIT=1 -> fails, correct.
- atk_2.lean (prepatch bug for method B: `isOperatorClass other` arm only, drops the Dagger fix) EXIT=1 -> fails, correct.
- atk_3.lean (control-flow-effect: inverted branch, collapse in the wrong case) EXIT=1 -> fails, correct.
- atk_4.lean (ungrounded over-collapse: identityProduct always `return other`) EXIT=1 -> fails, correct.
- atk_7.lean (dropped-arm boundary: identityProduct collapses only on isDaggerClass, drops operator arm) EXIT=1 -> fails, correct.
- prepatch.lean & prepatch2.lean (shipped Solution_prepatch{,_2}.lean) EXIT=1 -> both reproduce the pre-patch bug (fail their discriminating clause).

TWO EXTRA CANDIDATES (not counted as attacks): atk_5.lean (daggerProduct via `match other` instead of isIdentityClass) and atk_6.lean (identityProduct via explicit `match` enumerating op/ident/dag/mul). Both are behaviorally EQUIVALENT to the spec's pure functions but EXIT=1 because the FROZEN proof tactic (`loom_solve <;> simp_all [...]`) cannot close the reshaped goals (unsolved-goals errors on the match-arm cases). They are neither verifying nor wrong, so they do NOT falsify verify=>correct; recorded for completeness only.

RESOLVE / harness: no verifying wrong impl exists, so no attack patch needed a resolve run (patches={} by construction). The G-RESOLVE harness was exercised as a positive anchor: run_resolve('sympy__sympy-19783', gold patch.diff, timeout=1800) -> RESOLVED=True, COMPLETED=True, note='resolved'. Confirms harness live + gold target resolves.

REFINEMENT.md AUDIT: legs A1(R)/A2(A-reference)/A3(I)/A4(I+R)/B1(R)/B2(A-reference)/B3(I)/B4(I+R). No kind-3 (inexpressible-changed-op) legs; no consumed axioms; no dead axioms. The three A-references validated against the real repo at base_commit 586a43201d0357e92e8c93548d69a9f42bf548f4: `class IdentityOperator(Operator)` confirms `isOperatorClass QExpr.ident=true` <-> isinstance(IdentityOperator(),Operator)=True; `class Dagger(adjoint)` (NOT an Operator subclass) confirms B2's explicit Dagger arm is genuinely the fix and isDaggerClass<->isinstance(other,Dagger); isIdentityClass<->isinstance(other,IdentityOperator). Model<->patch correspondence holds. conformance_check.py shadow/oracle match the two gold __mul__ bodies (mapping.md bijection, seed 19783).

VERDICT: SOUND. >=5 distinct wrong same-spec impls attacked (partial-domain, prepatch bug, boundary/dropped-arm, control-flow-effect, ungrounded over-collapse), all correctly rejected by verification; both prepatches reproduced; gold resolves; no verify=>correct gap found.

## Role 2 — G-PANEL-1 (spec-too-weak): pass (agent: SOUND)

- **status (recorded):** `pass`
- **machine verdict:** panel_1: 5 attacks re-run, none breaks the spec; positive control verifies

**What was measured.** The harness re-ran 5 candidate wrong implementations submitted against this specification, recording for each whether it verifies and, where it does, whether its patch resolves the instance. An attack that verifies without resolving would be a counterexample to `verify => correct`; the graded outcomes were:

| re-run outcome | attacks | source |
| --- | ---: | --- |
| does not verify against this specification, so the specification excludes it | 5 | `atk_1.lean`, `atk_2.lean`, `atk_3.lean`, `atk_4.lean`, `atk_7.lean` |

**Non-vacuity.** The positive control `pos.lean` verifies, so the specification is satisfiable by a correct implementation and the outcomes above are not an artifact of a spec nothing can satisfy. The bug this instance fixes is re-encoded as one of the attacks above, so the specification is checked to exclude the original defect and not merely to admit the fix.

Counterexample / evidence:

```
None found. The spec is a TOTAL functional pin: daggerProduct.ensures = (out = daggerProd self other) and identityProduct.ensures = (out = identityProd self other), where daggerProd/identityProd are total pure functions over the whole QExpr carrier. Any verifying impl must compute exactly those functions, so there is no verifying-but-wrong impl to materialize a non-resolving patch from. All 5 genuinely-wrong same-spec impls FAIL to verify (exit 1).
```

**Attacks re-run (5):** each keeps the spec byte-for-byte and changes only the implementation; a TIGHT/SOUND spec rejects every one that reached the verifier.

_The 5 attack bodies behind this role are not republished in this section: each is byte-identical to the block published under `G-EQ` (Role 1 above, refinement fidelity), and each was compared byte for byte before it was dropped. One agent's single submission feeds both gate verdicts — `G-EQ` scores it for `verify => correct` through the resolve oracle, this role for any same-spec implementation that verifies at all — so the two roles re-ran ONE battery and each recorded its own outcome for every attack in it. Those outcomes are the lines below; this role's positive control is retained here in full._

Attack 1 — `atk_1.lean` → rejected (same spec, does not verify — good)

Attack 2 — `atk_2.lean` → rejected (same spec, does not verify — good)

Attack 3 — `atk_3.lean` → rejected (same spec, does not verify — good)

Attack 4 — `atk_4.lean` → rejected (same spec, does not verify — good)

Attack 5 — `atk_7.lean` → rejected (same spec, does not verify — good)

**Positive control** (a correct impl that MUST verify — non-vacuity): `pos.lean`

```lean
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
    -- When `other` is the identity operator the product collapses to `self`;
    -- otherwise emit the ordinary product of the two operands.
    if isIdentityClass other then
      return self
    else
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
```

Prepatch bug re-encoded as an attack: `True`.

PROTOCOL: same_spec(velvet) True for all 8 files (pos + atk_1..7). Verify cmd: `bash scripts/lean_verify.sh <f>`.

### RESULTS (exit: 0=verifies, 1=error):
- pos.lean (correct impl) EXIT=0 -> positive control verifies.
- atk_1.lean (partial-domain: daggerProduct always `return self`) EXIT=1 -> fails, correct.
- atk_2.lean (prepatch bug for method B: `isOperatorClass other` arm only, drops the Dagger fix) EXIT=1 -> fails, correct.
- atk_3.lean (control-flow-effect: inverted branch, collapse in the wrong case) EXIT=1 -> fails, correct.
- atk_4.lean (ungrounded over-collapse: identityProduct always `return other`) EXIT=1 -> fails, correct.
- atk_7.lean (dropped-arm boundary: identityProduct collapses only on isDaggerClass, drops operator arm) EXIT=1 -> fails, correct.
- prepatch.lean & prepatch2.lean (shipped Solution_prepatch{,_2}.lean) EXIT=1 -> both reproduce the pre-patch bug (fail their discriminating clause).

TWO EXTRA CANDIDATES (not counted as attacks): atk_5.lean (daggerProduct via `match other` instead of isIdentityClass) and atk_6.lean (identityProduct via explicit `match` enumerating op/ident/dag/mul). Both are behaviorally EQUIVALENT to the spec's pure functions but EXIT=1 because the FROZEN proof tactic (`loom_solve <;> simp_all [...]`) cannot close the reshaped goals (unsolved-goals errors on the match-arm cases). They are neither verifying nor wrong, so they do NOT falsify verify=>correct; recorded for completeness only.

RESOLVE / harness: no verifying wrong impl exists, so no attack patch needed a resolve run (patches={} by construction). The G-RESOLVE harness was exercised as a positive anchor: run_resolve('sympy__sympy-19783', gold patch.diff, timeout=1800) -> RESOLVED=True, COMPLETED=True, note='resolved'. Confirms harness live + gold target resolves.

REFINEMENT.md AUDIT: legs A1(R)/A2(A-reference)/A3(I)/A4(I+R)/B1(R)/B2(A-reference)/B3(I)/B4(I+R). No kind-3 (inexpressible-changed-op) legs; no consumed axioms; no dead axioms. The three A-references validated against the real repo at base_commit 586a43201d0357e92e8c93548d69a9f42bf548f4: `class IdentityOperator(Operator)` confirms `isOperatorClass QExpr.ident=true` <-> isinstance(IdentityOperator(),Operator)=True; `class Dagger(adjoint)` (NOT an Operator subclass) confirms B2's explicit Dagger arm is genuinely the fix and isDaggerClass<->isinstance(other,Dagger); isIdentityClass<->isinstance(other,IdentityOperator). Model<->patch correspondence holds. conformance_check.py shadow/oracle match the two gold __mul__ bodies (mapping.md bijection, seed 19783).

VERDICT: SOUND. >=5 distinct wrong same-spec impls attacked (partial-domain, prepatch bug, boundary/dropped-arm, control-flow-effect, ungrounded over-collapse), all correctly rejected by verification; both prepatches reproduced; gold resolves; no verify=>correct gap found.

## Role 3 — G-PANEL-2 (faithfulness): pass (agent: FAITHFUL)

- **status (recorded):** `pass`
- **machine verdict:** Faithfulness (spec-too-strong / drift) attack on sympy__sympy-19783 velvet bundle. No divergence found between the modeled functions and the real (patched) repo callee anywhere in the modeled carrier domain.

SPEC INTEGRITY: same_spec(Solution, Solution_prepatch)=True and same_spec(Solution, Solution_prepatch_2)=True under the velvet backend tables -> spec region is byte-identical (frozen). Solution.lean elaborates cleanly via lean_verify.sh (exit 0, no sorry/errors).

MODEL vs REAL CALLEE: daggerProduct models Dagger.__mul__ (dagger.py, added by patch); identityProduct models IdentityOperator.__mul__ (operator.py:308). Branch conditions map exactly: isIdentityClass other == isinstance(other, IdentityOperator); (isOperatorClass||isDaggerClass) other == isinstance(other,(Operator,Dagger)). Verified against real library: isinstance(IdentityOperator(),Operator)=True (so isOperatorClass ident=true), Dagger is NOT a subclass of Operator, and the two __mul__ methods are the owned methods.

DIFFERENTIAL EVIDENCE (against actual patched worktree = base_commit 586a4320 + gold patch): boundary sweep over op/ident/dag/Mul/nested-dagger for both methods -> all MATCH; 300,000-input randomized fuzz with an independent seed (depth-3 carrier objects) -> 0 mismatches; the bundle's own conformance_check.py -> 'G-CONF OK ... 0 disagreements' on 100,000 inputs (seed 19783). The fall-through QExpr.mul is realized as the real Mul(...) call with default evaluation, so sympy normalization is inherited identically (confirmed by fuzz using real Mul).

CONCLUSION: The spec does not over-constrain and does not drift from the real callee. No diverging input exists within the modeled domain. Verdict FAITHFUL.

**What was measured.** This role asks whether the specification still describes the function it stands in for -- whether the abstract model diverges from that function on an input the function accepts, and whether the specification has been strengthened past it so that a correct implementation would be excluded. The reviewer recorded FAITHFUL. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical checks over the same artifact are recorded separately and re-runnable from the bundle: G-CONF `pass` (the conformance battery over the modelled function); G-AX `pass` (the axiom battery). The account names `Solution.lean`, `conformance_check.py`, all of which ship in this bundle, so a reader can start there.

## Role 4 — G-PANEL-3 (leakage): pass (agent: NO-LEAKAGE)

- **status (recorded):** `pass`
- **machine verdict:** Judged the CONSUMER SPEC VIEW (markers.spec_view of Solution.lean; refinement.md/mapping.md are auditor-only docs, not in the view). same_spec(Solution, prepatch1)=True and same_spec(Solution, prepatch2)=True — spec region is byte-identical across the impl variants, so the impl is genuinely elided. Mechanical G-LEAK screen passes (no hard failures).

Semantic gold-reconstruction check:
- No diff markers, no `@@`/`diff --git`/`+++`.
- Patched files `sympy/physics/quantum/dagger.py` and `operator.py` and their module paths do NOT appear anywhere in the spec view.
- The gold edit's touched methods are `Dagger.__mul__` and `IdentityOperator.__mul__`; `__mul__` is a non-distinctive dunder and is never named. Distinctive repo class names Dagger / Operator / IdentityOperator all already appear VERBATIM in the public problem_statement, so any conceptual overlap is already public via the task (leak.py's `if sl in problem: continue`).
- Spec-view identifiers (QExpr, daggerProduct, identityProduct, daggerProd, identityProd, isOperatorClass/isDaggerClass/isIdentityClass, mul) are Lean modeling names; none echo a patched Python symbol, file, or module path.
- Comments contain no bug/fix/regression narration (NARRATION_RE clean); they describe DESIRED behavior abstractly.

The one behavior specified beyond the terse problem_statement is the second gold case `IdentityOperator() * Dagger(O) -> Dagger(O)` (the operator.py widening), which the problem statement — mentioning only `Dagger * Identity` — omits. But this is stated as an abstract behavioral requirement ("the identity operator times a Hermitian-conjugate object simplifies to that conjugate object"), which is the legitimate role of a specification, not a reproduction of the gold patch's text, file, symbol, or bug/fix framing. Specifying correct target behavior is not edit-localization leakage. A solver reading the spec learns WHAT must hold, not the diff structure of the fix.

Note for context (not a leakage finding): G-EQ and G-PANEL-1 are recorded fail for this bundle; those are equivalence/panel concerns outside the G-PANEL-3 leakage scope.

**What was measured.** This role asks whether the consumer-facing spec view discloses the reference edit -- whether a solver reading only the specification could reconstruct the fix instead of deriving it from the public problem statement. The reviewer recorded NO-LEAKAGE. It is a judgment and not a machine re-run: unlike the two mechanized roles, nothing is submitted to the verifier for it and no candidate implementation is graded, so the recorded status is that judgment and the account above is the evidence for it rather than a summary of a measurement made elsewhere.

**How far this record can be re-checked.** This role records no per-attack table because nothing was re-run for it, so the account above is the whole of its evidence and this is the part of the cell whose verdict is prose by construction. The mechanical check over the same artifact is recorded separately and re-runnable from the bundle: G-LEAK `pass` (the mechanical leakage screen over the same spec view). The account names `Solution.lean`, `mapping.md`, `refinement.md`, all of which ship in this bundle, so a reader can start there.
