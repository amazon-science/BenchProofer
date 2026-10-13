# mapping.md — django__django-14792

## Instance
- repo: django/django
- base_commit: d89f976bddb49fb168334960acc8979c3de991fa
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
The gold patch changes how the display name of a time zone is chosen. Previously
the helper always returned the full textual form of the time-zone object. After
the patch it first asks the time-zone object for its short self-reported label
and uses that whenever the label is present and non-empty; only when the label is
absent or empty does it fall back to the full textual form. This makes
fixed-offset zones present themselves by their offset designation (e.g. `+10`)
while named zones keep their full textual form (e.g. `Europe/Madrid`).

```python
# post-patch  (django/utils/timezone.py:72)
def _get_timezone_name(timezone):
    return timezone.tzname(None) or str(timezone)
```

`timezone.tzname(None)` returns a `str` or `None`; Python `or` selects the
right-hand operand when the left is falsy (`None` **or** the empty string `''`).

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_getTimezoneName` | `_get_timezone_name` (django/utils/timezone.py:72) |
| `problem_spec_getTimezoneName`   | the post-condition this function must satisfy |

## Type bijection (Lean ↔ Python) — used by G-CONF / G-AX
| Lean | Python | notes |
|---|---|---|
| `tzLabel : Option String` | `timezone.tzname(None)` | a `str` or `None`. `None ↔ none`; a `str` `v ↔ some v`. The empty-string label `''` maps to `some ""` — falsy in Python `or`, handled by the empty-string branch of the spec. |
| `tzStr : String` | `str(timezone)` | the full textual form; always available (a non-optional `str`). |
| result `: String` | return value (str) | the chosen display name. |

`String` ↔ Python `str` is the identity bijection (byte-for-byte).

## Callee provenance / flag deps
- No unchanged repo callee is consumed. The two observables read off the
  time-zone object — its short self-reported label (`timezone.tzname(None)`) and
  its full textual form (`str(timezone)`) — enter as plain data (`Option String`
  / `String`). The only operation performed is the truthiness selection between
  them, modeled directly as Lean `match` + `if s ≠ ""`. There is no `opaque`
  callee and no `axiom <callee>_prop`; the `axioms` region is empty and
  `axiom_check.py` is a skip stub.
- Truthiness note: Python `a or b` returns `a` iff `a` is truthy. For a `str`/
  `None` left operand, the falsy cases are exactly `None` and `''`. The spec's
  two clauses (`some s, s ≠ ""` ⇒ label; `none ∨ some ""` ⇒ full form) cover this
  exhaustively.

## G-CONF fuzz seed
- pinned seed: `14792`
- ≥10^5 fuzzed `(tzLabel, tzStr)` tuples, drawn both from real time-zone objects
  (datetime fixed-offset with/without name, pytz/zoneinfo named and fixed-offset —
  the F2P examples) and from synthetic `(Option str, str)` pairs that exercise the
  `none` / `some ""` / `some nonempty` boundaries.
