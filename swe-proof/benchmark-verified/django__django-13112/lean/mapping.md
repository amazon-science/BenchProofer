# mapping.md — django__django-13112

## Instance
- repo: django/django
- base_commit: 09914ccf688974e068941f55412b930729bafa06
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`ForeignKey.deconstruct` (django/db/models/fields/related.py:575) returns the
`(name, path, args, kwargs)` tuple used to serialize the field into a migration.
When the related model is given as a *string* reference (a lazy reference such as
`'MyApp.Category'`), the `kwargs['to']` entry is set to a normalized form of that
string. At base_commit the normalization is:

```python
if isinstance(self.remote_field.model, str):
    kwargs['to'] = self.remote_field.model.lower()
```

i.e. the WHOLE reference string is lowercased. A lazy reference may be qualified
as `app_label.ModelName`; lowercasing the whole string also lowercases the
`app_label`. When the app's real label is mixed-case (e.g. `DJ_RegLogin` /
`MiXedCase_migrations`), the deconstructed `to` no longer matches the actual
app label, so the migration carries a reference to an app that "isn't installed"
and `makemigrations`/`migrate` crashes with a lazy-reference `ValueError`.

The gold patch lowercases only the model-name segment, preserving the app label:

```python
if isinstance(self.remote_field.model, str):
    if '.' in self.remote_field.model:
        app_label, model_name = self.remote_field.model.split('.')
        kwargs['to'] = '%s.%s' % (app_label, model_name.lower())
    else:
        kwargs['to'] = self.remote_field.model.lower()
```

The modeled behavior is exactly this string normalization: given the lazy
reference string, produce the normalized `to` value.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_modelRef` | the value assigned to `kwargs['to']` in the `isinstance(self.remote_field.model, str)` branch of `ForeignKey.deconstruct` (django/db/models/fields/related.py:584-588 post-patch), as a function of `self.remote_field.model` (the lazy reference string) |
| `problem_spec_modelRef` | the post-condition that normalized value must satisfy |
| `RefToken` | an in-domain lazy reference string: the character sequence packaged with the two domain constraints (at most one `.`, all-ASCII) |
| `prefixSeg` | the text before the first `.` (the app-label segment, kept verbatim); `s.split('.')[0]` for a single-dot token |
| `nameSeg` | the text after the first `.` (the model-name segment, lowercased); `s.split('.')[1]` for a single-dot token |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `t : RefToken` (`t.chars : List Char`) | the lazy reference string `self.remote_field.model` | per-code-point sequence; the `RefToken` structure carries the two domain constraints (single separator, all-ASCII) as fields, so the Lean type ranges over exactly the modeled subset of Python strings |
| result `: List Char` | the resulting `kwargs['to']` string | per code point |
| `Char.toLower` | `str.lower` per character | ASCII letter case folding. Lean `Char.toLower` and Python `str.lower` agree **only on the ASCII range** (code point < 128); outside ASCII they diverge (Python folds `Σ`→`σ`, `İ`→`i̇`, `ẞ`→`ß`; `Char.toLower` leaves them unchanged, and the folded form may even change length). The bijection is therefore asserted **only over ASCII characters**, and this is not left to prose: the `RefToken.ascii` field carries `asciiToken t.chars` (`∀ c ∈ t.chars, c.val < 128`) so the domain type itself admits only tokens where the two callees provably coincide. Non-ASCII tokens are outside the modeled domain. |
| `'.' ∈ t.chars` | `'.' in s` | membership of the separator |
| `prefixSeg t.chars` / `nameSeg t.chars` | `s.split('.')[0]` / `s.split('.')[1]` | exact for a token with one separator (the modeled domain); for a bare token `'.' ∉ t.chars` and the bare branch applies |

`List Char` ↔ Python `str` is the per-code-point bijection. The G-CONF fuzzer
draws identifier-shaped tokens (ASCII letters, digits, `_`, and the `.`
separator) so `Char.toLower` ↔ `str.lower` is exact on the tested domain.

## Domain restriction
The modeled domain is tokens that are (1) **at most single-separator**
(`(chars.filter (· == '.')).length ≤ 1`) and (2) **ASCII** (`asciiToken chars`,
i.e. `∀ c ∈ chars, c.val < 128`), both carried as FIELDS of the input type
`RefToken` — every value the spec and theorem quantify over is in-domain by
construction, and `correct_modelRef` has no side hypotheses, so the theorem
pins the output on every expressible input (no out-of-hypothesis slack).

(1) matches the patch: `app_label, model_name = self.remote_field.model.split('.')`
unpacks into exactly two parts, so the patch itself assumes a single separator
(two-or-more would raise `ValueError: too many values to unpack`). A bare token
(`'.' ∉ t.chars`) and a single-dot token are the two in-domain shapes; both are covered
by the spec.

(2) pins the domain to the ASCII range on which the modeled per-character fold
`Char.toLower` provably equals the real `str.lower` callee. Non-ASCII code points
(e.g. `Σ`, `İ`, `ẞ`) are excluded because `Char.toLower` (ASCII-only) disagrees
there with Python's Unicode-aware `str.lower` — folding those inside the domain
would make the model unfaithful. The type encodes this restriction formally
rather than leaving it to prose, so no expressible input can witness a
Lean↔Python divergence.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The transformation is spelled
  out deeply: `str.split('.')` becomes `prefixSeg`/`nameSeg` (takeWhile/dropWhile
  on the separator), and `str.lower` becomes per-character `Char.toLower`. The
  proof needs no `axiom <callee>_prop`; `axiom_check.py` is a skip stub.
- `Char.toLower` (the per-character case fold) is recorded as an A-reference
  solely to document the G-CONF binding to the real `str.lower`.
- No flag dependency: the branch runs whenever `self.remote_field.model` is a
  `str`; no configuration affects the normalization.

## G-CONF fuzz seed
- pinned seed: `13112`
- ≥10^5 fuzzed reference tokens, drawn from the alphabet
  `{A, a, B, b, M, m, X, x, '_', '0', '9', '.'}` with lengths 0–10, restricted to
  the modeled domain (at most one `.`), to exercise: bare lower/mixed/upper
  tokens, qualified `prefix.name` tokens with mixed-case prefixes and names,
  leading/trailing `.`, and empty segments. Each token is checked against the
  REAL patched `ForeignKey.deconstruct` `kwargs['to']` value, exercised on a live
  `ForeignKey` whose string `to=` is the fuzzed token.
