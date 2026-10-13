# mapping.md — django__django-15128

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = cb383753c0e0eb52306e1024d32a782549c27e61`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance.

Repo file under change: `django/db/models/sql/query.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildRelabeling (aliases) (newPrefix) (preserved)` | the rename-map dict comprehension at the end of `Query.bump_prefix` — `django/db/models/sql/query.py:931-936` (post-patch `:931-940`) | the modeled changed operation: construct the old→new alias relabeling, holding back the aliases that must remain shared |
| `relabeling` / `relabelFrom` (deep model — pure region) | the comprehension `{alias: '%s%d' % (prefix, pos) for pos, alias in enumerate(alias_map) if alias not in exclude}` | pure spec of the rename map; transliterated directly (R/I), NOT an axiom |

Callers / unchanged surrounding machinery (refinement audit only, not modeled):
- `Query.combine` (`query.py:562`, post-patch adds `initial_alias =
  self.get_initial_alias(); rhs.bump_prefix(self, exclude={initial_alias})` at
  `:575-583`) — chooses the `preserved` set (the base-table alias) and calls the
  modeled construction. UNCHANGED in how it relabels; only *which* exclusion it
  passes is new, and that value is an input to the modeled op.
- `Query.change_aliases` (`query.py:843`) — consumes the rename map; UNCHANGED by
  the fix except for an added explanatory comment on the pre-existing
  `assert set(change_map).isdisjoint(change_map.values())`.
- `bump_prefix` parameter rename `outer_query → other_query` and the early-return
  guard / prefix generator — UNCHANGED behaviour (pure renaming); not modeled.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `list(self.alias_map)` — the ordered table aliases (dict keys, unique) | `aliases : List String` | Python alias `str` ↔ Lean `String`; insertion order ↔ list order; uniqueness preserved (distinct dict keys ↔ distinct list elements) |
| `self.alias_prefix` — the freshly bumped prefix letter(s) | `newPrefix : String` | identity on the prefix `str` |
| the `exclude` set passed to `bump_prefix` (`{initial_alias}` from `combine`) | `preserved : List String` | Python `set[str]` ↔ Lean `List String`; `alias in exclude` ↔ `preserved.contains alias`. Modeled as a list because only membership is observed (set vs list is observationally identical for `contains`) |
| the constructed `change_map` (`dict[str,str]`, old→new) | `out : List (String × String)` | each emitted entry `alias: name` ↔ pair `(alias, name)`; the list is compared to the dict as a mapping (entry order is immaterial to `change_aliases`, but the model emits insertion order so the comparison is also order-faithful). G-CONF builds a `dict` from both sides and compares. |
| `'%s%d' % (prefix, pos)` — fresh alias name | `newPrefix ++ toString pos` | `str` concat ↔ `String` `++`; `pos` is the 0-based `enumerate` index ↔ the position counter, which advances for EVERY alias (preserved ones included) |

The subtle invariant the bijection preserves: `enumerate` numbers all aliases
positionally; the `if alias not in exclude` filter decides only *emission*, not
*numbering*. The Lean `relabelFrom` mirrors this exactly — its position counter
`pos` steps unconditionally (`relabelFrom … (pos + 1) rest`), while a preserved
alias contributes `[]`. So omitting a preserved alias never shifts the names
assigned to the others.

## 3. Callee provenance — NONE

There is **no axiomatized callee and no deep-model reference to a foreign
callee**. The modeled operation is a pure, self-contained construction over its
three inputs: a list scan emitting prefixed names. Every observable is computed
structurally from `aliases`, `newPrefix`, and `preserved`. The `'%s%d'`
formatting, the `enumerate` numbering, and the membership filter are all concrete
ops transliterated directly (R/I) and refuted by G-CONF. Hence `axioms = []`,
`deep_model_references = []`, no `axiom_check.py`, and G-AX is `skip`
(precedent: django__django-12193).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`15128`** so the
consumer-side verdict is reproducible. The shadow transliterates `relabeling`/
`relabelFrom` (all R/I ops, no A-tagged callees) to Python; the oracle is the
gold-patched comprehension transliterated verbatim from `bump_prefix`. They are
compared as dicts over 10⁵+ (alias-sequence, prefix, exclude) triples, including
the issue-shaped `T4/T5/T6` boundary and base-table-preserved cases.
