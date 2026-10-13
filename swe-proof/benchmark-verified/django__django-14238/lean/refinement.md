# refinement.md — django__django-14238

Maps every operation in `implementation_subclassCheck` to its `patch.diff`
counterpart in `AutoFieldMeta.__subclasscheck__`
(django/db/models/fields/__init__.py:2523). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** op left as the real repo
callee in G-CONF (not axiomatized), **I** identical concrete op.

## Patch (post-patch `__subclasscheck__`)
```python
def __subclasscheck__(self, subclass):
    return issubclass(subclass, self._subclasses) or super().__subclasscheck__(subclass)
```
where `self._subclasses == (BigAutoField, SmallAutoField)`.

The single changed token replaces the identity-membership test
`subclass in self._subclasses` with the reflexive-transitive subclass test
`issubclass(subclass, self._subclasses)`. Everything else is unchanged: the
`or super().__subclasscheck__(subclass)` disjunct and the fixed member tuple.

## Modeling decision
The observable behavior of `__subclasscheck__` is the boolean it returns. That
boolean is

    issubclass(subclass, (m0, m1, …))  or  super().__subclasscheck__(subclass)

and `issubclass(c, (m0, m1, …))` is `True` iff `issubclass(c, mi)` for some member
`mi`. So the model:

- represents class objects as an abstract type `Cls` compared only through
  relations (no internal structure assumed);
- takes the reflexive-transitive subclass relation `issubclass` as an arbitrary
  parameter `isSub : Cls → Cls → Bool` (the unchanged builtin);
- takes the inherited default check `super().__subclasscheck__` as an arbitrary
  parameter `superCheck : Cls → Bool` (the unchanged inherited method);
- computes `subclasses.any (fun d => isSub subclass d) || superCheck subclass`.

Universally quantifying `isSub` and `superCheck` makes the spec hold for EVERY
subclass relation and inherited check, so the only thing it pins is that
membership against the designated members is tested by the (reflexive-transitive)
subclass relation rather than by identity — which is exactly the fix. The fold-as
`for d in subclasses do if isSub subclass d then matched := true` is the
skeleton-faithful imperative form of `any(issubclass(subclass, d) for d in
self._subclasses)`.

## Operation correspondence
| # | Lean op (`implementation_subclassCheck`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut matched := false` | initial accumulator for `any(...)` | I | the `any` short-circuit identity element. |
| 2 | `for d in subclasses do` | iterate `self._subclasses` | R | tuple `(BigAutoField, SmallAutoField)` ↔ `subclasses : List Cls`; order irrelevant to the disjunction. |
| 3 | `if isSub subclass d then matched := true` | `issubclass(subclass, self._subclasses)` (per-member leg) | A-reference | reflexive-transitive subclass relation; the UNCHANGED builtin `issubclass`, left abstract (universally quantified) in spec/proof and bound to the REAL `issubclass` in G-CONF. This is the FIXED leg (was identity `subclass in ...`). |
| 4 | `matched \|\| superCheck subclass` | `... or super().__subclasscheck__(subclass)` | A-reference | unchanged inherited default check; left abstract and bound to the REAL inherited `type.__subclasscheck__` in G-CONF. |
| 5 | `return ...` | `return ...` | I | return the boolean. |

## R/I legs ⇒ G-CONF
Ops 1, 2, 5 are the R/I content (accumulator init, list iteration over the member
tuple, return). Ops 3 and 4 are A-references: G-CONF leaves them as the REAL
`issubclass` and the REAL inherited `__subclasscheck__` (it does NOT substitute an
axiom model), which is precisely how the R/I structure (any-over-members ∨
inherited) is isolated and tested. `conf_skip = false`: the impl region has genuine
R/I content (the any-over-members disjunction structure is the modeled behavior),
so `conformance_check.py` differential-tests the shadow against the patched
`issubclass(candidate, AutoField)` over ≥10^5 fuzzed candidate classes.

## No A-consumed row
The proof consumes no property of `isSub` or `superCheck` (both universally
quantified), so `meta.json axioms = []`. Ops 3, 4 are recorded as A-references
solely to document the G-CONF binding to the real callees; there is no
`opaque`/`axiom` declaration in `Solution.lean` and `axiom_check.py` is a skip
stub.

## F2P alignment
`test_issubclass_of_autofield` builds `MyBigAutoField(BigAutoField)` and
`MySmallAutoField(SmallAutoField)` and asserts `issubclass(field, AutoField)` is
true for them (and for the base members). `test_default_auto_field_setting_bigautofield_subclass`
configures `MyBigAutoField` as the default primary-key class and asserts the model
picks it up (which requires the subclass check to accept it). Pre-patch the
membership leg tested IDENTITY (`subclass in self._subclasses`), so a class merely
DERIVED from a designated member was rejected by that leg, and the inherited
`super().__subclasscheck__` also rejects it (the designated members are not in the
base class's ordinary MRO) — the whole check returned false. The discriminating
clause `problem_spec_subclassCheck` pins (candidate that is a reflexive-transitive
subclass of a member ⇒ accepted), and the prepatch impl (identity-only leg) cannot
satisfy it. `patch.diff` (gold verbatim) makes the harness resolve.
