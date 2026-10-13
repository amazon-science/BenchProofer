# refinement.md — sphinx-doc__sphinx-9698

Maps every operation in `implementation_getIndexText` to its `patch.diff` /
real-source counterpart in `PyMethod.get_index_text`
(`sphinx/domains/python.py:784-803`). Tags: **R** type-refinement, **A-consumed**
proof uses a callee axiom, **A-reference** deep-modeled changed op validated ==
real callee, **I** identical concrete op.

## Source (post-patch `get_index_text`)
```python
def get_index_text(self, modname, name_cls):
    name, cls = name_cls
    try:
        clsname, methname = name.rsplit('.', 1)
        if modname and self.env.config.add_module_names:
            clsname = '.'.join([modname, clsname])
    except ValueError:
        if modname:
            return _('%s() (in module %s)') % (name, modname)
        else:
            return '%s()' % name

    if 'classmethod' in self.options:
        return _('%s() (%s class method)') % (methname, clsname)
    elif 'property' in self.options:
        return _('%s (%s property)') % (methname, clsname)        # <-- gold edit: was '%s() (%s property)'
    elif 'staticmethod' in self.options:
        return _('%s() (%s static method)') % (methname, clsname)
    else:
        return _('%s() (%s method)') % (methname, clsname)
```
The modeled value is the returned label `str`. (The unpacked `cls` is unused in
the real source; not modeled.)

## Operation correspondence
| # | Lean op (`implementation_getIndexText`) | source op | tag | note |
|---|---|---|---|---|
| 1 | `match rsplitLastDot name with` | `try: clsname, methname = name.rsplit('.', 1) ... except ValueError:` | R | `rsplit('.',1)` ↔ split on last dot; the unpack-`ValueError` (no dot) ↔ `none`; success ↔ `some (clsname0, methname)`. Bijection in mapping.md. |
| 2 | `none ⇒ if modname != "" then return name ++ "() (in module " ++ modname ++ ")"` | `if modname: return _('%s() (in module %s)') % (name, modname)` | R/I | gettext identity + `%s` substitution ↔ concatenation. |
| 3 | `none ⇒ else return name ++ "()"` | `else: return '%s()' % name` | R/I | `'%s()' % name` ↔ `name ++ "()"`. |
| 4 | `let mut clsname := clsname0` | `clsname` from the unpack | I | accumulator starts at the trailing-class part. |
| 5 | `if addModuleNames && modname != "" then clsname := modname ++ "." ++ clsname0` | `if modname and self.env.config.add_module_names: clsname = '.'.join([modname, clsname])` | R/I | `'.'.join([modname, clsname])` (two elements) ↔ `modname ++ "." ++ clsname0`; Python `modname and add_module_names` ↔ Lean `addModuleNames && modname != ""` (truthiness of non-empty `modname`). |
| 6 | `if isClassmethod then return methname ++ "() (" ++ clsname ++ " class method)"` | `if 'classmethod' in self.options: return _('%s() (%s class method)') % (methname, clsname)` | R/I | format-string ↔ concatenation. |
| 7 | `else if isProperty then return methname ++ " (" ++ clsname ++ " property)"` | `elif 'property' in self.options: return _('%s (%s property)') % (methname, clsname)` | R/I | **the gold edit**: no `()` after `methname` for the property kind. |
| 8 | `else if isStaticmethod then return methname ++ "() (" ++ clsname ++ " static method)"` | `elif 'staticmethod' in self.options: return _('%s() (%s static method)') % (methname, clsname)` | R/I | unchanged call-like kind. |
| 9 | `else return methname ++ "() (" ++ clsname ++ " method)"` | `else: return _('%s() (%s method)') % (methname, clsname)` | R/I | unchanged default kind. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference of an
unchanged callee — `rsplit`, `.join`, `_()`, `%` are modeled deeply as string
ops). Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the post-patch `get_index_text` behavior over ≥10^5
fuzzed inputs. `conf_skip = false`.

## Prepatch = the real bug
Pre-patch, the `property` arm returns `_('%s() (%s property)') % (methname,
clsname)` — i.e. WITH the empty argument list `()` after the member name. The
prepatch impl (`Solution_prepatch.lean`) is exactly this: its property branch
returns `methname ++ "() (" ++ clsname ++ " property)"`. It therefore cannot
satisfy `problem_spec_getIndexText` on the discriminating clause
(`isClassmethod = false → isProperty = true → result = methname ++ " (" ++
clsname ++ " property)"`) for any non-empty `methname` (the `()` makes the strings
differ). This is precisely the behavior the FAIL_TO_PASS test
`test_pymethod_options` exercises: the `:property:` index entry must read
`meth5 (Class property)`, not `meth5() (Class property)`. The carried gold proof
fails to typecheck against the buggy impl (G-DIFF). The other three label shapes
are unchanged, so only the property behavior is independently fixed (one
prepatch).
