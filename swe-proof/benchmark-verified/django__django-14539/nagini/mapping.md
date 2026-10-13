# mapping.md — django__django-14539

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 6a5ef557f80a8eb6a758ebe99c8bb477ca47459e`, states the type
abstraction, and gives the provenance of the unchanged callees.

Repo file under change: `django/utils/html.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `trim_trailing_punct(middle, trail, decoded_len, kept_len)` | the trailing-punctuation trim block inside `urlize.trim_punctuation(lead, middle, trail)` — `django/utils/html.py:280-288` (the three changed lines are 286-287 → the patched 286-288) | the modeled changed operation: moving trailing punctuation off the end of `middle` onto the front of `trail` |
| `decoded_len` (int parameter) | `len(html.unescape(middle))` — `middle_unescaped` at `django/utils/html.py:283` | observable output #1 of the unchanged decode callee: length of the decoded central part |
| `kept_len` (int parameter) | `len(html.unescape(middle).rstrip(TRAILING_PUNCTUATION_CHARS))` — `stripped` at `django/utils/html.py:284` | observable output #2 of the unchanged decode+strip callees: decoded length after dropping trailing punctuation |
| `middle` (`List[int]`) | `middle` (`str`) — local of `trim_punctuation` | the ENCODED central part of the word |
| `trail` (`List[int]`) | `trail` (`str`) — local of `trim_punctuation` | the trailing part accumulated so far |

`TRAILING_PUNCTUATION_CHARS = '.,:;!'` is a module constant
(`django/utils/html.py:19`); it parameterises the unchanged `rstrip` callee and
is therefore folded into the `kept_len` value, not modeled symbolically.

The guard `if middle_unescaped != stripped:` (`html.py:285`) is exactly
`kept_len < decoded_len` (rstrip removed at least one character); it is the
model's `Requires(kept_len < decoded_len)`, since the modeled block is the body
of that `if`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (`middle`, `trail`) | `List[int]` of Unicode code points | `s[k]` ↔ `cp[k] == ord(s[k])`; `len(s)` ↔ `len(cp)`; `str` slice `s[a:b]` ↔ list slice `cp[a:b]` (Nagini translates to `ToSeq.take/.drop`); `str` `+` ↔ list `+`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` | `ToSeq(list)` materialises the list as a `PSeq`; `take`/`drop`/`len`/`+` mirror `str` slice/`len`/`+` |
| `middle[-punctuation_count:]` (Python negative slice) | `middle[split:]` with `split = len(middle) - punctuation_count` (`ToSeq(middle).drop(split)`) | for `0 < punctuation_count <= len(middle)`, Python `s[-k:]` == `s[len(s)-k:]`; the model uses the equivalent non-negative form. |
| `middle[:-punctuation_count]` | `middle[:split]` (`ToSeq(middle).take(split)`) | likewise `s[:-k]` == `s[:len(s)-k]` for `0 < k <= len(s)`. |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; slicing translates to `PSeq` `take`/`drop` (probed: a list slice
`xs[:k]` / `xs[k:]` verifies against `ToSeq(xs).take(k)` / `.drop(k)`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

There is **no consumed `@ContractOnly` axiom**: the changed operation (the
slicing) is modeled deeply and the unchanged callees enter the model only
through two integer summaries.

### 3.1 The decode + strip callees → `decoded_len`, `kept_len` (A-reference)
**Callees:** CPython `html.unescape(middle)` (the stdlib HTML entity decoder,
`Lib/html/__init__.py`, `_charref.sub(_replace_charref, s)` + named-entity
expansion; docs: https://docs.python.org/3/library/html.html#html.unescape) and
`str.rstrip(TRAILING_PUNCTUATION_CHARS)`. Neither is changed by the patch; the
patch only changes how their *length outputs* are used to slice `middle`.

The model summarises them by the two integers they feed into the slice
arithmetic:

  `decoded_len = len(html.unescape(middle))`,
  `kept_len    = len(html.unescape(middle).rstrip('.,:;!'))`,

and relies only on the relationship the slice arithmetic needs:

  `0 <= decoded_len <= len(middle)`   — decoding never lengthens a string
  (every entity it expands, e.g. `&lt;` → `<`, is *replaced by a shorter or
  equal* run; the worst case `&` → `&` is length-preserving), and
  `0 <= kept_len <= decoded_len`      — `rstrip` only removes characters.

These bounds make `punctuation_count = decoded_len - kept_len` satisfy
`0 < punctuation_count <= len(middle)`, so both slices `middle[split:]` and
`middle[:split]` are in range. The model does NOT assume any exact value of
`decoded_len`/`kept_len`, only the bounds — the weakest facts the proof needs.

**Soundness check (G-AX):** `axiom_check.py` runs the real `html.unescape` +
`rstrip` on the issue example, on entity-bearing boundary middles (where the
encoded form is strictly longer than the decoded form — exactly the inputs the
bug mishandled), on plain trailing-punctuation cases, and on 50 000 randomized
fuzz inputs built from text + the six common entities + the trailing-punct
characters. It asserts (a) the two bounds hold on every input, and (b) feeding
the real callee outputs into the model's deep slicing reproduces the GOLD
patched block's `(middle, trail)` result exactly, while (c) on entity-bearing
inputs the result differs from the PRE-FIX block — so the spec genuinely
discriminates the bug. Imports only the standard-library `html` module (the
very module the patched code calls). Exit 0 iff sound.
