# refinement.md — operation correspondence (sympy__sympy-19637)

Maps every op in `implementation_kernSHit` to its `patch.diff` counterpart.
Tags: **R** type refinement · **A-consumed** proof uses axiom property ·
**A-reference** deep model validated == real callee (G-AX) · **I** identical op.

The post-patch Python slice is:
```python
hit = False                       # init, line 471
...
if '(' in s and not quoted:       # branch gate -> parenBranch
    ...
    if ' ' in s:                  # space present?
        kern = '_'; while kern in s: kern += choice(...)
        s = s.replace(' ', kern)
        hit = kern in s           # marker now present -> True   (gold: moved in)
    else:
        hit = False               # gold: new else branch
```

| # | Lean impl op | patch.diff counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut hit := false` | `hit = False` (line 471) | I | identical boolean init |
| 2 | `if parenBranch then` | `if '(' in s and not quoted:` (line 473) | R | unchanged upstream bool predicate ↔ `parenBranch : Bool` (mapping.md) |
| 3 | `if s.contains ' ' then` | `if ' ' in s:` (line 510) | R | Python `' ' in s` (str) ↔ `List.contains ' '` |
| 4 | `hit := true` (space-present subcase) | `hit = kern in s` MOVED inside `if ' ' in s:` (gold line 9) | A-reference | the changed op; post-patch `kern in s` is necessarily `True` once a fresh marker is substituted for the present spaces. Modeled deeply; validated == real `kernS` flag by G-AX. NOT axiomatized. |
| 5 | `else hit := false` | `else: hit = False` (gold lines 10-11, NEW) | I | the new else branch — flag unset when no space |
| 6 | `return Except.ok hit` | the routine continues with a well-defined `hit` (never raises) | I | well-defined flag return; `Except.ok` frames the no-crash guarantee |

The prepatch impl (`Solution_prepatch.lean`) models the actual bug: the
membership read runs unconditionally and, when `parenBranch = true` with no
space, the marker is unbound, so it `return Except.error ()` — the
`UnboundLocalError`. This op corresponds to the pre-patch `hit = kern in s` at
the OUTER indentation (gold-removed line 8). It has no faithful R/A/I row in the
POST-patch impl (it is the removed-and-relocated op), which is exactly the
G-DIFF signal.

No A-consumed rows: the proof discharges the flag value directly from the
inputs; no UNCHANGED callee property is assumed. No changed-inexpressible op.

The discriminating clause is rows 4-6 together: for `parenBranch = true` and a
space-free `s`, the post-patch spec demands `Except.ok false` (no crash, flag
unset), while the prepatch impl yields `Except.error ()` (the crash). The frozen
`problem_spec_kernSHit` pins `Except.ok (parenBranch && s.contains ' ')`, so the
prepatch `correct_kernSHit` cannot close.
