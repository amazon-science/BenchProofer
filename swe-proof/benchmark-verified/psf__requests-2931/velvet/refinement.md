# refinement.md — psf__requests-2931

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `encodePayload` `do` block, plus the deep `toNativeString` model used by the
prepatch baseline) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses this
axiom's `ensures`), **A-reference** (deep model validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs + this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs for the F2P-pinned behaviour, so it
resolves (G-RESOLVE).

`patch.diff` is the gold patch **verbatim**.

## The gold patch and what the spec models

The gold patch edits two methods of `requests/models.py`:

1. `RequestEncodingMixin._encode_params` (`models.py:83-84`): for a `str`/`bytes`
   payload, `return to_native_string(data)` → `return data`. This is the
   **observable, F2P-pinned fix** — a `bytes` body is no longer coerced to a
   native string, so a binary payload stays `bytes` (F2P `test_binary_put`).
2. `PreparedRequest.prepare_url` (`models.py:387-388`): a new guard
   `if isinstance(params, (str, bytes)): params = to_native_string(params)`
   inserted just before `enc_params = self._encode_params(params)`. This is a
   **behaviour-preserving compensating edit** that guards pre-existing P2P tests
   (`test_params_bytes_are_encoded`,
   `test_params_original_order_is_preserved_by_default`); the str/bytes param is
   `to_native_string`-coerced either way (previously inside `_encode_params`,
   now in its caller), so no observable param-path behaviour changes.

**The spec models hunk 1 only** (`encodePayload`). Hunk 2 is deliberately NOT
modeled: it is not pinned by the sole F2P (`test_binary_put`, which pins only the
binary-body-stays-binary behaviour) and is behaviour-preserving, so modeling it
would add no resolution discriminator while disclosing the gold's compensating-
edit design (which site to touch and that the coercion was relocated) — content
absent from the public `problem_statement`. The faithful, F2P-pinned obligation
is fully captured by `encodePayload`'s `ensures out = data` alone.

## A. The encoder — `_encode_params(data)` (`models.py:83-84`)

| # | Solution.lean impl op (`encodePayload`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `data : Payload` (`.text`/`.binary`) | the `str`/`bytes` branch of `_encode_params(data)` | R | `str ↔ Payload.text (List Char)`, `bytes ↔ Payload.binary (List UInt8)` (mapping.md §2). G-CONF bridges via `Char.ofNat u.toNat ↔ chr(u)`. |
| A2 | `return data` (`ensures out = data`) | `return data` | I | identical concrete op: the payload is returned unchanged, preserving BOTH kind and content. The discriminating clause `out = data` distinguishes `.binary b` from `.text (...)`, i.e. the body stays `bytes`. |

The pre-patch op was `return to_native_string(data)`, which for a `bytes`
payload yields a `str` — modeled by `Solution_prepatch.lean`'s
`return toNativeString data`. Against the frozen `ensures out = data` it fails
for any binary input (`toNativeString (.binary b) = .text (...) ≠ .binary b`),
which is exactly the reported bug (G-DIFF).

`toNativeString` (pure region) is the deep model of the **unchanged** callee
`requests.utils.to_native_string`. In `Solution.lean` it is not invoked by the
impl (the encoder is the identity); it is retained because the prepatch baseline
uses it to reproduce the pre-patch coercion bug, and its equality to the real
callee on its ASCII in-domain inputs is the **A-reference** G-AX validates
(axiom_check.py). It is named verbatim in the public `problem_statement` ("fails
due to calling to_native_string"), so it is not a leaked symbol.

## B. The URL param path — `prepare_url` hunk 2 (`models.py:387-388`)

Not modeled (see "what the spec models", above). Justification: hunk 2 is a
behaviour-preserving compensating edit, not pinned by F2P and not a resolution
discriminator — a str/bytes param is `to_native_string`-coerced both before and
after the patch (relocated, not changed). Modeling it would disclose the gold's
compensating-edit mechanism beyond the public issue without strengthening the
F2P-pinned obligation. The one observable change (the encoder's identity vs its
pre-patch coercion) is fully exercised by site A and its prepatch.

## C. No kind-3 (inexpressible-changed-op) steps

Every modeled step is R, A-reference, or I. The one operation that genuinely
*changed* — the encoder dropping its `to_native_string` coercion — is modeled
**deeply** as the identity (`encodePayload`, A2), not hidden behind an axiom
about the function under change. The only modeled external callee,
`toNativeString`, is the **unchanged** `requests.utils.to_native_string`; it is
an **A-reference** (deep model, G-AX-validated), never a consumed axiom. There
are no consumed axioms.

## D. verify(Solution) ⇒ resolved

`encodePayload` verifies only if its output equals its input EXACTLY, kind
included (A2) — so a verifying impl preserves `bytes` as `bytes`, the property
`test_binary_put` asserts. By R (`str ↔ Payload.text`, `bytes ↔ Payload.binary`,
`Char.ofNat u.toNat ↔ chr(u)`) the verified op equals the gold-patched
`_encode_params` behaviour on its str/bytes branch; by G-CONF the I
transliteration agrees with `patch.diff` over ≥10⁵ inputs (bytes preserved as
bytes). `patch.diff` is the gold verbatim and includes hunk 2, so applying it
resolves and preserves the P2P param tests (G-RESOLVE). Therefore a model
satisfying this spec, refined by the map above, reproduces the gold patch's
F2P-pinned behaviour up to type refinement and the one audited callee — and the
gold patch resolves. Trust points are exactly the two of plan §1.1: A-reference
soundness (G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
