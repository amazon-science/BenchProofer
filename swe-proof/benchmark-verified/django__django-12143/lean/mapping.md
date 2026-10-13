# mapping.md — django__django-12143

## Instance
- repo: django/django
- base_commit: 5573a54d409bb98b5c5acdb308310bed02d392c2
- changed file: `django/contrib/admin/options.py`
- changed function: `ModelAdmin._get_edited_object_pks(self, request, prefix)`
  (file:line 1631–1633 @ base_commit; gold edit wraps the formset `prefix`
  argument in `re.escape(...)` before it is interpolated into the per-row
  primary-key matching pattern).

## What the real code does (@ base_commit, pre-patch)

```python
def _get_edited_object_pks(self, request, prefix):
    """Return POST data values of list_editable primary keys."""
    pk_pattern = re.compile(r'{}-\d+-{}$'.format(prefix, self.model._meta.pk.name))
    return [value for key, value in request.POST.items() if pk_pattern.match(key)]
```

It compiles a pattern of the form `<prefix>-\d+-<pkName>$`, then returns the
POST values whose key matches (`re.match`, i.e. anchored at the start, and the
trailing `$` anchors the end). The gold patch changes only the pattern
*construction*: `prefix` becomes `re.escape(prefix)`, so the formset prefix is
matched as a literal string instead of as a regex fragment.

## Modeled function (the Lean triple)

| Lean symbol | Python counterpart |
|---|---|
| `implementation_rowKeySelection` / `problem_spec_rowKeySelection` / `correct_rowKeySelection` | the `[value for key, value in request.POST.items() if pk_pattern.match(key)]` selection in `_get_edited_object_pks`, with the **fixed** (escaped-prefix) pattern |
| `matchesRowKey mark pkName key` (deep-modeled, A-reference) | `re.compile(r'{}-\d+-{}$'.format(re.escape(prefix), pkName)).match(key)` is truthy |
| `stripPrefix?` (pure helper) | the start-anchored literal `<re.escape(prefix)>` head, and the literal `pkName` segment |
| `isDecimalDigit` / `digitRanges` (pure helpers) + the `takeWhile/dropWhile isDecimalDigit` split inside `matchesRowKey` | the `\d+` middle segment: a non-empty run of **Unicode decimal digits** (general category Nd) — see the digit-class note below |
| `atEnd` (pure helper) | the `$` end anchor: end of the key, or a position just before ONE final `'\n'` — see the end-anchor note below |
| input `items : List (List Char × α)` | `request.POST.items()` — ordered `(key, value)` pairs |
| input `mark : List Char` | the `prefix` argument (a formset prefix; **no** syntactic restriction — may contain any character) |
| input `pkName : List Char` | `self.model._meta.pk.name` — a Python **identifier** (`[A-Za-z0-9_]`, not starting with a digit), hence regex-literal; matched literally |
| result `List α` | the returned list of POST values |

### Type bijection (Lean ↔ Python) — used by G-CONF and G-AX
- Python `str` (per-code-point) ↔ Lean `List Char`.
- A POST key/prefix/pk-name string ↔ its `String.toList` / `List Char`.
- A POST value is an opaque payload never inspected by the selection logic, so
  it is modeled by an arbitrary element type `α` (frame: values pass through
  untouched, in order). In G-CONF the value carrier is a `str`.
- `request.POST.items()` order ↔ Lean list order (insertion order preserved).

### `matchesRowKey` semantics (the deep model of the fixed matcher)
`matchesRowKey prefix pkName key = true` iff `key` decomposes **literally** as
`prefix ++ ['-'] ++ ds ++ ['-'] ++ pkName ++ tail` where `ds` is a non-empty
run of Unicode decimal digits (`isDecimalDigit`) and `tail` passes `atEnd`
(empty, or exactly `['\n']`). This is exactly the behavior of
`re.match(r'<re.escape(prefix)>-\d+-<pkName>$', key)` on the instance image's
engine, with no domain restriction on the key alphabet: the escaped prefix
matches literally, so the head is a literal prefix; `\d+` is the non-empty
Unicode-digit run; the trailing literal `pkName` plus `$` pins the tail to the
end of the key (modulo the one-trailing-newline tolerance of `$`).

#### Digit-class note (`\d` ↔ `isDecimalDigit`)
The pattern uses `\d` (not `[0-9]`) over a Python 3 `str`, so it is
Unicode-aware: it accepts the decimal digits of every decimal number system
(Unicode general category Nd), not only `'0'..'9'`. The model reproduces this
exactly: `isDecimalDigit` tests membership in `digitRanges`, the inclusive
code-point bounds of every Nd run per the Unicode data shipped with the
instance image's Python (3.6, unidata 9.0.0; the range table was extracted
mechanically in-container by enumerating `re.compile(r'\d').match(chr(i))`
over all scalar values — 54 runs, 580 code points, `0x30-0x39` through
`0x1E950-0x1E959`). The G-CONF fuzzer exercises non-Latin decimal digits and
digit-like non-Nd near-misses (superscripts, fractions, circled digits) so
this correspondence is differentially tested, not assumed.

#### End-anchor note (`$` ↔ `atEnd`)
Python's `re` `$` (without `re.MULTILINE`) matches at the end of the string
**or** just before a single trailing `'\n'`. `atEnd cs := cs.isEmpty || cs ==
['\n']` captures exactly this: after the literal `pkName`, either nothing
remains, or exactly one trailing newline remains. Verified against the real
engine in the G-CONF fuzz harness over keys carrying trailing `'\n'`s.

### Callee provenance + flag deps
- The regex engine (`re.compile` / `re.match`) and `re.escape` are **UNCHANGED**
  callees. Their *composite* effect on the matching decision — "the formset
  prefix is matched literally" — is modeled DEEPLY by `matchesRowKey`
  (A-reference), and validated against the real `re` engine by
  `conformance_check.py` (G-CONF). No callee is consumed as an axiom; there is
  no `opaque`/`axiom` declaration.
- No flag dependency.

### Domain assumptions (carried as fuzz constraints, faithful to the real call)
- `pkName` is a Python identifier: ASCII letters/digits/underscore, not starting
  with a digit (so it is regex-literal and contains no `-`). `re.match` does not
  escape it in either the pre- or post-patch code; an identifier needs none.
- No restriction on the key or prefix alphabets: the model covers Unicode
  decimal digits in the row-index position and trailing newlines at the end
  anchor directly (`isDecimalDigit`, `atEnd`), so no input class is excluded
  from the modeled domain.

## G-CONF fuzz seed (pinned)
`conf_seed = 20240627` (also in meta.json).
