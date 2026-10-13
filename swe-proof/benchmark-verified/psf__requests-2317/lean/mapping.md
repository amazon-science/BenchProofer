# mapping.md — symbol binding & type bijection (psf__requests-2317)

## Modeled function

| Lean | Python symbol (file:line @ base_commit `091991b`) | note |
|---|---|---|
| `implementation_normalizeMethod` | the request-method normalization performed at the top of `Session.request` (`requests/sessions.py:428`), i.e. the value finally stored as the request's method | the patched function is `Session.request`; only its method-normalization step is modeled (the rest of `request` — building/sending the `Request` — is unchanged plumbing) |

The gold patch's two hunks:
1. import hunk (`requests/sessions.py:16`) — drops `builtin_str` from the
   `.compat` import list. Pure plumbing consequence of hunk 2; not modeled.
2. body hunk (`requests/sessions.py:428`) — replaces `method =
   builtin_str(method)` with `method = to_native_string(method)`, immediately
   before `req = Request(method = method.upper(), …)`. THIS is the modeled
   behavior. (`to_native_string` is `requests/utils.py:655`, an UNCHANGED callee
   that already existed at base_commit.)

## The bug, precisely

`builtin_str` is `str` on Python 3. When a caller passes the method as a *bytes*
token — e.g. `b'GET'` (some clients encode all of their arguments to bytes) —
`builtin_str(b'GET')` returns the **repr** `"b'GET'"` (the printable description
of the bytes object), NOT the decoded text `"GET"`. After `.upper()` the request
method is the literal `B'GET'`, so the server returns 404.

The fix uses `to_native_string`, which for a non-native (bytes) input ASCII-
*decodes* it (`string.decode('ascii')`) back to `"GET"`, and is the identity on
an already-native `str`. So the stored method carries the decoded textual content
regardless of whether the caller passed text or bytes.

The observable difference (text method → no change; bytes method → decoded text
vs `b'…'` repr) is directly visible on the Python-3 testbed, so G-CONF
differential-tests it end-to-end.

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX

| Lean type | Python reality |
|---|---|
| `PyMethod.text cs` | a native `str` method whose characters are `cs` |
| `PyMethod.bytes bs` | a `bytes` method whose raw bytes are `bs` (e.g. `b'GET'` ↔ `.bytes [71,69,84]`) |
| `nativeContent method` | the decoded textual content of the supplied method: `str` value for text, `bytes.decode('ascii')` for bytes — modeled by `bs.map (Char.ofNat ∘ UInt8.toNat)`, the per-byte ASCII/latin-1 decode that agrees with `.decode('ascii')` on the ASCII method-token domain |
| `result : List Char` | the code points of the method finally stored on the request (`req.method` after `.upper()`) |
| `cs.map Char.toUpper` | `s.upper()` restricted to the ASCII domain (HTTP method tokens are ASCII; `Char.toUpper` is ASCII-only — see domain note) |

### Domain note
HTTP method tokens (`GET`, `POST`, `b'get'`, …) are ASCII. `Char.toUpper`
performs ASCII case folding only; Python `str.upper()` performs full-Unicode case
folding. On the ASCII method-token domain the two agree code-point-for-code-point,
length preserving, and `bytes.decode('ascii')` is total. G-CONF fuzzes the ASCII
domain accordingly. (`to_native_string` decodes with `encoding='ascii'` by
default, matching this domain.)

## Callee provenance / flag deps

* `to_native_string` (`requests/utils.py:655`, unchanged) — modeled **deeply** as
  `nativeContent` (select the underlying characters; for bytes that is the decoded
  text), tag **R**, NOT axiomatized. It is the callee the patch switches TO; its
  text-recovery behavior is exercised end-to-end by G-CONF.
* `str.upper` — modeled deeply as `List.map Char.toUpper` (R). Unchanged by the
  patch and exercised end-to-end by G-CONF; no `_prop` axiom is consumed.
* No `opaque` callee / consumed axiom is needed → `axiom_check.py` is a skip stub.

## G-CONF fuzz seed (pinned)
`SEED = 23170630`, `N_RANDOM = 120000`.
