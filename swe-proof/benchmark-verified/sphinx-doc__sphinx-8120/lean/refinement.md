# refinement.md — sphinx-doc__sphinx-8120

Maps every operation in `implementation_searchDirs` to its `patch.diff`
counterpart in `Sphinx._init_i18n` (sphinx/application.py — the modeled site, see
mapping.md). Tags: **R** type-refinement, **A-consumed** proof uses a callee
axiom, **A-reference** deep-modeled changed op validated == real callee, **I**
identical concrete op.

## Patch (post-patch assembly inside `_init_i18n`)
```python
locale_dirs = [None]  # type: List[Optional[str]]
locale_dirs += list(repo.locale_dirs)
locale_dirs += [path.join(package_dir, 'locale')]
```
(The buggy pre-patch line was
`locale_dirs = [None, path.join(package_dir, 'locale')] + list(repo.locale_dirs)`.)

## Operation correspondence
| # | Lean op (`implementation_searchDirs`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut searchDirs : List (Option String) := [none]` | `locale_dirs = [None]` | R | `None : Optional[str] ↔ none : Option String` (the system-default sentinel). List literal ↔ list literal; entry type `str|None ↔ Option String`. |
| 2 | `searchDirs := searchDirs ++ userDirs.map some` | `locale_dirs += list(repo.locale_dirs)` | R | `list(repo.locale_dirs) : list[str] ↔ userDirs : List String`; each `str` element is a present value ⇒ `.map some`. Python `+=` (list extend) ↔ Lean `++`. Order preserved positionally. |
| 3 | `searchDirs := searchDirs ++ [some bundledDir]` | `locale_dirs += [path.join(package_dir, 'locale')]` | R | `path.join(package_dir, 'locale') : str ↔ bundledDir : String`; wrapped as a singleton present-value list `[some bundledDir]`. `+=` ↔ `++`. |
| 4 | `return searchDirs` | (value of `locale_dirs`, passed onward) | I | return the assembled search list. |

Every op is R or I; **no A row** (no axiom consumed, no deep-model reference).
Therefore `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## R/I legs ⇒ G-CONF
The whole impl is R/I, so `conformance_check.py` mechanically differential-tests
the impl shadow against the post-patch `locale_dirs` assembly (transcribed
verbatim) over ≥10^5 fuzzed inputs. `conf_skip = false`.

## Second patched file — NOT separately modeled
`patch.diff` also edits `sphinx/locale/__init__.py`: the `init` signature's
parameter annotation changes from `List[str]` to `List[Optional[str]]`. This is
a **type-annotation-only** change with no runtime effect — at base_commit the
caller already passed a list containing `None` (the system-default sentinel), and
`init` already iterated it unchanged; the annotation merely documents the entry
type so the now-explicitly-typed `locale_dirs` variable type-checks. No
observable behavior changes, so there is no triple for it and no prepatch
variant. The single behavioral fix (and the only thing the F2P test
`test_customize_system_message` exercises) is the search-list reordering modeled
above: a caller-supplied `sphinx.po`/`.mo` override now precedes the bundled
catalog and therefore wins precedence in the unchanged downstream loader.

## Why the prepatch is the real bug
`Solution_prepatch.lean` assembles `[none, some bundledDir] ++ userDirs.map some`
— the bundled directory placed *before* the caller's directories, exactly the
pre-patch `[None, path.join(package_dir,'locale')] + list(repo.locale_dirs)`.
Its `correct_searchDirs` cannot close: the spec demands each caller directory
precede the bundled directory, and the discriminating goal
`none :: some bundledDir :: map some userDirs = none :: (map some userDirs ++ [some bundledDir])`
is false whenever `userDirs` is non-empty. That is precisely the user-override-
ignored bug from the issue.
