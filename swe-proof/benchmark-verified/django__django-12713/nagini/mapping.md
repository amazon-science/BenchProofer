# mapping.md — django__django-12713

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 5b884d45ac5b76234eca614d90c83b347294c332`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/contrib/admin/options.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_component(options, test_primary, test_secondary, test_tertiary)` | `ModelAdmin.formfield_for_manytomany(self, db_field, request, **kwargs)` — `django/contrib/admin/options.py:242` (the widget-selection block, body lines 252-260) | the modeled changed function: the keyword-option widget-selection block |
| `options` (`Dict[int, int]`) | the `**kwargs` dict of `formfield_for_manytomany` (`options.py:242`) | the keyword options being assembled; mutated in place |
| `component_present` (`bool`) | the value of `'widget' in kwargs` evaluated AT ENTRY to `formfield_for_manytomany` (i.e. before the guarded selection block at `options.py:252` runs) | spec-only capture of the entry presence of the presentation component; pinned by `Requires(component_present == (key_component() in options))`. Lets the default-selection postcondition gate on the genuine entry state rather than on a post-mutation membership query. No runtime counterpart in the patch (the live guard `if 'widget' not in kwargs` is logically equal to `not component_present` at entry). |
| `key_component()` (`== 0`) | the string literal key `'widget'` (`options.py:253,255,257`) | the presentation-component option name |
| `test_primary` (`bool`) | `db_field.name in autocomplete_fields` where `autocomplete_fields = self.get_autocomplete_fields(request)` (`options.py:252-253`) | highest-priority name-membership test |
| `test_secondary` (`bool`) | `db_field.name in self.raw_id_fields` (`options.py:254`) | second-priority name-membership test |
| `test_tertiary` (`bool`) | `db_field.name in [*self.filter_vertical, *self.filter_horizontal]` (`options.py:256`) | third-priority name-membership test (combined filter set) |
| `default_primary()` (`== 1`) | `AutocompleteSelectMultiple(db_field.remote_field, self.admin_site, using=db)` (`options.py:253`) | component identity selected by the primary test |
| `default_secondary()` (`== 2`) | `widgets.ManyToManyRawIdWidget(db_field.remote_field, self.admin_site, using=db)` (`options.py:255`) | component identity selected by the secondary test |
| `default_tertiary()` (`== 3`) | `widgets.FilteredSelectMultiple(db_field.verbose_name, db_field.name in self.filter_vertical)` (`options.py:257-260`) | component identity selected by the tertiary test |

The sibling function the issue compares against,
`ModelAdmin.formfield_for_foreignkey` (`options.py:218`), already wraps its
widget-selection block in `if 'widget' not in kwargs:` (`options.py:224`); the
fix brings `formfield_for_manytomany` into line with it. (Not referenced from
the consumer spec view; provenance only.)

How a caller-supplied component reaches the options dict: `formfield_overrides`
(`options.py:148-149`) merges the per-field-class overrides into `kwargs`
*before* `formfield_for_manytomany` is invoked
(`kwargs = {**self.formfield_overrides[db_field.__class__], **kwargs}`), so a
`{'widget': forms.CheckboxSelectMultiple}` override arrives as `'widget' in
kwargs` (i.e. `key_component() in options` on entry). This is precisely the
entry state the F2P test exercises.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `**kwargs` dict (`str` keys → widget objects / arbitrary values) | `Dict[int, int]` (option-name token → component-identity token) | only membership of `'widget'` and its value are observed by the changed block; integer identity is the faithful carrier. `'widget'` ↔ `key_component() == 0`; any other option-name ↔ a distinct non-zero key; widget object identities ↔ distinct int codes |
| string-literal key `'widget'` | `key_component()` (`int` token `0`) | the one option key the block reads/writes |
| `db_field.name in <configured set>` (a membership test on `str`) | `bool` parameter (`test_primary` / `test_secondary` / `test_tertiary`) | each test is observationally a boolean; a `bool` needs no permission and carries the exact branch condition. Priority order primary>secondary>tertiary ↔ autocomplete>raw_id>filter (the if/elif order in the repo) |
| widget constructor results `AutocompleteSelectMultiple(...)`, `ManyToManyRawIdWidget(...)`, `FilteredSelectMultiple(...)` | `default_primary()` / `default_secondary()` / `default_tertiary()` (distinct `int` codes 1/2/3) | the block only stores these objects under `'widget'`; their identity (which of the three, vs. a caller-supplied component) is what the F2P test observes. A caller-supplied component (e.g. `CheckboxSelectMultiple`) is a value DISTINCT from all three (modeled as any other int) |

`options` is genuinely **mutated** in place by the block (the repo assigns
`kwargs['widget'] = ...`), so it is held at FULL permission and its exact
post-state is pinned (the entry membership/value of each key is captured with
`Old`). No `str` indexing is used (Nagini bans it); the option key is the
integer token `key_component()`.

## 3. Callee provenance — no axiomatized callee

There is **no `@ContractOnly` axiom** in this bundle. The changed operation —
guarding the widget-selection block with `if 'widget' not in kwargs:` — is
composed entirely of Python language primitives the gold patch uses directly:

  * the dict membership test `'widget' in kwargs` (real `dict.__contains__`),
  * the dict assignment `kwargs['widget'] = <component>` (real `dict.__setitem__`),
  * the `if / elif` priority chain over the three boolean membership tests.

These are modeled **deeply** in `model.py` (the `impl` region spells out the
exact guard + priority chain over a `Dict[int, int]`); they are not hidden
behind any axiom. The three widget constructors and the three name-set
membership tests are not *changed* by the patch and are abstracted as opaque
identities/booleans (their internals are irrelevant to the precedence behavior
under specification), so no contract about them is needed or consumed.

**Soundness check (G-AX / `axiom_check.py`):** the deep model (the
A-reference) is validated against the real Python primitives. `axiom_check.py`
reproduces the gold patch's exact control flow over a real `dict` and asserts
every observation meets `model.py`'s frozen postconditions — preservation of a
caller-supplied component and of all other entry keys, addition of no key but
the presentation key, and the priority-ordered default selection when the
presentation key is absent — across 7 boundary option-maps × 8 boolean-flag
combinations, the exact F2P caller-override case, and 20 000 randomized fuzz
cases. It imports only the standard library (`itertools`, `random`); nothing
repo-specific. Exit 0 iff sound.
