# refinement.md — sphinx-doc__sphinx-8595

The operation-by-operation correspondence between `model.py`'s implementation
(`select_module_members`, with the deep models `contains` / `exclusion_flags`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed**, the proof uses the axiom's Ensures,
vs **A-reference**, a deep model validated == the real operation by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The single changed site — `ModuleDocumenter.get_object_members`

Gold hunk (`sphinx/ext/autodoc/__init__.py:1077`):
```
     def get_object_members(self, want_all: bool) -> Tuple[bool, ObjectMembers]:
         members = self.get_module_members()
         if want_all:
-            if not self.__all__:
+            if self.__all__ is None:
                 # for implicit module members, check __module__ to avoid
                 # documenting imported objects
                 return True, list(members.values())
             else:
                 for member in members.values():
                     if member.__name__ not in self.__all__:
                         member.skipped = True
                 return False, list(members.values())
```

The model spec/impl covers the `want_all=True` path — the only path the patch
touches (the `want_all=False` else, lines 1087–1098, is unchanged and is not in
the modelled behaviour; mapping.md §1).

| # | model.py impl op (`select_module_members`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `member_names: List[int]`, `excluded: List[bool]` | `members = self.get_module_members()` (a `Dict[str, ObjectMember]`), iterated as `members.values()` | R | dict→two index-aligned lists; `ObjectMember.__name__` ↦ `member_names[k]`, `.skipped` ↦ `excluded[k]` (mapping.md §2). `get_module_members` is unchanged and upstream — its result is the modelled input, not a consumed callee. |
| A2 | params `all_present: bool`, `all_names: List[int]` | `self.__all__` (`Optional[Sequence[str]]`, set line 1020) | R | `self.__all__ is None` ⟺ `not all_present`; declared list/tuple ⟺ `all_present=True` + `all_names`=name ids; empty declared ⟺ `all_present=True, all_names=[]` (mapping.md §2). |
| A3 | `if not all_present:` … `return True` | `if self.__all__ is None:` … `return True, list(members.values())` | R + I | **the fix.** `self.__all__ is None` ⟺ `not all_present` exactly (A2); the implicit-membership branch returns `Result()==True` (the first tuple element) and leaves every flag clear (members returned in full). The post-patch condition tests presence by identity, NOT truthiness, so an empty present list does NOT enter here. |
| A4 | `else:` loop `i = len; while i>0: if not contains(seq, member_names[i-1]): excluded[i-1]=True else: excluded[i-1]=False` | `else: for member in members.values(): if member.__name__ not in self.__all__: member.skipped = True` then `return False, …` | A-reference + I | the membership test `not contains(seq, name)` ⟺ `member.__name__ not in self.__all__` (deep model `contains`, §3.1); the loop assigns each member's final exclusion flag `= (name not in __all__)` and returns `Result()==False`. The model writes the flag at every index (`if/else`); the repo sets `True` only for excluded members and relies on the `ObjectMember.skipped` default `False` (constructor line 282). Under the precondition that the flags enter clear, the two produce the **identical** final exclusion vector — `exclusion_flags(member_names, all_names)` (deep model, §3.2). G-AX validates `exclusion_flags` == a faithful transcription of this loop. |
| A5 | iteration `i = len … i-1` (backward) | `for member in members.values()` (forward) | I | iteration order is irrelevant to the result: each member's final flag depends only on its own name and the export set, never on other members or order. Backward iteration is the front-recursion-friendly transcription (mapping.md §2); the produced `excluded` vector is identical. |

## B. The discriminating behaviour (G-DIFF)

The bug is the branch CONDITION. The discriminating input is a **present-but-
empty** export list: `all_present=True, all_names=[]` (repo: `self.__all__ == []`).

- Post-patch / model: `not all_present` is `False` ⇒ the `else` branch runs;
  `contains([], name)` is uniformly `False` so every `excluded[k]` becomes `True`
  and `Result()==False`. No member is documented — the F2P `test_empty_all`
  expectation (only the module docstring, no `foo`/`bar`/`baz`).
- Pre-patch (`model_prepatch.py`, buggy condition `(not all_present) or
  len(all_names)==0`): the empty list takes the implicit branch ⇒ `Result()==True`
  and all flags stay `False` ⇒ every member documented (the bug).

`model_prepatch.py` keeps the spec byte-identical and **fails** the postcondition
`Implies(all_present, Result() == False)` (verified: the failing clause is
exactly this) — the spec sensing the change (G-DIFF). It is the sole
independently-fixed behaviour, so one prepatch variant suffices.

## B2. Total correctness (termination)

The real `get_object_members` always answers: both branches are bounded scans
over the finite `members.values()` and the finite `self.__all__`. The spec
carries this as `Requires(MustTerminate(2))`; the impl loop consumes the
obligation with `Invariant(MustTerminate(i))` (`i` strictly decreasing,
bounded below by the guard `i > 0`). Nagini is a partial-correctness verifier
by default, so without this obligation a same-spec implementation that never
advances its loop index (diverging instead of answering) satisfies every
`Ensures` vacuously while resolving nothing — the spec-too-weak attack class
G-PANEL-1 exercised. With `MustTerminate` such an implementation is rejected
(a leaked/undischarged termination obligation), so only genuinely answering
implementations verify.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operations that "changed" — the
branch condition (A3) and the membership-driven skipping it enables (A4) — are
modelled **deeply** (`not all_present` for the `is None` test; `contains` /
`exclusion_flags` spelled out over `PSeq`), never hidden behind an axiom about
the function under change. There are **no consumed `@ContractOnly` axioms**: the
membership test and the absent-vs-empty distinction are pure structural logic.
The two deep models (`contains`, `exclusion_flags`) are **A-reference**: G-AX
(axiom_check.py) validates each equal to the real Python operation
(`in`, the repo `else` loop) and confirms the `is None`-vs-truthiness
distinction on `None` and `[]`.

## D. verify(model) ⇒ resolved

`select_module_members` verifies only if (i) the absent export list yields
`Result()==True` with nothing excluded (A3), and (ii) a present export list
(incl. empty) yields `Result()==False` with `excluded == exclusion_flags(...)`
(A4) — in particular every member excluded when the list is empty. By R
(`is None` ⟺ `not all_present`; dict ⟺ parallel lists; names ⟺ ids) the verified
function equals the gold `get_object_members`'s `want_all=True` path on the
tested inputs; by G-AX the deep models equal the real membership test and
skipping loop (A-reference). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and audited references —
and the gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: reference-model soundness (G-AX) and refinement fidelity (this
document, G-EQ).
