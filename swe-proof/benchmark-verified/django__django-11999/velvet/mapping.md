# mapping.md — django__django-11999

## Symbol binding (file:line @ base_commit 84633905273fc916e3d17883810d9969c03f73c2)

| Lean symbol | Python symbol | location |
|---|---|---|
| `registerAccessor` / `registerDisplay` | the choices-branch of `Field.contribute_to_class(self, cls, name, …)` — the step that installs the auto-generated `get_<name>_display` accessor onto the model class namespace | `django/db/models/fields/__init__.py:749-767` (the `if self.choices is not None:` block at lines 765-767) |
| `key` (the registered name) | the string `'get_%s_display' % self.name` | `django/db/models/fields/__init__.py:766` |
| `gen` (the generated accessor token) | `partialmethod(cls._get_FIELD_display, field=self)` — the auto-generated display accessor | `django/db/models/fields/__init__.py:767` |
| `lookup` (the class namespace before the step) | the class's attribute namespace, queried via `hasattr(cls, key)` / written via `setattr(cls, key, …)` | `cls` at the call site |

The modeled function is the **registration step** in `contribute_to_class`. It is
the only behavior the FAIL_TO_PASS test observes:
`test_overriding_FIELD_display` defines a model that supplies its OWN
`get_foo_bar_display`; the test asserts that the model's own accessor is what
`get_foo_bar_display()` invokes, i.e. it is not displaced by the auto-generated
one. The observable change is purely *which* accessor ends up installed at `key`;
the auto accessor's internal computation (`_get_FIELD_display`) is unchanged and
not modeled.

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| class attribute namespace (a name→attribute map, as seen by `hasattr`/`getattr`) | `lookup : String → Option Nat` | for each accessor name `n`: `lookup n = some t` ⟺ the class already binds an accessor of identity-kind `t` at `n`; `lookup n = none` ⟺ no such binding exists. |
| the accessor name `'get_%s_display' % self.name` | `key : String` | identity on names. |
| accessor identity-kind | `Nat` token | `0` ⟺ a user-supplied accessor (defined in the class body / inherited); `1` ⟺ the auto-generated `partialmethod(...)`. Only the *kind* matters — the registration step never inspects the accessor's value, only its presence at `key`. |
| the auto-generated accessor `partialmethod(cls._get_FIELD_display, field=self)` | `gen = 1` | the generated-accessor token. |
| the namespace AFTER the registration step | `result : String → Option Nat` | `result n` = the identity-kind bound at `n` afterwards (`none` if unbound). |

The modeled domain is "the registration step runs" — i.e. the
`self.choices is not None` branch is taken (the field has choices, so an accessor
is generated). When the field has no choices the branch is skipped entirely and
no registration occurs; that case is outside the modeled operation (no `gen`
exists) and the `method` does not range over it. `registerAccessor` therefore
takes any `lookup`, `key`, `gen` with no `require`: it is exactly "when we
register, install the generated accessor only if the name is currently free,
otherwise keep what is already bound."

## Callee provenance + flag dependencies

- **No consumed callee axiom.** The registration step is modeled DEEPLY as a
  set-if-absent update on the namespace function (`pure` helper `registerDisplay`).
  There is no `axiom`/`:|`-stub callee: the only operations are a presence test
  on `lookup` and a single-name namespace update, both spelled out structurally.
  (Per SPEC_GUIDE §3, a deeply-modeled changed op is NOT axiomatized; there is
  therefore no `axiom_check.py` and G-AX skips.)
- The auto accessor itself (`partialmethod(cls._get_FIELD_display, field=self)`)
  is unchanged by the patch, and its internal computation is never observed by
  the modeled operation — only its presence/identity at `key`. It is therefore
  not a consumed axiom and not an A-reference; it is the opaque token `gen = 1`.
- **Ordering dependency (recorded for G-CONF).** A class body's plain methods
  (those without a `contribute_to_class`) are installed onto the class by
  `type.__new__` BEFORE the fields' `contribute_to_class` runs (see
  `ModelBase.__new__`, `django/db/models/base.py`). Hence a user-defined
  `get_<name>_display` is already present in the namespace when the registration
  step executes, so `hasattr(cls, key)` observes it. G-CONF builds its model
  classes through the real metaclass so this ordering is exercised faithfully.
- `hasattr(cls, key)` consults the full MRO, so an accessor defined on a *parent*
  model also suppresses regeneration. G-CONF includes an inherited-accessor
  boundary case in addition to the same-class and no-override cases.

## G-CONF fuzz seed

Pinned LCG / `random.Random` seed: **11999** (see `conformance_check.py` `SEED`).
Corpus: model classes built dynamically through Django's metaclass, varying the
field name, the `choices` list, and whether the model (or a parent) supplies its
own `get_<name>_display`. Observable per case: the *identity kind* of the
accessor installed at `key` (the user's own callable vs the auto-generated
`partialmethod`), compared against the set-if-absent shadow of
`registerDisplay`. ≥1.0×10⁵ cases.
