# refinement.md — astropy__astropy-7166

Operation correspondence between `implementation_inheritDocstrings` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are declared or consumed. The only operation the patch changes — the
eligibility guard that decides which members get their missing documentation
filled — is modeled DEEPLY in Lean (`eligible`, spelled out as the boolean
predicate). The unchanged base-class MRO lookup is folded into the `superDoc`
input (an A-reference, validated by G-CONF). Every row is **R**,
**A-reference**, or **I**.

## `implementation_inheritDocstrings` ↔ the docstring-filling loop of `InheritDocstrings.__init__`

The gold patch turns

```python
for key, val in dct.items():
    if (inspect.isfunction(val) and                       # PRE-PATCH guard
        is_public_member(key) and
        val.__doc__ is None):
        for base in cls.__mro__[1:]:
            super_method = getattr(base, key, None)
            if super_method is not None:
                val.__doc__ = super_method.__doc__
                break
```

into the same loop with the guard widened:

```python
    if ((inspect.isfunction(val) or inspect.isdatadescriptor(val)) and   # POST-PATCH
            is_public_member(key) and
            val.__doc__ is None):
```

Everything else (the `is_public_member` helper, the `val.__doc__ is None` test,
the MRO walk, and `super().__init__`) is unchanged.

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `for m in members do … result := result ++ [...]` | `for key, val in dct.items():` | I | iterate the class namespace in order; one output entry per input member |
| `isPublicMember m.key` | `is_public_member(key)` (dunder-or-not-private) | I | pure string predicate reproduced concretely |
| `m.doc.isNone` | `val.__doc__ is None` | I | "currently undocumented" test |
| `m.isFunction \|\| m.isDataDescriptor` | `inspect.isfunction(val) or inspect.isdatadescriptor(val)` | A-reference | the EDITED guard. `isFunction`/`isDataDescriptor` are the observed boolean results of the real stdlib predicates; modeled deeply as flags, validated == real `inspect.*` by G-CONF. Pre-patch dropped the `isDataDescriptor` disjunct |
| `eligible m` (= guard conjunction) | the whole `if (… and is_public_member(key) and val.__doc__ is None)` | A-reference | conjunction of the three concrete predicates |
| `{ m with doc := superDoc m.key }` | `val.__doc__ = super_method.__doc__` after `for base in cls.__mro__[1:]: super_method = getattr(base,key,None); if super_method is not None: …; break` | A-reference | the unchanged MRO lookup result, folded into the `superDoc` input function; validated by G-CONF building real classes under the real metaclass and reading resulting `__doc__` |
| `else result := result ++ [m]` | member not matching the guard is left as-is | I | name/kind/doc preserved verbatim (frame) |
| `return result` | the mutated namespace members | R | each `(key, val)` ↦ a `Member`; `val.__doc__` ↦ `Member.doc` |

## Independently-observable behavior (G-DIFF)

- `Solution_prepatch.lean`: the impl guard is `m.isFunction && isPublicMember
  m.key && m.doc.isNone` — it omits the `m.isDataDescriptor` disjunct. A public,
  undocumented member that is a descriptor but not a callable
  (`isFunction = false`, `isDataDescriptor = true`) is therefore left untouched
  (`doc` stays `none`) instead of inheriting `superDoc m.key`. The carried gold
  proof of `correct_inheritDocstrings` fails to close on the `doc` clause for
  exactly those members (`eligible m = true` but the impl returns `m.doc`, not
  `superDoc m.key`). This is the single fixed behavior.
  (FAIL_TO_PASS: `astropy/utils/tests/test_misc.py::test_inherit_docstrings`,
  whose new assertion checks that a subclass `property` without its own
  docstring inherits the base property's docstring.)
