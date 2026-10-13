# mapping.md — sphinx-doc__sphinx-9230

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 567ff22716ac258b9edd2c1711d766b440ac0b11`, states the type
abstraction, and gives the provenance of the deep-model reference.

Repo file under change: `sphinx/util/docfields.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `parsed_argument_name(tokens)` | the `argname` produced by `argtype, argname = fieldarg.split(None, 1)` inside `DocFieldTransformer.transform` (`sphinx/util/docfields.py:301`), consumed at `:305` (dict key) and `:307` (`fieldarg = argname`) | modeled changed behaviour: the parsed parameter NAME |
| `parsed_argument_type(tokens)` | the `argtype` produced by the same split (`:301`), consumed at `:305-306` (`[nodes.Text(argtype)]`, the type text) | modeled changed behaviour: the parsed TYPE text |
| `joined(run)` *(deep model — A-reference, single-space domain)* | the type side of `str.rsplit(sep=None, maxsplit=1)`: the leading-token run re-emitted separated by single spaces (CPython semantics) | pure spec: single-space-separated rendering of a token run; validated `joined == real str.rsplit type side` **on single-space-separated input** by axiom_check.py (G-AX), NOT a consumed axiom |
| `last_token(run)` | the LAST whitespace token of `fieldarg` (the second element of `fieldarg.rsplit(None, 1)`) | pure spec: the final token of a run |
| `encode_name(t)` | identity on a token's text — a tagging that keeps a token disjoint from the separating space code point in a rendered type | pure spec helper (token-vs-separator disjointness) |
| `empty_seq()` | the empty string | pure spec helper |

The changed line (the entire gold patch):

```
-                    argtype, argname = fieldarg.split(None, 1)
+                    argtype, argname = fieldarg.rsplit(None, 1)
```

`fieldarg` is the whitespace-separated text of a typed field argument, e.g.
`":param dict(str, str) opc_meta:"` yields `fieldarg = "dict(str, str) opc_meta"`.
`split(None, 1)` splits at the FIRST whitespace boundary (type = first token,
name = remainder); `rsplit(None, 1)` splits at the LAST (type = leading tokens,
name = last token). The `maxsplit=1` means exactly one split, and `sep=None`
means runs of whitespace are the delimiter and leading/trailing whitespace is
stripped; the unpacking into two names raises `ValueError` iff there are fewer
than two whitespace tokens.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `fieldarg: str` (a typed field argument) | `tokens: List[int]` — the sequence of its maximal whitespace-free runs, one distinct `int` token per run | the k-th whitespace token of `fieldarg` ↔ `tokens[k]`; the number of whitespace tokens ↔ `len(tokens)` |
| a token's text (`str`) | one `int >= 0` | each whitespace-free run is reproduced verbatim downstream (it becomes a `nodes.Text` / dict key), so its internal spelling is irrelevant to the parse structure and is abstracted to a single distinct symbol |
| `argname: str` (the parsed name) | `List[int]` (a one-token rendering in the correct case) | `argname` ↔ the single token `tokens[n-1]` (its text ↔ `encode_name(tokens[n-1])` under the token bijection) |
| `argtype: str` (the parsed type) | `List[int]` (the leading tokens rejoined) | `argtype` ↔ the leading `n-1` tokens joined by single spaces ↔ `joined(tokens.take(n-1))` |
| whitespace separator (a run of whitespace) | a single `SPACE` (32) in a rejoined type | the F2P input uses single-space separators, so the single-space rejoin reproduces the original `argtype` substring exactly (e.g. `"dict(str, str)"`); axiom_check.py drives the real callee on single-space-joined runs (the abstraction's image) |

`str` indexing/iteration is banned in Nagini, so the argument is carried as the
`List[int]` of its tokens; the specification is phrased over `PSeq[int]` via
`ToSeq`.

### Modelled domain

The parse is modelled for `len(tokens) >= 2` — exactly the case where the
`split`/`rsplit` unpacking succeeds (≥ 2 whitespace tokens) and is therefore the
ONLY case where the gold one-liner changes behaviour. For `len(tokens) < 2`
both `str.split(None, 1)` and `str.rsplit(None, 1)` raise `ValueError` on the
2-tuple unpacking, the `except ValueError: pass` runs, and `fieldarg` is left
untouched — identical pre- and post-patch (verified by
`check_valueerror_path_unchanged` in axiom_check.py). That unchanged path needs
no model and no prepatch.

## 3. Callee provenance (A-reference — checked by G-AX / axiom_check.py)

### 3.1 `joined` / `last_token` ↔ `str.rsplit(None, 1)` (A-reference, single-space domain)
**Callee:** CPython `str.rsplit(sep=None, maxsplit=1)` (and, for the bug,
`str.split(sep=None, maxsplit=1)`). With `sep=None` Python splits on runs of
whitespace and discards leading/trailing whitespace; with `maxsplit=1` it
performs a single split and keeps the remainder (including its internal
whitespace, **verbatim**) as the other piece. Docs:
https://docs.python.org/3/library/stdtypes.html#str.rsplit ,
https://docs.python.org/3/library/stdtypes.html#str.split .

The changed string operation is modelled **deeply**: the `@Pure` fold `joined`
(the leading-token run re-emitted separated by single spaces) plus the verified
construction loop in `parsed_argument_type` ARE the type side, and `last_token`
is the name side. There is **no `@ContractOnly` axiom** the proof consumes.

**Modelled-domain restriction (load-bearing).** The model abstracts each
maximal whitespace-free chunk to one token AND collapses every inter-token
separator to a single space (§2). Its type side (`joined`) therefore equals the
real `str.rsplit(None, 1)` type side **only when the input is
single-space-separated** — i.e. canonical `" ".join(tokens)` with no leading /
trailing / internal multi-whitespace. On genuine multi-whitespace input (e.g.
`'dict(str,  str) opc_meta'` with a double space, or leading whitespace, or a
tab) the real left piece is preserved verbatim while the model rejoins with a
single space, so the model legitimately diverges and that input is **out of the
modelled domain**. The name side (`last_token`) is separator-insensitive and
matches the real `argname` on all inputs. The A-reference claim is thus stated
**conditionally on single-space-separated input** — which is exactly the form
every F2P/P2P field argument in `tests/test_domain_py.py` takes (e.g.
`Dict[str, str] params`, `int age`, `Tuple[str, ...] items`).

**Soundness check (G-AX), de-rigged.** `axiom_check.py` fuzzes the REAL callee's
NATIVE input domain — arbitrary whitespace separators (multi-space, tabs,
leading/trailing), NOT only the abstraction's own `" ".join` image — over 7
single-space boundary forms (incl. the issue's `dict(str, str) opc_meta` and the
F2P `Dict[str, str] params`), 4 tested-fieldarg representatives, and 20 000
randomized 2..6-token runs joined with random separators. It then routes each
input by domain:
  * **in-domain (single-space):** asserts `(joined(take(n-1)), last_token)` ==
    real `(argtype, argname)`;
  * **excluded (multi-whitespace):** asserts the model is out-of-domain exactly
    per the documented restriction — the name side still matches, and the type
    side matches IFF the real left piece is already single-space-collapsed,
    otherwise it legitimately diverges (demonstrated on explicit double-space /
    leading-whitespace / tab witnesses, with a real divergence required to be
    witnessed) — so the restriction is VERIFIED, not dodged.
It also asserts the OLD `str.split(None, 1)` disagrees for every multi-token
type (`n >= 3`) — keeping only the first token as the type — which is exactly the
reported bug, and that the `< 2`-token path raises `ValueError` identically for
both. It imports only the standard library (`str` is built in — the very type
the patch calls `.rsplit` on); nothing repo-specific. Exit 0 iff sound.
