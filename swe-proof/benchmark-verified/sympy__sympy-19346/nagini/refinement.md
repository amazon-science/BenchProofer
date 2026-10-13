# refinement.md — sympy__sympy-19346

The operation-by-operation correspondence between `model.py`'s implementation
(the `render_collection_codepoints` / `render_mapping_codepoints` impl regions,
the deep `set_seq`/`dict_seq`/`joined_*` models, and the live `elem_repr` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses the axiom's `Ensures`), **A-reference** (a deep
model / contrast callee validated against the real callee by axiom_check.py /
G-AX, NOT consumed), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The unordered-collection site — `_print_set` (`sympy/printing/repr.py`)

Gold hunk (added method):
```python
def _print_set(self, expr):
    if not expr:
        return "set()"
    return "{%s}" % self.reprify(expr, ", ")
```
`reprify(args, sep)` (`repr.py:27-31`) is `sep.join([self.doprint(item) for item in args])`.

| # | model.py impl op (`render_collection_codepoints`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elems: List[int]` | `expr` (a `set`) iterated by `reprify`'s comprehension | R | one `set` ↔ `List[int]` of element tokens (mapping.md §2); iteration order is the only structural data and is preserved. |
| A2 | `if len(elems) == 0: return [115,101,116,40,41]` | `if not expr: return "set()"` | R + I | empty test ↔ `not expr`; the literal `"set()"` ↔ its five code points (mapping.md §2). |
| A3 | `piece = doprint_elem(elt)` per element | `self.doprint(item)` per item | A-consumed | the recursive srepr routine is the unchanged callee `doprint`. The proof consumes ONLY the value link `ToSeq(piece) == elem_repr(elt)` to discharge the join; `elem_repr` is wholly uninterpreted (`Ensures(True)`) and no property of it — in particular no non-emptiness — is assumed, because the real routine does render some elements as the empty string (mapping.md §3.1). G-AX runs the real `doprint` and witnesses that empty class. |
| A4 | the backward loop assembling `inner = piece + [COMMA,SPACE] + inner` (no separator after the last) so `ToSeq(inner) == joined_elems(...)` | `", ".join([... for item in args])` | R + I | `sep.join` ↔ comma-space between consecutive renderings, none trailing (mapping.md §2); the deep `joined_elems` fold spells out exactly that. |
| A5 | `result = [LBRACE] + inner + [RBRACE]` | `"{%s}" % ...` | R + I | brace wrap ↔ `123, ..., 125`. |

## B. The associative-mapping site — `_print_dict` (`sympy/printing/repr.py`)

Gold hunk (added method):
```python
def _print_dict(self, expr):
    sep = ", "
    dict_kvs = ["%s: %s" % (self.doprint(key), self.doprint(value)) for key, value in expr.items()]
    return "{%s}" % sep.join(dict_kvs)
```

| # | model.py impl op (`render_mapping_codepoints`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | parameter `flat: List[int]`, even length, positions `2j,2j+1` = key,value | `expr.items()` (ordered `(key, value)` pairs) | R | one `dict` ↔ flat even-length token list; `items()` order + pairing preserved (mapping.md §2). The flat carrier avoids nested `list_pred` (Nagini timeout risk). |
| B2 | `if len(flat) == 0: return [LBRACE,RBRACE]` | `expr.items()` empty ⇒ `sep.join([]) == ""` ⇒ `"{}"` | R + I | empty mapping ↔ `"{}"` = `123,125` (mapping.md §2). |
| B3 | `piece = doprint_elem(key) + [COLON,SPACE] + doprint_elem(val)` | `"%s: %s" % (self.doprint(key), self.doprint(value))` | A-consumed + I | both `%s` are the recursive srepr routine (A-consumed, as A3); the literal `": "` ↔ `58, 32` (I). |
| B4 | the backward loop assembling `inner = piece + [COMMA,SPACE] + inner` so `ToSeq(inner) == joined_pairs(...)` | `sep.join(dict_kvs)` with `sep = ", "` | R + I | comma-space between consecutive pair renderings, none trailing; `joined_pairs` spells it out. |
| B5 | `result = [LBRACE] + inner + [RBRACE]` | `"{%s}" % ...` | R + I | brace wrap. |

## C. The discriminator and the prepatch (G-DIFF)

The single behavioural change is that each element / key / value is rendered by
the **recursive executable representation** (`self.doprint(...)`, i.e.
`elem_repr`/`doprint_elem`) rather than by the whole-object **plain display
form** that the pre-patch fallback uses (`emptyPrinter` → `str(expr)`, which
renders each element via `str`, i.e. `elem_str`/`str_elem`). `elem_str` is a
**separate uninterpreted callee** from `elem_repr` — the spec assumes NO relation
between them. (It does NOT carry a universal `Ensures(elem_repr(t) != Result())`
nor `len(elem_str) >= 1`: the real callee relationship `str != srepr` is
**existential**, false on the constant/singleton class — e.g.
`str(oo) == srepr(oo) == 'oo'` — and `str(Symbol('')) == ''`, so a universal
inequality or non-empty claim would be unsound, mapping.md §3.2. Symmetrically
`elem_repr` carries no `len >= 1` either — the real routine returns the empty
string for some element classes, mapping.md §3.1.)

How the rejection is REPORTED, precisely (the shipped state): `str_elem` carries
no `Requires(MustTerminate(...))` while the rendering functions hold
`MustTerminate(3)`, so a `str_elem`-based rival is rejected with an
*obligation-leak* error at the call site (`model_prepatch.py:200` set,
`:260` dict) rather than with the fold-invariant error. The semantic
discriminator underneath is real and was measured separately: with
`Requires(MustTerminate(2))` added to `str_elem` in a scratch copy, the prepatch
fails exactly the two fold invariants named below. That strengthening is not
shipped because it pushes the single-leg `str_elem` battery cases past the
verifier budget (`wrong-str-elem-set`: no convergence in 1200s with it, 27s
rejection without), and a timeout is not a sound rejection signal.

`model_prepatch.py` reproduces the pre-patch behaviour: the same brace/separator
assembly, but each `piece` built from `str_elem` instead of `doprint_elem`. It
shares the spec byte-identically (G-DIFF `same_spec` = True) and **fails** the
loop invariants `ToSeq(inner) == joined_elems(elems_s.drop(i))` (set,
model_prepatch.py:197) and `ToSeq(inner) == joined_pairs(flat_s.drop(i))` (dict,
model_prepatch.py:254) — reported as the obligation-leak error noted above —
because
the assembled `inner` is built from `elem_str`, and `elem_str`/`elem_repr` are
**distinct uninterpreted functions** that Nagini cannot prove equal, so the
`str_elem`-built `inner` can never be shown to equal the `elem_repr`-built fold.
(This discriminator is sound WITHOUT any universal inequality and without any
non-emptiness claim on either callee — it rests only on the open-world
distinctness of two separately-declared `@ContractOnly` callees; verified
empirically: with `str_elem` made callable in a scratch copy, the prepatch fails
exactly these two semantic fold invariants, and it still does so with `elem_repr`
fully uninterpreted.) The spec senses the bug on BOTH the set and the
dict behaviour (one prepatch covers both independently-observable behaviours; the
graded F2P is `test_dict`).

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — the existence of a dedicated container renderer that routes each
element through the recursive srepr routine instead of the whole-object `str`
fallback — is modeled **deeply**: the brace/separator/empty-literal assembly is
spelled out (`set_seq`/`dict_seq`/`joined_elems`/`joined_pairs` + the verified
loops), and the per-element recursion is the **unchanged** callee `doprint`
(`elem_repr`, A-consumed). There is no axiom about the function under
specification; `elem_str` (the pre-patch `str` per element) is the
**A-reference** contrast — a separate uninterpreted callee that G-AX validates is
**existentially** distinct from `srepr` (str≠srepr on the discriminating class,
str==srepr on the constant class), never universally. Neither per-element callee
carries any length or content constraint: the only consumed fact is
`doprint_elem`'s value link `ToSeq(Result()) == elem_repr(t)`.

## E. verify(model) ⇒ resolved

`render_collection_codepoints` / `render_mapping_codepoints` verify only if the output is
the exact brace-wrapped, comma-space-joined sequence of per-element/per-pair
recursive representations with the correct `set()`/`{}` empty literals and the
`": "` pair separator (clauses A2–A5, B2–B5), and only if each rendering is the
recursive `elem_repr` rather than the plain `elem_str` (the prepatch fails
exactly here). By R (str ↔ List[int], `set`/`dict` ↔ token carriers, the
literal punctuation bijections) the verified renderers equal the gold
`_print_set`/`_print_dict` on the tested inputs; by G-AX the deep model
`set_seq`/`dict_seq` equals the real new-method output and `doprint`/`str` meet
their axioms. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and audited callees — and the gold patch
resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1: axiom
soundness (G-AX) and refinement fidelity (this document, G-EQ).
