# mapping.md — psf__requests-1724

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1ba83c47ce7b177efe90d5f51f7760680f72eda0`, states the type
abstraction, and gives the provenance of each modeled callee (source + the exact
behaviour the model encodes).

Repo file under change: `requests/sessions.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `normalizeMethod (text, native)` | the method-handling step of `Session.request` — `requests/sessions.py:278` (body at `req = Request(method = method.upper(), …)`) | the modeled behaviour: the method carried into the constructed request |
| `flavour :| flavour = true` *(imperative-callee stub — A-consumed)* | `builtin_str` — `requests/compat.py:95` (py2) / `:111` (py3); invoked at the construction site immediately before `.upper()` | unchanged native-text-flavour constructor applied to the supplied method before any further processing |
| `upperCp` / `upperSeq` *(deep model — A-reference)* | `str.upper` — CPython builtin, called as `method.upper()` | pure spec: case-normalisation as a per-code-point ASCII upper map; the deep model of the **unchanged** `str.upper`, validated `upperSeq == str.upper` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `TextToken (chars, native)` | the text value of `method`, and the `method` field of the constructed `Request` (`requests/models.py` `Request.method`) | minimal carrier of the two touched aspects of a text value: code-point content + native flavour |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a text value (`method`: a `str` on py3, a `str`/`unicode` on py2) | `TextToken` = (`chars : List Char` of code points, `native : Bool`) | `s[k]` ↔ `chars[k]`; `len(s)` ↔ `chars.length`; the byte-`str`/native flavour ↔ `native = true`; the `unicode`/non-native flavour ↔ `native = false` |
| `Request(method = …, url = …, …)` constructor | projection onto the `method` field only | the change touches only `method`; every other `Request` argument (`url`, `headers`, `files`, `data`, `params`, `auth`, `cookies`, `hooks`) is forwarded unchanged and is irrelevant to the tested behaviour, so it is omitted from the model. |

Lean `List Char` indexing is total and sound, so the content carrier is
`List Char` directly. The flavour aspect (native vs. non-native) cannot be
expressed by code points alone — it is the *kind* of the text object — so it is
carried as an explicit `Bool` field on `TextToken`. This is the precise aspect
the change concerns (directive 5: `text` and `native` are read-only — neither is
`mut`; the result is a freshly-constructed `TextToken`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 native-flavour stub ↔ `builtin_str` (A-consumed)
**Callee:** `requests.compat.builtin_str`. In `requests/compat.py` the name is
bound to the native string constructor **before** the module rebinds the public
`str` name:

```python
if is_py2:
    builtin_str = str          # the byte-str constructor
    bytes = str
    str = unicode              # public str is now unicode
    ...
elif is_py3:
    builtin_str = str          # py3: builtin_str IS str
    str = str
    ...
```

So `builtin_str(method)` always produces a value of the **native** text
flavour — a byte-`str` on py2 (the flavour the HTTP header assembly requires),
the ordinary `str` on py3 — independent of whether `method` was a `unicode`
(py2) or any other object. The stub (`flavour :| flavour = true`) encodes only
the single property the proof consumes: the produced value IS native. It does
**not** claim character preservation (not needed — the content fold operates on
the original `text`, which the constructor leaves unchanged for the ASCII method
names the tests use) and does **not** claim anything stronger. This is the
**weakest** contract the flavour postcondition needs.

**Soundness check (G-AX):** `axiom_check.py` imports the real
`requests.compat.builtin_str` and asserts `type(builtin_str(v)) is str` (the
native flavour on the running interpreter) for native, bytes, and non-native
arguments. On the Python-2 runtime the issue reports, `builtin_str` is the
byte-`str` constructor, so the produced value is byte-`str` (native), never
`unicode` — which is exactly the behaviour the fix relies on.

### 3.2 `upperSeq` deep model ↔ `str.upper` (A-reference)
**Callee:** CPython `str.upper`, invoked as `method.upper()`. The
case-normalisation is **unchanged** (the change only inserts the native coercion
*before* it); it is modelled **deeply** by the front-recursive fold `upperSeq`
(with `upperCp`) in the `pure` region — there is **no `upper` axiom** the proof
consumes. The deep model is validated equal to the real callee out-of-band by
axiom_check.py (G-AX). On the ASCII domain that HTTP method names inhabit (code
points 0–127), `str.upper` is exactly:

  `'a'..'z' (97..122) → 'A'..'Z' (65..90)`, every other code point unchanged,

which is what `upperCp` / `upperSeq` encode. G-AX asserts
`upperSeq(s) == str.upper(s)` over all 128 ASCII code points (exhaustive
single-character sweep), the ten HTTP method names, and 20 000 randomized ASCII
strings — 0 mismatch. (The model claims faithfulness only on this ASCII method
domain; full-Unicode `str.upper` has locale/multi-char expansions outside it,
which the tested method names never exercise.) Docs:
https://docs.python.org/3/library/stdtypes.html#str.upper.

## 4. Conformance (G-CONF) seed
The R/I legs (content fold + length) are differential-tested in
`conformance_check.py` against the patched behaviour with a pinned seed (1724).
