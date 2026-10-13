# mapping.md — sympy__sympy-23262

Binds every `model.py` symbol to its repository counterpart at
`base_commit = fdc707f73a65a429935c01532cd3970d3355eab6`, states the type
abstraction, and gives the provenance of the deep-model A-references (the real
Python operations the deep model is validated against by G-AX). There are no
`@ContractOnly` axioms.

Repo file under change: `sympy/utilities/lambdify.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_container(elems, is_paren)` | the iterable branch of `_recursive_to_string(doprint, arg)` — `sympy/utilities/lambdify.py:948` (body lines 957–964) | the modeled changed function: the container-literal serialiser |
| `left_delim(is_paren)` / `right_delim(is_paren)` | `left, right = "(", ",)"` (tuple) / `left, right = "[", "]"` (list) — `lambdify.py:961` / `:959` (post-patch) | pure spec: the container-kind delimiter pair |
| `joined(elems)` *(deep model — A-reference)* | `', '.join(_recursive_to_string(doprint, e) for e in arg)` — `lambdify.py:964` | pure spec: the `", "`-joined element body; deep model of Python's `str.join`, validated `joined == ", ".join` by axiom_check.py (G-AX) |
| `rendered(elems, is_paren)` *(deep model — A-reference)* | `left + ', '.join(...) + right` — `lambdify.py:964` (post-patch delimiters) | pure spec: the full container literal; deep model validated `== ` the real fixed-serialiser text (and re-parse arity) by axiom_check.py (G-AX) |
| `lparen/rparen/lbracket/rbracket/comma/sep` | the literal delimiter / separator characters `( ) [ ] ,` and `', '` | pure spec: delimiter and separator code points |

The pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): `left, right = "()"` (`lambdify.py:961`)
— the 2-character-string unpack that yields `right = ")"` (the lone closing
parenthesis, no trailing comma), the bug.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (each element's rendered source fragment, and the assembled literal) | `PSeq[int]` of Unicode code points | `s[k]` ↔ code point `ord(s[k])`; `len(s)` ↔ `len`; `str` `+` ↔ `PSeq` `+`; empty `str` ↔ empty `PSeq`. `str` indexing/iteration is banned in Nagini, so the carrier is `PSeq[int]`. |
| the recursively-rendered element fragments `[_recursive_to_string(doprint, e) for e in arg]` | `elems: PSeq[PSeq[int]]` (a pure sequence of code-point sequences) | the k-th element fragment ↔ `elems[k]`; arity ↔ `len(elems)`. The per-element recursion is UNCHANGED machinery, taken as given. |
| `isinstance(arg, tuple)` / `isinstance(arg, list)` kind test (`lambdify.py:958,960`) | `is_paren: bool` | `is_paren == True` ↔ `arg` is a `tuple` (parenthesis kind); `False` ↔ `arg` is a `list` (square-bracket kind). The `else: raise NotImplementedError` branch (other iterables) is outside the modeled domain — the F2P/issue concern only list and tuple. |

The specification is phrased over `PSeq[int]` / `PSeq[PSeq[int]]`, which carry no
heap permission, so no `Acc`/`list_pred` is required (directive 5 is satisfied
vacuously: there is no mutable heap input — pure sequences are immutable values).

**Termination (total correctness):** the real serialiser always answers —
assembling a finite container literal from finitely many fragments is a bounded
computation (`str.join` over a finite list plus two concatenations). The spec
carries `Requires(MustTerminate(2))` on `render_container` (consumed in the impl
loop by `Invariant(MustTerminate(i))`). Nagini is a partial-correctness verifier
by default, so without the obligation a diverging implementation would satisfy
every `Ensures` vacuously while sharing the spec.

## 3. Deep-model A-reference provenance (checked by G-AX / axiom_check.py)

### 3.1 `joined` deep model ↔ Python `str.join` (A-reference)
**Callee semantics:** `', '.join(...)` — the standard Python string join
(`lambdify.py:964`). The changed assembly operation models this DEEPLY by the
`@Pure` front-recursive fold `joined` (model.py pure region): element fragments
concatenated left-to-right with exactly one `', '` (`[44, 32]`) between adjacent
pairs, no separator before the first or after the last. There is **no
`@ContractOnly` axiom**; the deep model is validated equal to the real callee
out-of-band by axiom_check.py (G-AX), which asserts `joined(elems) == ", ".join`
on boundary + 40000 fuzz inputs.

### 3.2 `rendered` deep model ↔ the fixed serialiser text (A-reference)
**Callee semantics:** `left + ', '.join(...) + right` with the post-fix
delimiter pair (`lambdify.py:959,961,964`):
```
if isinstance(arg, list):
    left, right = "[", "]"
elif isinstance(arg, tuple):
    left, right = "(", ",)"
...
return left + ', '.join(_recursive_to_string(doprint, e) for e in arg) + right
```
The model encodes this as `rendered(elems, is_paren) == left_delim + joined +
right_delim`, with `right_delim(True) == PSeq(44, 41) == ",)"`. The
**parenthesis kind's trailing comma** is the single behavioural change: it makes
a one-element tuple's surface text `"(" + e + ",)"` re-parse (via
`ast.literal_eval`) to a one-element tuple rather than to the bare element `e`.

**Soundness check (G-AX):** `axiom_check.py` runs the real Python operations —
`", ".join` and the fixed `left + body + right` assembly — on boundary element
lists (incl. the 0- and 1-element cases), end-to-end witnesses matching the F2P
test (`(1,)` re-parses to `(1,)`; `(3, 2,)` to `(3, 2)`), and 40000 randomized
fuzz inputs (20000 join/assembly + 20000 integer-literal round-trips). It
asserts: (a) `joined == ", ".join`; (b) `rendered ==` the real fixed-serialiser
text with the required trailing comma before `')'`; (c) the re-parsed arity of
every (non-empty for the paren kind) container equals the input arity — in
particular a one-element parenthesis container re-parses to a 1-tuple. Exit 0
iff sound. It imports only the standard library (`ast`, `random`) — `", ".join`,
string `+`, and `ast.literal_eval` are Python itself, the same operations the
gold patch relies on; nothing repo-specific.

The empty-parenthesis case (`"(,)"`, a syntax error) is excluded from the
re-parse check: lambdify never serialises a zero-element tuple, and the issue +
gold fix concern the one-element-tuple regression only. The deep-model
structural check still covers the 0-element parenthesis container.
