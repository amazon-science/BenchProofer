# refinement.md — operation correspondence (psf__requests-2317)

Each op of `implementation_normalizeMethod` ↔ its `patch.diff` counterpart.
Tags: **R** type refinement, **A-consumed** axiom property consumed by proof,
**A-reference** deep model validated == real callee by G-AX, **I** identical op.

Modeled function: the request-method normalization at the top of
`Session.request` (`requests/sessions.py:428`). See mapping.md.

| # | Lean op (`implementation_normalizeMethod`) | patch.diff counterpart | tag | note |
|---|---|---|---|---|
| 1 | `let mut m := nativeContent method` | `method = to_native_string(method)` (changed line, `sessions.py:428`) | R | `to_native_string(...)` returns the *textual content* of the supplied token: identity on a native `str`, and `.decode('ascii')` of a `bytes` token. Modeled deeply by `nativeContent`: text passes through, and a raw byte token (`List UInt8`) is decoded per-byte via `Char.ofNat ∘ UInt8.toNat` (agrees with `.decode('ascii')` on the ASCII method-token domain). This is the operation the patch CHANGES — modeled deeply, never axiomatized. |
| 2 | `m := m.map Char.toUpper` | `method.upper()` inside `Request(method = method.upper(), …)` (`sessions.py:432`, unchanged by patch) | R | `str.upper()` ⟷ `List.map Char.toUpper` over the code points. On the ASCII method-token domain the two agree code-point-for-code-point, length preserving (mapping.md domain note). Unchanged callee, modeled deeply, exercised end-to-end by G-CONF. |
| 3 | `return m` | the normalized value stored as `req.method` / carried into the assembled request | I | the stored method. |

Every modeled op is **R** or **I**. There are **no A-consumed axioms** and **no
A-reference** callees: both `to_native_string` (changed-to) and `str.upper`
(unchanged) are modeled deeply, so no `opaque`/`axiom` callee contract is needed.
`axiom_check.py` is therefore a skip stub.

There is no changed-inexpressible op: the entire fix is the switch from the
bytes-`repr` rendering (`builtin_str`) to text recovery (`to_native_string`),
modeled deeply by `nativeContent` returning the decoded characters of a bytes
token instead of its `b'…'` printable description.

## conf_skip
`conf_skip = false` — the impl region is all-R/I (no A-tagged ops). G-CONF
differential-tests the runtime-observable leg (decoded-text content, upper-cased)
against the real patched `Session.request` over both the native-`str` and `bytes`
method domains. The bytes-token discriminator IS runtime-observable on the
Python-3 testbed (`builtin_str(b'GET') == "b'GET'"` vs
`to_native_string(b'GET') == "GET"`), so the conformance check exercises the bug
directly. G-DIFF independently confirms the spec sees the bug: the prepatch impl
(which renders a bytes token as its `b'…'` repr) fails to typecheck on the
`bytes` case of `correct_normalizeMethod`.
