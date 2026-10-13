# mapping.md — django__django-13925

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0c42cdf0d2422f4c080e93594d5d15381d6e955e`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance / flag-dependency of every observation the decision reads.

Repo file under change: `django/db/models/base.py`. The gold patch adds one
conjunct to the boolean guard of `Model._check_default_pk` (the routine that
emits the `models.W042` advisory): it suppresses the advisory when the model's
auto-created primary key is the implicit key inherited from an ancestor model
(a parent-link one-to-one relation to the parent).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `implicitPrimaryKeyAdvisory (…)` | `Model._check_default_pk(cls)` — `django/db/models/base.py:1298-1320` | the modeled changed routine: returns `[W042]` iff the guard holds, else `[]` |
| `out : Bool` | whether the returned list is `[Warning(... id='models.W042')]` (`true`) vs `[]` (`false`) — `base.py:1304-1319` / `1320` | the single observable the F2P tests assert (warning present or absent) |
| `pkAutoCreated` | `cls._meta.pk.auto_created` — `base.py:1300` | the model's primary key was auto-supplied (not declared on this model) |
| `pkInheritedFromAncestor` | `isinstance(cls._meta.pk, OneToOneField) and cls._meta.pk.remote_field.parent_link` — added at `base.py:1301-1305` (post-patch) | that auto-created PK is the implicit parent-link key inherited from an ancestor model |
| `defaultKeyTypeConfigured` | `settings.is_overridden('DEFAULT_AUTO_FIELD')` — `base.py:1301` (pre) / `1306` (post) | a project-wide default primary-key type is configured |
| `appKeyTypeConfigured` | `cls._meta.app_config._is_default_auto_field_overridden` — `base.py:1302` (pre) / `1307` (post) | the model's own application configures a default primary-key type |

`OneToOneField` is imported in `base.py` from
`django.db.models.fields.related` (`base.py:25-27`); `remote_field.parent_link`
is the boolean flag set on a child model's auto-generated link field to its
parent (multi-table inheritance). The F2P tests construct models with and
without that parent-link relation and assert the advisory list.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. Every guard input is read **only** as a
boolean (`bool(...)` truthiness / an `and`-chain of boolean tests), so each maps
to a Lean `Bool`; the output is the presence/absence of the single advisory, a
`bool`.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `cls._meta.pk.auto_created` : bool | `pkAutoCreated : Bool` | exact (`True ↔ true`, `False ↔ false`) |
| `isinstance(cls._meta.pk, OneToOneField) and cls._meta.pk.remote_field.parent_link` : bool | `pkInheritedFromAncestor : Bool` | exact; the whole `isinstance(...) and ...parent_link` sub-expression is the single boolean "the PK is the inherited parent-link key" |
| `settings.is_overridden('DEFAULT_AUTO_FIELD')` : bool | `defaultKeyTypeConfigured : Bool` | exact |
| `cls._meta.app_config._is_default_auto_field_overridden` : bool | `appKeyTypeConfigured : Bool` | exact |
| `x and y` (all operands bool) | `x && y` | short-circuit conjunction; both are pure boolean tests with no side effects, so `and` ↔ `&&` |
| `not x` | `!x` | boolean negation |
| return `[Warning(..., id='models.W042')]` vs `[]` | `out = true` vs `out = false` | the list is a one-element advisory iff the guard holds, else empty (`base.py:1304-1320`); the tests compare exactly these two shapes |

The body's emitted `Warning`'s message/hint/`obj` are not behavior the guard
governs — they are produced unconditionally once the guard fires (`base.py:1304-1319`)
and are unchanged by the patch; the F2P discrimination is purely "is the
advisory present for this model?" Hence the observable is the boolean `out`.

## 3. Callee provenance — none (no axioms, G-AX skip)

There is no axiomatized callee and no deep-model reference. Every operand of the
guard is a direct boolean attribute read / `isinstance` test on already-resolved
model metadata (`cls._meta.pk`, its `remote_field.parent_link`, the settings and
app-config flags). The patch neither calls into nor changes any helper routine;
it only conjoins one more boolean test into an existing `if`. So there is no
external routine whose return value the spec contracts — nothing for G-AX to
validate. `axiom_check.py` is therefore omitted and `meta.json` records
`gates.G-AX.status = "skip"`. (Mirrors django__django-12276, also a pure
boolean-guard change with no contracted callee.)

### Flag dependency (for completeness)
`pkInheritedFromAncestor` is the conjunction `isinstance(pk, OneToOneField) AND
pk.remote_field.parent_link`: an explicit `OneToOneField(..., parent_link=True)`
the user writes AND the implicit parent link Django auto-creates for multi-table
inheritance both set `auto_created`/`parent_link` such that the model's `pk`
becomes that link. A plain `OneToOneField` without `parent_link` (or any
non-O2O auto field) does NOT set this true — which is why the bundle models the
whole sub-expression as one boolean rather than its pieces.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13925`** so the
consumer-side verdict (§11.3) is reproducible. The shadow it builds
transliterates the `implicitPrimaryKeyAdvisory` post-image boolean expression to
Python; the oracle is the patched guard of `_check_default_pk` transliterated
verbatim (the four boolean operands left as free inputs, since each is an
independent observation of the model/environment). It differential-tests over
all 2⁴ = 16 boolean combinations plus seeded fuzz.
