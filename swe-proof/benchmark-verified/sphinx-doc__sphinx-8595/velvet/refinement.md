# refinement.md — sphinx-doc__sphinx-8595

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`selectDocumentedMembers` `do` block plus the deep `decideMembers` /
`markAllExposed` / `markByPublished` / `selectRequested` models) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); this narrative is audited by **G-EQ**. There are **no axioms**, so there
is no A leg and `axiom_check.py` is absent (G-AX skipped). Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the observed return, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `ModuleDocumenter.get_object_members` (`sphinx/ext/autodoc/__init__.py:1077`)

Gold hunk:
```
  if want_all:
-     if not self.__all__:
+     if self.__all__ is None:
          # for implicit module members, check __module__ to avoid
          # documenting imported objects
          return True, list(members.values())
      else:
          for member in members.values():
              if member.__name__ not in self.__all__:
                  member.skipped = True
          return False, list(members.values())
```

| # | Solution.lean impl op (`selectDocumentedMembers`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `exposeAll : Bool`, `published : Option (List Int)`, `roster : List Int`, `requested : List Int` | `want_all` arg; `self.__all__`; `members = self.get_module_members()`; `self.options.members or []` | R | `want_all ↔ Bool`; `self.__all__ : Optional[Sequence[str]] ↔ Option (List Int)` (`None ↔ none`, list ↔ `some`); names ↔ distinct `Int`; the `members` dict values + the explicit subset ↔ `List Int` (mapping.md §2). G-CONF bridges names by instantiating `Int`s as distinct strings. |
| A2 | `if exposeAll then …` | `if want_all:` | I | identical branch on the mode flag. |
| A3 | `match published with \| none => { checkOrigin := true, entries := markAllExposed roster }` | the fixed `if self.__all__ is None: return True, list(members.values())` | I + R | the presence test `published = none` ↔ `self.__all__ is None` (**the fix**); `checkOrigin = true ↔` returning `True` (caller filters implicit members by origin); `markAllExposed roster` ↔ `list(members.values())` with no member pre-marked (R: each value ↔ `{name, skipped:=false}`). |
| A4 | `\| some pub => { checkOrigin := false, entries := markByPublished pub roster }` | the `else:` arm: `for member in members.values(): if member.__name__ not in self.__all__: member.skipped = True; return False, list(members.values())` | I + R | `checkOrigin = false ↔ False`; `markByPublished pub roster` (mark skipped iff `n ∉ pub`) ↔ the `for`-loop that sets `member.skipped = True` for `member.__name__ not in self.__all__` (R: `member.skipped ↔ skipped`, `member.__name__ ↔ name`). The loop's set-membership ↔ `decide (n ∉ pub)`. |
| A5 | `else` branch: backward `while` fold building `selectRequested roster requested`, returned as `{ checkOrigin := false, entries := result }` | the `else:` of `if want_all:` (the `memberlist = self.options.members or []` path, `__init__.py:1088-1097`): for each requested name in `members`, append it; warn+drop the missing ones; `return False, ret` | I + R | the not-`want_all` path is UNCHANGED by the gold hunk but is part of the modeled function's contract; it is transliterated identically. `ret.append(members[name])` ↔ keep `{name, skipped:=false}` when `n ∈ roster`; the `else: logger.warning` (drop) ↔ the `[]` branch. The warning is an unmodeled R-identity (not observed by the documented-set assertion). `return False, ret` ↔ `{ checkOrigin := false, entries := result }`. |

## B. The discriminator (the bug)

The pre-patch guard `if not self.__all__:` is FALSY for both `__all__ is None`
**and** `__all__ == []`, so an explicitly empty published list takes the
"document everything, filter by origin" branch — the reported bug (`empty
__all__ is ignored`). The fix `if self.__all__ is None:` distinguishes the two.

In the model this is `published = none` (take the full-roster origin-filter
branch, A3) vs `published = some []` (take the marking branch, A4, where
`markByPublished [] roster` marks EVERY entry skipped → nothing documented). The
post-conditions

```
ensures (exposeAll = true ∧ published = some []) →
          out.checkOrigin = false ∧
          out.entries = roster.map (fun n => { name := n, skipped := true })
ensures (exposeAll = true ∧ published = none) → out.checkOrigin = true
```

pin the two cases apart. `Solution_prepatch.lean` reproduces the truthiness test
(`if pub.isEmpty then <none-branch> else …`) and **fails** the `some []` clause
(G-DIFF): its `loom_solve` is left the unsolvable goal `¬published = some []`.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the guard
distinguishing an absent published list from a present-but-empty one — is modeled
**deeply** (the `match published with | none … | some …` in `decideMembers` and
the impl), not hidden behind an axiom. The roster `members` produced by the
unchanged callee `get_module_members` is consumed as the input carrier `roster`
(mapping.md §3), not axiomatized; G-CONF feeds the SAME roster to the real
patched function, so it is an input, not a trust point.

## D. verify(Solution) ⇒ resolved

`selectDocumentedMembers` verifies only if its output equals `decideMembers`,
which (A3/A4/B) takes the marking branch for ANY present published list including
`some []`, marking every entry skipped — and takes the origin-filter branch only
for `none`. By R (`Optional[Sequence[str]] ↔ Option (List Int)`, names ↔ `Int`,
`member.skipped ↔ skipped`, `list(members.values()) ↔ roster`) the verified
decision equals the gold-patched `get_object_members` on the observed return; by
G-CONF the R/I transliteration agrees with the real patched callee on the boundary
cases + ≥10⁵ fuzzed inputs. The F2P test `test_empty_all` documents a module with
`__all__ = []` and asserts NO member entries are rendered — exactly the
`published = some [] ⇒ all skipped` clause. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement, and the
gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc + G-CONF); there are no axioms (no G-AX trust point).
