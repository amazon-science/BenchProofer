# refinement.md — sympy__sympy-14531

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_equation` / `render_directed_limit` / `render_name` /
`render_operand` impl regions, the deep `render_rational` / `lit_name` /
`registered` / `eq_text` / `eq_registry` / `limit_text` / `limit_registry`
models, and the live `digits` / `coprime` axioms) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized callee —
split into **A-consumed**, where the proof uses the axiom's `Ensures`, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE). Line citations are in the gold-patched
worktree (mapping.md preamble).

## 0. The modeled domain (faithfulness boundary)

**The fractional operand carrier** is the canonical, **non-collapsing** region of
a sympy `Rational`: a proper fraction in lowest terms — `q >= 2` and
`coprime(p, q)`. This is forced by the carrier's auto-canonicalisation:

- `Rational(p, q)` REDUCES a non-coprime pair (`Rational(3898, 1754)` →
  `1949/877`), so only coprime `(p, q)` faithfully renders as
  `digits(p)/digits(q)`.
- `Rational(n, 1)` IS an `Integer` and dispatches through `_print_Integer`, which
  under `sympy_integers=True` renders `'S(n)'` (not `'n'`); the integer slot is a
  DIFFERENT print method, so it is out of this leaf's modeled domain (`q >= 2`
  excludes it).

**The name operand carrier** is a `Symbol` with a one-character lowercase name,
modeled by its code point `c` with `is_name(c)` (97..122). `Symbol(chr(c)).name`
is BOTH its rendered text (`lit_name(c)`, identical under either setting) and its
registry key (`registered`). The name is a *parameter*, not a fixed `'x'`, so a
slot rendered under a hard-coded name is observable. (`Eq` / `Limit` between a
name and a fraction is exactly the F2P shape; a relation between two numeric
constants would auto-evaluate to a Boolean and never reach the template.)

**The registry carrier** is the receiver's own `self.symbols`
(`sympy/printing/python.py:21`), a duplicate-free ordered list of name strings,
modeled by `reg: List[int]` / `PSeq[int]` of code points (mapping.md §2). It is a
*mutable* parameter because the modeled call writes it.

The same delegation refinement applies verbatim to integer/sign/other operand
classes and to multi-character names; they add no independent observable beyond
delegation and are covered by `patch.diff` + G-RESOLVE.

## 0.1 The two observables of the changed operation

The gold patch replaces `%s`-of-operand with `self._print(operand)` at each
operand slot. `%s` is `str(operand)` → `Basic.__str__` → a **fresh**
default-settings `StrPrinter` (mapping.md §1); `self._print` is the **owning
receiver**. Two pieces of receiver state therefore start participating, and the
spec pins both, because *each F2P test reads one of them* (mapping.md §1.1):

1. **CONFIGURATION** — `self._settings['sympy_integers']`, modeled as `wrap`.
   Visible on the FRACTION slot: `'S(p)/q'` vs `'p/q'`. Read by F2P
   `test_Rational` through `sstr`.
2. **NAME REGISTRY** — `self.symbols`, modeled as `reg`. Visible on each NAME
   slot: the name is appended (unless already present) by
   `PythonPrinter._print_Symbol` (`python.py:38-42`) and drained into the
   `x = Symbol('x')` preamble by `python()` (`python.py:52-69`). Read by F2P
   `test_python_relational` through `python()`.

Observable 2 is not optional decoration. A name's TEXT is byte-identical whether
the owning receiver rendered it or a detached printer did, so a text-only spec
leaves every name slot free: an impl emitting the name as a constant token
satisfies all text clauses, and its faithful patch resolves `test_Rational` while
failing `test_python_relational`. §F.1 records the machine-checked control that
the registry clauses are what reject that impl.

## A. The relation site — `_print_Relational` (`sympy/printing/str.py:636-637`)

Gold hunk:
```
- return '%s(%s, %s)' % (charmap[expr.rel_op], expr.lhs, expr.rhs)
+ return '%s(%s, %s)' % (charmap[expr.rel_op], self._print(expr.lhs),
+                        self._print(expr.rhs))
```

Modeled by `render_equation(wrap, nl, rp, rq, reg)` — a relation
`Eq(name, p/q)`. Note the hunk changes **both** operand slots; the model has one
step per slot.

| # | model.py impl op (`render_equation`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `wrap: bool` parameter | `self._settings['sympy_integers']` | R | `bool` ↔ the one setting that changes the fractional rendering (mapping.md §2). |
| A2 | `reg: List[int]` parameter, held at full `Acc(list_pred(reg))` | `self.symbols` on the receiver (`python.py:21`) | R | code-point list ↔ the receiver's duplicate-free ordered name list; `reg.append(c)` ↔ `self.symbols.append(name)` (mapping.md §2). Full permission because the modeled call WRITES it. |
| A3 | name operand `nl` with `is_name(nl)`; fractional operand `(rp, rq)`, `rq>=2`, `coprime` | `expr.lhs = Symbol(chr(nl))`; `expr.rhs = Rational(rp, rq)` | R | a NAME operand ↔ its code point (its own text and its own registry key); a proper-fraction operand ↔ `(p, q)` coprime, `q>=2` (mapping.md §2, §0). |
| A4 | literals `[69,113,40]` / `[44,32]` / `[41]` | the `'Eq('`, `', '`, `')'` template fragments (here `charmap['=='] == 'Eq'`) | I | identical template bytes (`'Eq('`=69,113,40; `', '`=44,32; `')'`=41). The patch does not touch the template; only the two operand slots. |
| A5 | `render_name(nl, reg)` for the lhs slot | `self._print(expr.lhs)` | A-reference | **the changed call at the NAME slot.** `Printer._print` (`printer.py:238`) dispatches the `Symbol` to the receiver's own `_print_Symbol`: the TEXT comes from `StrPrinter._print_Symbol` (`str.py:699`, `expr.name`) and the REGISTRATION from `PythonPrinter._print_Symbol` (`python.py:38-42`), which the two receivers reach through the SAME patched `_print_Relational` object (mapping.md §1.1). Modeled deeply by `render_name`, whose post pins `lit_name(nl)` AND `registered(old reg, nl)`. G-AX validates both against the real callees (mapping.md §3.3). Pre-patch this slot was `%s` = `str(Symbol)`, which reaches neither. |
| A6 | `render_operand(wrap, rp, rq, reg)` | `self._print(expr.rhs)` | A-reference | **the changed call at the FRACTION slot.** The operand is rendered with the **same** receiver ⇒ the same `_settings` ⇒ the same `wrap`; and, a fraction not being a name, it leaves `self.symbols` alone. Modeled deeply by `render_operand` (post pins `render_rational(wrap, …)` AND `ToSeq(reg) == Old(ToSeq(reg))`). G-AX validates `eq_text == real sstr(Eq(name, p/q), sympy_integers=wrap)` and `eq_registry == real PythonPrinter.symbols` growth (mapping.md §3.4). |

## B. The limit site — `_print_Limit` (`sympy/printing/str.py:219`)

Gold hunk — **both** arms of the method, which the patch changes together:
```
  def _print_Limit(self, expr):
      e, z, z0, dir = expr.args
      if str(dir) == "+":
-         return "Limit(%s, %s, %s)" % (e, z, z0)
+         return "Limit(%s, %s, %s)" % tuple(map(self._print, (e, z, z0)))
      else:
-         return "Limit(%s, %s, %s, dir='%s')" % (e, z, z0, dir)
+         return "Limit(%s, %s, %s, dir='%s')" % tuple(map(self._print,
+                                                         (e, z, z0, dir)))
```

**When the `dir` argument appears in the output.** Exactly when
`str(expr.args[3]) != "+"` — no other condition. `expr.args[3]` is the direction
`Symbol` the CONSTRUCTOR stored (`sympy/series/limits.py:126-146` at
base_commit `205da797`): it is the caller's `dir` (default `"+"`), except that
`z0 is S.Infinity` forces `"-"` and `z0 is S.NegativeInfinity` forces `"+"`, and
it is restricted to one of `'+'`, `'-'`, `'+-'` (anything else raises
`ValueError`). So the arm is **not** a function of the limit point: measured on
the gold-patched worktree, `Limit(x, x, 7/2)` and `Limit(x, x, -oo, dir='-')`
take the three-slot arm while `Limit(x, x, oo)` and `Limit(x, x, 7/2, dir='-')`
take the four-slot one. The printer does not decide the arm; it reads the
direction off the compound it was handed.

Modeled by
`render_directed_limit(wrap, plus, ke, ue, ve, kz, uz, vz, k0, u0, v0, ud, reg)`
— a limit over three arbitrary operands, taken in a direction. `plus` carries
`str(dir) == "+"` and so selects the template form; `ud` is the direction
operand's handle. Both arms are modeled, and each of the four slots the taken
arm has gets one delegation step, the slots being SEPARATELY parameterised
because `map` delegates them independently.

| # | model.py impl op (`render_directed_limit`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `wrap: bool`; `reg: List[int]`; operands `(ke,ue,ve)`, `(kz,uz,vz)`, `(k0,u0,v0)` with `is_atom` | `self._settings['sympy_integers']`; `self.symbols`; `e = expr.args[0]`, `z = expr.args[1]`, `z0 = expr.args[2]` | R | as A1/A2/A3, with each slot ranging over all three operand kinds (mapping.md §2). No branch assumption is smuggled in here: the arm is carried by `plus` (B1a), not derived from the point. |
| B1a | `plus: bool` | `str(dir) == "+"` for `dir = expr.args[3]` | R | the template selector, read off the compound. Free (not a function of the other parameters) because the real selector is not one: the constructor forces `"-"` for `z0 is S.Infinity` and `"+"` for `z0 is S.NegativeInfinity`, and otherwise keeps the caller's `dir` (`limits.py:126-146`). Quantifying over BOTH values is what obliges an implementation to have both arms. |
| B2 | literals `[76,105,109,105,116,40]` / `[44,32]` / `[41]` / `[44,32,100,105,114,61,39]` / `[39,41]` | `'Limit('`, `', '`, `')'`, `", dir='"`, `"')"` template bytes | I | identical bytes in both `%`-format strings; the patch does not touch either template. |
| B3 | `render_atom(ke,…)` then `render_atom(kz,…)`, in that order | the `e` and `z` slots of `tuple(map(self._print, …))`, in tuple order | A-reference | **the changed calls at the two NAME slots**, per A5. The ORDER matters to the observable: `self.symbols` is ordered and `python()` emits one preamble line per entry in list order, so `limit_registry(r, ne, nz) = registered(registered(r, ne), nz)` mirrors the left-to-right `map`. Keeping `ne` and `nz` distinct parameters is what makes the second slot separately visible — with one shared name the duplicate-free registry would mask a missing second delegation (§F.1). |
| B4 | `render_atom(k0, u0, v0, wrap, reg)` | the `z0` slot of `tuple(map(self._print, …))` | A-reference | `map(self._print, …)` renders the limit point with the SAME receiver ⇒ same settings; a fractional point registers nothing (per A6), a name point registers per A5, and a point of the third kind contributes whatever it contributes. G-AX validates `limit_text == real sstr(Limit(n1, n2, p/q), sympy_integers=wrap)` and `limit_registry == real symbols` growth (mapping.md §3.4). |
| B5 | `render_unmodeled(ud, wrap, reg)` at `not plus` | the `dir` slot of `tuple(map(self._print, (e, z, z0, dir)))` | A-reference | **the changed call at the DIRECTION slot** — present only in the four-slot arm, and delegated exactly like the other three: `self._print(dir)` dispatches the direction `Symbol` to the receiver's own `_print_Symbol`, so the text is `dir.name` (`str.py:699`) and `self.symbols` gains that name (`python.py:38-42`). Pre-patch it was a bare `%s` = `str(Symbol)`, a detached printer, so `python(Limit(x, x, oo))` lost its `- = Symbol('-')` preamble line. Modeled as the third operand kind because a direction is neither a fraction nor a lowercase one-letter name; `opaque_text(ud, wrap)` / `opaque_registry(·, ud)` are therefore uninterpreted, which is what makes the slot unreproducible at the compound site. Measured on the gold worktree: `PythonPrinter.symbols` after `Limit(y, z, 7/2, dir='-')` is `['y','z','-']` — the direction registers **last**, after all three operands, with the same append-unless-present rule. |
| B6 | at `plus` the model emits no direction slot and takes no `opaque_registry(·, ud)` step | the three-slot arm, which never mentions `dir` | I | measured: `python(Limit(x, x, 7/2))` has the single preamble line `x = Symbol('x')` — the `+` direction is neither printed nor registered. |

## C. The leaf renderers

### C.1 `render_operand` / `render_rational` — the fraction slot

`render_operand`'s impl IS the deep model of the unchanged `_print_Rational`
selected by `self._print` for a proper-fraction operand:

| # | model.py impl op (`render_operand`) | repo op (`_print_Rational`, `str.py:574-580`) | tag | justification |
|---|---|---|---|---|
| C1 | `if wrap: return [83,40] + digits(p) + [41,47] + digits(q)` | `if self._settings.get('sympy_integers', False): return "S(%s)/%s" % (expr.p, expr.q)` | A-consumed (`digits`) + I | template bytes `'S('`=83,40; `')/'`=41,47; `%s` of p,q ↔ `digits` (A-consumed, §D). |
| C2 | `return digits(p) + [47] + digits(q)` | `return "%s/%s" % (expr.p, expr.q)` | A-consumed + I | `'/'`=47; `%s` ↔ `digits`. |
| C3 | (no statement touching `reg`) | `_print_Rational` never touches `self.symbols` | I | a fraction is not a name; the post-condition `ToSeq(reg) == Old(ToSeq(reg))` records the absence as an obligation, which is what makes the compounds' registry growth attributable to the NAME slots only. |

(The repo `_print_Rational` also has a `q == 1` branch returning `str(expr.p)`;
the modeled operand domain excludes `q == 1` (§0), so it is not in the leaf's
control flow. The integer slot is reached via `_print_Integer` under dispatch,
out of the modeled fraction domain.)

`render_rational` (the `@Pure` spec form of C1–C2) is the **A-reference** deep
model validated `== real sstr(Rational(p, q), sympy_integers=wrap)` by
axiom_check.py (mapping.md §3.2) — at the public dispatch entry point, not a
hand-picked leaf method. `materialize` is an R glue step: it realises a
`PSeq[int]` spec value as a `List[int]`, the identity on character content.

### C.2 `render_name` / `lit_name` + `registered` — the name slot

`render_name`'s impl IS the deep model of the two unchanged `_print_Symbol`
methods the patched delegation now reaches:

| # | model.py impl op (`render_name`) | repo op | tag | justification |
|---|---|---|---|---|
| C4 | `return [c]` | `StrPrinter._print_Symbol` (`str.py:699`) returns `expr.name`, a one-character string | R + I | the code point IS the name's text; setting-independent (asserted under both settings for all 26 keys, mapping.md §3.3). |
| C5 | `if not (c in reg): reg.append(c)` | `PythonPrinter._print_Symbol` (`python.py:40-41`): `if symbol not in self.symbols: self.symbols.append(symbol)` | I (up to R on the carrier) | statement-for-statement identical: the same membership guard, the same append at the end. The dedup and the ordering are both observable through `python()`'s preamble (`python.py:69`, one line per entry in list order). |

`lit_name` and `registered` (the `@Pure` spec forms of C4/C5) are the
**A-reference** deep models validated against the real `sstr(Symbol(...))` and
the real `PythonPrinter.symbols` / `python()` preamble by axiom_check.py over all
26 keys × 7 registry pre-seeds (mapping.md §3.3), so both arms of the guard are
exercised out-of-band as well as in-proof.

## D. The consumed axioms — `digits` and `coprime` (A-consumed)

`digits(n)` is the leaf integer-spelling callee `str(int)` that spells `expr.p`/
`expr.q`. The proof uses exactly its `Ensures(len(Result()) >= 1)` (non-empty)
and its determinism (same `n` ⇒ same sequence, so the numerator spelling is
shared across `wrap`). G-AX runs the real `str(n)` and confirms non-empty
(mapping.md §3.1). It is NOT the operation the patch changes.

`coprime(p, q)` is an abstract domain-restriction predicate: it asserts the
fractional operand is already in lowest terms, so `digits(p)/digits(q)` is the
faithful render of `Rational(p, q)` (a non-reduced pair denotes a different
canonical fraction). The proof does not otherwise depend on it; it only carves
out the non-collapsing carrier region (§0). G-AX enforces the matching domain
filter `gcd(p, q) == 1` and asserts `Rational(p, q)` does not reduce
(mapping.md §3.1).

`is_name(c)` is NOT an axiom: it is a `@Pure` function with a body
(`97 <= c <= 122`). The `ax-domain-containment` probe confirms every `c` it admits
is a real one-character `Symbol` whose name is both its rendered text and its
registry entry, i.e. the carrier is inhabited exactly where the model reaches it.

## E. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, A-reference, or I. The operation that
genuinely *changed* — replacing `%s`-of-operand (a detached, fresh
default-settings, registry-less re-print) with `self._print(operand)` (the owning
receiver) — is modeled **deeply at every slot it changed**:

* fraction slot: the `render_operand` impl takes the parent's `wrap` and produces
  the same-setting `render_rational`, and the compound specs `eq_text` /
  `limit_text` demand the operand text under that `wrap`;
* name slots: the `render_name` impl performs the receiver's own registration and
  the compound specs `eq_registry` / `limit_registry` demand exactly the resulting
  registry.

There is no consumed axiom about the function under change; the consumed axioms
(`digits`, `coprime`) cover the *unchanged* integer-spelling leaf and the domain
boundary. The changed rendering is the **A-reference** that G-AX validates the
deep models against (`render_rational` / `lit_name` / `registered` / `eq_text` /
`eq_registry` / `limit_text` / `limit_registry` == the real `sstr(...)` and the
real `PythonPrinter.symbols` / `python()` preamble).

## F. The differential (G-DIFF): the spec sees the pre-patch behaviour

`model_prepatch.py` keeps the spec byte-identical and reverts both compound impls
to the pre-patch behaviour at **every** operand slot: each name slot becomes a
detached re-render (`materialize(lit_name(...))` — the right text, produced
without the receiver, so no registration) and each fraction slot becomes an
ambient-default render (`render_operand(False, …)`), modeling `%s` =
`str(operand)` = a fresh default-settings, registry-less `StrPrinter`. It
**fails** verification with exactly two errors, on the text postconditions:

```
model_prepatch.py:236: Postcondition of render_equation might not hold.
    Assertion (ToSeq(Result()) == eq_text(wrap, nl, rp, rq)) might not hold.
model_prepatch.py:268: Postcondition of render_directed_limit might not hold.
    Assertion (ToSeq(Result()) == limit_text(wrap, ne, nz, z0p, z0q)) might not hold.
```

because for `wrap=True` the detached render yields `'p/q'` where the spec demands
`'S(p)/q'`. That is exactly the reported issue: `sstr(Eq(x, S(1)/2),
sympy_integers=True)` gave `'Eq(x, 1/2)'`. One prepatch file covers both sites
(they share the single delegation change); both failing clauses are exhibited.

### F.1 Why the twin's failure is NOT the control for the registry clauses

Viper reports the FIRST failing conjunct of an `Ensures` block and stops, so the
twin's two text failures say nothing about whether the registry clauses have
teeth — its registry clauses are never reached. The load-bearing control is
therefore a dedicated pair of rivals in `properties.py`, whose text clauses are
*satisfied* so that the verifier is forced to reach the registry clause. Both are
machine-checked to FAIL, and the reported failing assertion is the registry one:

| rival (properties.py id) | impl change | verifier's rejection |
|---|---|---|
| `registry-skip-name-equation` | lhs slot emitted as the bare token `[nl]` (correct text, no registration) — **the recorded refutation's shape** | `Postcondition of render_equation might not hold. Assertion (ToSeq(reg) == eq_registry(Old(ToSeq(reg)), nl)) might not hold.` |
| `registry-echo-text-only` | body replaced by `return materialize(eq_text(wrap, nl, rp, rq))` — every text clause satisfied by construction | same registry assertion |
| `registry-skip-second-name` | `z` slot of the limit emitted as `[nz]`; correct exactly when `ne == nz` | `Postcondition of render_directed_limit might not hold. Assertion (ToSeq(reg) == limit_registry(Old(ToSeq(reg)), ne, nz)) might not hold.` |
| `registry-no-dedup` | `reg.append(c)` unconditional | `Postcondition of render_name might not hold. Assertion (ToSeq(reg) == registered(Old(ToSeq(reg)), c)) might not hold.` |
| `registry-only-when-wrap` | registration only on the `wrap=True` half | `... Assertion (ToSeq(reg) == eq_registry(Old(ToSeq(reg)), nl)) might not hold.` |
| `registry-frac-writes` | the fraction slot writes to `reg` | `Postcondition of render_operand might not hold. Assertion (ToSeq(reg) == Old(ToSeq(reg))) might not hold.` |
| `registry-order-swapped` | the limit registers `nz` before `ne` (a set-valued registry model would accept it) | `... Assertion (ToSeq(reg) == limit_registry(Old(ToSeq(reg)), ne, nz)) might not hold.` |
| `registry-leaf-wrong-key` | `render_name` returns the right text but registers the fixed key 120 | `Postcondition of render_name might not hold. Assertion (ToSeq(reg) == registered(Old(ToSeq(reg)), c)) might not hold.` |

The positive control `pos-control-equation-cheapest` differs from
`registry-echo-text-only` by exactly one statement (the `render_name` call) and
VERIFIES, so the rejection is attributable to the missing registration and not to
a spec that rejects everything.

## G. verify(model) ⇒ resolved

`render_equation` / `render_directed_limit` verify only if **both** observables
match:

1. the fractional operand's rendered text equals `render_rational(wrap, …)` — the
   operand rendered under the compound's own setting (A6/B4) — and the leaf render
   matches `_print_Rational` (C.1);
2. the registry after the call equals `eq_registry` / `limit_registry` of the
   registry before it — one `registered` step per NAME slot in source order
   (A5/B3) — and the per-name step matches `PythonPrinter._print_Symbol`
   statement-for-statement (C.2), while the fraction slot writes nothing (C3).

By R (`bool` ↔ `sympy_integers`, `List[int]` ↔ `self.symbols`, `(p, q)` ↔
proper-fraction `Rational`, `c` ↔ `Symbol(chr(c))`, `List[int]` ↔ `str`) and the
identical template bytes (I), the verified renderers equal the gold methods'
output *and* leave the receiver in the gold state on the tested inputs. By G-AX
the deep models equal the real `sstr` at the dispatch entry point and the real
`PythonPrinter.symbols` / `python()` preamble (A-reference, executed RC=0
in-container under the gold patch), `digits` over-approximates `str(int)`, and
`coprime` matches `gcd(p,q)==1` (A-consumed). By G-CONF the contract-stripped impl
regions agree with the real patched methods on 100 324 `Requires`-satisfying
inputs in both observables, 0 disagreements.

The two observables are exactly the two the instance's `FAIL_TO_PASS` pair reads
(mapping.md §1.1): `test_Rational` through `sstr` (configuration) and
`test_python_relational` through `python()` (registry). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and audited callees over the modeled domain — including at the name
slots, where text alone cannot distinguish the receiver — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX, executed) and refinement fidelity (this document, G-EQ).

## H. Closed gap (recorded for the audit trail)

An earlier revision of this spec pinned only observable 1 and modeled every name
slot as the constant token `[120]`, tagged **I** ("identical template bytes"). That
tag was wrong: `self._print(expr.lhs)` is a *changed* operation whose text happens
to coincide with the pre-patch text, so the constant token abstracted away the
whole of observable 2. A rival that emitted the name slots as constants verified
against that spec, and its faithful patch — delegating only the fraction — failed
F2P `test_python_relational` (1 of 2 F2P failing; 84/84 P2P passing), i.e.
`verify ⇏ correct`. The repair does not add a precondition or narrow the domain:
it makes the previously-invisible receiver state OBSERVABLE (`reg`, a new
parameter) and pins it, and it parameterises each name slot so the slots are
separately visible. The domain grew (all 26 name keys, arbitrary registry
pre-states, distinct limit name pairs) rather than shrank, and every clause is
grounded in the source cited above.
