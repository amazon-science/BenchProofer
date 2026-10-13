# refinement.md — django__django-15554

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`computeEligible` `do` block and its deep model `eligibleEntries`/`entryEligible`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model
validated == a real callee by G-AX), or **I** (identical concrete op). EVERY step
is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`, §4.1);
the A legs and this narrative are audited by **G-EQ**. Claim: any impl verifying
against this frozen spec, refined per the map below, is behaviourally equal to the
gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The behavioural site — `reuse_aliases` in `Query.join` (`query.py:1014`)

The single behaviour the issue and the F2P `test_multiple` observe is **which
existing entries (`alias_map` entries) the requested join may share**. The gold
hunk rewrites that candidate list (`reuse_aliases`):

```
- reuse_aliases = [
-     a for a, j in self.alias_map.items()
-     if (reuse is None or a in reuse) and j.equals(join)
- ]
+ if reuse_with_filtered_relation and reuse:
+     reuse_aliases = [
+         a for a, j in self.alias_map.items() if a in reuse and j.equals(join)
+     ]
+ else:
+     reuse_aliases = [
+         a for a, j in self.alias_map.items()
+         if (reuse is None or a in reuse) and j == join
+     ]
```

Two coordinated changes: (1) the **default** branch's match strengthens from
`j.equals(join)` (structural — ignores `filtered_relation`) to `j == join`
(exact — includes it); (2) a new **restricted** branch (`reuse_with_filtered_relation
and reuse`) restricts reuse to the explicit `reuse` set while matching structurally.

| # | Solution.lean impl op (`computeEligible`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `registry : List (Nat × EntryId)` | `self.alias_map.items()` (ordered `{alias: Join}`) | R | dict→ordered-list, alias→`Nat`, `Join`→`EntryId` (mapping.md §2). G-CONF bridges via real `Join` objects. |
| A2 | `req : EntryId` | the requested `join` argument | R | `Join`→`(structKey, refineTag)` (mapping.md §2). |
| A3 | `allowed : Option (List Nat)` | the `reuse` parameter (`None` \| set) | R | `None`↔`none`; set↔`some l`; `a in reuse`↔`allowedMember`; empty-set falsiness↔`restrictedMode`'s non-empty requirement (mapping.md §2). |
| A4 | `restricted : Bool` | `reuse_with_filtered_relation` | R | identity. |
| A5 | `restrictedMode allowed restricted` | `reuse_with_filtered_relation and reuse` (Python truthiness: empty set false) | I | `restricted && allowance-non-empty` is the verbatim guard. |
| A6 | restricted branch: `allowedMember allowed e.1 && matchesStructural e.2 req` | `a in reuse and j.equals(join)` | I + A-reference | concrete transliteration; `matchesStructural` == real `Join.equals` is the **A-reference** G-AX validates (mapping.md §3). |
| A7 | default branch: `(allowed.isNone || allowedMember allowed e.1) && matchesExact e.2 req` | `(reuse is None or a in reuse) and j == join` | I + A-reference | concrete transliteration; `matchesExact` == real `Join.__eq__` is the **A-reference** G-AX validates (mapping.md §3). |
| A8 | the backward `while` fold building `eligibleEntries` in registry order | the list comprehension over `alias_map.items()` | I | both emit the eligible ids in registry/insertion order; the fold is the transliteration of the comprehension. |

`matchesStructural`/`matchesExact` are not consumed axioms — they are the direct
Lean models of the two comparison METHODS, validated executably against the real
`Join.equals`/`Join.__eq__` by G-AX (A-reference). There is no consumed axiom and
no axiomatized callee.

## B. Unmodeled-but-identical surroundings (tagged I)

* **Downstream selection** — `reuse_aliases[-1]` / `join.table_alias` /
  `ref_alias`, and new-alias creation via `table_alias(create=True)`
  (`query.py:1032-1054`) — is **byte-identical** pre/post-patch and consumes the
  candidate list `computeEligible` produces. The F2P observable (one JOIN vs two)
  is determined by whether the candidate list is empty (→ fresh alias) or not, so
  pinning the candidate list pins the observable. **I.**
* **Flag plumbing** — the new `reuse_with_filtered_relation` parameter threaded
  through `build_filter` (`query.py:1331,1416`), `setup_joins`
  (`query.py:1730,1843`: `reuse = can_reuse if join.m2m or
  reuse_with_filtered_relation else None`), and `build_filtered_relation_q`
  (`query.py:1578`, which passes `reuse_with_filtered_relation=True`) — only
  selects WHICH `(reuse, restricted)` pair reaches `join()`. Those pairs are the
  free inputs `allowed`/`restricted` of `computeEligible`, which is specified for
  EVERY pair, so the plumbing introduces no behaviour the spec misses. The
  docstring additions are comments. **R/I.**

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely changed — the
`reuse_aliases` selection rule — is modeled **deeply** (`eligibleEntries` /
`entryEligible`, steps A5-A8), not hidden behind an axiom about the function under
change. The only repository semantics relied on are the two comparison methods,
modeled directly and G-AX-validated (A-reference). No consumed axiom.

## D. The discriminating clause / prepatch

The change is observable exactly when two existing entries are **structurally
identical but carry different refinement tags** (two `FilteredRelation`s for the
same relation — the issue's scenario; F2P `test_multiple`). Default mode
pre-patch used `j.equals` and shared BOTH (the bug: the second filter's join is
ignored); the fix uses `j == join`, keeping only the exactly-matching entry.
`Solution_prepatch.lean` reproduces the pre-patch single-rule
`(reuse is None or a in reuse) and j.equals(join)` skeleton and **fails**
`out = eligibleEntries …` (G-DIFF) precisely at the `matchesStructural` vs
`matchesExact` divergence (the unsolved goal at the loop body).

## E. verify(Solution) ⇒ resolved

`computeEligible` verifies only if its output equals `eligibleEntries` — the exact
restricted/default selection rule (A5-A8). By R (mapping.md §2) that equals the
post-patch `reuse_aliases` comprehension over real `Join`s; by G-AX the comparison
models `matchesStructural`/`matchesExact` equal the real `Join.equals`/`__eq__`
(A-reference); by G-CONF the R/I transliteration agrees with `patch.diff`'s
behaviour (post-patch `reuse_aliases` over real `Join` objects) on ≥10⁵ inputs;
the unchanged downstream (§B) maps the agreed candidate list to the same JOIN.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and validated comparison semantics — and the gold
patch resolves (G-RESOLVE). Trust points are exactly the two of plan §1.1:
comparison-semantics fidelity (G-AX) and refinement fidelity (this doc, G-EQ +
G-CONF).
