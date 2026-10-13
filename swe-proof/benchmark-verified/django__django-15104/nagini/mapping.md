# mapping.md — django__django-15104

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a7e7043c8746933dafce652507d3b821801cdc7d`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
primitive it stands for + the exact behaviour it encodes).

Repo file under change: `django/db/migrations/autodetector.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reduce_to_relation_agnostic(kwargs, is_relation)` | the per-field body of `MigrationAutodetector.only_relation_agnostic_fields` — `django/db/migrations/autodetector.py:89` (the conditional removal at lines 98-99) | the modeled changed operation: drop the related-target keyword from a field's deconstructed kwargs when the field is a relation |
| `kwargs` (model param) | `deconstruction[2]` — the kwargs `dict` of `self.deep_deconstruct(field)` (built at `autodetector.py:81-84`; `deep_deconstruct` returns `(path, [args], {kwargs})`, so `[2]` is the kwargs mapping) — `autodetector.py:97` | the mapping that is edited in place |
| `is_relation` (model param) | the guard `field.remote_field and field.remote_field.model` — `autodetector.py:98` | true ⇒ a relation field whose target keyword must be dropped |
| `TO()` | the string key `'to'` — `autodetector.py:99` | the related-target keyword removed from the relation-agnostic form |
| `pop_default(d, k)` *(deep model — A-reference)* | `dict.pop(k, None)` — the post-patch primitive `deconstruction[2].pop('to', None)` (`autodetector.py:99` after the gold patch) | keyword removal applicable to ANY mapping (no-op when the keyword is absent) |
| `del_present(d, k)` *(deep model — A-reference)* | `del d[k]` — the pre-patch primitive `del deconstruction[2]['to']` (`autodetector.py:99` at base_commit) | keyword removal applicable only when the keyword is present (undefined / raises `KeyError` on an absent keyword) |

The pre-patch repo statement the change replaces (audited, not referenced from
the consumer spec view): `del deconstruction[2]['to']` (`autodetector.py:99`),
which raises `KeyError` when the field's deconstructed kwargs do not carry
`'to'` — e.g. a custom relation field that hardcodes its target and removes
`'to'` from its own `deconstruct()`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the kwargs `dict` `deconstruction[2]` (string keyword names → arbitrary deconstructed values) | `Dict[int, int]` (keyword-name token → opaque value token) | only key membership (`k in d`) and per-key value identity (`d[k] == d'[k]`) are ever observed by the operation; integer-keyed/valued identity is therefore an exact carrier. The single distinguished key is `'to'` ↔ `TO() == 0`; any other keyword is a distinct non-zero token; the value is an opaque token whose only relevant property is equality. |
| in-place edit of `deconstruction[2]` then `fields_def.append(deconstruction)` | functional model: `reduce_to_relation_agnostic` RETURNS the relation-agnostic mapping; the input `kwargs` is read-only (held at fractional permission, directive 5) | the detector mutates the deconstruction object in place and keeps the same object; the model returns the *equal* mapping. The detector compares deconstructions by value (rename detection), so same-object-vs-equal-fresh-object is observationally identical for what the comparison observes (refinement.md, tag R). Modeling functionally also keeps the input genuinely read-only, closing the directive-5 vacuity hole. |
| the per-field iteration `for name, field in sorted(fields.items()): … fields_def.append(deconstruction)` (`autodetector.py:96,100`) | elided (a single field's processing is modeled) | the loop is structurally unchanged by the patch; the entire fix lives in the per-field body. Modeling one invocation of that body is faithful — the loop steps are independent and identical (refinement.md, tag I). |
| the guard `field.remote_field and field.remote_field.model` | the `bool` param `is_relation` | a truth value consumed only to decide whether to drop `'to'`; modeled as the boolean it evaluates to. |

`str` keys are never indexed/iterated as strings (Nagini bans that); the carrier
is `Dict[int, int]` and the operation is phrased over key membership/values.

**Termination (total correctness).** The real per-field body is a bounded,
straight-line computation (a guard and one keyword removal) that always
delivers its relation-agnostic mapping to the detector. The model carries this
as `Requires(MustTerminate(2))` on `reduce_to_relation_agnostic` (Nagini is a
partial-correctness verifier by default, so without the obligation a
non-terminating implementation — e.g. bare self-recursion — would satisfy every
`Ensures` vacuously). Both deep-model primitives carry the strictly smaller
measure `MustTerminate(1)` — each stands for a single bounded `dict` primitive
step (`d.pop(k, None)` / `del d[k]`), so the contracted caller may invoke them,
but may NOT re-invoke itself (no smaller measure is available), closing the
vacuous-recursion hole.

## 3. Callee provenance (A-reference deep models — checked by G-AX / axiom_check.py)

Both removal primitives are unchanged *language* primitives, modeled DEEPLY (no
opaque consumed axiom about the function under change). axiom_check.py validates
each model against the real `dict` primitive on boundary + fuzz mappings.

### 3.1 `pop_default` ↔ `dict.pop(k, None)` (A-reference) — the post-patch primitive
`dict.pop(key, default)` removes `key` and returns its value if present, and
returns `default` (here `None`) WITHOUT raising if absent. So `d.pop('to', None)`
applied to the deconstruction's kwargs:

* is **applicable to every mapping** — never raises;
* leaves `'to'` absent from the resulting mapping;
* preserves every other key with its value and introduces none.

These are exactly `pop_default`'s `Ensures` (no precondition on the presence of
`k`). The model relates a fresh result mapping to the read-only input; the real
primitive edits in place — observationally identical for the value comparison
(§2). Docs: https://docs.python.org/3/library/stdtypes.html#dict.pop. G-AX
asserts the real `d.pop(k, None)` meets this on every tested mapping, including
the empty mapping and mappings without `'to'`.

### 3.2 `del_present` ↔ `del d[k]` (A-reference) — the pre-patch primitive
`del d[key]` removes `key` and raises `KeyError` if `key` is **absent**
(`object.__delitem__`). So it is applicable only to a mapping that already
carries `key`. That applicability condition is the model's `Requires(k in d)`;
when applicable, its result matches `pop_default`'s (remove `k`, preserve the
rest). Docs:
https://docs.python.org/3/reference/datamodel.html#object.__delitem__ and
https://docs.python.org/3/tutorial/datastructures.html (the `del` statement).

**The discriminating soundness fact:** `del d[k]` RAISES on an absent key while
`d.pop(k, None)` is a no-op. axiom_check.py asserts both directions — that real
`del d[k]` succeeds-and-preserves when `k` is present, and **raises** when `k`
is absent — which is precisely why `del_present` legitimately carries the extra
`Requires(k in d)` that `pop_default` omits. This is the bug: the relation-
agnostic reduction is invoked on relation fields whose deconstructed kwargs omit
`'to'`, where the partial `del` is undefined (the reported `KeyError`) but the
total `pop(...,None)` succeeds.

**Soundness check (G-AX):** `axiom_check.py` runs the real `dict.pop`/`del` on 9
boundary mappings (empty, target-only, no-target, target+others, falsy value,
scattered keys) plus 20 000 randomized fuzz mappings (with both target-present
and target-absent arms forced heavily) and asserts every observation meets the
corresponding model contract. It imports only `copy`/`random` and uses plain
`dict`; nothing repo-specific. Exit 0 iff sound.
