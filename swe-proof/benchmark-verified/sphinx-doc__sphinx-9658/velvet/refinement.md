# refinement.md — sphinx-doc__sphinx-9658

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`renderReference` `do` block and the deep `reportedName`/`renderedReference`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized/deep-modeled callee — none here), or **I**
(identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
narrative is audited by **G-EQ**. Claim: any impl verifying against this frozen
spec, refined per the map below, is behaviourally equal to the gold patch on the
tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The placeholder reference site

The observable behavior under test (`test_restify_mock`): for a stand-in
placeholder `cls` standing for `unknown.secret.Class`, `restify(cls)` must render
`:py:class:`unknown.secret.Class``, not `:py:class:`unknown.secret.``. The patch
fixes the value the placeholder reports as its simple name; `restify` then places
that name in the trailing position of whichever of its arms the placeholder's
module path selects.

`restify` is a **dispatch, not a single format**. It consults `cls.__module__`
(and, for the `isNewType` arm, `cls.__qualname__`) BEFORE it reaches the general
dotted arm, and each arm decorates differently. The model reproduces the arm
order:

| rule | guard on the placeholder | `restify` site | rendered shape |
|---|---|---|---|
| 1 | `__module__ == 'typing'` and reported name `== 'NewType.<locals>.new_type'` (`inspect.isNewType`, `sphinx/util/inspect.py:213-223`) | `sphinx/util/typing.py:119-125` | `` :py:class:`NAME` `` |
| 2 | `__module__ in ('__builtin__', 'builtins')` | `sphinx/util/typing.py:133-140` | `` :py:class:`NAME`\ [] `` |
| 3 | `__module__ == 'typing'`, other names | `sphinx/util/typing.py:193-195` | `` :py:class:`~typing.NAME` `` |
| 4 | any other `__module__` | `sphinx/util/typing.py:193, 196` | `` :py:class:`MODULE.NAME` `` |

`sphinx/util/typing.py` and `sphinx/util/inspect.py` are **not touched by the
patch**; their dispatch is repo behavior the specified rendering must agree with,
which is why it is modeled leg by leg rather than folded into one format. Rules
1-3 fire on three reserved module paths, and the patch changes the output of all
four rules (mapping.md §5), so none may be excluded from the domain.

Gold hunks (`sphinx/ext/autodoc/mock.py`):
```
 class _MockObject:
     __display_name__ = '_MockObject'
+    __name__ = ''
     ...
     def __init__(self, *args, **kwargs):
-        self.__qualname__ = ''
+        self.__qualname__ = self.__name__
 ...
 def _make_subclass(name, module, ...):
     attrs = {'__module__': module,
              '__display_name__': module + '.' + name,
+             '__name__': name,
              '__sphinx_decorator_args__': decorator_args}
```

| # | Solution.lean impl op (`renderReference`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `modulePath : List Char` | `cls.__module__` (= parent placeholder's `__display_name__`, `mock.py:75`) | R | `str` ↔ `List Char` (mapping.md §2). The module path is unchanged by the patch; it is an input to the rendering and the key `restify` dispatches on. |
| A2 | parameter `createdName : List Char` | the `name` a placeholder is created to stand for: the `name` arg of `_make_subclass`, stored post-patch as `__name__` (`mock.py:77`) | R | `str` ↔ `List Char`. The patch adds `'__name__': name` so this value is now carried on the placeholder. |
| A3 | `let simpleName := createdName` (the reported simple name **is** the creation name) | `self.__qualname__ = self.__name__` (`mock.py:44`, replacing `= ''`) | I | the single behavioral change: the reported simple name is the creation name, not the empty string. Modeled deeply by `reportedName createdName = createdName`. G-CONF transliterates this op directly. Post-patch `__name__` and `__qualname__` are the same string, so one modeled `reportedName` serves rule 2 (which reads `__name__`) and rules 1/3/4 (which read `__qualname__`) alike. |
| A4a | guard `modulePath = abbreviatedNamespace ∧ simpleName = aliasFactoryName` → `openMark ++ simpleName ++ closeMark` | `inspect.isNewType(cls)` (`inspect.py:219-223`) → `':py:class:`%s`' % cls.__name__` (`typing.py:125`) | I + R | concrete string-equality tests on `__module__`/`__qualname__` and a concrete concat (I); `str ↔ List Char` and the literal `':py:class:`'`/`` '`' `` fragments (R). This arm is *reachable only post-patch*: pre-patch `__qualname__` was `''`, so `isNewType` was always False for a placeholder. Python <3.10 branch, matching the pinned image (3.9.20). |
| A4b | guard `modulePath = coreNamespaceA ∨ modulePath = coreNamespaceB` → `openMark ++ simpleName ++ closeMark ++ elementListTail` | `cls.__module__ in ('__builtin__','builtins')` (`typing.py:133`) → `':py:class:`%s`\\ [%s]' % (cls.__name__, ', '.join(restify(a) for a in cls.__args__))` (`typing.py:135-138`) | I + R | the module-path test and the concat are concrete (I); the bracketed element list is the constant `'[]'` on the modeled domain because a placeholder answers every attribute access (`hasattr(cls,'__args__')` True) and the resulting mock iterates empty (`_MockObject.__iter__` returns `iter([])`), so the join is `''` (R, mapping.md §2 — an input-independent constant, which G-CONF checks on every rule-2 input rather than assuming). |
| A4c | guard `modulePath = abbreviatedNamespace` → `openMark ++ abbreviationMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark` | `_restify_py37`'s `hasattr(cls,'__qualname__')` arm, `cls.__module__ == 'typing'` → `':py:class:`~%s.%s`' % (cls.__module__, cls.__qualname__)` (`typing.py:193-195`) | I + R | dotted join behind the `'~'` abbreviation mark, concrete (I); `str ↔ List Char` and the literal fragments (R). |
| A4d | the `else` → `openMark ++ modulePath ++ ['.'] ++ simpleName ++ closeMark` | `_restify_py37`'s `hasattr(cls,'__qualname__')` arm, `else` → `':py:class:`%s.%s`' % (cls.__module__, cls.__qualname__)` (`typing.py:193, 196`) | I + R | the general dotted join, concrete (I); type refinement and literal fragments (R). This is the arm the F2P test exercises. |
| A5 | the ORDER of the four guards in the `do` block | the order of `restify`'s `elif` chain: `isNewType` (`typing.py:119`) precedes the builtins test (`typing.py:133`), which precedes the fall-through to `_restify_py37` (`typing.py:141-144`), inside which the `__qualname__` arm's `typing` sub-branch (`typing.py:194-195`) precedes its `else` (`typing.py:196`) | I | arm order is observable: `('__builtin__', 'NewType.<locals>.new_type')` takes rule 2, not rule 1, because `isNewType` also requires `__module__ == 'typing'`; and `('typing', 'Foo')` takes rule 3, not rule 4. Both crossings are in G-CONF's boundary cases. |

Discriminating content of the change — the reported simple name equals the
creation `name` rather than `''`. The pre-patch hard-coded `__qualname__ = ''`,
so every rule rendered a reference whose trailing segment was dropped
(`module.` not `module.name`; `` :py:class:``\ [] `` under a core namespace).
`Solution_prepatch.lean` reproduces that (`simpleName := []`) and **fails** all
five postconditions of the frozen spec (G-DIFF) — exactly on the `createdName`
vs `[]` discriminator, in every one of the four rules.

## B. No axioms / no A-reference

There is no axiomatized callee and no deep model of an outside callee. The whole
behavior is a total function of the placeholder's own carried data, modeled
deeply in the `pure` region — including `restify`'s dispatch, which is reproduced
rather than abstracted. `axioms` is empty; `axiom_check.py` is omitted and G-AX is
`skip` (mirroring `astropy__astropy-13236`).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the reported
simple name becomes the creation name instead of the empty string — is modeled
**deeply** (A3, `reportedName`), not hidden behind an axiom about the function
under change. The unchanged dispatch it flows through (A4a-A4d, A5) is likewise
modeled concretely, so no unchanged callee is owed a contract either.

## D. verify(Solution) ⇒ resolved

`renderReference` verifies only if, in each of the four rules, its output is that
rule's decoration around the trailing `createdName` (A3, A4a-A4d, A5) — the five
`ensures` pin the general law and each rule separately, so no single-rule reading
satisfies the spec. By R (`str ↔ List Char`, the per-rule literal fragments, the
constant empty element list) the verified rendering equals the real `restify`
output on a placeholder carrying the same data; on the F2P input
`('unknown.secret', 'Class')` that is `` :py:class:`unknown.secret.Class` ``.

G-CONF checks this mechanically: the R/I transliteration agrees with
`patch.diff`'s real `restify` on 2·10⁵ fuzzed inputs (seed 9658), with every one
of the four rules exercised (the run fails if a rule's hit count is zero) and with
the reserved paths and their near-misses drawn at real weight. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The single trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms to trust.
