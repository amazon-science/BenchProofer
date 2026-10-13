# refinement.md — sphinx-doc__sphinx-8595

Operation-by-operation correspondence between `implementation_selectMembers`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH
`ModuleDocumenter.get_object_members`). Tags: **R** type refinement,
**A-consumed** proof uses an axiom, **A-reference** deep model validated == real
callee, **I** identical concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if wantAll then …` | `if want_all:` | I |
| 2 | `match allAttr with \| none => …` (the implicit-members path) | `if self.__all__ is None: return True, list(members.values())` | R |
| 3 | `return (true, members.map (fun n => (n, false)))` | `return True, list(members.values())` (no member skipped; caller still origin-checks) | R |
| 4 | `\| some allNames => return (false, members.map (fun n => (n, !allNames.contains n)))` | `else: for member in members.values(): if member.__name__ not in self.__all__: member.skipped = True ; return False, list(members.values())` | R |
| 5 | `else (wantAll false): ret := requested.filterMap (fun name => if members.contains name then some (name,false) else none); return (false, ret)` | `memberlist = self.options.members or []; ret = []; for name in memberlist: if name in members: ret.append(members[name]) ; return False, ret` | R |

Notes:

- **Every step is R or I — no A.** The op the patch changes is step 2: the guard
  `if not self.__all__:` (which an empty list satisfies) becomes
  `if self.__all__ is None:` (which only the absent list satisfies). This is
  modeled DEEPLY by routing on the `Option` constructor (`none` vs `some _`)
  rather than on truthiness, so the empty export list (`some []`) flows to step 4
  and every member is tagged skipped. SPEC_GUIDE §3 forbids axiomatizing a
  deeply-modeled changed op; the `axioms` region is empty and **G-AX skips**.
- **R vs I.** Step 1 is **I** (literal control-flow transliteration). Steps 2–5
  are **R**: the Python objects (`self`, the `Dict[str, ObjectMember]`, the
  `ObjectMember.skipped` mutation, the returned `list(...)`) are refined to the
  `Bool × List (String × Bool)` carrier and `List String` / `Option (List
  String)` inputs per the mapping.md bijection. `x in self.__all__` ↔
  `allNames.contains x` and the dict-key test `name in members` ↔
  `members.contains name` hold because the modeled inputs are the name lists.
- **The fix itself** is step 2's constructor split. The pre-patch impl
  (`Solution_prepatch.lean`) keeps the truthiness guard: a present-but-empty
  export list (`some []`) is treated like `none`, taking the implicit-members
  path and returning `(true, every member unskipped)` — the actual bug, where an
  empty `__all__` documents everything instead of nothing. That impl's carried
  proof fails to typecheck against the spec (G-DIFF), since the spec demands
  `(false, every member skipped)` for `some []`.
- **The `logger.warning` for a missing requested attribute** (the `else` arm of
  the by-name loop, `__init__.py:1095-1098`) is an observational side effect, not
  part of the returned value; step 5 models only the returned `ret`, which simply
  drops absent requested names (`filterMap` → `none`). This branch is unchanged
  by the patch.
- **G-CONF** mechanically refutes the R/I legs: a faithful in-process replica of
  the post-patch `get_object_members` selection is diffed against the impl shadow
  over ≥1e5 fuzzed inputs, with the empty-`__all__` discriminator pinned as an
  edge case. No A legs.
