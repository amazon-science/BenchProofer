# refinement.md — sympy__sympy-19346

Operation-by-operation correspondence between `Solution.lean`'s impl regions
(the `printDict` and `printSet` `do` blocks, the deep `dictRender`/`setRender`/
`joinComma` models) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (deep model validated == real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. There are **no A-tagged ops**
(no consumed axioms, no deep-model references — see mapping.md §3), so G-AX is
skipped.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

**Termination semantics: total.** The obligations run under
`loom.semantics.termination "total"` (`TotalCorrectness`), and each `while`
fold in `printDict`/`printSet` carries an explicit `decreasing i` measure, so a
verifying impl must TERMINATE and produce `dictRender items` / `setRender
elems`. (An earlier revision used partial correctness, under which a same-spec
impl whose loop never advances `i` verified vacuously — the postcondition is
claimed only *if* the loop exits; the adversarial audit (G-PANEL-1) constructed
exactly that diverging counterexample. Total semantics excludes the whole
class. The real assembly is a bounded comprehension/`", ".join` over
`expr.items()` / the set's elements — it trivially terminates — so total
correctness is the faithful reading of the repo behavior, not an
over-tightening.)

## A. The mapping site — `_print_dict` (`sympy/printing/repr.py:147`)

Gold hunk:
```
+    def _print_dict(self, expr):
+        sep = ", "
+        dict_kvs = ["%s: %s" % (self.doprint(key), self.doprint(value)) for key, value in expr.items()]
+        return "{%s}" % sep.join(dict_kvs)
```

| # | Solution.lean impl op (`printDict`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `items : List (Obj × Obj)` | `expr.items()` of the `dict` arg | R | `dict` (ordered) ↔ `List (Obj × Obj)` (mapping.md §2). G-CONF iterates the same dict object. |
| A2 | `kvText (k,v) = doprint k ++ ": ".toList ++ doprint v` | `"%s: %s" % (self.doprint(key), self.doprint(value))` | I + R | identical "key: value" assembly; the two `doprint` outputs are supplied as `Obj.reprText` (R — unchanged recursive helper, input carrier; mapping.md §3). |
| A3 | `joinComma (items.map kvText)`, computed by the backward `while` fold | `", ".join(dict_kvs)` | I | the fold IS the comma-join (no leading/trailing sep); concrete, transliterated by G-CONF. |
| A4 | `"{".toList ++ joined ++ "}".toList` returned | `"{%s}" % ...` | I | identical brace wrap. |

The empty dict: `items = []` ⇒ `dictRender [] = "{}".toList`, matching
`"{%s}" % "".join([]) = "{}"` (the F2P `srepr({}) == "{}"`).

Discriminating content: each key/value goes through the **recursive** renderer
`doprint` (`Obj.reprText`), not the shallow `Obj.strText`. The pre-patch fall
through to `str(expr)` rendered elements shallowly; `Solution_prepatch.lean`
reproduces that (`.strText`) and **fails** `out = dictRender items` (G-DIFF).

## B. The collection site — `_print_set` (`sympy/printing/repr.py:152`)

Gold hunk:
```
+    def _print_set(self, expr):
+        if not expr:
+            return "set()"
+        return "{%s}" % self.reprify(expr, ", ")
```

| # | Solution.lean impl op (`printSet`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `elems : List Obj` | the `set`/`frozenset` arg | R | `set` ↔ `List Obj` in the object's own iteration order (mapping.md §2). |
| B2 | `if elems = [] then "set()".toList` | `if not expr: return "set()"` | I | identical empty-collection token (the F2P/`test_set` `srepr(set()) == "set()"`). |
| B3 | `joinComma (elems.map doprint)`, backward `while` fold | `self.reprify(expr, ", ")` = `", ".join(self.doprint(e) for e in expr)` | I + R | `reprify` joins the per-element recursive renderings with ", "; the `doprint e` outputs are `Obj.reprText` (R). |
| B4 | `"{".toList ++ joined ++ "}".toList` | `"{%s}" % ...` | I | identical brace wrap. |

Discriminating content: same as A — recursive `doprint` per element, not the
shallow `strText`. `Solution_prepatch_2.lean` substitutes `.strText` for the
set elements and **fails** `out = setRender elems` (G-DIFF). `test_set` is not
in the F2P set but the second site is independently fixed by the patch, so it
gets its own failing prepatch.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — selecting the
**recursive** element rendering and assembling the brace/comma-delimited string
with the `set()` empty case — is modeled **deeply** (`kvText`/`doprint`,
`joinComma`, `dictRender`, `setRender`, the verified folds), not hidden behind
an axiom. The only callee invoked, the recursive renderer `doprint`, is
**unchanged** by the patch and treated as input carrier (R), so there is no
consumed axiom and no A-reference (mapping.md §3) — exactly the
sympy__sympy-16766 discipline.

## D. verify(Solution) ⇒ resolved

`printDict` verifies only if its output equals `dictRender items` — braces +
", "-joined `kvText` entries built from the **recursive** key/value renderings
(A2–A4); `printSet` only if its output equals `setRender elems` — `"set()"`
when empty else braces + ", "-joined **recursive** element renderings (B2–B4).
By R (`str ↔ List Char`, `dict`/`set` ↔ `List`, `doprint` ↔ `Obj.reprText`)
the verified renderers equal the gold `_print_dict` / `_print_set` on the
tested inputs; by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour on ≥10⁵ fuzzed inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The single trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there are no axioms to trust (G-AX skipped).
