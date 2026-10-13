# mapping.md — sphinx-doc__sphinx-8595

## Symbol binding (file:line @ base_commit b19bce971e82f2497d67fdacdeca8db08ae0ba56)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_selectMembers` / `problem_spec_selectMembers` | `ModuleDocumenter.get_object_members(self, want_all)` | `sphinx/ext/autodoc/__init__.py:1073-1098` |
| `selectMembers` (pure helper) | the body of `get_object_members` (the `want_all` branch's export-list selection + the by-name branch) | `__init__.py:1074-1098` |
| input `allAttr : Option (List String)` | `self.__all__` (an `Optional[Sequence[str]]`) | set at `__init__.py:992` (`None`) / `1020` (`inspect.getall(...)`) |
| input `members : List String` | the names of `self.get_module_members()` (a `Dict[str, ObjectMember]`), in iteration order | `__init__.py:1074` |
| input `requested : List String` | `self.options.members or []` | `__init__.py:1093` |
| output flag | the returned `bool` (whether the caller still applies the implicit `__module__` origin check) | the `return True/False, …` |
| output `tagged : List (String × Bool)` | the returned `list(members.values())` / `ret`, each `ObjectMember` reduced to `(__name__, skipped)` | the returns |

## What the function does (base_commit)

```python
def get_object_members(self, want_all):
    members = self.get_module_members()
    if want_all:
        if not self.__all__:                       # <-- base_commit guard
            # for implicit module members, check __module__ to avoid
            # documenting imported objects
            return True, list(members.values())
        else:
            for member in members.values():
                if member.__name__ not in self.__all__:
                    member.skipped = True
            return False, list(members.values())
    else:
        memberlist = self.options.members or []
        ret = []
        for name in memberlist:
            if name in members:
                ret.append(members[name])
            else:
                logger.warning(...)                 # missing attribute
        return False, ret
```

`self.__all__` is `None` when the module declares no export list, and the list
of exported names (possibly the empty list) when it does.

The **discriminating behavior**: with a declared-but-empty export list
(`self.__all__ == []`), the base-commit guard `if not self.__all__:` is truthy
(an empty list is falsy in Python), so the function takes the implicit-members
path and returns `True, list(members.values())` — every member kept, none
skipped. The intended behavior is that a declared (even empty) export list
restricts the selection: every member not named in it is marked skipped, so an
empty export list skips every member. The post-patch guard
`if self.__all__ is None:` distinguishes "no list declared" (`None`) from "empty
list declared" (`[]`), routing the empty list into the else branch where each
member is skipped.

## Lean modeling

- `self.__all__ : Optional[Sequence[str]]` → `allAttr : Option (List String)`
  (`None ↔ none`; a declared list — empty or not — ↔ `some xs`). This Option is
  the soundness-critical carrier: the bug is precisely the conflation of `none`
  with `some []`.
- `self.get_module_members()` is a `Dict[str, ObjectMember]`; only each member's
  `__name__` and resulting `skipped` flag are observable here, so it is modeled
  as `members : List String` (the names, in dict order) and the output tags each
  with a `Bool` skipped flag.
- `member.__name__ not in self.__all__` → `!allNames.contains n`.
- The by-name branch (`want_all` false): `self.options.members or []` →
  `requested : List String`; `for name in memberlist: if name in members:
  ret.append(...)` → `requested.filterMap (membership keep)`, preserving the
  requested order. Each kept member is not skipped (`false`).
- The two returned `bool`s map directly; the returned member objects are reduced
  to `(name, skipped)` pairs — the only observable distinction the F2P test and
  the issue depend on (an all-skipped result documents nothing).

## Lean ↔ Python type bijection (used by G-CONF / G-AX)

| Python | Lean | bijection |
|---|---|---|
| `want_all` | `wantAll : Bool` | identity |
| `self.__all__` | `allAttr : Option (List String)` | `None ↔ none`; declared list (incl. `[]`) ↔ `some xs` |
| names of `self.get_module_members()` | `members : List String` | dict-order names |
| `self.options.members or []` | `requested : List String` | identity (ordered) |
| `x in self.__all__` | `allNames.contains x` | list membership |
| `name in members` (dict key test) | `members.contains name` | list membership |
| `(bool, [ObjectMember…])` | `Bool × List (String × Bool)` | each member → `(__name__, skipped)` |
| `member.skipped` | second component | `True ↔ true` |

## Callee provenance + flag dependencies

- **No consumed callee axiom; no A-reference.** The selection logic that the
  patch changes (the export-list guard and the skipped tagging) is modeled
  DEEPLY over the observable inputs; SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op. The `axioms` region is empty and **G-AX skips**.
- `self.get_module_members()` and `self.options.members` are unchanged by the
  patch; their values are inputs.
- `self.__all__` is governed by the `ignore_module_all` option (set at
  `__init__.py:1019-1020`): when not ignoring, it is `inspect.getall(self.object)`
  (the module's actual `__all__`, possibly `[]`), else stays `None`. Both
  configurations are covered by the `Option` input (G-CONF fuzzes `none`,
  `some []`, and `some nonempty`).

## G-CONF fuzz seed

Pinned LCG seed: **8595** (see `conformance_check.py` `SEED`). Corpus: randomized
inputs crossing every branch — `want_all` true/false; `allAttr` = `none`,
`some []` (the discriminating empty-list case), and `some` non-empty; member
name lists overlapping the export list to varying degrees; and by-name requests
with present/absent names — over ≥1e5 fuzzed inputs. The R/I shadow of
`implementation_selectMembers` is diffed against an in-process replica of the
POST-PATCH `get_object_members` selection. Hand-picked edge cases pin the F2P
scenario: `want_all=True`, `allAttr=some []`, members `["foo","bar","baz"]`
→ `(False, [("foo",True),("bar",True),("baz",True)])` (every member skipped, so
nothing is documented), contrasted with `allAttr=none` over the same members
→ `(True, [("foo",False),…])`.
