# mapping.md — django__django-14500

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 8c3bd0b708b488a1f6e8bd8cc6b96569904605be`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/migrations/executor.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `recordUnappliedKeys (m : Migration)` | `MigrationExecutor.unapply_migration(self, state, migration, fake=False)` — `django/db/migrations/executor.py:246` (recording block, lines 253–258) | the modeled changed function, projected onto its single observable effect: the ordered keys recorded as unapplied |
| `Migration.replaces` | `migration.replaces` — list of `(app_label, name)` of the migrations a squashed migration stands in for (empty list for an ordinary migration) | the replaced-set the recording iterates over |
| `Migration.appLabel` | `migration.app_label` | first component of the migration's own key |
| `Migration.name` | `migration.name` | second component of the migration's own key |
| `recordUnappliedKeys`'s output `List (String × String)` | the ordered sequence of `self.recorder.record_unapplied(app_label, name)` calls (`executor.py:255,258`) | the migration's unapplied-record observable |

The modeled function abstracts away the parts of `unapply_migration` the change
does NOT touch and the F2P test does not observe through this effect: the
`progress_callback` calls (lines 248–249, 260–261) and the `if not fake:`
schema-editor / `migration.unapply` state mutation (lines 250–252). Those are
state/IO orthogonal to which keys get recorded; the recorded-key sequence is the
behavior the issue and the F2P test (`test_migrate_marks_replacement_unapplied`)
pin down. See §3 for why this projection is faithful and conservative.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a migration key `(app_label, name)` — a `tuple[str, str]` | `String × String` | `(a, n)` ↔ `(a, n)`; component-wise string identity |
| `migration.replaces` — `list[tuple[str, str]]` | `List (String × String)` | Python list ↔ Lean `List`; order-preserving; `len` ↔ `.length`; empty ↔ `[]` |
| `migration` rich object | `Migration` structure (only `replaces`, `appLabel`, `name`) | a structure with exactly the touched fields; other attributes are unobserved by the recording effect (mapping.md §1) |
| the ordered `record_unapplied(...)` call sequence | the returned `List (String × String)` | the i-th recorded key ↔ the i-th list element; list `++` ↔ call-sequence concatenation |

`String` equality and list operations are total and decidable in Lean — no
workaround needed.

## 3. Callee / effect provenance (no axioms, no deep-model references)

There are **no axioms** in this bundle and **no A-reference deep models**. The
changed operation is the recording control flow itself, which is expressed
directly with concrete (I-tagged) list operations:

- `recorder.record_unapplied(app_label, name)` is modeled as **appending the key
  `(app_label, name)` to the result list** — a concrete I-op, not an
  axiomatized callee. It is an unchanged sink whose only observable for this
  effect is "the key it was called with, in order"; the model records exactly
  that key, so the model is the identity on the observable. No contract about
  `record_unapplied` is *consumed* by the proof (the postcondition is a pure
  statement about list structure), so axiomatizing it would be a dead axiom
  (SPEC_GUIDE §3) — hence none is shipped and **G-AX legitimately skips** ("no
  axiom_check.py / no axioms in bundle").

- The `for app_label, name in migration.replaces: record_unapplied(...)` loop is
  modeled by the backward `while` fold that prepends each `m.replaces[i-1]!`,
  proven equal to `m.replaces ++ [ownKey]` via the single `drop_step` lemma
  (the M1 front-recursive-fold pattern, here over an already-front-recursive
  `++`).

- The `fake` / `state` / `schema_editor` prelude (lines 250–252) and the
  `progress_callback` calls are **unchanged** by the gold patch and orthogonal
  to the recorded-key observable; G-CONF invokes the real patched method with
  `fake=True` and `progress_callback=None` so the only effect exercised is the
  recording sequence (the change site). This is conservative: the projection
  cannot hide any patched behavior, because the patch touches only lines
  253–258 (the recording block), which is exactly what the projection keeps.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14500`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `recordUnappliedKeys` (`out = m.replaces ++ [ownKey]`) to Python;
the oracle calls the REAL patched `MigrationExecutor.unapply_migration` with a
capturing stub recorder (`fake=True`, no progress callback) and observes the
ordered `record_unapplied` key sequence. Boundary inputs cover the F2P squash
scenario, an ordinary migration, a single replaced key, a self-referential
replaced set, and empty-string fields.
