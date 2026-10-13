# mapping.md — django__django-11999

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 84633905273fc916e3d17883810d9969c03f73c2`, states the type
abstraction, and gives the provenance of the single A-reference (the deep model
validated against the real callee by `axiom_check.py` / G-AX). This bundle has
**no consumed axioms**.

Repo file under change: `django/db/models/fields/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `preserve_existing_accessor(cls, accessor_name)` | the `choices` branch of `Field.contribute_to_class` (`django/db/models/fields/__init__.py:765-767`), in the case where the class **already provides** `get_<name>_display` | modeled changed function, behaviour 1: an author-defined accessor must NOT be overwritten |
| `install_missing_accessor(cls, accessor_name)` | the same branch (`django/db/models/fields/__init__.py:765-767`), in the case where the class **does not yet provide** `get_<name>_display` | modeled changed function, behaviour 2: the generated accessor is installed when absent |
| `cls` (the `Dict[int, int]` parameter) | the model class object `cls` whose attribute namespace `contribute_to_class` mutates via `setattr` | the class attribute namespace under mutation |
| `accessor_name` (the `int` parameter) | the attribute name string `'get_%s_display' % self.name` | the display-accessor name derived from the field name |
| `generated_accessor()` *(pure const)* | the bound `partialmethod(cls._get_FIELD_display, field=self)` installed by the patched `setattr` | the method-identity token of the generated display accessor |
| `other_name()` *(pure const)* | any other attribute name already present on the class (e.g. an unrelated method) | representative untouched attribute, witnessing the frame condition |

The generated accessor's behaviour (what `_get_FIELD_display` computes) lives in
`Model._get_FIELD_display` (`django/db/models/base.py:941-944`): it returns the
human-readable label from `dict(field.flatchoices).get(value, value)`. This
behaviour is what `axiom_check.py` observes to distinguish the generated
accessor (the install case) from an author-defined one (the preserve case).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the model class object `cls` (an attribute namespace mapping attribute names → bound callables) | `Dict[int, int]` from an attribute-name token to a method-identity token | `hasattr(cls, name)` ↔ `name_token in cls`; the callable bound under `name` ↔ `cls[name_token]` (its identity token); `setattr(cls, name, m)` ↔ `cls[name_token] = m_token` |
| the attribute name `'get_%s_display' % self.name` (a `str`) | an `int` token `accessor_name` | distinct attribute names ↔ distinct tokens; equality of names ↔ equality of tokens |
| `not hasattr(cls, 'get_%s_display' % self.name)` (the patched guard) | `accessor_name not in cls` | the resolvability test on the class ↔ key membership |
| the patched branch always returns (straight-line: one `hasattr` test, at most one `setattr`), so `contribute_to_class` returns and class assembly completes | `Requires(MustTerminate(2))` on both modeled functions | "the step runs to completion and hands control back" ↔ the discharged termination obligation. Makes the accessor postconditions TOTAL: under Viper's partial-correctness reading they would otherwise be claimed only of runs that reach the return, and a non-returning step would satisfy all of them (frame clauses included) vacuously. Budget 2 = the cost of the single guarded namespace write; see refinement.md step 6 |
| the installed `partialmethod(cls._get_FIELD_display, field=self)` | the constant identity `generated_accessor()` (token `0`) | the generated accessor ↔ a single fixed identity (its concrete behaviour is observed separately by axiom_check.py via `_get_FIELD_display`) |
| an author-defined `get_<name>_display` method | any identity token `!= generated_accessor()` | a hand-written accessor ↔ a distinct identity |

`str` indexing/iteration is banned in Nagini, and the only properties the change
turns on are **presence of the accessor name** (`hasattr`) and **which callable
is bound under it** (overwrite vs preserve). Integer-token identity is therefore
the faithful carrier; no string content is needed.

The `self.choices is not None` precondition of the patched branch is the
trigger under which both modelled functions operate (when there are no choices
the branch is a no-op and there is nothing to specify); it is represented by the
functions being invoked at all, not by an extra parameter.

## 3. The A-reference (deep model ↔ real operation, checked by G-AX)

There is **no `@ContractOnly` axiom**: the changed operation — the guarded
installation of the display accessor — is the behaviour under specification and
is spelled out **deeply** in each function's impl region
(`if accessor_name not in cls: cls[accessor_name] = generated_accessor()`).

The corresponding real operation is the `choices` branch of
`Field.contribute_to_class` after the gold fix:

```python
if self.choices is not None:
    if not hasattr(cls, 'get_%s_display' % self.name):
        setattr(
            cls,
            'get_%s_display' % self.name,
            partialmethod(cls._get_FIELD_display, field=self),
        )
```

(pre-patch: the unconditional `setattr(cls, 'get_%s_display' % self.name,
partialmethod(...))`, `django/db/models/fields/__init__.py:766-767`).

`axiom_check.py` validates the deep model **== this real operation** out of
band (G-AX, A-reference). The SWE-bench instance image is checked out at
`base_commit`, whose `contribute_to_class` installs the display accessor
*unconditionally* (the bug). So the check does NOT trust the ambient
`contribute_to_class`: it drives BOTH code states by wrapping the real method at
runtime, reusing the real internals (`partialmethod` + `cls._get_FIELD_display`)
and controlling only the single guard around the display-accessor `setattr`:

  * **GUARDED state** (the gold guard self-applied at runtime): install the
    generated accessor only when the class does not already provide one of that
    name. The deep model's claims must HOLD — the author method is preserved
    when present (`hasattr` true), the generated label-returning accessor is
    installed when absent (`hasattr` false) — over 4 boundary cases + 2000
    randomized assemblies (with/without an author-defined `get_<field>_display`,
    both declaration orders).
  * **UNGUARDED state** (the base_commit unconditional install): the author
    accessor must be CLOBBERED (both declaration orders), proving the observable
    genuinely discriminates the fixed behaviour from the buggy one.

The behaviour is observed through the accessor's return value
(`_get_FIELD_display`'s choice label vs the author's value), exactly as the
hidden tests observe it. The check imports only the standard library and the
repository package under evaluation (the very module the gold patch edits), and
is base_commit-self-sufficient: it exits 0 on the stock instance image with no
external `git apply` (and is equally correct if the harness pre-applies gold).
Exit 0 iff sound.

## G-CONF (differential conformance: shadow of the impl region ↔ real patched repo function)

`conformance_check.py` refutes the R/I refinement leg by executing both sides on
the same inputs. It is **not** covered by G-VERIFY (impl ⊨ spec) or G-PBT (no
wrong impl ⊨ spec), neither of which looks at the repository.

* **Shadow (provenance `direct`)** — the `# impl-start` / `# impl-end` region of
  `model.py`, copied verbatim with only the contract calls stripped. Both
  modelled functions share one byte-identical region
  (`if accessor_name not in cls: cls[accessor_name] = generated_accessor()`),
  which is plain executable Python over the `Dict[int, int]` carrier. The two
  `@Pure` helpers (`generated_accessor`, `other_name`) are copied minus
  contracts. No `PSeq`/`ToSeq` carrier occurs in this model, so no sequence shim
  is needed, and per §3 there is **no `@ContractOnly` callee**, so nothing is
  assumed — both impl branches are executed.
* **Oracle** — the REAL patched repo function is **called**, not
  transliterated: `django.db.models.fields.Field.contribute_to_class`
  (`django/db/models/fields/__init__.py:749-767` @ base_commit; the gold patch
  rewrites 765-767 into the guarded form). The gate applies `patch.diff` before
  the script runs; the script additionally asserts via `inspect.getsource` that
  the ambient method carries the patched guard
  (`if not hasattr(cls, 'get_%s_display' % self.name)`) and exits non-zero
  otherwise, so it can never silently diff the shadow against the base_commit
  bug. The function is driven by real Django model-class assembly (a
  `models.IntegerField(choices=...)` contributed to a real `ModelBase` class).
* **Type bridge (§2 inverted)** — name token → real attribute-name string
  (`1` = `other_name()` → an unrelated method on the class; `2` → the accessor
  name `'get_%s_display' % field.name`; `3..5` → further unrelated names,
  optionally inherited); identity token → real bound object (`0` =
  `generated_accessor()` → the `partialmethod(cls._get_FIELD_display,
  field=self)` the patched `setattr` installs, recognised structurally by
  `.func`/`.keywords`; `101..104` → distinct author-defined bindings, all `≠ 0`,
  one of them non-callable). Abstraction back to `Dict[int, int]` looks each
  tracked name up along `cls.__mro__` (`hasattr` ↔ key membership). `Old(cls)`
  is obtained by assembling the same shape with `choices=None`, which makes the
  patched branch a no-op. Which modelled function runs is decided by the
  concretised pre-state, so every input satisfies that function's `Requires` by
  construction (`other_name() in cls`, `other_name() != accessor_name` are
  re-checked at runtime).
* **Observable** — the tracked name→identity carrier compared key-for-key, plus
  a pre/post diff of the class's whole flattened MRO key-set requiring the
  accessor name to be the only addition and nothing removed: the executable
  reading of the model's whole-namespace frame `Ensures`.
* **Inputs** — the structural space is FINITE and enumerated **exhaustively**
  (2560 shapes = 5 field names × 4 accessor placements {absent, own, parent,
  grandparent} × 4 accessor identities × 4 unrelated-attribute identities × 8
  tracked-extra configurations), preceded by 8 named boundary shapes (incl. the
  exact F2P shape: a model body defining its own `get_foo_bar_display`), then
  seeded fuzz over the same space to reach **100000** inputs
  (74877 `preserve_existing_accessor` / 25123 `install_missing_accessor`; both
  impl branches taken). Exhaustive coverage of the finite space is a stronger
  check than 1e5 samples of it.
* **Pinned seed** — `SEED = 11999` (module constant `SEED` in
  `conformance_check.py`).
* **Discrimination self-test** — after the differential passes, the same
  differential is re-run with the display-accessor install forced into its
  base_commit UNGUARDED form (the real method wrapped, real
  `partialmethod`/`cls._get_FIELD_display` internals reused, restored after) and
  must REPORT a disagreement on all three accessor-present placements. It does
  (3/3), so a green G-CONF here is not vacuous.
* **Verdict** — exit 0, 0 disagreements over 100000 inputs.
