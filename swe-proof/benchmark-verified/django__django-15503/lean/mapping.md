# mapping.md — django__django-15503

## Modeled function

`HasKeyLookup.as_sql` — the RHS JSON-path assembly loop.
File: `django/db/models/fields/json.py` @ base_commit.

- `compile_json_path` : `json.py:129-139`
- `HasKeyLookup.as_sql` (RHS branch, the changed region) : `json.py:186-206`
- the new `compile_json_path_final_key` : introduced by the patch at `json.py:175`
- `HasKeyOrArrayIndex` + the `KeyTransformIsNull`/oracle rewiring
  (`json.py:255-258`, `393-411`, `472-478`) : preserve the OLD (array-index)
  final-key behavior for the `isnull`/oracle path — see "Scope" below.

The Lean triple models the single, independently-observable behavioral change
that the FAIL_TO_PASS tests (`test_has_key_number`, `test_has_keys`) exercise:
the RHS path built for one key of a `has_key`/`has_keys`/`has_any_keys` lookup.

## Symbol binding

| Lean symbol | Python source | notes |
|---|---|---|
| `keyLookupPath` (modeled fn) | body of the `for key in rhs:` iteration in `HasKeyLookup.as_sql` producing one entry of `rhs_params` | one iteration = one assembled path string |
| `lhsJsonPath : String` | `lhs_json_path` (`"$"` or `compile_json_path(lhs_key_transforms)`) | the path prefix; an opaque input to the modeled behavior |
| `keys : List String` | `rhs_key_transforms` for this key (`[key]`, or the transforms from a nested `KeyTransform`) | the RHS key steps; precondition `keys ≠ []` (Python always has ≥1) |
| `result : String` | the appended entry `lhs_json_path + rhs_json_path` | one element of `rhs_params` |
| `encodeKey` (opaque) | `json.dumps(key_transform)` | JSON string serializer; renders a key as a quoted path token |
| `numericKey` | the `int(key_transform)` / `except ValueError` test in `compile_json_path` | non-empty digit run ⇒ positional index |
| `renderSegment` | one loop step of `compile_json_path(..., include_root=False)` | `[num]` for numeric, `.` + `json.dumps(k)` for named |
| `pathOfKeys` | `compile_json_path(rhs_key_transforms, include_root=False)` | the full RHS path builder (used on the intermediate keys) |
| `finalSegment` | new `compile_json_path_final_key` = `".%s" % json.dumps(key_transform)` | final key always addressed as a named member |

## Type bijection (Lean ↔ Python)

| Lean type | Python | bijection |
|---|---|---|
| `String` (key) | `str` (a `rhs_key_transforms` element, always coerced to `str` by `get_prep_lookup`/`str(item)`) | identity on text |
| `List String` | `list[str]` (`rhs_key_transforms`) | element-wise; order preserved |
| `String` (path) | `str` (SQL/JSON path fragment) | identity on text |
| `Option Nat` (`numericKey`) | success/failure of `int(str)` for a decimal-digit run | `some n` ↔ `int` succeeds with value `n`; `none` ↔ `ValueError` |

Note on `numericKey`: `int(s)` in CPython accepts surrounding whitespace and a
sign; but the keys reaching `compile_json_path` are JSON object member names /
list indices coerced with `str(...)`, and the behavior the fix and tests care
about is exactly the "a run of decimal digits is read as an array index" case
(`"1111"`, `"123"`, `"456"`, `"789"`, `"777"`, `"999"`, `"000"`). The
`numericKey` model captures that case precisely (`"000"` → `0`, matching
`int("000")`); non-digit keys are named members either way. Recorded here so
G-CONF/G-AX fuzz digit runs, mixed alnum, empty, and leading-zero keys.

## Callee provenance

- `encodeKey` ↔ `json.dumps` — UNCHANGED stdlib callee, used identically on
  every named-member key in BOTH the pre- and post-patch code. It is declared
  `opaque` (signature only); the proof needs NO property of it (the fix does not
  depend on how a key is escaped, only on WHICH renderer — positional vs named —
  is applied to the final key). Hence it is neither A-consumed nor A-reference —
  it is an opaque signature the impl carries. No `_prop` axiom is required.

## Scope — why one triple

The gold patch touches four call sites, but they collapse to ONE behavioral
change plus behavior-PRESERVING plumbing:

1. **The fix** (observable, tested): `HasKeyLookup.as_sql` now renders the final
   RHS key with `compile_json_path_final_key` (named member) instead of routing
   it through `compile_json_path` (which turns a digit-run key into an array
   index). This is what makes `has_key="1111"` match. Modeled by the triple.
2. **`HasKeyOrArrayIndex`** overrides `compile_json_path_final_key` to restore
   the OLD array-index rendering, and `KeyTransformIsNull`/`as_oracle` are
   rewired to use it. This deliberately keeps the pre-existing behavior for the
   `isnull`-on-array-index path — i.e. it is a no-op relative to base for those
   paths. It introduces no new observable behavior for the FAIL_TO_PASS tests
   (which use `HasKey`/`HasKeys`/`HasAnyKeys`, all of which get the new
   named-final-key behavior). Not separately modeled (no independent F2P
   behavior); it is behavior-preserving refactor plumbing around the one fix.

## G-CONF fuzz seed

Pinned seed: **15503**. Fuzz domain: `lhsJsonPath ∈ {"$", "$.a", "$[0]"}`;
`keys` = non-empty lists over the alphabet `{"foo","bar","1111","123","000",
"0","a1","", "12a", "ipsum"}` (lengths 1–4). The R/I shadow compares the Lean
impl (via `renderSegment`/`finalSegment`) against a Python reimplementation of
the post-patch RHS assembly. `encodeKey` is A-reference-free: the shadow uses a
fixed stub `encodeKey(k) = json.dumps(k)` on BOTH sides (it cancels), so the
comparison isolates the positional-vs-named routing that the fix changes.
