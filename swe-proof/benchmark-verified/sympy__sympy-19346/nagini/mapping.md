# mapping.md — sympy__sympy-19346

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 94fb720696f5f5d12bad8bc813699fd696afd2fb`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `sympy/printing/repr.py` (the `ReprPrinter`, the printer
behind the public `srepr`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_collection_codepoints(elems)` | `ReprPrinter._print_set(self, expr)` — added by the patch at `sympy/printing/repr.py` (after `_print_list`, line 145) | the modeled new function: render an unordered collection |
| `render_mapping_codepoints(flat)` | `ReprPrinter._print_dict(self, expr)` — added by the patch at `sympy/printing/repr.py` (after `_print_list`, line 145) | the modeled new function: render an associative mapping |
| `elem_repr(t)` / `doprint_elem(t)` *(axiom — A-consumed)* | `ReprPrinter.doprint` → `Printer._print` recursive dispatch — `sympy/printing/printer.py:249,253` (invoked by `reprify` at `repr.py:31` and directly in the new `_print_dict`) | unchanged community callee: the recursive executable-representation routine the new methods invoke on each element/key/value. `doprint_elem` is the concrete string-returning callee; `elem_repr` is its pure-sequence projection used inside the specs. |
| `elem_str(t)` / `str_elem(t)` *(axiom — A-reference, prepatch contrast)* | Python built-in `str()` applied to an element (the per-element rendering that the pre-patch whole-object fallback `emptyPrinter` → `str(expr)` performs) | the alternative rendering the assembly must NOT use. Modelled as its OWN uninterpreted callee, separate from `elem_repr`, with NO relation assumed between the two: their spellings differ only on SOME elements (`str(Symbol('x')) == 'x'` ≠ `srepr(Symbol('x')) == "Symbol('x')"`), and coincide on the constant/singleton class (`str(oo) == srepr(oo) == 'oo'`). The discriminator is existential, so no universal `elem_repr != elem_str` inequality is shipped (an over-claim the real callee falsifies). axiom_check.py (G-AX) witnesses both: str≠srepr on the discriminating class AND str==srepr on the constant class. |
| `joined_elems`, `joined_pairs`, `set_seq`, `dict_seq`, `empty_seq` | the deep structural model of the new methods' string assembly (`reprify` join + brace wrapping + the `set()`/`{}` empty literals + the `": "` pair separator) | pure spec: the container rendering, modeled deeply |

The pre-patch repo state the change addresses (for the refinement audit, not
referenced from the consumer spec view): `ReprPrinter` has **no** `_print_dict`
or `_print_set`, so `_print` dispatch (`printer.py:253`, the class-MRO scan at
`printer.py:286`) finds no matching `_print_<cls>` for `dict`/`set` and falls
through to `emptyPrinter` (`repr.py:33`), whose final branch returns
`str(expr)` (`repr.py:49`). `str` of a `dict`/`set` renders each element via the
element's `str`, not its `srepr` — e.g. `str({x: y}) == '{x: y}'`,
`srepr` should give `"{Symbol('x'): Symbol('y')}"`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (the value the new methods return; each `doprint(item)` result) | `List[int]` of Unicode code points | `s[k]` ↔ `out[k] == ord(s[k])`; `len(s)` ↔ `len(out)`; `str` concatenation / `"%s%s" % ...` / `sep.join(...)` ↔ list `+`; an empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materialises the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| one `set` of elements (`expr`) | `List[int]` of element tokens, one distinct `int` per element | element identity only; the spelling of each element's rendering is reproduced verbatim by `elem_repr` and is irrelevant to the container structure |
| one `dict` (`expr`, iterated as `expr.items()`) | flat `List[int]` of even length, positions `2j, 2j+1` carrying the j-th pair's key, value tokens | preserves `items()` order and pairing; the flat carrier avoids nested `list_pred` (a Nagini timeout risk) while keeping the key/value pairing explicit |
| `"%s: %s" % (doprint(k), doprint(v))` pair format | `elem_repr(k) + PSeq(COLON, SPACE) + elem_repr(v)` | the literal `": "` is code points `58, 32`; `%s` substitutions ↔ the two `elem_repr` renderings |
| `sep = ", "` join separator; `reprify(..., ", ")` | `PSeq(COMMA, SPACE)` = code points `44, 32` between renderings | `sep.join` ↔ separator between consecutive renderings, none after the last |
| `"{%s}"` brace wrap | `PSeq(LBRACE) + ... + PSeq(RBRACE)` = `123, ..., 125` | literal braces |
| `"set()"` empty-collection literal | `PSeq(115, 101, 116, 40, 41)` | the five code points of `set()` |
| `"{}"` empty-mapping literal | `PSeq(LBRACE, RBRACE)` = `123, 125` | the two code points of `{}` |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `elem_repr` / `doprint_elem` ↔ the recursive srepr routine (A-consumed)
**Callee:** `ReprPrinter.doprint(elem)` (`sympy/printing/printer.py:249`), which
calls the recursive dispatch `Printer._print(elem)` (`printer.py:253`). This is
the *unchanged* routine the two new methods invoke per element:
`_print_set` via `reprify` (`repr.py:27-31`, `self.doprint(item)`), and
`_print_dict` directly (`self.doprint(key)`, `self.doprint(value)`). The patch
does NOT change `doprint`/`_print`/`reprify`; it only adds the two container
methods that call them. The axiom encodes only the property the proof needs: the
**value link** `ToSeq(doprint_elem(t)) == elem_repr(t)` — that the concrete
per-element callee the container rendering invokes is exactly the routine the
spec's `elem_repr` denotes. `elem_repr` itself is left **wholly uninterpreted**
(`Ensures(True)`): the spec assumes **no** constraint on the length or content of
an element's representation.

In particular the spec does **not** claim `len(elem_repr(t)) >= 1`. That would be
**unsound**: `ReprPrinter` has no `_print_` method for every element class, and
`Printer._print`'s class-MRO scan (`printer.py:286`) then reaches a branch that
returns the object's bare `str` — `_print_AtomicExpr` (`repr.py:117-118`) or
`emptyPrinter`'s final `return str(expr)` (`repr.py:49`). For objects whose
`__str__` is empty this makes the whole representation the **empty string**.
Measured at `base_commit` and unchanged by the patch:
`srepr(Quantity(''))`, `srepr(stringPict(''))`, `srepr(CNF())` and
`srepr(ReferenceFrame(''))` are all `''` (length 0). (Note `ReprPrinter.__mro__`
is `(ReprPrinter, Printer, object)` — it does **not** inherit `StrPrinter`, so
`StrPrinter._print_Quantity` at `str.py:810` never applies.) Such an element is
still rendered by the container, and still separated from its neighbours, exactly
like any other: `srepr({Quantity(''), Symbol('x')}) == "{Symbol('x'), }"` and
`srepr({Quantity(''): Symbol('x')}) == "{: Symbol('x')}"`, both of which the deep
model `set_seq`/`dict_seq` predicts exactly. So dropping the non-emptiness claim
makes the model faithful on strictly MORE real inputs; the assembly needs no
change.

**Soundness (G-AX):** axiom_check.py constructs real sympy expressions for the
element tokens (Symbols, Integers, nested dicts/sets, the constant/singleton
class, and the empty-representation class above), and asserts on each only the
consumed value link — `ReprPrinter().doprint(elem) == srepr(elem)` — with **no**
length assertion. `check_empty_representation_witness` additionally asserts that
at least one real element genuinely renders as the empty string, so G-AX would
FAIL a model that re-introduced the `len(elem_repr) >= 1` over-claim (the same
way §3.2's checks guard its siblings).

### 3.2 `elem_str` / `str_elem` ↔ `str()` of an element (A-reference, contrast)
**Callee:** Python built-in `str(elem)`. This is the per-element rendering the
*pre-patch* whole-object fallback `str(expr)` performs (`repr.py:49`).
`elem_str` is modelled as its OWN uninterpreted callee, **separate** from
`elem_repr`, with **no relation assumed between the two** (`elem_str` carries no
`Ensures` constraining it relative to `elem_repr`, and no `len >= 1`). The
discriminating fact the F2P test `test_dict` observes is **existential, not
universal**: for the symbolic/numeric element class the test uses,
`str(elem) != srepr(elem)` (e.g. `str(Symbol('x')) == 'x'` vs
`srepr(Symbol('x')) == "Symbol('x')"`); but for the constant/singleton/boolean/
None class the two **coincide** (`str(oo) == srepr(oo) == 'oo'`,
`str(True) == srepr(True) == 'True'`), and `str(Symbol(''))` is the empty
string. A universal `Ensures(elem_repr(t) != Result())` (or `len(elem_str) >= 1`)
would therefore be **unsound** — falsified by the real callee on that class — so
the spec ships neither. (Symmetrically, and for the same reason, `elem_repr`
carries no `len >= 1`: see §3.1.) The G-DIFF discriminator does not need it:
`elem_str` and `elem_repr` are distinct uninterpreted functions, so Nagini cannot
prove `elem_str(t) == elem_repr(t)`, and the prepatch's `str_elem`-built `inner`
cannot discharge the `elem_repr`-built fold invariant.

Note on how a `str_elem`-based rival is reported: `str_elem` carries no
`Requires(MustTerminate(...))`, while the rendering functions hold
`MustTerminate(3)`, so Nagini rejects such a rival with an *obligation-leak*
error at the call site rather than with the fold-invariant error. The semantic
discriminator underneath is nonetheless real and was measured: adding
`Requires(MustTerminate(2))` to `str_elem` in a scratch copy makes the prepatch
fail exactly `ToSeq(inner) == joined_elems(elems_s.drop(i))` and the
`joined_pairs` analogue instead. That strengthening is NOT shipped because it
pushes the single-leg `str_elem` battery cases past the verifier budget (measured:
`wrong-str-elem-set` did not converge in 1200s with it, versus a 27s rejection
without it), and a timeout is not a sound rejection signal.

**Soundness (G-AX):** axiom_check.py runs the real `str(elem)` and the real
`srepr(elem)` and asserts BOTH (a) `str(elem) != srepr(elem)` on the
discriminating class AND (b) `str(elem) == srepr(elem)` on the constant class
(plus `str(Symbol('')) == ''`) — so it would FAIL a model that re-introduced the
universal inequality or the `len(elem_str) >= 1` over-claim. It checks the
A-consumed `elem_repr` value link (`doprint == srepr`, no length claim) on the
FULL pool including the constant class and the empty-representation class of
§3.1. It also reconstructs the full `srepr` of representative
dicts/sets (over that full pool) and asserts it equals the deep model
`dict_seq`/`set_seq` (token substitution) — validating that the modeled assembly
== the real new-method output.

All imports in axiom_check.py are either the standard library or the repo's own
public `sympy` API (`srepr`, `Symbol`) — the same surface the gold patch and the
F2P test exercise; nothing private is depended upon.
