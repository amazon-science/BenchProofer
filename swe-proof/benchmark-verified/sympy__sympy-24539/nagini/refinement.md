# refinement.md — sympy__sympy-24539

The operation-by-operation correspondence between `model.py`'s implementation
(the `select_render_symbols` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (proof uses an
axiom's `Ensures`), **A-reference** (a deep model validated == the real callee
by G-AX), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change site — `PolyElement.as_expr` (`sympy/polys/rings.py:618-624`)

Gold hunk:
```python
 def as_expr(self, *symbols):
-    if symbols and len(symbols) != self.ring.ngens:
-        raise ValueError("not enough symbols, expected %s got %s" % (self.ring.ngens, len(symbols)))
-    else:
+    if not symbols:
         symbols = self.ring.symbols
+    elif len(symbols) != self.ring.ngens:
+        raise ValueError(
+            "Wrong number of symbols, expected %s got %s" %
+            (self.ring.ngens, len(symbols))
+        )

     return expr_from_dict(self.as_expr_dict(), *symbols)
```

The semantic change: the three-way selection of the generator-symbol sequence
fed to `expr_from_dict`. Pre-patch the `else` arm fired on EVERY non-rejected
path, overwriting `symbols` with `self.ring.symbols` — so a correctly-sized
supplied sequence was silently discarded. Post-patch the default is used ONLY
when no symbols were supplied; a correctly-sized supplied sequence is kept.

| # | model.py impl op (`select_render_symbols`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | params `symbols`, `default_symbols`, `ngens: int` | `*symbols`, `self.ring.symbols`, `self.ring.ngens` | R | tuple-of-`Symbol` ↔ `List[int]` of symbol identities; `ngens` identity; `ngens == len(default_symbols)` precondition mirrors `PolyRing.__init__` (mapping.md §types). |
| 2 | `if len(symbols) == 0:` → `src = default_symbols` | `if not symbols: symbols = self.ring.symbols` | R + I | `not symbols` (empty var-args tuple) ↔ `len(symbols) == 0`; assignment of the ring's defaults ↔ selecting `default_symbols`. |
| 3 | `elif len(symbols) != ngens: raise SymbolCountError()` | `elif len(symbols) != self.ring.ngens: raise ValueError(...)` | R + I | the length-mismatch guard is identical (`len(symbols) != ngens`); `ValueError` ↔ user-defined `SymbolCountError` (R; builtin-exception `Exsures` is banned, mapping.md). The message string is not observable to the test (`raises(ValueError, ...)` checks only the type/fact-of-raise). |
| 4 | `else: src = symbols` | (the post-patch fall-through: a correctly-sized supplied `symbols` is kept and used) | I | the FIX: when a non-empty correctly-sized sequence is supplied, it is the selected sequence. In the gold this is the *absence* of the old `else` overwrite — `symbols` retains its supplied value into `expr_from_dict`. |
| 5 | the materialisation loop (`result = result + [c]` over `src`) producing `Result()` with `ToSeq(Result()) == ToSeq(src)` | `expr_from_dict(self.as_expr_dict(), *symbols)` is invoked over the selected sequence | R | the modeled `Result()` IS the `gens` sequence the downstream builder reads; the copy loop just materialises a fresh, element-wise-equal carrier (so `Result()` carries full permission without aliasing a read-only input). `expr_from_dict` is UNCHANGED and a deterministic function of `(rep, gens)`; for a fixed polynomial the rendered expression differs iff `gens` differs (mapping.md §callee). No axiom is consumed. |

## No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — the
three-way selection of which generator-symbol sequence flows into the
expression builder — is modeled **directly and deeply** (control flow + the
element-wise-equal materialisation of the selected sequence), not behind an
axiom. There are NO consumed axioms (`axioms` region empty) and NO A-reference
deep-model-vs-callee checks: the unchanged downstream callee `expr_from_dict`
is a deterministic function of its `gens` argument, and the only quantity the
patch alters is that argument, which the model returns directly. Hence
`axiom_check.py` for this bundle records that there is no axiom/deep-model to
validate against a real callee (it documents the deterministic-function
provenance and the F2P discriminator), and `meta.json` lists no axioms and no
deep_model_references.

## verify(model) ⇒ resolved

`select_render_symbols` verifies only if (a) a value is produced exactly when
`len(symbols) == 0` or `len(symbols) == ngens`; (b) when a non-empty
correctly-sized sequence is supplied, the selected sequence equals THAT supplied
sequence element-for-element; (c) when nothing is supplied, the selected
sequence is the default; (d) the error is raised on exactly the non-empty
wrong-length case. By R (Symbol ↔ int, tuple ↔ list, ValueError ↔
SymbolCountError) the verified selection equals the gold patch's selection of
`*symbols` for `expr_from_dict`. Because `expr_from_dict` is unchanged and a
deterministic function of `(rep, gens)`, equal selected `gens` ⇒ equal rendered
expression on the tested polynomial; thus the gold patch makes
`f.as_expr(U,V,W) == g` and `raises(ValueError, lambda: f.as_expr(X))` — it
resolves (G-RESOLVE). `model_prepatch.py` reproduces the pre-patch `else`
overwrite and FAILS clause (b) — exactly the bug the F2P test detects (G-DIFF).
