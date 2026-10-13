# mapping.md — sympy__sympy-15976

## Instance
- repo: sympy/sympy
- base_commit: 701441853569d370506514083b995d11f9a130bd
- modeled file: `sympy/printing/mathml.py`
- modeled function: `MathMLPresentationPrinter._print_Symbol(self, sym, style='plain')`
  at `sympy/printing/mathml.py:745-805 @ base_commit` (the presentation-printer
  variant; the *content* printer `_print_Symbol` at line 335 is untouched).

## What the modeled function computes
Given a symbol it produces a MathML *presentation* markup tree. The symbol name
is first decomposed (by an unchanged upstream helper) into a base `name` plus a
list of superscript strings and a list of subscript strings, each mapped through
an unchanged unicode-translation step. The changed code then **assembles the
markup tree** from those three pieces and the `style` flag. The assembly is the
only thing the gold patch changes.

### Lean ↔ Python type bijection (used by G-CONF / G-AX)
| Python | Lean | note |
|---|---|---|
| the decomposed base name `name : str` | `name : String` | output of `split_super_sub` + `translate`, an INPUT to the modeled boundary |
| `supers : list[str]` | `supers : List String` | superscript pieces, post-translate |
| `subs : list[str]` | `subs : list[str]` → `subs : List String` | subscript pieces, post-translate |
| `style : str` (`'plain'`/`'bold'`) | `style : String` | rendering flag (mat_symbol_style for MatrixSymbol) |
| a `minidom` Element / Text node | `MathNode` (`elem tag attrs children` / `text value`) | `nodeName`=tag, `childNodes`=children, `nodeValue`=text; `attrs : List (String×String)` carries `mathvariant` |
| `el.nodeName` | tag string | |
| `el.childNodes` | `children` | order-significant |
| `txt.nodeValue` | `text` value | |
| `el.setAttribute('mathvariant','bold')` | append `("mathvariant","bold")` to attrs | |

### The four structural cases (post-patch, the desired behavior)
With `mname := <mi>name</mi>`:
- no supers, no subs → result is `mname` itself (a bare `<mi>`).
- no supers, some subs → `<msub>[mname, join(subs)]`.
- some supers, no subs → `<msup>[mname, join(supers)]`.
- some supers, some subs → `<msubsup>[mname, join(subs), join(supers)]`.
Then, if `style == 'bold'`, the `mathvariant="bold"` attribute is set on the
resulting top element.

`join(items)`: a single item renders as `<mi>item</mi>`; several items render as
`<mrow>` containing the item `<mi>`s separated by `<mo> </mo>` spacer elements.
(`join` is a local helper, unchanged by the patch — modeled deeply, R/I.)

### Pre-patch (buggy) behavior
The pre-patch code always allocated an outer `<mi>` element, set `mathvariant`
on it up front, and *appended* the scripted element (or a bare name text node)
as its child — i.e. every result was wrapped in an extra `<mi>…</mi>`. For a
symbol carrying scripts this produced `<mi><msub>…</msub></mi>`, which the F2P
test (`test_presentation_symbol`) rejects: it expects `mml.nodeName == 'msub'`
(etc.), not `'mi'` with a scripted child.

## Callees (provenance)
- `split_super_sub` (`sympy/printing/conventions.py:14`) — UNCHANGED. Decomposes
  the symbol name into `(name, supers, subs)`. It is an **upstream input
  provider**: its output constitutes the modeled inputs. Not consumed in the
  proof, not axiomatized.
- `translate` / `greek_unicode` (`sympy/printing/pretty/pretty_symbology.py`) —
  UNCHANGED per-piece unicode map, also an upstream input provider.
- `self.dom.createElement` / `createTextNode` / `appendChild` / `setAttribute`
  (minidom) — UNCHANGED DOM constructors; modeled directly by the `MathNode`
  constructors (R/I, the type bijection above). Not axiomatized.
- The local `join` closure — UNCHANGED, modeled deeply (R/I).

There are **no consumed-axiom callees and no A-reference callees**: the impl is
all R/I, so `axiom_check.py` is a skip stub and `conf_skip = false`.

## G-CONF fuzz seed
Pinned seed: **15976** (also in conformance_check.py and meta.json).
