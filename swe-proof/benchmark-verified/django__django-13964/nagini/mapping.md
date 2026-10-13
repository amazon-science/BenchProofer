# mapping.md — django__django-13964

Binds every `model.py` symbol to its repository counterpart at
`base_commit = f39634ff229887bf7790c069d0c411b38494ca38`, states the type
abstraction, and gives the provenance of the one A-reference the deep model is
validated against (there is no consumed `@ContractOnly` axiom).

Repo file under change: `django/db/models/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `adopt_referenced_key_if_unset(target, related_key)` | the `elif` branch of `Model._prepare_related_fields_for_save(self, operation_name)` — `django/db/models/base.py:911` (the modeled branch at lines 936-939) | the modeled changed function (adopt the referenced object's stored key into the local foreign-key attribute when that attribute is empty) |
| `SaveTarget` / `target.fk` | the model instance `self` and its local foreign-key value attribute reached by `getattr(self, field.attname)` / `setattr(self, field.attname, …)` (`base.py:936,939`) | the persisting object and its local stored-key (FK `attname`) attribute |
| `related_key` | `obj.pk` — the referenced object's stored primary key (`base.py:939`, `obj = getattr(self, field.name)` at `base.py:919`) | the already-saved referenced object's stored key, copied into the local attribute |
| `is_empty_placeholder(value)` *(deep model — A-reference)* | the membership test `getattr(self, field.attname) in field.empty_values` (`base.py:936`, post-patch) and the constant `field.empty_values` (`django/db/models/fields/__init__.py:91`, `= list(validators.EMPTY_VALUES)`, `validators.EMPTY_VALUES = (None, '', [], (), {})` at `django/core/validators.py:16`) | pure spec: whether the local key value is one of the recognized empty placeholders |
| `stored_seq(value)` | the character content of `getattr(self, field.attname)` | pure spec: the value's sequence content (empty for the absent marker) |

The gold patch (the one change, `base.py:936`) replaces the local-attribute
emptiness test `getattr(self, field.attname) is None` with
`getattr(self, field.attname) in field.empty_values`; the body
`setattr(self, field.attname, obj.pk)` is unchanged. The branch is reached only
once `obj.pk is not None` (the preceding `if obj.pk is None: … raise` guard,
`base.py:928-935`), i.e. the referenced object carries a real stored key —
hence `Requires(len(related_key) > 0)`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the model `self` object | `SaveTarget` instance | a minimal class carrying only the one touched attribute |
| `getattr(self, field.attname)` / `setattr(self, field.attname, …)` — the local FK value via its dynamic name | the field `target.fk` (`Optional[List[int]]`) | the attribute named by `field.attname` IS the local foreign-key value; reading/writing it ↔ reading/writing `target.fk`. The absent marker `None` (an unset numeric/`AutoField` key) ↔ `target.fk is None`; the empty character sequence `''` (a textual key not yet set) ↔ `target.fk == []`; a concrete textual key (a `str`) ↔ a non-empty `List[int]` of code points. **`None` and `''` are genuinely distinct** — exactly as the abstraction keeps them. |
| `obj.pk` — the referenced object's stored primary key (a non-numeric `str`, or a numeric value) | `related_key : List[int]` of code points | the saved key; non-empty (`len(related_key) > 0`) because the branch is past the `obj.pk is None` guard. A `str` ↔ `List[int]`; `str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`. |
| `field.empty_values` (the collection `[None, '', [], (), {}]`) | the `is_empty_placeholder` predicate (`value is None or len(value) == 0`) | the two members reachable by the local key attribute — the absent marker `None` and the empty character sequence `''` — are exactly the carriers `is_empty_placeholder` returns True for (`None` and `[]`). A non-empty key (a non-empty `List[int]`) is in neither, so `is_empty_placeholder` returns False. (See §3 for the A-reference soundness check.) |
| `str` value inside a specification | `PSeq[int]` via `ToSeq` / `stored_seq` | `PSeq` `take`/`drop`/`len`/`[i]` mirror `str` slice/`len`/index |

`field.attname` is a string-named attribute; Nagini bans dynamic attribute
access and `str` indexing, so the dynamic name is modelled as the concrete
field `target.fk`. This is sound because the patch's `getattr`/`setattr` touch
exactly that one local foreign-key attribute, which the F2P test observes via
`child.parent_id`.

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

### 3.1 `is_empty_placeholder` deep model ↔ `field.empty_values` membership (A-reference)
**Source.** `Field.empty_values = list(validators.EMPTY_VALUES)`
(`django/db/models/fields/__init__.py:91`), and
`validators.EMPTY_VALUES = (None, '', [], (), {})`
(`django/core/validators.py:16`). `ForeignKey`/`ForeignObject`
(`django/db/models/fields/related.py:444,771`) inherit this default unchanged,
so for the foreign-key field the change tests against,
`field.empty_values == [None, '', [], (), {}]`.

The changed string operation `getattr(self, field.attname) in field.empty_values`
is modelled **deeply** by the `@Pure` predicate `is_empty_placeholder` (with
`stored_seq`); there is **no consumed axiom**. The deep model is validated equal
to the real membership semantics out-of-band by axiom_check.py (G-AX). On the
values the local foreign-key attribute can actually hold:

  - `None` (the absent marker, an unset numeric/`AutoField` key) — `in
    empty_values` is **True**; `is_empty_placeholder(None) == True`.
  - `''` (the empty character sequence, a textual key not yet set) — `in
    empty_values` is **True**; `is_empty_placeholder([]) == True`.
  - a concrete textual key (`'jeff'`, `'foo'`, even `'0'`) — `in empty_values`
    is **False**; `is_empty_placeholder([c, …]) == False`.

So the deep model and the real `in field.empty_values` agree on every value the
attribute can take. The two further `empty_values` members `[]`, `()`, `{}`
(empty list/tuple/dict) are unreachable for a scalar foreign-key value and are
irrelevant to the modeled behaviour; the model abstracts the textual carrier as
`List[int]` whose only empty representative is `[]` (the empty string).

**Soundness check (G-AX):** `axiom_check.py` configures an in-memory sqlite
database and minimal dependency-free models (the structural twins of the test's
`ParentStringPrimaryKey`/`ChildStringPrimaryKeyParent`, plus a numeric-PK pair),
then (a) reads the REAL `field.empty_values` of each foreign-key field and
asserts its membership on `{None, '', 'foo', '0', 'jeff'}` matches
`is_empty_placeholder`, and (b) drives the REAL changed method
`Model._prepare_related_fields_for_save` end-to-end on the failing scenario,
asserting the referenced textual key is adopted into the local attribute (not
left as `''`), the numeric absent-marker case still adopts the parent pk, and a
deliberately-set non-empty key is preserved. Exit 0 iff sound. It imports only
Django (the module the patch lives in); nothing test-private. (Outside the
container Django is absent, so it prints `G-AX SKIP` and returns 0; the
orchestrator runs it in-container.)

The A-reference is flag-independent: `field.empty_values` is a model-level
constant, identical across database backends; G-AX exercises the default
`sqlite3` backend the harness uses.
