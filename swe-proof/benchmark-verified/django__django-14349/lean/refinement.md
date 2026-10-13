# refinement.md — django__django-14349

Maps every operation in `implementation_validateUrl` to its `patch.diff`
counterpart in `URLValidator.__call__` (django/core/validators.py — see
mapping.md). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (post-patch `__call__`, relevant head)
```python
unsafe_chars = frozenset('\t\r\n')
...
def __call__(self, value):
    if not isinstance(value, str):
        raise ValidationError(self.message, code=self.code, params={'value': value})
    if self.unsafe_chars.intersection(value):
        raise ValidationError(self.message, code=self.code, params={'value': value})
    # Check if the scheme is valid.
    scheme = value.split('://')[0].lower()
    ...  # unchanged structural validation (scheme/regex/IDN/IPv6)
```
(The `isinstance(value, str)` check is the type-modeling boundary: in Lean the
input is already a `List Char` (a string), so the non-`str` branch is outside the
model — see note below. The unchanged tail is the opaque `structurallyValid`
carrier, exercised by G-CONF.)

## Operation correspondence
| # | Lean op (`implementation_validateUrl`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `if containsForbidden value then` | `if self.unsafe_chars.intersection(value):` | R | `unsafe_chars = frozenset('\t\r\n')` ↔ the literal set `{'\t','\r','\n'}`; Python set-intersection truthiness ↔ `value.any (· ∈ {'\t','\r','\n'})`. Deeply modeled as `containsForbidden` (NOT axiomatized — it is the op the patch changes). Type bijection in mapping.md. |
| 2 | `return false` | `raise ValidationError(...)` | R | a raised `ValidationError` ↔ the rejection verdict `false`. |
| 3 | `return structurallyValid value` | (fall through to) `scheme = value.split('://')[0].lower(); if scheme not in self.schemes: raise ...; super().__call__(value); ...` | R | the UNCHANGED rest of `__call__` ↔ `structurallyValid`: a non-raising completion ↔ `true`, any raise within the tail ↔ `false`. Declared `opaque` so the unchanged structural validation can appear in the executable impl; G-CONF realizes it as the real patched validator with the guard neutralized. |

Every op is **R** (or the implicit early-return control flow, an **I** skeleton
op). **No A row is consumed:** `structurallyValid` is declared `opaque` purely so
the unchanged structural validation can appear in the executable impl, and the
proof closes by case analysis on `containsForbidden value`, consuming NO property of
`structurallyValid`. There is no `axiom structurallyValid_prop`. Therefore
`meta.json axioms = []`, `deep_model_references = []`, and `axiom_check.py` is a
skip stub. (`containsForbidden` is a deeply-modeled changed op — a pure `def`, an R
leg checked by G-CONF — not a callee axiom.)

### The `isinstance(value, str)` check
The pre-existing non-`str` guard (op before #1) is the type-modeling boundary:
the Lean model receives a `List Char`, i.e. a value that IS a string, so the
non-`str` rejection branch is not in scope (it is unchanged by the patch and
orthogonal to the modeled behavior). This is a standard type-refinement of the
`str` domain, not an omitted behavior.

## R/I legs ⇒ G-CONF
The impl is all R/I (no A-tagged op), so `conformance_check.py` mechanically
differential-tests the impl shadow — `containsForbidden` realized as the real
`frozenset('\t\r\n').intersection(value)` truthiness, `structurallyValid`
realized as the real patched validator with the guard neutralized — against the
real patched `URLValidator.__call__` over ≥10^5 fuzzed `value` strings. The test
pins the GUARD (the only behavioral edit): any of `{tab, CR, LF}` present ⇒
rejected; otherwise ⇒ the unchanged structural verdict. `conf_skip = false`.

## Prepatch = the real bug
`Solution_prepatch.lean` omits the guard (op #1/#2): it unconditionally returns
`structurallyValid value`. That is exactly the pre-patch `__call__` (no
`unsafe_chars` guard, straight to the scheme/regex/IDN/IPv6 checks) — the real
bug from the issue: on Python versions patched for bpo-43882 the URL splitter
strips tab/CR/LF before splitting, so an address containing those characters
reaches the structural checks stripped and is wrongly accepted. It cannot satisfy
`problem_spec_validateUrl` on the `containsForbidden value = true` clause (which
demands `result = false`, whereas the buggy impl yields `structurallyValid value`
which is not forced to `false`), so its `correct_validateUrl` is unclosable ⇒
G-DIFF fails verification as required (confirmed by `lean_verify` exit 1: the
`containsForbidden value = true` goal `pure (structurallyValid value) = false`
cannot close). This is the behavior the FAIL_TO_PASS test `test_validators`
exercises (it feeds URLs containing `\n`, `\r`, and `\t` and requires a
`ValidationError`).
