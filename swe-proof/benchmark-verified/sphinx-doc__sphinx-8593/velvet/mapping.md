# mapping.md — sphinx-doc__sphinx-8593

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 07983a5a8704ad91ae855218ecbda1c8598200ca`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo files under change: `sphinx/ext/autodoc/__init__.py`,
`sphinx/ext/autodoc/importer.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `collectMemberDocs (attrDocs, names)` | the newly-introduced `ModuleDocumenter.get_module_members(self)` (`sphinx/ext/autodoc/__init__.py`, added by the patch right after `add_directive_header`, ~line 1046) | the modeled changed function: the member collector that now attaches documentation text |
| `names : List Int` | `dir(self.object)` — the candidate member names, in iteration order (`__init__.py`, the `for name in dir(self.object)` loop of the new method) | the candidate roster of member names |
| `attrDocs : List (Int × List (List Int))` | `attr_docs = self.analyzer.attr_docs` (or `{}` when there is no analyzer) restricted to the module-level keys `('', name)` (`__init__.py`, `attr_docs.get(('', name), [])`) | the per-name documentation lines: a `Dict[Tuple[str,str], List[str]]` whose value for `('', name)` is the list of doc-comment lines recorded for `name` |
| `MemberDoc { name, doc }` | an `ObjectMember(name, value, docstring=...)` (`__init__.py:260`) as observed by the downstream metadata extractor: its `__name__` and its `docstring` | one collected member |
| `out : List MemberDoc` | `members` / `list(members.values())` returned by the new method, consumed by `get_object_members` and ultimately by `filter_members` | the collected members in name order |

Discriminating content of the change: each collected member now carries
`docstring = "\n".join(attr_docs.get(('', name), []))` instead of no docstring.
That documentation text is what the downstream `filter_members` →
`extract_metadata` pipeline reads to honour `:meta public:` / `:meta private:`
on module data members; with no docstring it could not, falling back to the
leading-underscore heuristic. The pre-patch path — the importer-level
`get_module_members(module)` returning bare `(name, value)` pairs — is reproduced
by `Solution_prepatch.lean` (every `doc := []`), which **fails**
`out = buildMembers attrDocs names` (G-DIFF).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a member name (`str`, a `dir()` entry / `member.__name__`) | `Int` | each distinct name ↔ a distinct `Int` identifier (names are observed by equality and as association-table keys only). G-CONF instantiates the `Int`s as distinct strings. |
| `attr_docs : Dict[Tuple[str,str], List[str]]` restricted to `('', name)` keys | `List (Int × List (List Int))` | the table `name ↦ [line₀, line₁, …]`. A key absent from the table ↔ a name absent from the association list; `attr_docs.get(('', name), [])` ↔ `lookupDocs n attrDocs`. Each line `str` ↔ `List Int` of its character codes. |
| `"\n".join(lines)` | `joinNL lines` | the standard "join with a single `'\n'` between consecutive elements" fold: `[]↦[]`, `[x]↦x`, `x::xs ↦ x ++ ['\n'] ++ join xs`. `'\n'` is character code `10`. |
| an `ObjectMember(name, value, docstring=d)` | `MemberDoc { name, doc }` | only the two observed fields are modeled; `value`/`object`, `class_`, `skipped` are unmodeled R-identities (the F2P metadata decision reads `__name__` and `docstring` only). `member.__name__ ↔ name`; `member.docstring ↔ doc` (decoded back to a `str`). |
| `list(members.values())` (insertion-ordered) | `out : List MemberDoc` | dict-insertion order ↔ list order; the new method inserts in `dir(self.object)` order, then appends annotation-only names not already present. |

Lean indexing/membership over `List Int` is total and sound; the carriers are
`List Int` / `List (List Int)` because the operation observes names only by
equality / table lookup and documentation only as character sequences.

### 2.1 Scope of the model vs. the full patch

The gold patch spans two files. The behaviour that **resolves the F2P tests** is
the documentation-attachment done by the new `ModuleDocumenter.get_module_members`
(modeled here as `collectMemberDocs`). The other edits are behaviour-preserving
plumbing that the model treats as R-identities (see refinement.md §B):

- the annotation-only second loop (`inspect.getannotations`) appends names not
  already collected, carrying their own `attr_docs` lines — the SAME
  per-name doc-attachment, just over a second name source; modeled by the same
  `buildMembers` fold (G-CONF feeds annotation-only names through the roster).
- `get_object_members` is rewired to call the new method and to use
  `list(members.values())` / `member.__name__ not in self.__all__`; in the F2P
  scenario (no `__all__`) it returns the collected members unchanged, so it is an
  order-preserving R-identity over the collected list.
- the importer-level `get_module_members(module)` only gains a deprecation
  `warnings.warn(...)`; it is no longer on the resolving path and emits no
  observable difference for the tests. R-identity (refinement.md §B3).

## 3. Callee provenance

There are **no axiomatized callees** (no `axiom`, no `:|` stub). The two inputs
the new method reads from elsewhere are modeled as **input carriers**, per the §2
cheatsheet for an unchanged callee whose OUTPUT is consumed as data:

- `dir(self.object)` (the unchanged name enumerator) → the input `names`;
- `self.analyzer.attr_docs` (the unchanged doc-comment table, produced by
  `ModuleAnalyzer`) → the input `attrDocs`.

The conformance check feeds the SAME `names` and `attrDocs` to the real
gold-patched method, so both unchanged callees are bridged as inputs — exactly
the sibling-bundle pattern (e.g. sphinx-8595). The collection logic itself
(per-name doc lookup + `"\n".join` + ordered assembly) is modeled **deeply** and
is therefore an **I/R leg**, refuted by G-CONF.

No flag-dependent callees: the only conditional in the modeled behaviour is the
per-name presence of recorded documentation lines, which the model handles
explicitly via `lookupDocs`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`8593`** so the
consumer-side verdict is reproducible. Its SHADOW transliterates `lookupDocs` /
`joinNL` / `buildMembers` (all R/I-tagged ops) to Python; the ORACLE is the real,
gold-patched `ModuleDocumenter.get_module_members` driven on a duck-typed
documenter whose `self.object` (a synthetic module exposing the case's names),
`self.analyzer.attr_docs`, and analyzer presence are configured per case.

## 5. G-AX

Skipped: the bundle has no axioms (no `axiom_check.py`). `meta.json
gates.G-AX.status = "skip"`.
