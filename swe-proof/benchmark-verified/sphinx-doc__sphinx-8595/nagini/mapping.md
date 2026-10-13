# mapping.md — sphinx-doc__sphinx-8595

Binds every `model.py` symbol to its repository counterpart at
`base_commit = b19bce971e82f2497d67fdacdeca8db08ae0ba56`, states the type
abstraction, and gives the provenance of the deep-model reference.

Repo file under change: `sphinx/ext/autodoc/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_module_members(member_names, excluded, all_present, all_names)` | `ModuleDocumenter.get_object_members(self, want_all)` — `sphinx/ext/autodoc/__init__.py:1074` (changed line 1077) | the modelled changed function, restricted to its `want_all=True` path (the only path the patch touches) |
| `all_present` / `all_names` | `self.__all__` — set at `import_object` line 1020 via `inspect.getall(self.object)` (`sphinx/util/inspect.py:144`) | the module's optional export list: `None` (undeclared) ↦ `all_present=False`; a `list`/`tuple` of names (possibly empty) ↦ `all_present=True`, `all_names`=its name ids |
| `member_names` / `excluded` | `members = self.get_module_members()` (line 1075), each value an `ObjectMember` with `.__name__` (the member name) and `.skipped` (the exclusion flag, default `False`) — `ObjectMember` at `sphinx/ext/autodoc/__init__.py:260` | the discovered module members: their names (read-only) and their per-member exclusion flags (mutated; model carrier `excluded` ↦ repo `ObjectMember.skipped`) |
| `Result()` (bool) | the first element of the returned `Tuple[bool, ObjectMembers]` (the "check `__module__` for implicit members" / `want_all`-implicit flag) — `return True, …` / `return False, …` (lines 1080, 1086) | whether membership is implicit (`True`) or governed by an explicit export list (`False`) |
| `contains(names, v)` *(deep model — A-reference)* | the Python membership test `member.__name__ not in self.__all__` (line 1083) | pure spec: is a member name one of the export names |
| `exclusion_flags(member_names, all_names)` *(deep model — A-reference)* | the whole `else:` loop over `members.values()` (lines 1081–1086) that sets `member.skipped = True` for each member whose name is not in `self.__all__` | pure spec: the per-member exclusion vector against a present export list |

The full returned member list (`list(members.values())`, lines 1080/1086) is the
member set in both branches; the model carries it as the preserved `member_names`
/ `skipped` carriers (length unchanged, `Ensures len == len`).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.__all__ : Optional[Sequence[str]]` | `(all_present: bool, all_names: List[int])` | `self.__all__ is None` ⟺ `not all_present`; a declared list/tuple ⟺ `all_present=True` with `all_names = [id(s) for s in self.__all__]`; empty declared list ⟺ `all_present=True, all_names=[]`. This split removes `Optional` narrowing from the spec while preserving the absent-vs-empty distinction the fix turns on. |
| a member name `str` | an `int` name identifier | equal ids ⟺ equal strings (`a == b` ⟺ `id(a)==id(b)`); membership `s in __all__` ⟺ `contains(all_names, id(s))`. Only equality of names is observed, so the identifier abstraction is exact for the tested behaviour. |
| `members : Dict[str, ObjectMember]` | two index-aligned `List[int]` (`member_names`) + `List[bool]` (`excluded`) | iteration order over `members.values()` ↦ index order; `ObjectMember.__name__` ↦ `member_names[k]`; `ObjectMember.skipped` ↦ `excluded[k]`. The dict→parallel-list refinement keeps only the two touched fields. |
| `ObjectMember.skipped` default `False` (constructor, line 282) | precondition `Forall k: excluded[k] == False` | freshly discovered members enter with the exclusion flag clear; the loop only ever sets it. |
| return `Tuple[bool, ObjectMembers]` | `bool` Result + the mutated `excluded` carrier | the second tuple element (the member list) is returned in full unchanged in both branches; modelled by the preserved `member_names`/`excluded` carriers, so only the discriminating `bool` is `Result()`. |

`str` indexing/iteration is banned in Nagini, so names are integer identifiers
and the specification is phrased over `PSeq[int]`/`PSeq[bool]` via `ToSeq`.

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**: the changed decision is pure
structural logic, modelled deeply. The two deep models are validated equal to
the real Python operations out-of-band.

### 3.1 `contains` ↔ Python `in` on the export list (A-reference)
`contains(ToSeq(all_names), v)` is the membership test `name in self.__all__`.
`exclusion_flags`'s entry `not contains(...)` is exactly the repo's
`member.__name__ not in self.__all__` (line 1083). The real operation is the
built-in `in` over a `list`/`tuple` of strings; `axiom_check.py` asserts the
deep model `contains` equals Python's `in` on boundary + fuzz name sets.

### 3.2 `exclusion_flags` ↔ the `else`-branch skipping loop (A-reference)
`exclusion_flags(member_names, all_names)[k]` is the final `skipped` flag the
repo loop assigns to member `k`: the loop sets `member.skipped = True` iff
`member.__name__ not in self.__all__`, leaving the constructor default `False`
otherwise — i.e. the per-member flag is `(name not in __all__)`. The model
writes that value at every index (the `if/else` form), which is observationally
the composition of (default `False`) ∘ (conditional set-`True`) — identical
final state under the precondition that the flags enter clear. `axiom_check.py`
runs a faithful Python transcription of the repo loop and asserts the resulting
`skipped` vector equals `exclusion_flags` on boundary + fuzz.

### 3.3 The branch distinction `self.__all__ is None` ↔ `not all_present` (the fix)
The single changed line is the branch condition. Post-patch
`if self.__all__ is None:` ⟺ model `if not all_present:` (absent only); the
pre-patch `if not self.__all__:` ⟺ `if (not all_present) or len(all_names)==0:`
(absent OR empty). `axiom_check.py` confirms, against real Python truthiness,
that `not self.__all__` is True for both `None` and `[]` while
`self.__all__ is None` is True only for `None` — the exact source of the bug:
an empty `__all__` must be treated as PRESENT (excludes everything), not absent.

**Soundness check (G-AX):** `axiom_check.py` imports only the standard library.
It (a) asserts `contains` == Python `in`, (b) asserts `exclusion_flags` == a
faithful transcription of the repo `else` loop, and (c) asserts the
`is None` vs truthiness distinction for `None` and `[]`, over boundary cases
(undeclared / empty / disjoint / overlapping / all-listed export sets, duplicate
and shared names) plus randomized fuzz. Exit 0 iff every observation holds.
