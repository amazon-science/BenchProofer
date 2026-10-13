# mapping.md — django__django-14238

## Instance
- repo: django/django
- base_commit: 30e123ed351317b7527f632b3b7dc4e81e850449
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`AutoFieldMeta.__subclasscheck__` (django/db/models/fields/__init__.py:2523) decides
whether a candidate class should be treated as a subclass of the auto-field base
class. It answers true when the candidate is one of the metaclass's designated
member classes, or when the ordinary type machinery already considers it a
subclass.

At base_commit the membership test was an IDENTITY test (`subclass in
self._subclasses`): it matched only the two designated member classes themselves,
not classes derived from them. A user class deriving from one of the designated
members was therefore NOT recognized, so configuring it as the project default
primary-key class raised "must subclass AutoField". The gold patch replaces the
identity-membership test with a reflexive-transitive subclass test against the
same two designated classes:

```python
-        return subclass in self._subclasses or super().__subclasscheck__(subclass)
+        return issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)
```

`self._subclasses` is the fixed pair `(BigAutoField, SmallAutoField)`. Neither of
those derives from the auto-field base class in the ordinary MRO (they are
siblings sharing a common mixin), which is exactly why the metaclass needs this
explicit member list and why the default `super().__subclasscheck__` does not
cover them.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_subclassCheck` | `AutoFieldMeta.__subclasscheck__` (django/db/models/fields/__init__.py:2523) |
| `problem_spec_subclassCheck`   | the post-condition this method must satisfy |
| `isSub` (parameter)            | the builtin `issubclass(subclass, d)` reflexive-transitive subclass relation (CPython `type.__subclasscheck__` / `issubclass`) — unchanged callee |
| `superCheck` (parameter)       | `super().__subclasscheck__(subclass)` — the ordinary metaclass subclass check inherited from `type` — unchanged callee |
| `subclasses` (parameter)       | `self._subclasses`, the designated member tuple `(BigAutoField, SmallAutoField)` |
| `subclass` (parameter)         | the candidate class being checked |

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX
| Lean | Python | notes |
|---|---|---|
| `Cls : Type` | a Python class object | abstract; classes compared only by the relations below (no structure assumed) |
| `subclass : Cls` | the candidate class argument | |
| `subclasses : List Cls` | `self._subclasses` as an ordered list `[BigAutoField, SmallAutoField]` | tuple ↔ list; order is irrelevant to the result (`any`/`or`) |
| `isSub : Cls → Cls → Bool` | `issubclass(c, d)` (bool) | reflexive-transitive subclass relation; `isSub c d ↔ issubclass(c, d) == True` |
| `superCheck : Cls → Bool` | `super().__subclasscheck__(subclass)` (bool) | the inherited default subclass check |
| result `: Bool` | the bool returned by `__subclasscheck__` | `true ↔ True` |

`issubclass(c, (d0, d1, …))` is `True` iff `issubclass(c, di)` for some `i`; this
is modeled as `subclasses.any (fun d => isSub subclass d)`.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The subclass relation
  `issubclass` (`isSub`) and the inherited default check
  `super().__subclasscheck__` (`superCheck`) are both UNCHANGED builtins; they are
  left as universally-quantified parameters, so the spec holds for every such
  relation and the proof consumes no property of either. The modeled change is
  solely WHICH relation tests membership of the candidate against the designated
  classes (identity vs reflexive-transitive subclass). `axiom_check.py` is a skip
  stub.
- `issubclass` is recorded as an A-reference (deep_model_references): it is left
  abstract in the spec/proof and bound to the REAL `issubclass` builtin in G-CONF.
- No flag dependency.

## G-CONF fuzz seed
- pinned seed: `14238`
- ≥10^5 fuzzed candidate classes drawn from a fixed pool of real classes built in
  the patched testbed: the auto-field base class, its two designated member
  classes, user subclasses of each member class (the regression case), deeper
  subclasses, sibling/unrelated field classes, and `object`/`int`. The shadow
  (`subclasses.any (isSub subclass ·) || superCheck subclass`, with `isSub` =
  real `issubclass`, `superCheck` = the inherited `type.__subclasscheck__`) is
  diffed against the REAL patched `issubclass(candidate, AutoField)` (which
  dispatches through `AutoFieldMeta.__subclasscheck__`).
