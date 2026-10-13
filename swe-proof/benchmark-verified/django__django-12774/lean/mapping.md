# mapping.md — django__django-12774

## Symbol binding (file:line @ base_commit 67f9d076cf)
Modeled function: the field-name validation decision at the head of
`QuerySet.in_bulk(self, id_list=None, *, field_name='pk')`,
`django/db/models/query.py:685-693` (the guard that raises `ValueError` when
`field_name` is not a unique field). The rest of `in_bulk` (the id-list
batching and the `{getattr(obj, field_name): obj for obj in qs}` dict build,
`query.py:694-711`) is UNCHANGED by the gold patch and is downstream of the
guard; it is not modeled (the fix is purely the raise/proceed decision).

The gold patch widens the set of accepted field names: previously a non-`pk`
field was accepted only when its own `unique` attribute was true; now it is
additionally accepted when it is the sole field of an *unconditional*
`UniqueConstraint` declared on the model.

Lean modeled function name: `inBulk` (names the public method, which the
solver-visible `problem_statement` already calls `in_bulk`).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `fieldName : String` | the `field_name` keyword argument (`query.py:685`) |
| `fld : Field` | the resolved field object `self.model._meta.get_field(field_name)` (`query.py:692`), observed only through its `.unique` flag |
| `fld.unique` | `self.model._meta.get_field(field_name).unique` (the field's own unique attribute, `query.py:692`) |
| `cs : List UniqueConstraint` | `self.model._meta.constraints` projected to its `UniqueConstraint` members (the `isinstance(constraint, UniqueConstraint)` filter inside `Options.total_unique_constraints`, `options.py:837-841`) |
| `c.fields` | `constraint.fields` (the tuple of field names a constraint spans, `constraints.py:78`) |
| `c.isPartial` | `constraint.condition is not None` — `True` marks a conditional/partial unique constraint (the `condition is None` filter in `total_unique_constraints`, `options.py:840`) |
| `singleFieldUniqueConstraintFields cs` | `unique_fields = [constraint.fields[0] for constraint in opts.total_unique_constraints if len(constraint.fields) == 1]` (the post-patch list comprehension, `query.py` gold hunk) |
| result `Except String Unit` | `.error fieldName` ⟷ the method raises `ValueError("…must be a unique field but %r isn't." % field_name)` (`query.py:693`); `.ok ()` ⟷ the guard is passed and the method proceeds to build the result dict |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `field_name : str` | `fieldName : String` |
| `get_field(field_name).unique : bool` | `fld.unique : Bool` |
| `opts.constraints` ∩ `UniqueConstraint` | `cs : List UniqueConstraint` |
| `constraint.fields : tuple[str, ...]` | `c.fields : List String` |
| `constraint.condition is not None : bool` | `c.isPartial : Bool` |
| `total_unique_constraints` = `[c for c in constraints if isinstance(c, UniqueConstraint) and c.condition is None]` | `cs.filter (fun c => !c.isPartial)` (the `isinstance` filter is the R projection that defines `cs`; the `condition is None` filter is `!c.isPartial`) |
| `[c.fields[0] for c in total_unique_constraints if len(c.fields) == 1]` | `(cs.filter (fun c => !c.isPartial && c.fields.length == 1)).map (fun c => c.fields.headD "")` |
| raise `ValueError(... % field_name)` | `Except.error fieldName` |
| (no raise — method proceeds) | `Except.ok ()` |

### Result-type modeling note
The real `in_bulk` either raises `ValueError` or returns a dict. The fix changes
only the raise/proceed *decision*; the dict construction is unchanged and
downstream. We therefore model the outcome as `Except String Unit`: `.error
fieldName` for the raising branch (the offending field name stands in for the
formatted message, which embeds `field_name`), and `.ok ()` for "guard passed,
method proceeds". This faithfully captures the single behavior the patch alters.

### `get_field` provenance
`get_field(field_name)` is an UNCHANGED callee; the validation reads only its
`.unique` flag. Rather than axiomatize it, the resolved field's observable
(`fld.unique`) is supplied as the model input `fld` (a type-level R refinement —
`get_field` is not the fixed operation). For `field_name == "pk"` the real code
short-circuits before calling `get_field`, so `fld` is irrelevant on that branch
(matched by the Lean guard's first conjunct).

### `total_unique_constraints` provenance
`Options.total_unique_constraints` (`options.py:831-841`) is the unchanged callee
the patch consumes. Its two filters are modeled deeply, NOT axiomatized: the
`isinstance(c, UniqueConstraint)` filter is the R projection defining the input
`cs : List UniqueConstraint`; the `condition is None` filter is `!c.isPartial`.
The patch's own `len(constraint.fields) == 1` filter and `constraint.fields[0]`
projection are spelled out directly in `singleFieldUniqueConstraintFields`. No
`opaque`/`axiom` callee contract is consumed ⇒ `axiom_check.py` is a skip stub.

## Callee provenance + flag deps
No flag dependency. The decision fires purely on `fieldName`, the resolved
field's `unique` flag, and membership of `fieldName` among the single-field
unconditional unique-constraint fields.

## G-LEAK
The solver-visible `problem_statement` publicly names `QuerySet.in_bulk`,
`field_name`, `unique=True`, `UniqueConstraint`, `fields=[...]`, `constraints`,
and `Meta`, and shows the `ValueError("in_bulk()'s field_name must be a unique
field but %r isn't.")` message in the traceback. The spec view uses only those
public terms (`inBulk`, `UniqueConstraint`, `unique`, `fieldName`, `"pk"`). It
does NOT name the patched internal helper `total_unique_constraints`, the local
`unique_fields`, `opts`, the file path, or any diff line, and it does not narrate
the bug→fix mechanism — it states the abstract acceptability rule only.

## Pinned G-CONF fuzz seed
`12774`.
