# mapping.md — symbol binding & type bijection (django__django-13346)

## Modeled function
- **Lean** `implementation_inClauseSql : Vendor → Nat → List Char`
- **Python** the membership-lookup RHS renderer registered for key transforms on
  a JSON field: `<new lookup>.process_rhs(self, compiler, connection)` —
  `django/db/models/fields/json.py` @ base_commit (added by the gold patch,
  registered on `KeyTransform`).

The renderer first delegates to the base membership lookup
(`lookups.In.process_rhs` via `super()`), which for a direct value list of `n`
items produces the placeholder SQL fragment
`'(' + ', '.join(['%s'] * n) + ')'` = `(%s, %s, …, %s)` together with the bound
parameters. On a backend WITHOUT a native JSON column type, each value
placeholder must then be wrapped in that backend's JSON value-extraction
function so the bound value is compared against the *extracted* scalar/array
rather than the raw stored text. The wrap is done by
`rhs = rhs % func`, where `func` is an `n`-tuple of the wrapping template; the
`%s` inside each template element survives (single substitution pass), so

```
"(%s, %s)" % ("JSON_EXTRACT(%s, '$')",)*2  ==  "(JSON_EXTRACT(%s, '$'), JSON_EXTRACT(%s, '$'))"
```

On a backend WITH a native JSON column type the fragment is left exactly as the
base lookup produced it.

The observable behavior the F2P test (`test_key_in`, run on the SQLite eval
backend) demands: a single-element `__in` on a key transform must render the
value placeholder wrapped in the value-extraction function
(`(JSON_EXTRACT(%s, '$'))`), not bare (`(%s)`); only then does
`value__c__in=[14]` match the same rows as the scalar key lookup.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| database backend identity (`connection.vendor` + `connection.features.has_native_json_field`) | `vendor : Vendor` (enum) | the four modeled string-builder backends; native-JSON-ness is a function of the vendor (`hasNativeJson`) |
| `len(rhs_params)` = number of `__in` values (None-stripped) | `n : Nat` | one value placeholder per element; `n ≥ 1` (empty list ⇒ `EmptyResultSet`, never reaches the renderer) |
| rendered RHS placeholder SQL (`rhs`) | `List Char` | per-character; the unchanged `rhs_params` list is out of model scope |

`Vendor` enum ↔ Python `connection.vendor` / native flag:
| Lean | Python | `has_native_json_field` |
|---|---|---|
| `Vendor.postgresql` | `vendor == 'postgresql'` | `True` (native ⇒ no wrap) |
| `Vendor.sqlite` | `vendor == 'sqlite'` | `False` ⇒ wrap `JSON_EXTRACT(%s, '$')` |
| `Vendor.mysql` | `vendor == 'mysql'`, not MariaDB | `False` ⇒ wrap `JSON_EXTRACT(%s, '$')` |
| `Vendor.mariadb` | `vendor == 'mysql'` and `mysql_is_mariadb` | `False` ⇒ wrap `JSON_UNQUOTE(JSON_EXTRACT(%s, '$'))` |

## Callee provenance
- `super().process_rhs` (`lookups.In.process_rhs`) builds the base placeholder
  `(%s, …, %s)`. UNCHANGED by the patch; reproduced concretely as
  `basePlaceholder n` (I-tagged), so no `opaque`/axiom is needed.
- `rhs % func` (Python `%`-substitution of the `n`-tuple of wrap templates into
  the base placeholder) is reproduced concretely as the equivalent fixed-order
  build `'(' + ', '.join([wrapper] * n) + ')'` (I-tagged). The `%s` markers
  inside `wrapper` are literal and survive the single substitution pass, so the
  rebuild is exact.
- The per-vendor wrap template (`'JSON_EXTRACT(%s, '$')'` etc.) is the **changed
  op**, modeled deeply as `valueExtractor` (R/I), NOT axiomatized.
- No UNCHANGED callee property is consumed: the axioms region is empty; G-AX is a
  skip stub.

## Scope note (Oracle sub-behavior NOT modeled)
The gold also adds an Oracle branch that, instead of a fixed wrap template,
round-trips each bound value through a JSON deserialize/serialize
(`json.loads` then `json.dumps({'value': value})`), picks a query-vs-value
extraction function by the value's runtime type (list/dict vs scalar), and
clears the bound-parameter list. That is a distinct sub-behavior requiring a
full JSON-value serialization model; it is **out of model scope** and excluded
from the `Vendor` enum (the renderer's `vendor == 'oracle'` path). Justification:
(a) the SWE-bench eval harness runs on SQLite, so the Oracle branch is exercised
by neither G-RESOLVE nor the F2P `test_key_in`; (b) the public issue's primary
report is MySQL/SQLite; (c) the four modeled backends already pin the
fix's core string-builder behavior (wrap-vs-bare placeholder) that the F2P test
discriminates. This mirrors the type-only scope restrictions used elsewhere
(e.g. django-10880 scoping the orthogonal filter branches).

## Frame discipline
The renderer returns `(rhs, rhs_params)`. For every modeled vendor the fix
leaves `rhs_params` exactly as the base lookup produced it (unchanged), so it is
not a fix-observable output component and is out of model scope; only `rhs`
(fully pinned to `vendor` and `n` by `problem_spec_inClauseSql`) is modeled.

## G-CONF fuzz seed
Pinned seed: **13346**. ≥10^5 fuzzed inputs over the four modeled vendors and
`__in` list lengths `n ∈ [1, 12]` (plus deterministic boundary cases incl. the
exact `n = 1` F2P shape).
