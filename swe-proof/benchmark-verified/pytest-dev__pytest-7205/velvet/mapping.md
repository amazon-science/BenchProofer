# mapping.md — pytest-dev__pytest-7205

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 5e7f1ab4bf58e473e5d7f878eb2b499d7deabd29`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and gives
the provenance of the deep-model reference.

Repo file under change: `src/_pytest/setuponly.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `renderParameterDisplay (param : ParamValue)` | the bracketed-parameter rendering step of `_show_fixture_action(fixturedef, msg)` — `src/_pytest/setuponly.py:68-69` (`tw.write("[{}]".format(...))` under `if hasattr(fixturedef, "cached_param")`) | the modeled changed display step |
| `ParamValue` (`textVal` / `bytesVal`) | the runtime type of `fixturedef.cached_param` — `str` (text params/ids) or `bytes` (the F2P `b'Hello World'` case) | the two payload shapes the F2P observations distinguish |
| `quotedRepr : ParamValue → List Char` *(deep model — A-reference)* | `saferepr` — `src/_pytest/_io/saferepr.py:75` (`saferepr(obj, maxsize=240)`), called post-patch as `saferepr(fixturedef.cached_param, maxsize=42)` | pure spec: the size-limited safe representation of the parameter value on both shapes; deep model of the unchanged callee `saferepr`, validated `quotedRepr == saferepr(·, maxsize=42)` over the `simpleParam` domain by axiom_check.py (G-AX), NOT consumed as an axiom |
| `bracket (s : List Char)` | the `"[{}]".format(...)` square-bracket wrapping (`setuponly.py:69`, both pre- and post-patch) | pure spec: wrap a rendered token in `[` … `]` (unchanged) |
| `simpleParam : ParamValue → Prop`, `simpleChars` | the F2P parameter-value/id domain (short printable text and short printable ASCII byte-strings — see §3.1) | precondition: the domain on which the deep model is exact |

The pre-patch expression the change replaces (refinement audit only, not in the
consumer spec view): `"[{}]".format(fixturedef.cached_param)` — an implicit
`str(cached_param)` of the parameter value (`setuponly.py:69` pre-patch). On a
`str` it renders the bare characters; on a `bytes` value under `-bb` it raises
`BytesWarning` (the issue's crash).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `param = cached_param` when it is text (`str`) | `ParamValue.textVal s`, `s : List Char` | `s` (Python str) ↔ `s`-as-`List Char`; `len(s)` ↔ `s.length`; `str` concat ↔ `List` `++`; empty `str` ↔ `[]` |
| `param = cached_param` when it is a byte-string (`bytes`) of printable-ASCII bytes | `ParamValue.bytesVal s`, `s : List Char` | each byte `b` ↔ `Char.ofNat b` (total and exact on the ASCII range `simpleChars` allows); `bs.decode('ascii')` ↔ `s`; `len(bs)` ↔ `s.length` |
| the rendered token, a `str` | `List Char` | as for text above |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; `ord ch` ↔ `c.toNat`; on the BMP this is total and exact |
| the format literal `"[{}]".format(t)` (`setuponly.py:69`) | `bracket` (`'[' :: t ++ [']']`) | identity on the inserted token `t`; the two literal brackets ↔ the two `Char`s `'['`, `']'` |
| `str(text)` coercion implicit in the pre-patch `"[{}]".format` | identity on the text payload's `List Char`; **no total counterpart on the bytes payload** (it is a `-bb` error) | on `simpleChars` text values `str` is the identity; on a `bytes` value the coercion is the very defect under repair |

Lean `String`/`List Char` indexing is total and sound; the payload carrier is
`List Char` because the operation is per-code-point (per-byte) token rendering,
and the shape split lives in the `ParamValue` constructor.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `quotedRepr` deep model ↔ `saferepr(·, maxsize=42)` (A-reference)
**Callee:** the repo helper `saferepr(obj, maxsize)` (`src/_pytest/_io/saferepr.py`),
which the post-patch code calls as `saferepr(fixturedef.cached_param, maxsize=42)`.
For a text or bytes value `obj`, `saferepr` returns
`_ellipsize(SafeRepr(maxsize).repr(obj), maxsize)`, and `SafeRepr.repr` falls
back to `reprlib.Repr.repr_str` / `repr_instance` → `builtins.repr`.
`_ellipsize(s, maxsize)` truncates only when `len(s) > maxsize`.

The **`simpleParam` domain** is precisely where this safe representation reduces
to apostrophe-wrapping (plus the `b` prefix on the bytes shape) with no
truncation:

- `textVal s`, `len(s) ≤ 40` ⇒ `len(repr(s)) = len(s) + 2 ≤ 42 = maxsize`, so
  `_ellipsize` returns the string unchanged (no `"..."` marker).
- `bytesVal s`, `len(s) ≤ 39` ⇒ `len(repr(bs)) = len(s) + 3 ≤ 42 = maxsize`
  (the extra `b` prefix), so again no `"..."` marker.
- every code point is printable ASCII in `32..126`, and excludes the apostrophe
  `'` (U+0027) and the backslash `\` (U+005C). Python's `repr` of such a `str`
  uses **single quotes** (no `'` inside to force double quotes) and escapes
  **nothing** ⇒ `repr(s) = "'" + s + "'"`; `repr` of such a `bytes` likewise
  gives `repr(bs) = "b'" + s + "'"` where `s = bs.decode('ascii')`.

Hence on `simpleParam`, `saferepr(param, maxsize=42)` equals `quotedRepr` under
the §2 bijection — `'…'` on text, `b'…'` on bytes. This is the behavioural
change the F2P tests observe: a text parameter/id `foo` now renders as `'foo'`
(quoted) instead of the bare `foo` the pre-patch `str()` produced, and a bytes
parameter `b'Hello World'` now renders as `[b'Hello World']` without the
pre-patch's implicit `str()` — which under `-bb` raised `BytesWarning`, so
`test_show_fixture_action_with_bytes` now exits 0.

**Why `simpleParam` covers the F2P observations.** Every F2P parameter/id value
is a short printable payload with no apostrophe or backslash: `'foo'`,`'bar'`
(params), `'spam'`,`'ham'` (ids), `'FOO'`,`'BAR'` (callable ids via
`p.upper()`) — all `textVal` — and `b'Hello World'` (the BytesWarning test) —
`bytesVal` of length 11 ≤ 39. Nothing the F2P tests observe lies outside the
modeled domain.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL `saferepr` on
boundary inputs (empty, the length-40 text / length-39 bytes edges, every
printable-ASCII code point alone as both shapes, the F2P literals including
`Hello World`) plus 200 000 randomized `simpleParam` fuzz rounds (each round a
text sample and, when short enough, its bytes twin), asserting
`saferepr(s, maxsize=42) == "'" + s + "'"` and
`saferepr(bs, maxsize=42) == "b'" + s + "'"` (the `quotedRepr` deep model) on
every one. It additionally asserts the length-41 text and length-40 bytes
boundaries *do* ellipsize (witnessing the `maxsize=42` bound is load-bearing on
both shapes), and witnesses in `-bb` subprocesses that `saferepr` of a bytes
value raises no BytesWarning while the pre-patch implicit `str()` does.
Exit 0 iff sound.

### 3.2 No consumed axioms
There is no module-level `axiom` and no `:|` callee stub. The only callee
(`saferepr`) is modeled deeply as `quotedRepr` and validated as an A-reference,
per directive 7 (a deeply-modeled callee is an A-reference, not a dead axiom).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7205`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `quotedRepr`/`bracket` (the I-tagged construction of the token)
to Python — `"[" + "'" + s + "'" + "]"` for text, `"[" + "b'" + s + "'" + "]"`
for bytes — and compares against the ORACLE: the patched expression
`"[{}]".format(saferepr(param, maxsize=42))` evaluated with the REAL repo
`saferepr`. They agree on every `simpleParam` input (both shapes fuzzed).
