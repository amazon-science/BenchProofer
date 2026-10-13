# mapping.md — django__django-14349

## Instance
- repo: django/django
- base_commit: a708f39ce67af174df90c5b5e50ad1976cec7cb8
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch adds an early raw-character guard to `URLValidator.__call__`
(django/core/validators.py). It introduces a class attribute
`unsafe_chars = frozenset('\t\r\n')` and, immediately after the `isinstance`
check, rejects any value whose character set intersects `unsafe_chars`:

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
    ...  # (unchanged: scheme check, regex match, IDN fallback, IPv6 check)
```

Pre-patch, `__call__` had no such guard: it proceeded directly to the scheme
check, the regex match, the IDN fallback, and the IPv6 host check. The fix is
needed because on Python versions patched for bpo-43882 the URL splitter strips
tab/CR/LF before splitting, so those characters never reach the structural
checks and an address containing them would otherwise be accepted. Rejecting
them up front restores the intended rejection regardless of splitter behavior.

The single observable behavioral change at the `__call__` site is the **guard**:
when the value contains any of `{tab, CR, LF}`, validation now fails outright;
otherwise validation proceeds exactly as before (the unchanged structural
checks). The `(value : str)` is judged unmodified by both legs.

## Symbol binding
| Lean symbol | Python source @ base_commit / patch |
|---|---|
| `implementation_validateUrl` | `URLValidator.__call__` (django/core/validators.py:101) — the guarded validation the patch introduces |
| `problem_spec_validateUrl` | the post-condition `__call__` must satisfy after the patch |
| `containsUnsafe` | `self.unsafe_chars.intersection(value)` truthiness — the set-membership test on `unsafe_chars = frozenset('\t\r\n')` (added by the patch) |
| `structurallyValid` | the UNCHANGED rest of `__call__` after the guard: scheme check + regex match + IDN fallback + IPv6 host check (i.e. the entire pre-patch `__call__` body) |

`structurallyValid` is declared `opaque` (a pure carrier) so the unchanged
structural validation can appear in the executable impl. The modeled behavior is
how the raw-character guard combines with the structural verdict, not the
internal grammar the structural checks apply — the spec inspects no internal of
`structurallyValid`, and the proof consumes no property of it (it closes by case
analysis on `containsUnsafe`). Hence NO `axiom _prop` is declared.

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `value : List Char` | `value` (str) | per-code-point modeling (`List Char`) — the guard is a per-character membership test |
| `containsUnsafe value : Bool` | `bool(self.unsafe_chars.intersection(value))` | `true` ⇔ the value contains at least one of `'\t'`, `'\r'`, `'\n'` |
| `structurallyValid value : Bool` | the rest-of-validation verdict on `value` | `true` ⇔ the unchanged structural checks accept (do not raise) |
| result `: Bool` | acceptance verdict of `__call__` | `true` ⇔ `__call__` does NOT raise `ValidationError`; `false` ⇔ it raises |

`List Char` ↔ Python `str` is the per-code-point bijection. A Python exception
(`ValidationError`) is modeled as the verdict `false`; a non-raising return is
`true`. The three disallowed characters `'\t' '\r' '\n'` ↔ Lean `'\t' '\r' '\n'`.

## Callee provenance / flag deps
- `structurallyValid` ↔ the unchanged rest of `__call__` (scheme check, the
  `RegexValidator.__call__` regex match, the `urlsplit`/`punycode` IDN fallback,
  the `validate_ipv6_address` host check). It is the entire pre-patch `__call__`
  body, UNCHANGED by the gold patch. Deterministic for a fixed input. G-CONF
  realizes it by running the real patched `URLValidator` with the guard disabled
  (`unsafe_chars = frozenset()`), so the only difference exercised is the guard.
- `containsUnsafe` ↔ `self.unsafe_chars.intersection(value)` truthiness — the
  set the patch ADDS, `frozenset('\t\r\n')`. Deeply modeled (R), not axiomatized.
- No flag dependency: the guard is unconditional. The disallowed characters are
  described in the public `problem_statement` ("LF, CR and tab characters").

## G-CONF fuzz seed
- pinned seed: `14349`
- ≥10^5 fuzzed `value` strings: drawn from a pool of valid/invalid URL bodies,
  with each of `\t`, `\r`, `\n` injected at random positions in ~half the cases
  (biasing toward the guard discriminator and its near-misses, e.g. other
  whitespace like a plain space). The verdict (raise vs not) is deterministic.
