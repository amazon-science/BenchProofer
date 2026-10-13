# mapping.md — sphinx-doc__sphinx-9229

## Instance
- repo: sphinx-doc/sphinx
- base_commit: 876fa81e0a038cda466925b85ccf6c5452e0f685
- changed file: `sphinx/ext/autodoc/__init__.py` (class `ClassDocumenter`)
- spec_provenance: cold

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_getDoc` / `problem_spec_getDoc` / `correct_getDoc` | `ClassDocumenter.get_doc` (the `doc_as_attr` alias branch) | `sphinx/ext/autodoc/__init__.py:1676-1681` |
| `implementation_addContent` / `problem_spec_addContent` / `correct_addContent` | `ClassDocumenter.add_content` | `sphinx/ext/autodoc/__init__.py:1724-1732` |
| `commentPresent` (pure helper) | the truthiness test `if comment:` applied to the value returned by `ClassDocumenter.get_variable_comment` (post-patch helper) | `get_variable_comment` post-patch lines 1728-1736 in patch.diff |

## Callee provenance / inputs

The post-patch code introduces `get_variable_comment(self)`, which does:
```python
key = ('', '.'.join(self.objpath))
analyzer = ModuleAnalyzer.for_module(self.get_real_modname())
analyzer.analyze()
return list(self.analyzer.attr_docs.get(key, []))   # None on PycodeError
```
Its result is consumed in two places ONLY via Python truthiness (`if comment:`,
`not self.get_variable_comment()`):
- `None`  → failed lookup (`PycodeError`)  → falsey
- `[]`    → key absent / empty doc-comment → falsey
- `[..]`  → a documentation comment present → truthy

This value is an **abstract input** to the modeled decision logic — it is
produced by the environment (the module source being analyzed), not computed by
the changed branch. It is modeled as `comment : Option (List String)` and its
truthiness as the pure helper `commentPresent` (`some (_::_) → true`, else
`false`). No `opaque`/`axiom` callee is declared: `get_variable_comment`,
`ModuleAnalyzer.for_module`, `attr_docs`, `get_real_modname` are NOT modeled as
callees — only the boolean their result feeds into matters to the fix, and that
boolean is the abstract input.

Likewise `restify(self.object)` (the rendered alias-target description) is an
abstract input `aliasText : String`; `normalDoc`/`incoming` are the
ordinary-path doc block and the caller-supplied `more_content`, also abstract
inputs (their unchanged values are pinned by the frame conjuncts).

## Lean ↔ Python type bijection (used by G-CONF)

| Python | Lean | bijection |
|---|---|---|
| `bool` `self.doc_as_attr` | `docAsAttr : Bool` | identity |
| `get_variable_comment()` value (`None` \| `list[str]`) | `comment : Option (List String)` | `None ↔ none`, `list xs ↔ some xs` |
| `if comment:` truthiness | `commentPresent comment` | `None/[] ↔ false`, non-empty list ↔ `true` |
| `get_doc()` return (`None` \| `list[list[str]]`) | `Option (List (List String))` | `None ↔ none`, `list ↔ some` (`[] ↔ some []`) |
| `restify(self.object)` | `aliasText : String` | identity |
| `more_content` (`None` \| `StringList`/`list[str]`) | `incoming : Option (List String)` | `None ↔ none`, list ↔ `some` |
| forwarded `more_content` | `result : Option (List String)` | as above; alias line ↔ `some ["alias of " ++ aliasText]` |

## Flag dependencies
None. The two branches are governed only by `doc_as_attr` and the truthiness of
the looked-up comment; no configuration flag changes which per-element map runs.

## G-CONF fuzz seed
`SEED = 9229` (pinned in conformance_check.py).
