# mapping.md — django__django-12406

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 335c9c94acf263901fb023404408880245b0c4b4`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each axiom.

Two repo files change, and the change is a **two-site, coupled** fix:

1. `django/db/models/fields/related.py` — `ForeignKey.formfield` forwards the
   model field's `blank` flag into the constructed choice field's kwargs.
2. `django/forms/models.py` — `ModelChoiceField.__init__` uses that flag (plus
   the widget kind) to decide whether the synthetic blank choice is offered.

Both functions are CHANGED by the patch, so each is modeled as its own `method`
(plan §3, multi-site). Neither modeled function is axiomatized.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `relationBlankFlag (modelAllowsBlank : Bool)` | the `blank` entry forwarded by `ForeignKey.formfield` — `django/db/models/fields/related.py:973` (kwargs dict body, line ~984 post-patch) | modeled changed function (site B): the blank flag the relation hands to its choice field |
| `blankChoiceOffered (required initialPresent widgetIsRadio blank : Bool)` | the blank-choice decision in `ModelChoiceField.__init__` — `django/forms/models.py:1184` (decision body lines 1188-1191 pre-patch) | modeled changed function (site A): whether the synthetic blank choice is presented |
| `modelAllowsBlank` (param of `relationBlankFlag`) | `self.blank` of the relation field — attribute set on the `Field` base (`django/db/models/fields/__init__.py`, `blank=` kwarg) | the model field's declared blank-allowed flag |
| `required` (param) | `required` arg of `ModelChoiceField.__init__` (default `True`) | the form field is required |
| `initialPresent` (param) | `initial is not None` for the `initial` arg of `__init__` | an initial value is supplied |
| `widgetIsRadio` (param) | `isinstance(self.widget, RadioSelect)` — `RadioSelect` from `django/forms/widgets.py:757` | the resolved widget is a radio widget |
| `blank` (param of `blankChoiceOffered`) | the `blank` arg threaded into `__init__` (post-patch keyword), supplied by site B | blank is a permitted selection |
| `out` of `blankChoiceOffered` | `self.empty_label is not None` — whether `ModelChoiceIterator` yields the leading `("", empty_label)` choice (`django/forms/models.py:1149-1150`) | True ⇔ the blank choice appears in `field.choices` |

`ModelChoiceIterator.__iter__` (`django/forms/models.py:1148-1156`) yields the
leading `("", self.empty_label)` pair **iff** `self.empty_label is not None`;
hence "the blank choice is offered" is exactly `empty_label is not None`, which
is the negation of the `empty_label = None` assignment the patch governs. The
spec models that observable boolean directly (directive 8: grounded in the
inputs, not an opaque oracle).

The pre-patch repo behavior the change corrects (refinement audit only, not in
the consumer spec view): `__init__` set `empty_label = None` **only** when
`required and initial is not None`, ignoring the widget kind and `blank`; and
`ForeignKey.formfield` did not forward `blank`, so the choice field never saw
it.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and (where applicable) G-AX use to translate
values between the Lean value domain and the Python repo types. A wrong entry
surfaces as spurious G-CONF disagreements (the falsifiability the plan §4 trust
statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.blank` : Python bool | `Bool` | `True ↔ true`, `False ↔ false` |
| `required` : bool | `Bool` | as above |
| `initial is not None` : bool | `Bool` (`initialPresent`) | truth value of the `is not None` test |
| `isinstance(self.widget, RadioSelect)` : bool | `Bool` (`widgetIsRadio`) | truth value of the radio-widget test (`RadioSelect` and its subclasses) |
| `blank` arg of `__init__` : bool | `Bool` | as above |
| `self.empty_label is not None` : bool | `Bool` (`out` of `blankChoiceOffered`) | `empty_label is not None ↔ out = true` |
| the forwarded `blank` kwarg value : bool | `Bool` (`out` of `relationBlankFlag`) | exact (identity forwarding) |
| `not x` | `!x` | logical negation |
| `x and y` | `x && y` | short-circuit conjunction (no side effects in either decision; equivalent to `&&`) |
| `x or y` | `x \|\| y` | short-circuit disjunction |

All inputs are observationally boolean (the decision reads only their truth
values), so each maps to Lean `Bool`. The decisions mutate none of their inputs
and compute a single boolean — they are declared without `mut` and the inputs
are read-only (directive 5).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

**None.** Both modeled functions are CHANGED functions whose new logic is a pure
boolean combination of the inputs, modeled **deeply** (spelled out in the
`method` postconditions). There are no unchanged opaque callees in the modeled
behavior:

- The `isinstance(self.widget, RadioSelect)` test and `initial is not None` test
  are reduced to their boolean results at the bridge (mapping.md §2); the
  decision observes only those booleans.
- `Field.__init__(...)` is called by `ModelChoiceField.__init__` but does not
  participate in or alter the blank-choice decision (it sets unrelated
  attributes); per the plan it is abstracted away, not axiomatized (no axiom
  about the function under change, directive 7).
- `ModelChoiceIterator.__iter__` is the *observer* (it yields the leading choice
  iff `empty_label is not None`); the bijection in §2 (`empty_label is not None
  ↔ out`) ties the modeled boolean to the observable choices list, which is what
  the F2P tests inspect. It is unchanged by the patch and is part of the
  observation bridge, not a consumed axiom.

Therefore there is no `axiom_check.py` for this bundle (G-AX = skip; no axioms).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`12406`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates both decisions (all R/I-tagged boolean ops) to Python; there are
no A-tagged callees to leave as real-repo calls. The oracle for each site is the
patched source expression transliterated verbatim (see `conformance_check.py`
docstring for why the full Django form/model machinery is not constructed
in-container merely to read back two booleans).
