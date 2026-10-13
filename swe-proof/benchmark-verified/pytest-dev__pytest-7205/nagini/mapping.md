# mapping.md — pytest-dev__pytest-7205

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5e7f1ab4bf58e473e5d7f878eb2b499d7deabd29`, states the type
abstraction, and gives the provenance of the deep-model reference (the
size-limited representation helper the change switches to).

Repo file under change: `src/_pytest/setuponly.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `render_param_token(param, maxsize)` | the bracketed parameter rendering inside `_show_fixture_action(fixturedef, msg)` — `src/_pytest/setuponly.py:46` (changed line 69) | the modeled changed behaviour: producing the text shown between `[` and `]` for the recorded fixture parameter |
| `repr_quote(s)` *(deep model — A-reference)* | `saferepr(obj, maxsize=...)` — `src/_pytest/_io/saferepr.py:75` (newly imported and called at `setuponly.py:69` post-patch) | pure spec: the size-limited programmer's representation of a short, plainly-printable text value (apostrophe-delimited verbatim text); the deep model of the helper the change calls, validated `repr_quote == saferepr(_, maxsize=42)` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `QUOTE` (`= 39`) | the apostrophe `'` (U+0027) that `repr` of a plain string emits as its delimiter | pure spec: the delimiter code point |

The pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): the format expression
`"[{}]".format(fixturedef.cached_param)` (`setuponly.py:69`), whose `{}` field
applies an implicit `str(...)` to the recorded parameter. The gold patch adds
`from _pytest._io.saferepr import saferepr` (`setuponly.py:2`) and rewrites line
69 to `"[{}]".format(saferepr(fixturedef.cached_param, maxsize=42))`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the recorded parameter value `fixturedef.cached_param` (a `str` in the tested domain — the fixture `params`/`ids` strings) | `param: List[int]` of Unicode code points | `s[k]` ↔ `param[k] == ord(s[k])`; `len(s)` ↔ `len(param)`; empty `str` ↔ `[]` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| the `maxsize` argument (the gold passes the literal `42`) | `maxsize: int` | identical integer |
| the surrounding `"[{}]".format(...)` brackets | omitted (constant `[` / `]` framing) | the brackets are emitted identically pre- and post-patch by `tw.write`; the only changed content is the token between them, which `render_param_token` models |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout and the specification is phrased over `PSeq[int]` via `ToSeq`.

### The tested domain (model `Requires`)
The F2P parametrized-fixture tests use simple text parameter values and ids
(`foo`, `bar`, `spam`, `ham`, and the upper-cased `FOO`, `BAR`). The model's
precondition pins exactly the domain on which the size-limited representation is
the verbatim text wrapped in apostrophes (no escaping, no elision):
`maxsize >= 2`, `len(param) + 2 <= maxsize`, and every code point is plainly
printable ASCII (`32..126`) other than the apostrophe delimiter (`39`) or
backslash (`92`). On that domain `saferepr(s, maxsize=42)` is exactly
`"'" + s + "'"` (§3).

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### `repr_quote` deep model ↔ `saferepr(obj, maxsize=42)` (A-reference)
**Callee:** pytest's `saferepr(obj, maxsize=240)` (`src/_pytest/_io/saferepr.py:75`),
which the gold patch calls with `maxsize=42`. It is
`SafeRepr(maxsize).repr(obj)`: a `reprlib.Repr` subclass whose `.repr` computes
`repr(obj)` (guarding against a failing `__repr__`) and then `_ellipsize`s the
result to at most `maxsize` characters (`saferepr.py:27-31,45-61`).

For a Python `str` `s`, `repr(s)` returns `s` surrounded by `'` delimiters,
**verbatim and unescaped**, whenever `s` contains no apostrophe (so the
delimiter does not flip to `"`), no backslash, and no non-printable character
(so no `\x..`/`\t`/`\n` escape is introduced). For such an `s` shorter than
`maxsize - 2`, `_ellipsize` is the identity. Hence on the model's tested domain

    saferepr(s, maxsize=42)  ==  "'" + s + "'"

which is exactly what `repr_quote(ToSeq(param)) == PSeq(39) + ToSeq(param) + PSeq(39)`
encodes. The genuinely-changed operation (render the parameter through this
helper, not through the implicit `str()`) is therefore modeled **deeply**;
there is **no consumed axiom**. G-AX (`axiom_check.py`) validates the deep model
against the real callee.

**Length bound.** Independently of the domain restriction, `saferepr(_, 42)`
never returns more than 42 characters (its whole purpose: `_ellipsize` clamps to
`maxsize`). The model's `Ensures(len(Result()) <= maxsize)` reflects this; on the
tested domain it follows from `len(param) + 2 <= maxsize`.

**The discriminating behaviour vs. the bug.** The pre-patch line applied an
implicit `str(param)`, yielding the bare text `s` (no delimiters) — and, on a
`bytes` parameter under `python -bb`, raising `BytesWarning: str() on a bytes
instance` (the reported crash). The new helper uses `repr`, which (a) wraps a
string in apostrophe delimiters — observed by the F2P trace tests as
`arg_same['foo']` rather than `arg_same[foo]` — and (b) renders `bytes` via
`repr(b'...')` without ever invoking `str()` on the bytes, so it does not raise
under `-bb` (the F2P `test_show_fixture_action_with_bytes`).

**Soundness check (G-AX).** `axiom_check.py` runs the real `saferepr` on the six
F2P parameter ids plus boundary printable-ASCII strings and 20 000 randomized
in-domain fuzz strings, asserting `saferepr(s, 42) == "'" + s + "'"` code point
for code point and that the rendering differs from the bare text exactly by the
two surrounding apostrophes. It asserts the `<= 42` length bound on 5 000 long
inputs (including apostrophes, backslashes, control and non-ASCII characters,
where `saferepr` escapes and elides). Finally, in a fresh `python -bb`
subprocess — the exact configuration of the F2P bytes regression — it asserts
that `saferepr(b'...', 42)` does not raise while the pre-patch `"{}".format(b)`
DOES raise `BytesWarning`. It imports only `_pytest._io.saferepr` (the very
module the gold patch imports `saferepr` from) and the standard library. Exit 0
iff every obligation holds.
