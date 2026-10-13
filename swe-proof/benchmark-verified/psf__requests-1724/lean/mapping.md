# mapping.md — symbol binding & type bijection (psf__requests-1724)

## Modeled function

| Lean | Python symbol (file:line @ base_commit `1ba83c4`) | note |
|---|---|---|
| `implementation_normalizeMethod` | the request-method normalization performed at the top of `Session.request` (`requests/sessions.py:311-313`), i.e. the value finally stored as the request's method | the patched function is `Session.request`; only its method-normalization step is modeled (the rest of `request` — building/sending the `Request` — is unchanged plumbing) |

The gold patch's two hunks:
1. import hunk (`requests/sessions.py:15`) — adds `builtin_str` to the
   `.compat` import list. Pure plumbing; not modeled.
2. body hunk (`requests/sessions.py:311-313`) — inserts `method =
   builtin_str(method)` immediately before `req = Request(method =
   method.upper(), …)`. THIS is the modeled behavior.

## The bug, precisely

`method.upper()` (line 313) is called on the *raw* incoming `method`. Under
Python 2.7 a caller may pass a *wide* (unicode) text string (`u'POST'`); then
`method.upper()` is still a unicode string, which later poisons the assembled
header with unicode and triggers a `UnicodeDecodeError`. The fix coerces the
method to a *native* byte string first (`builtin_str(method)`), so the stored
method is always a native string.

In a pure per-codepoint character model the pre- and post-patch results are
**identical** (uppercasing is unchanged). The only observable difference is the
*string type* (wide/unicode vs native). The model must therefore carry that
type tag, or G-DIFF cannot see the bug.

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX

| Lean type | Python reality |
|---|---|
| `PyStr` (`{ chars : List Char, wide : Bool }`) | a Python text string, with `chars` = its code-point sequence and `wide` = "is a Python-2 `unicode`/wide string" (`True`) vs "is a native byte `str`" (`False`) |
| `input.chars` | the code points of the incoming `method` argument |
| `input.wide` | whether the incoming `method` was a wide (unicode) string |
| `result.chars` | the code points of the method finally stored on the request |
| `result.wide` | whether that stored method is a wide string (the bug ⟺ `result.wide = true`) |
| `cs.map Char.toUpper` | `s.upper()` restricted to the ASCII domain (HTTP method tokens are ASCII; `Char.toUpper` is ASCII-only — see domain note) |
| `{ m with wide := false }` | `builtin_str(m)` — coercion of a text string to a native byte string (identity on ASCII content, forces native type) |

### Domain note
HTTP method tokens (`GET`, `POST`, `u'POST'`, …) are ASCII. `Char.toUpper`
performs ASCII case folding only; Python `str.upper()` performs full-Unicode
case folding (and some code points may expand). On the ASCII method-token domain
the two agree code-point-for-code-point, length preserving. G-CONF fuzzes the
ASCII domain accordingly.

## Callee provenance / flag deps

* `builtin_str` — modeled **deeply** as the native-coercion `{ m with wide :=
  false }` (R), NOT axiomatized. It is the operation the patch *adds*, so it may
  not be an opaque callee.
* `str.upper` — modeled deeply as `List.map Char.toUpper` (R). It is unchanged by
  the patch and is exercised end-to-end by G-CONF; no `_prop` axiom is consumed.
* No `opaque` callee / consumed axiom is needed → `axiom_check.py` is a skip stub.

## G-CONF observability caveat (Python-2-only discriminator)

The discriminating component — `result.wide` — is a Python-2 `unicode`-vs-`str`
distinction. The testbed image is **Python 3.9**, where the single text type is
`str` (`builtin_str is str`); the wide/native distinction is collapsed at
runtime and cannot be observed. G-CONF therefore differential-tests the
runtime-observable leg over the ASCII domain:

* the stored method's character content equals `builtin_str(method).upper()`
  (the uppercasing + native-coercion-idempotence-on-ASCII leg), and
* the stored method's runtime type is the native `builtin_str` type.

The `wide`-flag clause (the Py2-only bug) is pinned by the spec and verified by
G-DIFF (the prepatch fails on it), not by Python-3 runtime differential.

## G-CONF fuzz seed (pinned)
`SEED = 17240626`, `N_RANDOM = 120000`.
