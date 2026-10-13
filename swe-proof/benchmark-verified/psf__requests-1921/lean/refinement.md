# refinement.md — psf__requests-1921

Modeled function: `merge_setting` (both-operands-are-`Mapping` tail; the only part
the fix touches). Lean: `implementation_effectiveSetting`.

The patch (gold) adds, after the per-request `None`-deletion loop and before the
`return`, the line:
```
merged_setting = dict((k, v) for (k, v) in merged_setting.items() if v is not None)
```
The pre-existing code (context, unchanged) is the session→merged copy, the
request `.update`, and the per-request `del`-on-`None` loop.

## Operation correspondence

| # | `implementation_effectiveSetting` op | `patch.diff` / repo counterpart | tag |
|---|---|---|---|
| 1 | `let mut merged := ses` | `merged_setting = dict_class(to_key_val_list(session_setting))` — start from session defaults | R (dict ↔ ordered assoc-list `List Entry`; `to_key_val_list` on a dict = `.items()` = identity in the model) |
| 2 | `for p in req do merged := dictSet merged p.1 p.2` | `merged_setting.update(to_key_val_list(request_setting))` — request entries overlay/override by key | R (`dict.update` ↔ in-place `dictSet` fold; existing key replaced in place, new key appended) |
| 3 | `for p in req do if p.2.isNone then merged := merged.filter (·.1 != p.1)` | `for (k, v) in request_setting.items(): if v is None: del merged_setting[k]` — drop keys the REQUEST nulled | I (per-request null-deletion loop, line-for-line) |
| 4 | `merged := merged.filter (·.2.isSome)` | **the added line:** `dict((k,v) for (k,v) in merged_setting.items() if v is not None)` — drop EVERY remaining null-valued entry (this catches nulls inherited from the session defaults) | I (filter to value-present entries; this IS the fix) |
| 5 | `return merged` | `return merged_setting` | I |

Every step is R or I. No A-consumed (the proof uses no callee axiom). No
A-reference (no deeply-modeled unchanged callee). No changed op is inexpressible
— the fix is a pure structural list filter, modeled exactly.

`conf_skip = false`: the impl region is all R/I (no A-tagged op), so G-CONF
mechanically differential-tests it against the patched repo `merge_setting`.

`axiom_check.py` is a skip stub (G-AX = skip): there is no consumed `_prop`
axiom to validate.

## Domain / scope notes
- **Unique keys.** `List Entry` models a Python *dict* (insertion-ordered, unique
  keys). The real call site only ever passes dicts, so duplicate-key lists are
  outside the modeled domain; G-CONF fuzzes exclusively over `OrderedDict`-built
  inputs (unique keys), matching the real domain. The spec is nonetheless stated
  for ALL `req ses` (no precondition) because `implementation = effective` holds
  unconditionally — both sides share the identical `dictSet`/`filter` fold
  structure — which keeps the contract maximally strong against G-PANEL: an
  attacker's wrong impl must equal `effective` on every input, not just unique-key
  ones.
- **`dict_class`.** The model fixes the default `OrderedDict` (case-sensitive,
  insertion-ordered) semantics. The header call site's `CaseInsensitiveDict` is an
  orthogonal key-type concern the fix does not touch (see mapping.md).
- **`dropNulledKeys` (step 3) is retained for skeleton fidelity.** Under unique
  keys it is redundant with the final value-present filter (step 4), but the
  patched repo function keeps BOTH the per-request `del`-on-`None` loop and the
  new comprehension, so the impl — and the `effective` shadow it mirrors — keep
  both to stay a line-for-line skeleton of the fix (SPEC_GUIDE §0.3).
