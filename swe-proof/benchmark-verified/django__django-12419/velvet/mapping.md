# mapping.md — django__django-12419

Binds `Solution.lean` symbols to the repo at
`base_commit = 7fa1a93c6c8109010a6ff3f604fda83b604e0e97`.

Repo file under change: `django/conf/global_settings.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `defaultReferrerPolicy` (returns `policy : List Char`) | `SECURE_REFERRER_POLICY` — `django/conf/global_settings.py:640` | the default referrer-policy provider (the module-level setting value) |
| `sameOriginPolicy = "same-origin".toList` | the patched value `'same-origin'` | the pinned default policy token |

No callee is axiomatized: the default policy is a value the provider supplies
directly, modeled deeply as its concrete token sequence.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

| repo reality | Lean carrier | bijection |
|---|---|---|
| `SECURE_REFERRER_POLICY` : `str` `'same-origin'` (post-patch) | `List Char` | exact, per-code-point: the Python `str` `'same-origin'` ↔ `"same-origin".toList` (each ASCII code point maps to the corresponding `Char`). |
| pre-patch `None` (no definite policy) | unset sentinel, modeled as `[]` (prepatch only) | absent default ↔ the empty token sequence; never equals `sameOriginPolicy` and is `= []`. |

The setting is consumed downstream by `SecurityMiddleware.process_response`
(`django/middleware/security.py:46`), which, when the policy is truthy, sets the
`Referrer-Policy` response header to
`','.join(v.strip() for v in policy.split(','))` (a str) or `','.join(policy)`
(an iterable). For the single-token string `'same-origin'` this header value is
exactly `same-origin`. The F2P test
`test_middleware_headers (project_template.test_settings.TestStartProjectSettings)`
asserts the default middleware stack emits `b'Referrer-Policy: same-origin'`.
The provider's returned value IS that default policy, so pinning
`policy = sameOriginPolicy` pins the test-observed behavior; the consumer logic
is byte-identical pre/post and merely forwards the value.

### 2.1 Why `mut`-frame (directive 5) is trivially satisfied
`defaultReferrerPolicy` takes no parameters and declares no `mut` state; it is a
pure provider returning a value. There is no read-only input to over-permit and
no `mut` frame to pin.

## 3. Callee provenance

None (no axioms). The whole behavior is the constant default value, modeled
deeply as the literal token `"same-origin".toList`. The consumer
(`SecurityMiddleware.process_response`) is **unchanged** between pre- and
post-patch and is therefore NOT modeled or axiomatized (§0.7: never axiomatize an
unchanged function that is not the locus of the change). Its forwarding logic is
mirrored only inside `conformance_check.py`'s `emit_header` to confirm the R leg
reaches the test-observed header, not in the spec.

## 4. G-CONF fuzz seed

`conformance_check.py` seeds with **12419**. The R shadow is the constant token
`"same-origin"`; the oracle is the patched repo's
`django.conf.global_settings.SECURE_REFERRER_POLICY`, read in-container. The
check also bridges through the consumer's header-emission rule
(`','.join(v.strip() for v in policy.split(','))`) so the shadow is compared at
the test-observed header level. The provider takes no input, so the relation is a
constant; the comparison is repeated over the ≥10⁵ fuzz budget for harness
parity.
