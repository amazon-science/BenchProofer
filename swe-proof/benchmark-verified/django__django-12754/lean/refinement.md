# refinement.md — django__django-12754

Maps every operation in `implementation_createModelDeps` (and its helpers
`baseDeps` / `removedFieldDeps`) to its `patch.diff` / base-source counterpart.
Tags: **R** type refinement · **A-consumed** proof uses this axiom ·
**A-reference** deep model validated == real callee by G-AX · **I** identical op.

| # | Lean op | Python counterpart (autodetector.py @ base_commit) | tag | note |
|---|---|---|---|---|
| 1 | `deps := [⟨appLabel, modelName, none, false⟩]` | `dependencies = [(app_label, model_name, None, False)]` (line 558–560) | I | identical 4-tuple seed; `none ↔ None`, `false ↔ False`. |
| 2 | `for base in bases do deps := deps ++ baseDeps …` | `for base in model_state.bases:` (line 562) | I | iterate bases in order, append per-base deps. |
| 3 | `Base.other => []` | guard `if isinstance(base, str) and "." in base:` fails ⇒ no append (line 563) | R | a non-dotted/non-string base is `Base.other`; the `str`+`"."` test is the constructor discriminator (mapping.md). |
| 4 | `Base.dotted ba bn => ⟨ba, bn, none, true⟩ :: …` | `base_app_label, base_name = base.split(".",1)` ; `dependencies.append((base_app_label, base_name, None, True))` (line 564–565) | R | the dotted reference arrives pre-split into `(ba, bn)`; `split(".",1)` is the refinement (mapping.md). `true ↔ True`. |
| 5 | inner `match fromLookup ba bn, toLookup ba bn with \| some _, some _ => removedFieldDeps … \| _,_ => []` | `old_base_model_state = self.from_state.models.get(...)` ; `new_base_model_state = self.to_state.models.get(...)` ; `if old_base_model_state and new_base_model_state:` (lines 566–569) | R | both-present guard = both `Option`s `some`; truthiness of a `ModelState` ↦ `some` (mapping.md). **gold fix.** |
| 6 | `removedFieldDeps`: `oldFields.filter (fun f => !(newFields.contains f) && modelFields.contains f)` | `set(old.fields).difference(new.fields).intersection(model_state.fields)` (lines 569–571) | R | set difference∩intersection ↦ filter over `oldFields`; result compared by membership, so set vs list order is immaterial (mapping.md "Set vs list"). **gold fix.** |
| 7 | `… .map (fun f => ⟨ba, bn, some f, false⟩)` | `for removed_base_field in removed_base_fields: dependencies.append((base_app_label, base_name, removed_base_field, False))` (line 571–572) | I | one removal 4-tuple per field; `some f ↔ removed_base_field`, `false ↔ False`. **gold fix.** |
| 8 | `if let some (pa, pn) := primaryKeyRel then deps := deps ++ [⟨pa, pn, none, true⟩]` | `if primary_key_rel: dependencies.append((primary_key_rel._meta.app_label, primary_key_rel._meta.object_name, None, True))` (lines 567–573 of base) | R | `primary_key_rel` truthiness ↦ `Option`; `_meta.app_label`/`object_name` ↦ the pair (mapping.md). |

No A-consumed and no A-reference rows: the bundle declares no `opaque` callee
and consumes no `axiom`. Every op is **R** or **I**, so G-CONF mechanically
refutes the whole impl and `meta.json conf_skip = false`.

## How the prepatch differs (G-DIFF signal)
`Solution_prepatch.lean` keeps rows 1–4 and 8 but drops rows 5–7: its `baseDeps`
returns only `[⟨ba, bn, none, true⟩]` for a dotted base. This is exactly the
base-commit behavior (lines 558–565 with the gold block 566–572 absent). Against
the unchanged spec the carried gold proof cannot close, because the spec's third
disjunct requires a `⟨ba, bn, some f, false⟩` member for every moved field and
the prepatch impl never emits one — so G-VERIFY fails on the prepatch (G-DIFF).
