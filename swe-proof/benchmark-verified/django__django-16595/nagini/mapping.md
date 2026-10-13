# mapping.md — django__django-16595

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f9fe062de5fc0896d6bbbf3f260b5c44473b3c77`, states the type
abstraction, and records callee provenance. There are **no axioms** in this
bundle: the changed behaviour is pure control flow over operation kinds and the
same-field test, which Nagini expresses directly — nothing the changed method
CALLS is opaque.

Repo file under change: `django/db/migrations/operations/fields.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduce(this, operation)` | `AlterField.reduce(self, operation, app_label)` — `django/db/migrations/operations/fields.py:249-267` | the modeled changed method (the field-alteration combiner) |
| `is_same_field(this, other)` | `FieldOperation.is_same_field_operation(self, operation)` — `fields.py:25-29` | unchanged predicate, modeled directly (same model name AND same field name, both lower-cased) |
| `Operation` (class) | `AlterField` / `RemoveField` / `RenameField` (subclasses of `FieldOperation`, `fields.py:8-72,75,154,198,270`) | the operations passed to / returned from `reduce`, abstracted to the fields the method reads |
| `KIND_ALTER / KIND_REMOVE / KIND_RENAME / KIND_OTHER` | `isinstance(operation, AlterField)` / `RemoveField` / `RenameField` / other | the runtime class tested by the `isinstance` checks, abstracted to a kind tag |
| `Operation.model_name_lower`, `Operation.name_lower` | `FieldOperation.model_name_lower`, `FieldOperation.name_lower` (`fields.py:14-20`, cached `.lower()`) | the two attributes `is_same_field_operation` compares |
| `Operation.new_name_lower` | `RenameField.new_name` (lower-cased; `fields.py:273-284`) | the new field name carried across a rename |
| `Operation.has_explicit_column` | `self.field.db_column is not None` (the rename guard `self.field.db_column is None`, `fields.py:258`) | whether the altered field pins an explicit stored-column name |
| `Operation.elidable` | `Operation.elidable` — `django/db/migrations/operations/base.py:32` (default `False`), read by `Operation.reduce` at `base.py:130,132` | whether a step is safe to elide and to optimize across; the two marks decide the generic fall-through |
| `joined_by_field_rule(this, nxt)` | the disjunction of `AlterField.reduce`'s own guards — `fields.py:250-259` — i.e. exactly the condition under which the method returns before delegating to `super().reduce` | unchanged derived predicate, spelled out (not an axiom); its negation is the fall-through's reachability condition |

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `isinstance(operation, AlterField/RemoveField/RenameField)` | `operation.kind == KIND_ALTER/KIND_REMOVE/KIND_RENAME` | the runtime class of an operation ↔ a distinct integer tag; the `isinstance` disjunction `(AlterField, RemoveField)` ↔ `kind == KIND_ALTER or kind == KIND_REMOVE` |
| `self.model_name_lower` / `self.name_lower` (`str`, case-folded) | `int` identifiers | string equality of the case-folded names ↔ integer equality; only equality is observed, so any injective `str`→`int` encoding preserves the tested behaviour |
| `RenameField.new_name` (`str`) | `new_name_lower: int` | same encoding. It is the OPERAND's facet, and its only use is as the `name=` argument of the carried `AlterField` (`fields.py:263`) — i.e. the constructed step is built UNDER that name, which lands in the built step's plain `name_lower`, not in a new-name slot of its own |
| **`new_name` is defined ONLY on `RenameField`** (`fields.py:270-284`); `AlterField` (`fields.py:198`, whose `__init__` at `fields.py:204` sets only `preserve_default` above `FieldOperation`'s `model_name`/`name`/`field`), `RemoveField` (`fields.py:154`) and any non-field `Operation` (`base.py:8`) have no such attribute, and reading it off one is an `AttributeError`, not a value (measured on the patched tree: `hasattr(AlterField('Foo','name',f), 'new_name') is False`) | the slot exists on the flat `MigrationStep` carrier, but PERMISSION on it is granted only where the real class defines the attribute. Three places, one rule: the operand's slot is lent CONDITIONALLY, `Requires(Implies(nxt.kind == KIND_RENAME, Acc(nxt.new_name_lower, 1/2)))`; the reducing step is lent none at all (no `Acc(this.new_name_lower)` conjunct, matching `AlterField` having no `new_name`); and the CONSTRUCTOR grants it on the same condition, `Ensures(Implies(kind == KIND_RENAME, Acc(self.new_name_lower) and self.new_name_lower == new_name_lower))`, so a step BUILT as an alteration yields nothing to read back either | a partial attribute ↔ a conditionally held resource. This is the only device in Nagini that can express "there is nothing here to read": a total slot plus an unconditional grant would model every operation as carrying a new name, and an impl could consult the operand's new name before establishing that the operand IS a rename — faithfully refined, that impl raises `AttributeError` on the first pair whose later operation is an alteration or a removal. Provenance does not change the rule, which is why the grant is conditioned in the constructor too: the reduction BUILDS an `AlterField` at `fields.py:258-264`, and an impl that read that step's own new-name slot back verified while its refinement raised `AttributeError: 'AlterField' object has no attribute 'new_name'` (the G-EQ refutation this section's last bullet used to dismiss). The `Ensures` returns the operand's facet under the same condition, so the caller's frame is unchanged. The real method obeys exactly this discipline: with `patch.diff` applied, `AlterField.reduce` spans `fields.py:249-267` and its single read of `operation.new_name` is at `fields.py:263`, reached only under the `isinstance(operation, RenameField)` test at `fields.py:255` |
| `self.field.db_column is None` | `not has_explicit_column` (`bool`) | the rename branch fires only when no explicit column is pinned; modeled as a boolean flag the spec reads |
| **the pinned-column status is a facet of the FIELD DEFINITION a step carries, and `field` is PARTIAL**: `FieldOperation.__init__(self, model_name, name, field=None)` stores it (`fields.py:9-12`); `AlterField.__init__` requires one (`fields.py:204`) and `RemoveField` (`fields.py:154`) inherits the optional parameter, so both may carry a definition — but `RenameField.__init__(self, model_name, old_name, new_name)` (`fields.py:273-276`) takes NO field and calls `super().__init__(model_name, old_name)`, so a rename's `field` is ALWAYS `None` and `self.field.db_column` is an `AttributeError` (measured: `AttributeError: 'NoneType' object has no attribute 'db_column'`), while a bare `Operation` (`base.py`) has no `field` attribute at all | the reducing step is lent the facet (it is an `AlterField`, so it has a definition); the operand is lent none (no `Acc(nxt.has_explicit_column)` conjunct, matching the real method reading only `self.field`); and the CONSTRUCTOR grants it exactly on the kinds whose class accepts a definition: `Ensures(Implies(kind == KIND_ALTER or kind == KIND_REMOVE, Acc(self.has_explicit_column) and self.has_explicit_column == has_explicit_column))` | the same partial-attribute ↔ conditional-resource device as the row below, on the sibling facet. A total grant here let an impl BUILD a rename-kind (or other-kind) step and read its column status back: that verified, and refined faithfully it raises. Measured on the patched tree over the instance's 38 optimizer tests — a rename-kind probe read: 1 error, `test_alter_field_rename_field`, `AttributeError: 'NoneType' object has no attribute 'db_column'`; an other-kind probe read (`Operation()`): 3 errors including the F2P itself, `AttributeError: 'Operation' object has no attribute 'field'`. The grant stops exactly at the kinds that carry a definition and no further, because a REMOVE-kind probe read is *satisfiable* in the repository (`RemoveField(model_name=…, name=…, field=self.field).field.db_column`) and its refinement resolves 38/38 — conditioning it out would reject a resolving rival, i.e. be spec-too-strong (battery: `uniq-rename-probe-column`, `uniq-guard-rename-probe-column`, `uniq-other-probe-column` reject; `pos-remove-probe-column` verifies) |
| `Operation.elidable` (`base.py:32`, class attribute defaulting to `False`; set by a subclass or by the `RunSQL`/`RunPython` `elidable=` kwarg) | `elidable: bool` | read directly on BOTH operands; the only other input the fall-through consults |
| `[operation]` / `[self]` / `[operation, AlterField(...)]` (Python lists of operations) | `List[Operation]` | list `+`/length/index/`is` mirror Python list construction/length/index/identity |
| `super().reduce(operation, app_label)` — a **four-state**; `super()` from `AlterField.reduce` binds **`FieldOperation.reduce`, `fields.py:69-72`** (MRO: `[AlterField, FieldOperation, Operation, object]`), which post-processes `Operation.reduce` (`base.py:129-139`) | `([nxt], False)` / `([this], False)` / `(None, True)` / `(None, False)` | the fall-through is NOT a plain flag and NOT a tri-state. `FieldOperation.reduce` is `super().reduce(operation, app_label) or not operation.references_field(self.model_name, self.name, app_label)`. `Operation.reduce`'s two LIST arms — `[operation]` when `self.elidable`, `[self]` when `operation.elidable` (the earlier operand's mark taking precedence) — are truthy and pass straight through, mapping to the corresponding singleton `List[Operation]` (paired with the verdict normalised to `False`, no reordering question being asked). Otherwise `Operation.reduce` yields `False`, so the answer is `not operation.references_field(...)`: the bool is **TRUE when the later step does not reference the altered field and FALSE when it does**, and BOTH states are reachable. That bit is read by the optimizer and must not be erased (see below), so it maps to the `bool` component of the result rather than being collapsed into one `None`. |

The optimizer driver (`django/db/migrations/optimizer.py:39-69`) reduces a pair
only when `reduce` returns a **list**, but it reads the boolean TWICE and the
second read is identity-sensitive, so the bool is a REORDERING VERDICT and not
merely "cannot combine here":

* `optimizer.py:46-47` — `elif not result: right = False`. A `True` keeps
  right-reduction alive; a `False` disables it.
* `optimizer.py:50` — `elif all(op.reduce(other, app_label) is True for op in
  in_between)`. An in-between operation must answer **exactly `True`** to
  license a left reduction.

The second is where the difference bites for this instance: two collapsible
same-field `AlterField`s separated by a third operation collapse only if that
operation answers `True`, and only `not references_field(...)` supplies it.
Measured on the patched tree: materialising the fall-through as a constant
`False` leaves the issue's own 3-`AlterField` sequence at length 3 instead of 1,
and as a constant `True` it over-optimizes (`[Alter(B.title),
AddField(B.title), RemoveField(B.title)]` → `()`, dropping an operation gold
keeps). So **no single bool reproduces the real method**, which is why the
verdict is modeled as a value rather than erased.

The F2P test `test_alter_alter_field` runs the optimizer on two `AlterField`s on
the same field and asserts the result is the single second `AlterField` — i.e.
`reduce(alter1, alter2)` must return `[alter2]`.

Note the two ways `AlterField.reduce` can produce a singleton list, which the
bridge keeps distinct by IDENTITY rather than by shape: the same-field collapse
arms return `[operation]` (the LATER step survives), while the fall-through's
`operation.elidable` arm returns `[self]` (the EARLIER step survives). Comparing
only lengths would conflate them.

## 3. Callee provenance

None. The method's only callees are `isinstance` (modeled by the kind tag),
`self.is_same_field_operation` (modeled directly as the `@Pure is_same_field`,
an UNCHANGED predicate spelled out — not an axiom), and the `AlterField`/
`RemoveField`/`RenameField` constructors (modeled by `Operation`). No stdlib or
opaque-repo callee is involved, so there is no `@ContractOnly` axiom and nothing
for G-AX to execute beyond the structural equivalence check in `axiom_check.py`.

## G-CONF

Differential conformance check: `conformance_check.py`.

* **Shadow** — the `# impl-start`/`# impl-end` region of `reduce`, copied
  verbatim with only the contract calls stripped, together with its two
  dependencies (the `MigrationStep` carrier and the `@Pure is_same_field`). The
  model IS Python, so there is no transliteration. No `@ContractOnly` callees
  exist in this bundle (§3), so every shadow line is real modeled computation.
* **Oracle** — the REAL patched `AlterField.reduce`, **called** (not replicated):
  `django/db/migrations/operations/fields.py:249-267`, the symbol §1 binds
  `reduce` to. Its `super().reduce(...)` fall-through is likewise really
  executed — the same call chain reaching `FieldOperation.reduce`
  (`fields.py:69-72`) and through it `Operation.reduce` (`base.py:129-139`),
  not a replica, so the `references_field` post-processing runs for real
  (including whichever override the operand's own class supplies). The chain reads only the operand classes,
  the cached lower-cased names, `self.field.db_column` and the two `elidable`
  marks, so genuine `AlterField` / `RemoveField` / `RenameField` / `AddField` /
  `CreateModel` / `DeleteModel` / `RunSQL` / `RunPython` instances (elidable and
  not) are constructed directly — no app registry, database or migration state
  is needed.
* **Bridge** — §2 inverted, generating CONCRETE-FIRST: each input is a real
  operation pair, and the abstraction function `abstract_step` (runtime class →
  kind tag; injective case-folded-name interner `str` → `int`;
  `field.db_column is not None` → `has_explicit_column`; `op.elidable` →
  `elidable`; `op.references_field(altered.model_name, altered.name,
  app_label)` — the real predicate, called — → `references_altered_field`)
  maps it onto the carrier, so no generated input can escape the model's
  `Requires`. Results are compared as (shape, surviving-element IDENTITY,
  carried-step facets), which keeps the fall-through's `[operation]` and
  `[self]` arms distinct; the real method's non-list return is compared **on
  its value** (`("flag", True)` vs `("flag", False)`), not collapsed onto one
  tag per §2. Erasing that distinction is exactly what blinded an earlier
  revision of this check.
* **Pinned seed** — `SEED = 16595`. Boundary grid (13 next-step families — each
  modeled kind plus non-field classes, in elidable and non-elidable form ×
  self elidable/not × same/different model × same/different field × case-shift ×
  `db_column` present/absent × 4 new-names) + the explicit F2P shape + the
  fall-through's four outcomes spelled out, then seeded fuzz. A green run
  additionally asserts non-vacuity: all FOUR distinct shadow results
  (`none` / `[nxt]` / `[this]` / `[nxt, carried]`), the matching real results,
  all four kind tags, the F2P alter-then-alter collapse, both elidable arms, the
  both-elidable precedence case and a same-field pair reaching the fall-through
  (the rename guard's rejection path) must have been exercised, else the run
  fails as vacuous.

### Recorded verdict: **pass** — 101 670 inputs, 0 disagreements

TWO earlier revisions of this bundle recorded **fail** on this same
fall-through arm, each one MRO hop short of the real chain.

**The second (this repair).** The model had been corrected to the tri-state
`[nxt]` / `[this]` / `None`, still on the premise that `super()` binds
`Operation.reduce`. It does not: AlterField's MRO is `[AlterField,
FieldOperation, Operation, object]`, so `super()` binds `FieldOperation.reduce`
(`fields.py:69-72`), which post-processes the base bool with `... or not
operation.references_field(self.model_name, self.name, app_label)`. The real
fall-through is therefore a FOUR-state and the single `None` arm was
**over-strong**: it asserted one answer where the callee gives two. Observed on
the patched tree at `base_commit`:

    AlterField('Book','title',CharField(128)).reduce(AlterField('Book','pages',...), 'app')
      real       -> True    (the later step does not reference `title`)
      old model  -> None, forced by Ensures(... Result() is None)

Not a formal artifact — the optimizer reads the bool twice and the second read
(`optimizer.py:50`) requires exactly `True`, so materialising the modeled `None`
as `False` leaves the issue's own 3-`AlterField` sequence at length 3 instead of
1, and as `True` it drops an operation gold keeps. No constant works, which is
why the verdict is now modeled as a VALUE (`(None, not
references_altered_field)`) rather than deleted or weakened. Both harnesses were
un-blinded with it: `axiom_check.py` now transcribes the `FieldOperation.reduce`
wrapper rather than stopping at `Operation.reduce`, and `conformance_check.py`'s
`norm_real` compares the bool instead of mapping both values to one tag —
verified load-bearing by re-running the un-blinded check against the old model,
which now FAILS with 8 disagreements on the boundary grid.

**The first.** §2 had claimed that `super().reduce(operation, app_label)`
returns "a plain combinability flag, **never a list**", which is false:

    Operation.reduce (django/db/migrations/operations/base.py:129-139)
        if self.elidable:        return [operation]
        elif operation.elidable: return [self]
        return False

For a later step with `elidable=True` (e.g. `RunSQL(..., elidable=True)`,
`RunPython(..., elidable=True)`) the real `AlterField.reduce` returns the LIST
`[self]`, whereas the old model's impl returned `None` and its postcondition
`Ensures(Implies(not is_same_field(this, nxt), Result() is None))` *forced*
`None`. Observed on the patched tree at `base_commit`:

    AlterField('Book','title',CharField(5)).reduce(RunSQL('SELECT 1', elidable=True), 'app')
      real       -> [<AlterField model_name='Book', name='title', ...>]   (a list)
      old shadow -> None

That was not a formal artifact: it changes optimizer output. `MigrationOptimizer
().optimize([alter, RunSQL(elidable=True)], 'app')` returns `[alter]` — the
elidable step is dropped — while the modeled `None` said "cannot combine", which
would retain it.

The repair took the route this section prescribed — re-modeling the fall-through
as the real tri-state and replacing the over-strong `Result() is None` clause
with the three clauses that state what the chain actually guarantees — rather
than narrowing the input domain to exclude elidable operands (which would have
been the "route around the disagreement" that yields a green certifying
nothing). The elidable mark is now part of the carrier (§1, §2), the fall-through
is modeled as `[nxt]` / `[this]` / `None` with the earlier operand's mark taking
precedence, and the postcondition is guarded on `joined_by_field_rule` — not on
"different field" — because a SAME-field pair also reaches the fall-through when
the rename arm's `db_column is None` guard rejects it.

The re-run agrees with the real patched chain on **101 670 inputs with 0
disagreements** (boundary grid + fuzz, seed 16595), with every non-vacuity
obligation above discharged: earlier-elides 27 987, later-elides 23 384,
both-elidable 12 672, same-field-fall-through 12 914. The gold change itself (the
widened `(AlterField, RemoveField)` guard) was faithful through both revisions
and remains so; what changed each time is the pre-existing fall-through arm the
model used to over-constrain.

## Carrier slots with no repo counterpart (G-EQ artifacts, not spec weakness)

`MigrationStep` is one flat carrier standing in for several operation classes,
so a step necessarily carries slots its real class does not define. **A slot the
real class does not define is not a benign artifact wherever the reduction can
READ it**: the flat carrier plus an unconditional permission grant models a
missing attribute as a present one, and an impl that reads it verifies while its
faithful refinement raises. That is why the operand's `new_name_lower` is lent
only under `nxt.kind == KIND_RENAME` and the reducing step is lent none (§2,
rows on `new_name` and on the pinned column): the partiality is modelled as a
resource, so the read is a proof obligation and not a free value. **That applies
to a step the reduction BUILDS exactly as it does to one handed in** — the entry
below used to claim otherwise and a G-EQ audit refuted it, and the sibling facet
(`has_explicit_column`) had to be conditioned the same way for the same reason
after a second audit found the rule stated in prose but implemented for one slot
only. The residual cases are the ones where the slot is
genuinely unreachable or genuinely absent, so G-EQ's own step (write the REFINED
real patch and show it does not resolve) terminates immediately for each — the
refined patch is byte-identical to gold and there is no repository state to
change:

* `new_name_lower` on a step the reduction CONSTRUCTS. The carried step is an
  `AlterField`, and `AlterField` defines no `new_name` at all (measured:
  `hasattr(carried, 'new_name') is False`; instance `__dict__` is
  `['_constructor_args','field','model_name','name','preserve_default']`). This
  bundle previously argued from that fact that a VALUE pin on the slot suffices,
  because "the constructed step's `new_name_lower` is written by the reduction
  and never read back by it". The premise was false of the SPEC, not of the
  repository: the constructor was granting the slot unconditionally, so an impl
  *could* read it back, and one did. The refuting rival built the carried step
  and then named the step it returned by reading that step's own new-name slot
  (`carried.new_name_lower`); it satisfied the value pin and VERIFIED, while its
  faithful refinement — `AlterField(model_name=self.model_name,
  name=carried.new_name, field=self.field)` — raises `AttributeError:
  'AlterField' object has no attribute 'new_name'`. Measured over the instance's
  38 optimizer tests: 1 error / 38 on `test_alter_field_rename_field` (gold
  38/38 OK); the G-EQ harness recorded FAIL_TO_PASS 1/1 pass, PASS_TO_PASS 1/37
  fail, "RenameField should optimize to the other side of AlterField". So the
  slot is now governed by the RESOURCE on this side too: the constructor grants
  it only for `kind == KIND_RENAME` (§2, last row), the postcondition claims
  neither permission nor value for the carried step's new name, and the carried
  step is instead pinned harder on the facets an `AlterField` really has, plus
  freshness against BOTH operands (`is not nxt and is not this` — true of a
  construction at `fields.py:258-264`). Nothing observable was un-pinned: the
  conformance bridge already mapped the absent name to a never-repeated
  `_fresh()` id and `_carried_facets` never compared it, so no value of that
  slot is observable in the repo, whereas READING it is. The two rivals are
  pinned as `expect: "reject"` cases (`uniq-read-back-carried-name`,
  `uniq-eager-built-name`), each rejected for insufficient permission.
* `references_altered_field` as per-step state. This was a real modelling error
  in an earlier revision of THIS repair and is now gone: the repository asks the
  question as `references_field(model_name, name, app_label)`, a QUERY over the
  pair, and no operation caches the answer. Storing it per step created a slot
  on the carried step that no constant can fill faithfully — pinning it to the
  model's `False` makes the real callee disagree on 8 boundary inputs (real
  `True` for a rename-to-the-same-name and for a field reaching the altered
  field through `from_fields`; measured). It is therefore an ARGUMENT to
  `reduce`, matching the repo's shape, and no step object carries it.
