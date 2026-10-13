# mapping.md — django__django-16667

## Symbol binding (file:line @ base_commit 02c356f2f3945b8075735d485c3cf48cad991011)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_coerceDateEntry` / `problem_spec_coerceDateEntry` | the date-construction `try/except` block inside `SelectDateWidget.value_from_datadict` | `django/forms/widgets.py:1158-1164` |
| `DateEntry` (pure helper) | the trichotomy of outcomes of `datetime.date(int(y), int(m), int(d))`: succeeds / raises `ValueError` / raises `OverflowError` | `django/forms/widgets.py:1159-1163` |
| `pseudoIso` (pure helper) | `"%s-%s-%s" % (y or 0, m or 0, d or 0)` — the pseudo-ISO fallback | `django/forms/widgets.py:1163` |
| `rendered` (input) | `date_value.strftime(input_format)` — the canonical rendering of a representable date | `django/forms/widgets.py:1164` |
| `y`, `m`, `d` (inputs, `String`) | the raw `data.get(...)` text for the year / month / day sub-widgets | `django/forms/widgets.py:1150-1152` |
| `result` (output, `Option String`) | the value `value_from_datadict` hands on (`some s`) vs an uncaught failure that produces none (`none`) for this `(y, m, d)` triple | the three `return` statements at `:1163`, `:1164`, and the patched `"0-0-0"`; pre-fix the OverflowError outcome produced no return (`none`) |

The modeled function is the date-coercion block of `SelectDateWidget.value_from_datadict`.
It is the only behavior the patch changes and the behavior the FAIL_TO_PASS tests
observe (`test_form_field`, `test_value_from_datadict`): a month component of
`str(sys.maxsize + 1)` must coerce to `"0-0-0"` (and the field then rejects it as
invalid) rather than crashing the request with an uncaught `OverflowError`.

### What the function does (base_commit, lines 1149-1165)

```python
def value_from_datadict(self, data, files, name):
    y = data.get(self.year_field % name)
    m = data.get(self.month_field % name)
    d = data.get(self.day_field % name)
    if y == m == d == "":
        return None
    if y is not None and m is not None and d is not None:
        input_format = get_format("DATE_INPUT_FORMATS")[0]
        input_format = formats.sanitize_strftime_format(input_format)
        try:
            date_value = datetime.date(int(y), int(m), int(d))
        except ValueError:
            # Return pseudo-ISO dates with zeros for any unselected values,
            # e.g. '2017-0-23'.
            return "%s-%s-%s" % (y or 0, m or 0, d or 0)
        return date_value.strftime(input_format)
    return data.get(name)
```

The modeled block is `:1158-1164` (the `try`/`except`/`return`). Three outcomes
of `datetime.date(int(y), int(m), int(d))`:

1. **succeeds** — the three components denote a representable calendar date; the
   value handed on is `date_value.strftime(input_format)` (the canonical
   rendering). Modeled as `DateEntry.valid`, result `= rendered`.
2. **raises `ValueError`** — `int(...)` fails (non-numeric text) or `date(...)`
   rejects an impossible month/day/out-of-range year; the value handed on is the
   pseudo-ISO fallback `"%s-%s-%s" % (y or 0, m or 0, d or 0)`. Modeled as
   `DateEntry.malformed`, result `= pseudoIso y m d`.
3. **raises `OverflowError`** — a component is a syntactically valid integer but
   too large to convert to a C `long` for `date`'s constructor (`int(y) >
   sys.maxsize`); at base_commit this is UNCAUGHT and crashes the request. The
   patch adds `except OverflowError: return "0-0-0"`. Modeled as
   `DateEntry.unrepresentable`, result `= "0-0-0"`.

The `"0-0-0"` sentinel is itself not a representable date, so the subsequent
`DateField` parse rejects the entry (`"Enter a valid date."`) rather than
crashing — exactly the F2P assertions.

### Lean modeling

- The classification of the entry (which of the three outcomes
  `datetime.date(int(y), int(m), int(d))` produces) is determined by the
  UNCHANGED callees `int` and `datetime.date`. The patch does NOT change how the
  entry is classified — only what value the OverflowError branch hands on. The
  classification therefore enters this computation as an arbitrary input
  `c : DateEntry`; this computation only DISPATCHES on it. It is not axiomatized
  (no `opaque`/`axiom` is needed): the dispatch is modeled deeply and the binding
  of `c`/`rendered` to the real callees is differential-tested by G-CONF.
- `rendered : String` is the canonical rendering produced on the `valid` outcome
  (`date_value.strftime(input_format)`). It is an arbitrary input — the patch
  does not touch it and the dispatch only passes it through unchanged.
- `pseudoIso y m d` is the pure helper modeling `"%s-%s-%s" % (y or 0, m or 0,
  d or 0)`: an empty component renders as the single character `"0"`, any other
  (numeric or not) renders as itself. (Python truthiness: `"" or 0` is `0`,
  rendered `"0"`; any non-empty string is truthy and rendered verbatim.)

## Lean ↔ Python type bijection (used by G-CONF + G-AX)

| Python | Lean | bijection |
|---|---|---|
| the raw `data.get(...)` strings for year/month/day | `y m d : String` | identity on text |
| outcome of `datetime.date(int(y), int(m), int(d))` (success / `ValueError` / `OverflowError`) | `c : DateEntry` (`valid` / `malformed` / `unrepresentable`) | the trichotomy above; computed in G-CONF by actually running `int`+`datetime.date` |
| `date_value.strftime(input_format)` | `rendered : String` | identity on text (same `input_format` in both legs) |
| `"%s-%s-%s" % (y or 0, m or 0, d or 0)` | `pseudoIso y m d` | empty ↦ `"0"`, else verbatim, joined by `"-"` |
| the value `value_from_datadict` returns for this triple (vs an uncaught failure producing no value) | `result : Option String` | `some s` ↔ a value `s` is handed on; `none` ↔ no value produced (uncaught failure). In G-CONF, modeled as the tag `("some", s)` vs `("none", None)`; the post-patch block is always `("some", …)`. |

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The behavior the patch changes — what the
  OverflowError outcome hands on — is modeled DEEPLY (`DateEntry.unrepresentable
  → "0-0-0"`), never axiomatized (SPEC_GUIDE §3). The dispatch on the classified
  entry is all R/I. The `axioms` region is empty and **G-AX skips**.
- `int(...)` / `datetime.date(...)` — the UNCHANGED callees whose
  raise-or-succeed behavior CLASSIFIES the entry. The patch does not change them;
  it only adds a handler for one outcome they already produced. Their
  classification is captured by the input `c`, and the binding `(y, m, d) ↦ c`
  is exercised by G-CONF (which runs the real `int`+`datetime.date`), not assumed.
- `date_value.strftime(input_format)` — the UNCHANGED rendering of a representable
  date, captured by the input `rendered`. Unchanged by the patch; passed through.
- `get_format("DATE_INPUT_FORMATS")[0]` / `formats.sanitize_strftime_format` — the
  input-format lookup, UNCHANGED and orthogonal to the fix. Not modeled; it only
  affects the exact text of `rendered`, which the spec treats as an opaque input
  (the same `input_format` is used in both G-CONF legs, so it cancels).
- The outer guards (`y == m == d == ""` ⇒ `None`; any of `y/m/d` is `None` ⇒
  `data.get(name)`) are UNCHANGED and precede the modeled block; they are not part
  of the modeled function. The F2P tests reach the modeled block (all three
  components present and non-empty).

## G-CONF fuzz seed

Pinned LCG seed: **16667** (see `conformance_check.py` `SEED`). Corpus: triples
`(y, m, d)` of strings crossed over the cases that drive the three outcomes —
empty strings, non-numeric text, ordinary in-range numbers, impossible
month/day (`"0"`, `"13"`, `"32"`), out-of-range years (`"0"`, `"10000"`), and
magnitudes above `sys.maxsize` (`str(sys.maxsize + 1)` and larger) so the
`OverflowError` branch fires — over ≥1e5 fuzzed inputs. The R/I shadow of
`implementation_coerceDateEntry` (with `c`/`rendered` computed by running the real
`int`+`datetime.date`+`strftime`) is diffed against an in-process replica of the
POST-PATCH date-coercion block. Hand-picked edge cases pin the discriminating
clause: a component `> sys.maxsize` ⇒ result `"0-0-0"` (pre-fix: uncaught crash).
