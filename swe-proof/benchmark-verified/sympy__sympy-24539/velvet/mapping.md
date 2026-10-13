# mapping.md — sympy__sympy-24539

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 193e3825645d93c73e31cdceb6d742cc6919624d`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the modeled callee.

Repo file under change: `sympy/polys/rings.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `asExpr (d) (ringSymbols) (symbols)` | `PolyElement.as_expr(self, *symbols)` — `sympy/polys/rings.py:618` | the modeled changed method |
| `exprFromDict` *(opaque — A-reference)* | `expr_from_dict(rep, *gens)` — `sympy/polys/polyutils.py:375` (imported at `rings.py:28`, called at `rings.py:624`) | unchanged rendering helper the method delegates to |
| `asExprSpec` *(pure deep model — R/I)* | the symbol-selection control flow of `as_expr` (`rings.py:619-624` post-patch) | which generator-name list is forwarded, or rejection |
| `AsExprErr.wrongNumberOfSymbols` | the `raise ValueError("Wrong number of symbols, expected … got …")` (`rings.py` post-patch) | the one distinguished failure |
| `d : Int` | `self.as_expr_dict()` — the sparse `{monom: coeff}` datum (`rings.py:624,626`) | opaque datum handle |
| `ringSymbols : List Int` | `self.ring.symbols` (a tuple of `Symbol`s; `len == self.ring.ngens`) | the datum's own ordered generator names |
| `symbols : List Int` | the caller-supplied `*symbols` varargs | the caller's optional generator names |

The number of generators `self.ring.ngens` is `len(self.ring.symbols)`
(`rings.py:201,217`), so the model's length check `symbols.length =
ringSymbols.length` is exactly the repo guard `len(symbols) == self.ring.ngens`.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the Lean
value domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| the sparse datum `self.as_expr_dict()` | opaque `Int` handle `d` | a single fixed `PolyElement`'s datum; the method never rebuilds it, so its content is irrelevant to the decision — modeled as one opaque handle. G-AX/G-CONF use a concrete `PolyElement`. |
| `self.ring.symbols` (tuple of `Symbol`, length `ngens`) | `List Int` `ringSymbols`; `len ↔ .length` | each `Symbol` ↔ an opaque `Int` slot; only the LENGTH and the IDENTITY-as-a-list (which list is forwarded) are observed, never a symbol's internals. The bijection preserves length and list identity. |
| the caller varargs `*symbols` (tuple of `Symbol`, possibly empty) | `List Int` `symbols`; empty tuple ↔ `[]` | same per-`Symbol` slot bijection; `symbols == ()` ↔ `symbols.isEmpty`. |
| `expr_from_dict(rep, *gens)` return (`Expr`) | opaque `Int` (`exprFromDict d gens`) | the rendered expression is never inspected by the method; identity-only handle. G-AX/G-CONF observe expression EQUALITY (`==` / SymPy structural equality), which the bijection respects: same `(rep, gens)` ⇒ equal `Expr`. |
| `raise ValueError("Wrong number of symbols, …")` | `Except.error AsExprErr.wrongNumberOfSymbols` | the only exception the method's control flow can raise; `Except.ok` ↔ a returned `Expr`. |

`*symbols` being a vararg tuple means "the caller supplied a list" ⇔ the tuple is
non-empty; an explicit empty call `f.as_expr()` ⇔ `symbols = []` ⇔
`symbols.isEmpty`. There is no way to pass a length-0 non-default list, so the
empty case is exactly the "use the datum's own names" branch.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `exprFromDict` ↔ `expr_from_dict` (A-reference, opaque, no `ensures`)
**Callee:** `sympy.polys.polyutils.expr_from_dict(rep, *gens)` (`polyutils.py:375`),
imported into `rings.py` at line 28 and called by `as_expr` at line 624 — both
pre- and post-patch, UNCHANGED by the gold patch. It renders a sparse multinomial
`rep` into a SymPy `Expr` using **exactly the generator symbols `gens` it is
passed** (it `zip`s `gens` against each monomial's exponent vector); it consults
nothing else for the generators. The method `as_expr` does not inspect the
returned `Expr`; its sole responsibility is to choose WHICH `gens` list to forward.

Modeled `opaque` with **NO asserted `ensures`** — the desired behavior assumes
nothing about which `Expr` the renderer produces, only that it is a pure function
of `(datum, chosen-name-list)` and that the chosen list is forwarded verbatim
(directive 7: weakest sufficient contract = none). Tagged **A-reference**, not a
consumed axiom.

**Soundness check (G-AX):** G-AX runs `axiom_check.py` in the **UNPATCHED
base_commit** container (it does NOT apply the gold patch — that is G-CONF's
job). So it validates ONLY facts about the UNCHANGED callee `expr_from_dict`
(and the unchanged default branch / rejection) that hold REGARDLESS of the
patch — never the behaviour the patch changes (directive 7: do not check the
operation under change). `axiom_check.py` constructs a concrete multivariate
`PolyElement` and asserts, against the REAL `expr_from_dict` and the REAL
base-commit `as_expr`:
  * (determinism) `expr_from_dict(datum, *gens) == expr_from_dict(datum, *gens)`
    — a pure deterministic function of `(datum, gens)` (the bijection §2 needs
    this);
  * (uses-gens / observability) rendering the same datum over distinct
    correctly-sized name lists yields DISTINCT expressions, so the modeled
    `exprFromDict d chosen` genuinely depends on `chosen` — the method's choice
    of list is observable, not masked by a constant renderer;
  * (default — UNCHANGED branch) `f.as_expr() == expr_from_dict(f.as_expr_dict(),
    *f.ring.symbols)` — no caller names ⇒ datum's own names; identical pre/post
    patch;
  * (rejection) `f.as_expr(*wrong)` raises `ValueError` for every non-empty
    wrong-length `wrong` (true at base_commit too; the patch only changes the
    message text).
The **discriminator** (a correctly-sized caller list being HONORED) is the
operation the patch CHANGES, so it is NOT a G-AX obligation — it is validated
against the patched oracle by G-CONF (≥10⁵ inputs), G-DIFF, and G-GOLD.
Imports only `sympy` (the same package the repo uses). Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24539`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `asExprSpec`'s symbol-selection decision to Python (the R/I-tagged
ops) and leaves the unchanged renderer as the real `expr_from_dict` (A-tagged →
run the real callee, not a model); it diffs the resulting `Expr` (or the raised
`ValueError`) against the patched `PolyElement.as_expr` over ≥10⁵ fuzzed
(symbol-count) inputs.
