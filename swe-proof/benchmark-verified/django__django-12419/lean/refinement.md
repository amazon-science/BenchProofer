# refinement.md — django__django-12419

Maps every operation in `implementation_referrerPolicy` to its `patch.diff`
counterpart. The patch is a one-line default-constant change; the observable
behavior it governs is the value resolved for `settings.SECURE_REFERRER_POLICY`,
which the (unchanged) security middleware then turns into the `Referrer-Policy`
response header (see mapping.md). Tags: **R** type-refinement, **A-consumed**
proof uses a callee axiom, **A-reference** deep-modeled changed op validated ==
real callee, **I** identical concrete op.

## Patch (post-patch)
```python
# django/conf/global_settings.py
SECURE_REFERRER_POLICY = 'same-origin'          # was: None
```
governing, unchanged:
```python
# django/middleware/security.py
self.referrer_policy = settings.SECURE_REFERRER_POLICY
...
if self.referrer_policy:
    response.setdefault('Referrer-Policy', ','.join(...))
```

## Operation correspondence
| # | Lean op (`implementation_referrerPolicy`) | patch.diff / governed op | tag | note |
|---|---|---|---|---|
| 1 | `let mut setting : Option String := defaultReferrerPolicy` | `SECURE_REFERRER_POLICY = 'same-origin'` (the changed default) seeded as the base value of `settings.SECURE_REFERRER_POLICY` | I | the post-fix built-in default; `defaultReferrerPolicy = some "same-origin"`. THIS is the line the patch changes (prepatch seeds `none`, the literal pre-patch `None`). |
| 2 | `match projectSetting with \| some v => setting := v \| none => pure ()` | resolving `settings.SECURE_REFERRER_POLICY`: a project `settings.py` declaration overrides the built-in default; absence leaves the default | R | `Option (Option String)` models "declared (`some v`) vs. left-at-default (`none`)"; the inner `Option String` is the policy-or-None the project pinned. |
| 3 | `return setting` | the resolved `settings.SECURE_REFERRER_POLICY` value read at `self.referrer_policy = settings.SECURE_REFERRER_POLICY` | I | the resolved value flowing to the consumer; no further transform is part of the modeled (changed) unit. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## Scope of the modeled unit (and why the header transform is out)
The patch changes the *resolved setting value*, not the middleware. The
downstream transform in `SecurityMiddleware.process_response`
(`if self.referrer_policy: response.setdefault('Referrer-Policy', …)`) is
UNCHANGED code and is a deterministic, total function of the resolved value: a
resolved `'same-origin'` yields exactly `Referrer-Policy: same-origin`; a
resolved `None` (falsy) yields no header. Pinning the resolved value therefore
pins the F2P observable. This mirrors django-10914, where the modeled unit
stopped at the resolved permission *mode* and did not re-implement the unchanged
filesystem `chmod`.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the patched repo behavior (the resolved
`settings.SECURE_REFERRER_POLICY`, read exactly as the security middleware reads
it) over ≥10^5 fuzzed inputs. `conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` seeds the default with `none` (the literal pre-patch
`SECURE_REFERRER_POLICY = None`) instead of `defaultReferrerPolicy =
some "same-origin"`. With no project override (`projectSetting = none`) it
returns `none`, but the spec's no-override clause demands `result =
defaultReferrerPolicy = some "same-origin"`. The carried gold proof
(`cases projectSetting <;> rfl`) fails to typecheck on exactly the `none`
branch — precisely the behavior the FAIL_TO_PASS test `test_middleware_headers`
asserts (the default project emits `Referrer-Policy: same-origin`; pre-patch the
falsy `None` emitted no header). The spec is byte-identical between the two files
(only the impl initializer differs).

## patch.diff == gold
`patch.diff` is the gold patch verbatim (the one-line `global_settings.py`
change); it applies at `base_commit` and the harness resolves.
