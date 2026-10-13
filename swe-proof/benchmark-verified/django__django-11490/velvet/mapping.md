# mapping.md — django__django-11490

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a7038adbd02c916315b16939b835f021c2ee8880`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of every callee. `spec_provenance: cold`.

Repo file under change: `django/db/models/sql/compiler.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `applyProjection (mut persistent : Carrier) (mut recorded : Bool) (requested projected : List String)` | the per-combined-sub-query body inside `SQLCompiler.get_combinator_sql` — `django/db/models/sql/compiler.py:410` (def), the `if not compiler.query.values_select and self.query.values_select:` block at lines 426–433 | the modeled changed operation: pushing the outer query's explicit column projection down onto one combined sub-query while building the compound SQL |
| `persistent` (mut field) | `compiler.query` — the `Query` carrier of one combined sub-query, an element of `self.query.combined_queries` (`django/db/models/sql/query.py:215`, set in `_combinator_query`, `django/db/models/query.py:934`). This object is **shared and persistent**: the same `Query` instance is referenced from the compound queryset's `combined_queries` across every evaluation of that queryset. | the carrier whose `values_select` the operation must leave **unchanged** (the preserved frame, directive 5) |
| `working` (return) | the `Query` carrier actually used to compile this sub-query's SQL fragment in this call — post-patch, the freshly `clone()`d copy that `set_values(...)` is applied to (`compiler.query` after line 427 reassigns it) | the within-call working carrier whose column projection drives this call's SQL |
| `requested` / `projected` (read-only) | see §2 — `requested` is the outer query's OWN `values_select` (the guard's second conjunct), `projected` the full pushed-down tuple at `compiler.py:430–432` | read-only inputs; never altered |
| `Carrier` (`columns`, `sideSelected`, `auxSelected`, `auxAvailable`, `ownFields`) | the five `Query` observations this step reads or is framed on — see the §2 table for each field's repo counterpart | the sub-query carrier, abstracted to the observations the changed operation touches |
| `shouldProject c requested` (pure) | the guard `not compiler.query.values_select and self.query.values_select` (`compiler.py:428`) | whether the push-down fires |
| `recordOnto c projected` (pure) | `Query.set_values(projected)` (`query.py:2030–2062`) — modelled step by step in §2 | the recording act, reshaping all three selection records at once |
| `workingCarrier persistentOld requested projected` (pure) | the post-state of the working carrier after the patched block runs | pure spec: what this call compiles its fragment from |
| `answerable c names` (pure) | the domain on which `add_fields` (`query.py:1788`) resolves every name rather than raising `FieldError` | the `require`; bounds the claim to the total sub-domain |
| `recorded` (mut ledger) | whether `set_values` was called on ANY carrier during this step | accounting: pinned to happen exactly on the push-down |

The pre-patch repo behaviour the change overrides (refinement audit only, NOT in
the consumer spec view): the block was

```python
if not compiler.query.values_select and self.query.values_select:
    compiler.query.set_values((*extra_select, *values_select, *annotation_select))
```

`set_values` is called **directly on the shared persistent sub-query** (`compiler.query`),
mutating its `values_select` in place. Because that `Query` object is the very
one held in `combined_queries` and reused on the next evaluation of the compound
queryset, a later evaluation finds `compiler.query.values_select` already
non-empty, so the guard `not compiler.query.values_select` is false and the
push-down is skipped — the sub-query keeps the column list installed by the
first evaluation. Hence "composed queries cannot change the list of columns when
`values()`/`values_list()` is evaluated multiple times."

## 2. Type abstraction (R-refinement) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. `Carrier` abstracts one sub-query `Query` to
the five observations this step reads or is framed on. The two SELECTION records
besides `columns` exist because the real callee keeps two separate masks and
consults them in a fixed order; collapsing them onto one field is what an earlier
revision got wrong.

| repo reality | Lean field | bijection |
|---|---|---|
| `Query.values_select` — the explicitly-selected value columns (`query.py:2061`) | `columns : List String` | `list(q.values_select)`; `[]` ↔ `()`; `columns.isEmpty` ↔ `not q.values_select` |
| `Query.extra_select` — the SELECTED side outputs, i.e. `extra` filtered by `extra_select_mask` (`query.py:2085`) | `sideSelected : List String` | `list(q.extra_select)`. Written by `set_extra_mask(extra_names)` (`query.py:2056`) |
| `Query.annotation_select` — the SELECTED auxiliary outputs, i.e. `annotations` filtered by `annotation_select_mask` (`query.py:2064`) | `auxSelected : List String` | `list(q.annotation_select)`. Written by `set_annotation_mask(annotation_names)` (`query.py:2057`) |
| `Query.extra` ∪ `Query.annotations` — every non-column output the carrier is ABLE to supply, UNMASKED | `auxAvailable : List String` | `list(q.extra) + list(q.annotations)`. Measured INVARIANT under `set_values` on 156/156 successful calls, so it is framed and never consulted by `recordOnto` |
| `[f.attname for f in q.model._meta.concrete_fields]` | `ownFields : List String` | the columns the carrier's own model defines; invariant under `set_values` |
| the outer request's pushed-down projection tuple | `projected : List String` | `list((*extra_select, *values_select, *annotation_select))` of the OUTER query (`compiler.py:430–432`) |
| the outer request's own explicit column list | `requested : List String` | `list(self.query.values_select)`; `!requested.isEmpty` ↔ `bool(self.query.values_select)` |
| `set_values(cols)` on a carrier | `recordOnto c cols` | see the step table below |
| `compiler.query = compiler.query.clone()` then `set_values(...)` | `let w := persistent; w := recordOnto persistent projected; return w` | the clone makes a private working copy; `persistent` is left identically equal to its entry value (directive 5 frame) |

### `recordOnto` ⇔ `Query.set_values` (`django/db/models/sql/query.py:2030–2062`), step by step

`set_values` is NOT a single assignment; it is a sequence, and the model needs a
leg for each observable step:

| # | real step (file:line @ base_commit) | modelled as |
|---|---|---|
| S1 | `fields` FALSY → `field_names = [f.attname for f in self.model._meta.concrete_fields]`, masks untouched (`query.py:2060`) | the `projected.isEmpty` leg: `{ c with columns := c.ownFields }` — BOTH mask records left as they stand |
| S2 | `fields` truthy, `not self.extra and not self.annotations` → shortcut, `field_names = list(fields)` (`query.py:2044–2047`) | the general leg with both records empty: every projected name falls to `columns`, in the projection's order and with its repetitions |
| S3 | `fields` truthy, general loop: `if f in self.extra_select` → `extra_names` (`query.py:2051–2052`) | `sideSelected := c.sideSelected.filter (· ∈ projected)` — and this arm is tested FIRST |
| S4 | `elif f in self.annotation_select` → `annotation_names` (`query.py:2053–2054`) | `auxSelected := c.auxSelected.filter (fun n => projected.contains n && !c.sideSelected.contains n)` — the `elif` is the PRECEDENCE: a name in both masks is consumed by S3 and never reaches S4 |
| S5 | `else` → `field_names` (`query.py:2055–2056`) | `columns := projected.filter (fun n => n ∉ c.sideSelected ∧ n ∉ c.auxSelected)` |
| S6 | `set_extra_mask(extra_names)` / `set_annotation_mask(annotation_names)` (`query.py:2057–2058`) then `self.values_select = tuple(field_names)` (`query.py:2061`) | the three fields are written TOGETHER by one `recordOnto`, which is why a partial restore does not undo it |
| S7 | `add_fields(field_names, True)` (`query.py:2062`) resolves each `field_names` entry against model fields, `extra` and `annotation_select`, raising `FieldError` when it cannot (`query.py:1788–1824`) | NOT modelled as a value; bounded away by `require answerable`. `answerable` counts `ownFields ∪ sideSelected ∪ auxSelected`, which is exactly the set on which S7 does not raise (measured: 481 admissible inputs, 0 raises; 0 excluded-but-succeeding inputs modulo relation-traversal names, below) |

Steps `select_related = False`, `clear_deferred_loading()`, `clear_select_fields()`
and `set_select(cols)` write observations the abstraction does not carry
(`select`, `default_cols`, `deferred_loading`); per SPEC_GUIDE §2 they are outside
the abstraction, and the `require`/frame make no claim about them.

**Documented domain limit.** `ownFields` carries only the model's own concrete
field attnames, so a projected name that traverses a relation (`maker__label`)
is not `answerable` even though the real `add_fields` resolves it. Those inputs
are EXCLUDED by the precondition rather than mispredicted — the spec makes no
claim there. Measured over 3060 (carrier, projection) pairs across 15 carrier
shapes: 0 admitted-but-raising, 0 value divergences, and the only
excluded-but-succeeding inputs are relation-traversal names.

## 3. Callee provenance

The modeled operation is the **changed** code itself: the per-sub-query
push-down block inside `get_combinator_sql`. Under the abstraction it reads one
observation of the sub-query carrier (whether its `values_select` is empty) and
one of the outer query (whether the outer query's OWN `values_select` is
non-empty — the guard's second conjunct, `requested`, not the pushed-down tuple
`projected`), and produces a working carrier — sorting `projected` across the
carrier's three selection records — while leaving the shared carrier unchanged. It calls
no other function whose contract the proof must consume, and it deep-models no
foreign callee:

- `Query.clone()` (`django/db/models/sql/query.py:292`) is modeled directly as
  Lean value-copy (`let w := persistent`): Lean values have no aliasing, so a
  fresh binding IS a clone. Its only relevant property — the original is not
  mutated by subsequent edits to the copy — is the frame the spec pins, not an
  axiom.
- `Query.set_values(cols)` (`django/db/models/sql/query.py:2030–2062`) is modeled
  directly as `recordOnto`, step for step — S1–S7 in §2 above, covering the
  empty-`fields` leg, the no-`extra`/no-`annotations` shortcut, the
  `if extra_select` / `elif annotation_select` / `else` three-way sort with the
  `elif` precedence, and the two mask writes landing together with
  `values_select`. It is a transliteration of the real callee's body, not a
  contract assumed about it; the resulting three selection records are the
  observables G-CONF checks against the real `set_values`.

There is therefore **no axiomatized callee** in this bundle (no consumed axiom,
no A-reference): `axiom_check.py` is omitted and **G-AX is skipped** (cf. the
no-axiom exemplars `django__django-13406` / `django__django-13569`).

The grounding the spec relies on (validated by G-CONF / G-RESOLVE, not assumed):

- a freshly built combined sub-query (from `qs.union(qs)`) has an empty
  `values_select`; the outer `values_list(...)` query has a non-empty
  `values_select`; so the push-down fires and the working carrier projects the
  outer columns;
- after the patched block runs, the **shared persistent** sub-query object's
  `values_select` is still empty (the clone absorbed the mutation), so a second
  evaluation with a different `values_list(...)` projection re-fires the
  push-down and selects the new columns — the behaviour the F2P test demands.

Both observations are executed directly against the real repo code by
`conformance_check.py` (it builds a real compound `QuerySet`, evaluates
`values_list(...)` twice with different column lists on the shared combined
sub-queries, and compares the rows the **real patched** `get_combinator_sql`
produces against the modeled rule), so the R/I shadow is checked against the
genuine operation, not a hand-copied rule.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11490`** so the
consumer-side verdict (§11.3) is reproducible. The input space (ordered pairs of
column projections drawn from the model's value columns, evaluated in sequence
against one shared compound queryset) is enumerated for the boundary
combinations and then sampled by the seed during the ≥10⁵ fuzz loop.
