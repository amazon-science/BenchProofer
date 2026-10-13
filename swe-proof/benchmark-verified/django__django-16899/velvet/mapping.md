# mapping.md — django__django-16899

Symbol binding, the Lean↔Python type bijection (used by G-CONF), callee
provenance, and the pinned G-CONF fuzz seed. Spec provenance: **cold** (derived
only from `problem_statement`, the gold `patch`, and the repo source at
`base_commit = d3d173425fc0a1107836da5b4567f1c88253191b`).

Repo file under change: `django/contrib/admin/checks.py`.

## 1. The modeled function

| Lean | Python | location @ base_commit |
|---|---|---|
| `readonlyItemCheck` | `BaseModelAdminChecks._check_readonly_fields_item(self, obj, field_name, label)` | `django/contrib/admin/checks.py:761` |

`_check_readonly_fields_item` validates ONE entry of a model administrator's
`readonly_fields` configuration. It returns either `[]` (the entry is
acceptable) or a one-element list `[checks.Error(<message>, obj=…, id="admin.E035")]`
(the entry is unresolvable). The four short-circuiting acceptance checks
(`callable`, `hasattr(obj, …)`, `hasattr(obj.model, …)`, the field-registry
`get_field`) are **unchanged** by the patch; the ONLY change is the text of the
`checks.Error` message produced on the unresolvable path: it now interpolates
`field_name` ("… refers to '<field_name>', which is not a callable, …"). The
`obj=` and `id="admin.E035"` arguments of the `Error` are unchanged and out of
scope. `readonlyItemCheck` models the produced message: `none` ↔ `[]`,
`some msg` ↔ the single `checks.Error` carrying `msg`.

The enclosing `_check_readonly_fields` (which iterates the `readonly_fields`
tuple, building `"readonly_fields[%d]" % index` labels and `chain`-ing the
per-item results) is unchanged by the patch and out of scope; the patch edits
only the per-item message.

## 2. The type bijection (Lean ↔ Python), used by G-CONF

| Lean | Python (real repo type) |
|---|---|
| `isCallable : Bool` | `callable(field_name)` |
| `hasAttrAdmin : Bool` | `hasattr(obj, field_name)` |
| `hasAttrModel : Bool` | `hasattr(obj.model, field_name)` |
| `fieldUnknown : Bool` | `obj.model._meta.get_field(field_name)` raises `FieldDoesNotExist` (`True`) vs. resolves (`False`) |
| `label : List Char` | the `label` argument, e.g. `"readonly_fields[1]"` (`str` ↔ `List Char`, `Char.ofNat (ord ch)` ↔ `ch`) |
| `name : List Char` | the `field_name` argument (the configuration entry's name), `str` |
| `adminName : List Char` | `obj.__class__.__name__` (the administrator class name), `str` |
| `modelLabel : List Char` | `obj.model._meta.label` (the `app_label.ModelName` of the administered model), `str` |
| `Option (List Char)` (`out`) | `[]` ↔ `none`; `[checks.Error(msg, obj=…, id="admin.E035")]` ↔ `some msg` |

The four observations are taken as **FREE INPUTS** (no axioms): the spec makes
no behavioural claim about *when* `callable` / `hasattr` / `get_field` succeed —
it holds for EVERY combination. The four quoted strings are also free inputs.
The only thing the spec pins is *how the decision routes to a message and how
the four strings are arranged into that message* — which is exactly what the
patch changes.

## 3. Callee provenance (all UNCHANGED by the patch — hence free inputs, no G-AX)

| accessor | real callee | unchanged? |
|---|---|---|
| `isCallable` | builtin `callable` | yes — same call pre/post-patch |
| `hasAttrAdmin` | builtin `hasattr(obj, …)` | yes |
| `hasAttrModel` | builtin `hasattr(obj.model, …)` | yes |
| `fieldUnknown` | `Options.get_field` raising `FieldDoesNotExist` (`django/db/models/options.py`) | yes — same call, same control role pre/post-patch |
| `label` / `name` / `adminName` / `modelLabel` | `label` arg / `field_name` arg / `obj.__class__.__name__` / `obj.model._meta.label` | yes — the strings are read identically; only their arrangement into the message changes |

None of these is changed by the patch, so none is axiomatized; they are the
free inputs above. There is therefore nothing for G-AX to check against a real
callee (no `axiom_check.py`; `gate_ax` reports `status=skip`). The patch's whole
content is in the message construction — modeled deeply (`itemDiagnostic`,
explicit `List Char` concatenation) and differential-tested by G-CONF (§4).

## 4. G-CONF fuzz seed

`SEED = 16899`, `N_FUZZ = 100_000` (pinned, deterministic). The differential
test runs the R/I shadow of `readonlyItemCheck` against an ORACLE that
transliterates the **gold-patched** `_check_readonly_fields_item` message logic
verbatim, over random combinations of the four boolean observations and four
random strings (boundary combinations first, incl. the two F2P scenarios
`readonly_fields[1]`/`nonexistent`/`SongAdmin`/`admin_checks.Song` and
`readonly_fields[0]`/`i_dont_exist`/`CityInline`/`admin_checks.City`). The four
observations and four strings are handed IDENTICALLY to both SHADOW and ORACLE,
so the only thing under differential test is the message arrangement the patch
edits. See `conformance_check.py`.

### Oracle choice — why transliterate rather than run the real method

The real `_check_readonly_fields_item` needs a configured `ModelAdmin`/`Inline`
instance, an administered model class with migrated `Options`, and the app
registry — essentially the F2P Django test harness — purely to read back one
message string. The four observations it performs are UNCHANGED by the patch;
only how the resolved strings are arranged into the message changes. So, per the
worker prompt and the §3 oracle-choice precedent (django__django-11820), the
ORACLE is the patched message logic transliterated verbatim, with the unchanged
observations abstracted into the free boolean/string inputs handed to both
sides.
