# refinement.md — sympy__sympy-24539

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`asExpr` `do` block plus the pure deep model `asExprSpec`) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement; state the bijection),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model /
opaque callee validated == the real callee by G-AX), or **I** (identical concrete
op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
plan §4.1); the A legs and this narrative are audited by **G-EQ** / **G-AX**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `PolyElement.as_expr` (`sympy/polys/rings.py:618`)

Gold hunk:
```
-        if symbols and len(symbols) != self.ring.ngens:
-            raise ValueError("not enough symbols, expected %s got %s" % (self.ring.ngens, len(symbols)))
-        else:
+        if not symbols:
             symbols = self.ring.symbols
+        elif len(symbols) != self.ring.ngens:
+            raise ValueError(
+                "Wrong number of symbols, expected %s got %s" %
+                (self.ring.ngens, len(symbols))
+            )

         return expr_from_dict(self.as_expr_dict(), *symbols)
```

| # | Solution.lean impl op (`asExpr`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `d : Int` | `self.as_expr_dict()` — the sparse `{monom: coeff}` datum | R | the datum ↔ an opaque `Int` handle (mapping.md §2); never decomposed by the method. G-CONF bridges with a concrete `PolyElement`. |
| A2 | param `ringSymbols : List Int` | `self.ring.symbols` (length `self.ring.ngens`) | R | tuple-of-`Symbol` ↔ `List Int`; only `.length` (= `ngens`) and list identity are observed (mapping.md §2). Read-only, not `mut`. |
| A3 | param `symbols : List Int` | the caller varargs `*symbols` | R | vararg tuple ↔ `List Int`; empty call ↔ `symbols.isEmpty` (mapping.md §2). Read-only, not `mut`. |
| A4 | `if symbols.isEmpty then chosen := ringSymbols` | `if not symbols: symbols = self.ring.symbols` | I | the no-caller-names branch: render over the datum's own names. Transliterated 1:1 by G-CONF. |
| A5 | `else if symbols.length = ringSymbols.length then chosen := symbols` | `elif len(symbols) != self.ring.ngens: raise …` (its negation: the correctly-sized list falls through and is forwarded) | I | **the discriminating clause.** A non-empty caller list of the right length is HONORED — `chosen := symbols` ⇔ the post-patch `elif` not firing, so the original `symbols` reaches `expr_from_dict`. `len == ngens` ⇔ `symbols.length = ringSymbols.length` (mapping.md §1). |
| A6 | `else return Except.error AsExprErr.wrongNumberOfSymbols` | `elif len(symbols) != self.ring.ngens: raise ValueError("Wrong number of symbols, …")` | I | a non-empty wrong-length caller list is rejected; `Except.error` ↔ the raised `ValueError` (mapping.md §2). The message text is not behaviorally observed by the F2P test (it asserts `raises(ValueError, …)`). |
| A7 | `return Except.ok (exprFromDict d chosen)` | `return expr_from_dict(self.as_expr_dict(), *symbols)` | A-reference + I | the UNCHANGED renderer is modeled `opaque` (`exprFromDict`) with NO `ensures`; that it is consulted with EXACTLY the chosen name list (and the datum) is the **A-reference** G-AX validates against the real `expr_from_dict`. The call op itself — pass `(d, chosen)` and return the result — is **I** (transliterated 1:1 by G-CONF). `Except.ok` ↔ a returned `Expr`. |

Discriminating content of the change — a correctly-sized caller list must be
FORWARDED to the renderer (A5/A7), not silently replaced by the datum's own
names — lives in the `else if symbols.length = ringSymbols.length then chosen :=
symbols` leg (A5). `Solution_prepatch.lean` reproduces the pre-patch control flow
(`if symbols and len != ngens: raise; else: symbols = self.ring.symbols`), whose
`else` overwrites `chosen` with `ringSymbols` on EVERY non-rejected path —
including the correctly-sized case — and so **fails** `out = asExprSpec d
ringSymbols symbols` precisely on that leg (G-DIFF; confirmed: the prepatch's
unsolved goal is `exprFromDict d ringSymbols = exprFromDict d symbols` under
`¬symbols = []`, i.e. the supplied-and-correctly-sized case where the spec
forwards `symbols` but the prepatch forwards `ringSymbols`).

## B. No consumed axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The renderer `expr_from_dict` is **unchanged** by the
patch — the patch only reorders the symbol-selection guard so a correctly-sized
caller list is honored instead of discarded; it does not touch the renderer.
`exprFromDict` is modeled `opaque` with **NO asserted `ensures`**, so there is
**no consumed axiom** to over-claim (directive 7): the desired behavior assumes
nothing about which `Expr` the renderer produces, only that the method forwards
the correctly-chosen name list to it. It is tagged **A-reference** — G-AX
(which runs at the UNPATCHED base_commit) validates the facts about the
UNCHANGED callee that hold regardless of the patch: that `expr_from_dict` is a
deterministic pure function of `(datum, gens)` which genuinely USES its `gens`
argument (so the method's choice of name list is observable), plus the unchanged
default branch and the wrong-length rejection. The forwarding/honoring of a
correctly-sized caller list is the operation the patch CHANGES, so it is NOT a
G-AX obligation — it is validated against the patched oracle by G-CONF (≥10⁵
inputs), G-DIFF, and G-GOLD.

The operation that genuinely *changed* — choosing the SUPPLIED names over the
datum's names when one name per generator is supplied — is the symbol-selection
control flow, modeled **directly** (A4/A5/A6, all I legs over an A-reference
callee), not hidden behind an axiom about the function under change. There is no
axiom about `as_expr` itself.

## C. verify(Solution) ⇒ resolved

`asExpr` verifies only if its output equals `asExprSpec d ringSymbols symbols` for
every input — including the non-empty correctly-sized leg (A5), which forces
`Except.ok (exprFromDict d symbols)` (forward the SUPPLIED names), the empty leg
(A4) forcing `exprFromDict d ringSymbols`, and the non-empty wrong-length leg (A6)
forcing the rejection. By R (datum ↔ `Int` handle, symbol tuples ↔ `List Int`) and
the I transliteration of the selection control flow and the renderer call, the
verified method equals the gold patch's `as_expr` on the tested calls; by G-AX
(at base_commit) the real `expr_from_dict` is a deterministic pure function of
`(datum, gens)` that actually uses its `gens` argument (so the chosen list is
observable) and the unchanged default branch + wrong-length rejection hold; by
G-CONF the R/I shadow of the selection agrees with the PATCHED `as_expr`'s
behaviour on ≥10⁵ fuzzed inputs — including the discriminating case where a
correctly-sized caller list is honored. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited callee — and the gold patch resolves (G-RESOLVE). Trust
points are exactly the two of plan §1.1: callee-fact soundness (G-AX) and
refinement fidelity (this doc, G-EQ + G-CONF).
