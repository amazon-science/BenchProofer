# refinement.md — django__django-12419

Correspondence between `Solution.lean`'s `defaultReferrerPolicy` impl and
`patch.diff` (the gold patch changes the default referrer-policy setting).
`patch.diff` is the gold verbatim (applies at base_commit, resolves — G-RESOLVE).

## A. The changed default — `SECURE_REFERRER_POLICY`

Gold hunk:
```
-SECURE_REFERRER_POLICY = None
+SECURE_REFERRER_POLICY = 'same-origin'
```

| # | Solution.lean impl op (`defaultReferrerPolicy`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `return sameOriginPolicy` (`= "same-origin".toList`) | `SECURE_REFERRER_POLICY = 'same-origin'` | R | value-level refinement: the Python `str` `'same-origin'` ↔ the Lean `List Char` `"same-origin".toList`, per-code-point identity (mapping.md §2). The provider yields the module-level default value; the `do` block returns it directly. Concrete-value identity under the str↔List Char bijection. |

No A (axiom) steps; no kind-3 (changed inexpressible) steps. The single op is the
default policy value, modeled deeply and tagged **R** (string-carrier refinement
`'same-origin'` ↔ `"same-origin".toList`).

## B. verify(Solution) ⇒ resolved

`defaultReferrerPolicy` verifies only if `policy = sameOriginPolicy`
(equivalently `policy = "same-origin".toList` and `policy ≠ []`) — clause B1. By
R (the str↔List Char value bijection) the verified result equals the patched
`SECURE_REFERRER_POLICY` (`'same-origin'`). The consumer
`SecurityMiddleware.process_response` (byte-identical pre/post) forwards a truthy
string policy to the `Referrer-Policy` header as
`','.join(v.strip() for v in policy.split(','))`, which for `'same-origin'` is
`same-origin`. The F2P test
`test_middleware_headers (project_template.test_settings.TestStartProjectSettings)`
asserts the default stack emits `b'Referrer-Policy: same-origin'`; that header IS
the default provided by this setting, so the test passes iff the default is
`'same-origin'` — exactly what the spec pins. G-CONF differential-tests B1 (the R
leg) against the patched repo's `SECURE_REFERRER_POLICY` (and through the header
emission). The prepatch (`return []`, the unset/`None` sentinel that emits no
header) fails `policy = sameOriginPolicy` and `policy ≠ []` (G-DIFF). No trust
points beyond the type bijection (mapping.md §2): there are no axioms.
