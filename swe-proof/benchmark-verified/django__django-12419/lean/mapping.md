# mapping.md — django__django-12419

## Instance
- repo: django/django
- base_commit: 7fa1a93c6c8109010a6ff3f604fda83b604e0e97
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch changes ONE line in `django/conf/global_settings.py`
(`django/conf/global_settings.py:640`): the built-in default of the
referrer-policy setting goes from `None` to the string `'same-origin'`. The edit
is a one-line constant change, but its *observable* behavior — what the
FAIL_TO_PASS test asserts — surfaces through the value the framework resolves for
that setting, which is then consumed by the security middleware:

```python
# django/middleware/security.py @ base_commit (lines 18, 47-53) — UNCHANGED consumer
self.referrer_policy = settings.SECURE_REFERRER_POLICY
...
if self.referrer_policy:
    response.setdefault('Referrer-Policy', ','.join(
        [v.strip() for v in self.referrer_policy.split(',')]
        if isinstance(self.referrer_policy, str) else self.referrer_policy
    ))
```

`settings.SECURE_REFERRER_POLICY` is the project-resolved value of the setting:
the project's `settings.py` value when one is declared, and otherwise the
built-in default from `global_settings.py` (the constant the patch changes). The
F2P test `test_middleware_headers` runs the default project template (NO project
override) and asserts the rendered response carries `Referrer-Policy: same-origin`
— i.e. the resolved setting is `'same-origin'` (pre-patch it was `None`, which is
falsy ⇒ no header at all).

## Modeled function
I model the **resolved referrer-policy setting value** — the value
`settings.SECURE_REFERRER_POLICY` resolves to — as a total function of its two
data layers: the built-in default (the changed constant) and the optional
project override. This is the smallest unit whose observable behavior the patch
changes and the F2P test pins. The downstream header transform in
`SecurityMiddleware.process_response` is UNCHANGED, deterministic code (the
analogue of "writing the file" in django-10914, which stopped at the resolved
mode); a resolved value of `'same-origin'` deterministically produces the
`Referrer-Policy: same-origin` header. So pinning the resolved value pins the
F2P observable.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_referrerPolicy` | resolution of `settings.SECURE_REFERRER_POLICY` (project value over the built-in default), the value read at `django/middleware/security.py:18` |
| `problem_spec_referrerPolicy` | the post-condition the resolved value must satisfy |
| `defaultReferrerPolicy` | the built-in default of the referrer-policy setting (post-fix `'same-origin'`), `django/conf/global_settings.py:640` |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `projectSetting : Option (Option String)` | whether the project's `settings.py` declares the referrer-policy setting vs. leaves it at the built-in default | OUTER `none ↔ "not declared in settings.py"` (built-in default applies); OUTER `some v ↔ "declared as v"`, where INNER `none ↔ None` and `some s ↔ str s` |
| `defaultReferrerPolicy : Option String` | the built-in default value | post-fix `some "same-origin"` |
| result `: Option String` | the resolved `settings.SECURE_REFERRER_POLICY` | `none ↔ None`; `some s ↔ str s` |

`Option String` ↔ the Python "policy string or None" domain is the identity
bijection: `None ↔ none`, string `s ↔ some s`. The value domain modeled is
`None | str` (the default is a string and the F2P path is a string); the rarely
used iterable-valued configuration is OUT of the fuzzed domain (documented here),
exactly as django-10914 restricted modes to `int | None`. The resolved-value
cascade is identical for string and iterable inputs (pure pass-through), so the
restriction does not affect what the patch changes.

## Callee provenance / flag deps
- No unchanged repo callee is consumed. The built-in default is the literal
  `some "same-origin"`, and the project-vs-default selection is a plain
  most-specific-wins cascade modeled directly in Lean. There is no `opaque`
  callee and no `axiom <callee>_prop`; the `axioms` region is empty and
  `axiom_check.py` is a skip stub.
- No flag dependency: the resolution does not branch on any unrelated flag. The
  only datum is the project override (fuzzed by G-CONF).

## G-CONF fuzz seed
- pinned seed: `12419`
- ≥10^5 fuzzed `projectSetting` values; policy strings drawn from a pool
  including `None`, the new default `'same-origin'`, other valid policies
  (`'origin'`, `'no-referrer'`, `'strict-origin'`,
  `'origin,no-referrer-when-downgrade'`), the empty string `''`, and a
  comma-list `'same-origin, origin'`, with project-setting left-at-default vs.
  declared uniformly mixed.
