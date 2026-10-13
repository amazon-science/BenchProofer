# mapping.md — sphinx-doc__sphinx-9698

## Symbol binding (file:line @ base_commit f050a7775dfc9000f55d023d36d925a8d02ccfa8)
Modeled function: `PyMethod.get_index_text`, `sphinx/domains/python.py:784-803`.
It builds the text of the single index entry registered for a documented class
member. The gold patch edits `:799` (the `property` arm), changing the format
string from `'%s() (%s property)'` to `'%s (%s property)'` — i.e. it removes the
empty argument list `()` after the member name for the value-like (property)
kind, while leaving the call-like kinds (ordinary method, class method, static
method) unchanged.

Lean modeled function name: `getIndexText` (neutral — names the *behavior*
"produce the index-entry label for a member", not a patched symbol).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `getIndexText` (modeled function) | `PyMethod.get_index_text`, `python.py:784-803` |
| `name` | `name` (the `name_cls[0]` argument), `python.py:785` |
| `modname` | `modname` argument, `python.py:784` |
| `isClassmethod` | `'classmethod' in self.options`, `python.py:796` |
| `isProperty` | `'property' in self.options`, `python.py:798` |
| `isStaticmethod` | `'staticmethod' in self.options`, `python.py:800` |
| `addModuleNames` | `self.env.config.add_module_names`, `python.py:788` |
| `rsplitLastDot name` | `clsname, methname = name.rsplit('.', 1)` (in `try`), `python.py:787`; the `except ValueError` arm is the `none` case |
| `clsname0` | `clsname` before module prefixing, `python.py:787` |
| `clsname` (after prefix) | `clsname = '.'.join([modname, clsname])` when `modname and add_module_names`, `python.py:788-789` |
| `methname` | `methname`, `python.py:787` |
| result | the `str` returned by `get_index_text`, `python.py:792-803` |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `name : str` (dotted member name) | `name : String` |
| `modname : str` (may be `''`) | `modname : String` |
| `'classmethod' in self.options : bool` | `isClassmethod : Bool` |
| `'property' in self.options : bool` | `isProperty : Bool` |
| `'staticmethod' in self.options : bool` | `isStaticmethod : Bool` |
| `self.env.config.add_module_names : bool` | `addModuleNames : Bool` |
| `name.rsplit('.', 1)` returning `[before, after]` / raising `ValueError` on unpack | `rsplitLastDot name = some (before, after)` / `none` |
| `'.'.join([modname, clsname])` | `modname ++ "." ++ clsname0` |
| the `str` index label | `result : String` |
| `_(fmt) % (a, b)` (gettext identity in default/test locale; `%s` substitution) | Lean string concatenation `a ++ "..." ++ b` |

### gettext / format-string note
`_(...)` is the gettext translation hook; under the default (and test) locale it
is the identity on the format string, and `% (methname, clsname)` performs the two
`%s` substitutions left-to-right. The four format strings are therefore modeled as
the exact concatenations:
- classmethod: `methname ++ "() (" ++ clsname ++ " class method)"`
- property (post-patch): `methname ++ " (" ++ clsname ++ " property)"`
- staticmethod: `methname ++ "() (" ++ clsname ++ " static method)"`
- ordinary method: `methname ++ "() (" ++ clsname ++ " method)"`
and the `except ValueError` fallbacks as `name ++ "() (in module " ++ modname ++ ")"`
(when `modname` truthy) / `name ++ "()"` (otherwise).

## rsplit semantics
`name.rsplit('.', 1)` splits on the LAST `.`. When `name` contains no `.`, it
returns a one-element list, and the tuple unpack `clsname, methname = ...` raises
`ValueError`, taking the `except` branch. `rsplitLastDot` mirrors this: `splitOn
"."` then reverse; a list of length ≤ 1 (no dot) yields `none`; otherwise the head
of the reversed list is `methname` and the remainder rejoined with dots is
`clsname0`. (Trailing-dot / leading-dot names produce empty segments on both
sides identically, since `str.rsplit('.',1)` and `splitOn "."` agree on empty
fields.)

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `name.rsplit`, `'.'.join`, the
  `_()` gettext hook, and `%` formatting are all modeled deeply as string
  operations (split / intercalate / concatenation), an all-R/I leg validated by
  G-CONF. There is no opaque callee contract.
- Flag dependency: the four label shapes are selected by an `if/elif/elif/else`
  chain on `classmethod` → `property` → `staticmethod` → (default) method. The
  `property` arm is the only one without `()` after the member name (post-patch).
  The module-name prefix on `clsname` fires iff `modname` is non-empty AND
  `add_module_names` is set.

## G-LEAK
The problem_statement mentions "index entry", "parens", "property", "py:method"
directive. The spec view uses neutral behavioral vocabulary ("index-entry label",
"value-like kind", "empty argument list", "member kind"). The modeled-function
identifier `getIndexText` shares no patched def/class name. The `property` term is
public (it is in the problem_statement). No diff line, file path, or narration of
the edit appears in the spec view.

## Pinned G-CONF fuzz seed
`9698`.
