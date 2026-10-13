# refinement.md — operation correspondence (django__django-14580)

Maps every op in `implementation_serializeType` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python `TypeSerializer.serialize` iterates a `special_cases`
table of `(type, source-string, import-list)` triples, returns the first whose
type *is* `self.value`, and otherwise derives the reference from `__module__` /
`__qualname__`. The fix is the import-list of the `models.Model` row, changed
from `[]` to `['from django.db import models']`.

| # | Lean impl op | patch.diff / repo counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `specialCases := [(baseModel, "models.Model", ["from django.db import models"]), (noneType, "type(None)", [])]` | the `special_cases` list literal (the patched line is the first triple's import list) | I | concrete table; the discriminating element is the base-model import list |
| 2 | `for entry in specialCases do … if sameType case v then return (str, imports)` | `for case, string, imports in special_cases: if case is self.value: return string, set(imports)` | R | `case is self.value` ↔ `sameType case v` (`BEq` on `TypeVal` = the identity the function observes); `set(imports)` ↔ duplicate-free `List String` (R: set↔list bijection, mapping.md) |
| 3 | `match v with \| .builtin name => return (name, [])` | `if module == builtins.__name__: return self.value.__name__, set()` | I | built-in branch: bare name, empty imports |
| 4 | `\| .other module qualname => return (module ++ "." ++ qualname, ["import " ++ module])` | `return "%s.%s" % (module, self.value.__qualname__), {"import %s" % module}` | R | string formatting ↔ `++`; singleton set ↔ singleton list (R, mapping.md) |
| 5 | `\| _ => return ("", [])` | implicit `None` fall-through when `__module__` absent | I | unreachable on real type objects (every type has `__module__`); total-function placeholder, never the modeled path |

No A-consumed rows and no A-reference rows: the proof discharges `serializeSpec`
directly; no UNCHANGED callee property is assumed and nothing is axiomatized. No
changed-inexpressible op.

The discriminating clause is row 1/row 2 for `v = .baseModel`: the import list of
the base-model special case. The prepatch impl emits `(("models.Model", []))` for
`.baseModel`, so its `correct_serializeType` cannot close against the frozen
`problem_spec_serializeType` (which pins `serializeSpec .baseModel =
("models.Model", ["from django.db import models"])`). That is the G-DIFF signal.
