# refinement.md — django__django-14771

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`relaunchArgv` `do` block and the deep `relaunchArgvSpec`/`xFlag`/`warnFlag`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; bijection stated), **A** (axiomatized callee — none here), or **I**
(identical concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); this narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The argument-vector site — `get_child_arguments()`

Gold hunk (`django/utils/autoreload.py`, after `args = [sys.executable] + [...]`):

```
  args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]
+ if sys.implementation.name == 'cpython':
+     args.extend(
+         f'-X{key}' if value is True else f'-X{key}={value}'
+         for key, value in sys._xoptions.items()
+     )
  # __spec__ … (unchanged tail: args += ['-m', name] + sys.argv[1:], or args += sys.argv)
```

| # | Solution.lean impl op (`relaunchArgv`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `executable : List Char`; `args := [executable]` | `args = [sys.executable]` | R + I | the interpreter-path `str` ↔ `List Char` (mapping.md §2); seeding a one-element list is **I**. |
| A2 | `args := args ++ warnopts.map warnFlag` (`warnFlag o = "-W" ++ o`) | `+ ['-W%s' % o for o in sys.warnoptions]` | I + R | the pre-existing warning-option forwarding, unchanged. `'-W%s' % o` ↔ `"-W".toList ++ o` (**R**, str ↔ List Char); the per-element map + list concat is **I**. |
| A3 | `if isCpython then args := args ++ xopts.map xFlag` | `if sys.implementation.name == 'cpython': args.extend(<gen>)` | I + R | the implementation-name guard `== 'cpython'` ↔ `isCpython` (**R**, `Bool`, mapping.md §2); the conditional `list.extend` of the per-option flags is **I**. Off CPython both sides contribute nothing. |
| A4 | each summand `xFlag (key, v)` = `if v = bare then "-X"++key else "-X"++key++"="++value` | `f'-X{key}' if value is True else f'-X{key}={value}'` | R + I | `value is True` ↔ `v = XVal.bare` and a string value `s` ↔ `XVal.eq s.toList` (mapping.md §2, the `_xoptions` value-shape note); the f-string concatenations ↔ `++` (**R**); the per-option map over `.items()` order is **I**. |
| A5 | `args := args ++ argv`; `return args` | the unchanged `__spec__`/`elif`/`else` tail that appends the trailing program arguments (`sys.argv[1:]` after `-m name`, or `sys.argv`) and returns `args` | R | the trailing program arguments are abstracted as the single ordered input `argv : List (List Char)` (**R**, element-wise str ↔ List Char). The patch does not touch this tail; the X-option block is inserted strictly before it, so the model places `xopts.map xFlag` before `argv`, matching the patch's insertion point. mapping.md §1. |

Discriminating content of the change — on CPython, the configured runtime
X-options are forwarded as `-X` flags (`-Xkey` bare, `-Xkey=value` keyed), in
order, after the `-W` flags and before the trailing arguments — lives in the
`(if isCpython then xopts.map xFlag else [])` summand of `relaunchArgvSpec`
(model) ⇔ the inserted `if … args.extend(…)` block (real). The pre-patch code
forwarded NO X-options; `Solution_prepatch.lean` reproduces that (it omits the
`xopts.map xFlag` append entirely) and **fails** `out = relaunchArgvSpec …`,
leaving the residual goal `isCpython = true → xopts = []` (G-DIFF) — the exact
F2P discriminator (`test_xoptions`, which sets `sys._xoptions = {'utf8': True,
'a': 'b'}` and expects `-Xutf8`, `-Xa=b`).

## B. No consumed axioms / no A-reference

The changed region calls no library function whose behaviour the proof must
assume. The list comprehension over `warnoptions`, the `== 'cpython'` test, the
generator over `_xoptions.items()`, and `list.extend`/`+` are all closed concrete
ops (transliterated I/R). `Path(...)`, `getattr(__main__, '__spec__', None)`,
`py_script.exists()`, and `subprocess.run` are unchanged and abstracted (the F2P
test mocks `sys.argv`/`sys.warnoptions`/`sys._xoptions` and reads the returned
list directly). Hence there is no `axiom`, no deep-model A-reference, and **no
`axiom_check.py`** (G-AX = skip). All refinement legs are R/I, fully covered by
G-CONF.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — forwarding the
configured runtime X-options to the relaunched interpreter on CPython, each
serialized by value shape — is modeled **deeply** (the spelled-out
`relaunchArgvSpec`/`xFlag` and the verified `do` block, A3–A4), not hidden behind
any axiom. There are no consumed axioms.

## D. verify(Solution) ⇒ resolved

`relaunchArgv` verifies only if its output equals `relaunchArgvSpec` — i.e. the
interpreter path, the `-W` warning flags, then (on CPython only) the `-X` flags
for every configured X-option in order with the correct `-Xkey` / `-Xkey=value`
shape, then the trailing arguments (A1–A5). By R (str ↔ List Char; `== 'cpython'`
↔ `isCpython`; `value is True` ↔ `XVal.bare`; the `_xoptions` value-shape
bijection) the verified construction equals the patched `get_child_arguments`'s
return list on every configuration; by G-CONF the R/I transliteration of
`relaunchArgvSpec` agrees with `patch.diff`'s behaviour on ≥10⁵ inputs (including
the F2P `test_xoptions` case). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point (plan §1.1) is refinement fidelity
(this doc, G-EQ + G-CONF); there is no axiom-soundness trust point because there
are no axioms.
