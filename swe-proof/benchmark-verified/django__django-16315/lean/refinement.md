# refinement.md — operation correspondence (django__django-16315)

Maps every op in `implementation_renderUpsertClause` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The fix has two cooperating edits: (1) `QuerySet.bulk_create` now resolves the
user-supplied field-name strings into field objects (`get_field`) before they
flow into `self.query.{unique,update}_fields`; (2) `SQLInsertCompiler.as_sql`
now passes `(f.column for f in …)` — each field's database column — into the
unchanged `on_conflict_suffix_sql` renderer, which previously received the raw
name strings. The net observable change is: the ON CONFLICT / DO UPDATE SET
suffix is keyed by each field's **database column** instead of its **declared
name**. We model the resolved fields as the `List FieldRef` input carrier and
the changed selection as `.column` (post) vs `.name` (pre).

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `uniqueFields : List FieldRef`, `updateFields : List FieldRef` | `self.query.unique_fields`, `self.query.update_fields` — the resolved field objects produced by `get_field` in `bulk_create` (query.py lines 788-792) | R | string→field resolution is the unchanged callee `get_field`; we carry the resolved fields directly. str-name ↔ `FieldRef.name`, db-column ↔ `FieldRef.column` bijection (mapping.md). The patch's *moving* of `get_field` into `bulk_create` is what makes field objects (not names) reach the compiler — captured by using `FieldRef` as the carrier. |
| 2 | `for f in uniqueFields do uniqueCols := uniqueCols ++ [quoteName f.column]` | `", ".join(map(quote_name, unique_fields))` where `unique_fields = (f.column for f in self.query.unique_fields)` (compiler.py:1729 changed line) | R+I | the **changed op**: `f.column` selects the database column (post-fix) rather than the field-name string (pre-fix). `quote_name` (sqlite `operations.py:187-190`) is reproduced concretely as `quoteName` (I). The accumulate-and-join loop mirrors the generator-then-`", ".join`. |
| 3 | `for f in updateFields do assigns := assigns ++ [assignColumn f]` | `", ".join(f"{q} = EXCLUDED.{q}" for q in map(quote_name, update_fields))` where `update_fields = (f.column for f in self.query.update_fields)` (compiler.py:1728 changed line) | R+I | same changed op on the update list: each assignment is built from the quoted **column** `q = EXCLUDED.q`. `assignColumn` reproduces the f-string concretely (I); `f.column` selection is the R/changed op. |
| 4 | `"ON CONFLICT(".toList ++ … ++ ") DO UPDATE SET ".toList ++ …` | the UPDATE-branch template `"ON CONFLICT(%s) DO UPDATE SET %s"` of `on_conflict_suffix_sql` (sqlite `operations.py:420-428`; identical in postgres `operations.py:356-364`) | I | identical concrete op: substitution into the fixed literal template is fixed-order concatenation of the two rendered slots with the literal framing text. The renderer is UNCHANGED by the patch — reproduced concretely, not axiomatized. |

No A-consumed rows: the proof discharges the concatenation/joins directly; no
UNCHANGED-callee property is assumed (axioms region empty, G-AX is a skip stub).
No A-reference rows: every callee (`get_field` name-resolution, `quote_name`,
`on_conflict_suffix_sql` template substitution) is either the R-refinement
carrier or reproduced concretely as an I op — none is abstracted behind a model
that needs G-AX validation. No changed-inexpressible op.

## Discriminating clause (G-DIFF)
The discriminator is rows 2-3: post-fix the suffix is keyed by `f.column`,
pre-fix by `f.name`. Whenever any field has `column ≠ name` (the F2P case:
`db_column="rAnK"` for field `rank`, `db_column="oTheRNaMe"` for field `name`),
the prepatch impl emits `quoteName f.name` and the frozen
`problem_spec_renderUpsertClause` demands `quoteName f.column`, so the rendered
strings differ. Hence the prepatch `correct_renderUpsertClause` cannot close —
verified (Solution_prepatch.lean fails G-VERIFY). When every `column == name`
the two legs coincide, which is why the bug was latent until a field declared a
distinct database column.
