# refinement.md — django__django-15128

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `buildRelabeling` `do` block and the deep `relabeling`/`relabelFrom` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, builds the same alias rename map as
the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The modeled site — the rename-map construction in `bump_prefix`

Gold hunk (`django/db/models/sql/query.py`, end of `bump_prefix`):
```
-        outer_query.subq_aliases = outer_query.subq_aliases.union(self.subq_aliases)
+        other_query.subq_aliases = other_query.subq_aliases.union(self.subq_aliases)
+        if exclude is None:
+            exclude = {}
         self.change_aliases({
             alias: '%s%d' % (self.alias_prefix, pos)
             for pos, alias in enumerate(self.alias_map)
+            if alias not in exclude
         })
```
The patch also (i) renames the parameter `outer_query → other_query` and
`bump_prefix`'s signature to accept `exclude=None`, and (ii) adds the call site
in `combine` (`initial_alias = self.get_initial_alias(); rhs.bump_prefix(self,
exclude={initial_alias})`) plus explanatory comments. (i) is pure renaming and
(ii)/comments are unchanged-behaviour scaffolding around the modeled op; only the
comprehension's emission filter changes what is computed — that is what
`buildRelabeling` models.

| # | Solution.lean impl op (`buildRelabeling`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `aliases : List String` | `enumerate(self.alias_map)` source | R | `list(alias_map)` (ordered, unique keys) ↔ `List String` (mapping.md §2). |
| A2 | param `newPrefix : String` | `self.alias_prefix` (the bumped prefix) | R | identity on the prefix `str` (mapping.md §2). |
| A3 | param `preserved : List String` | the `exclude` set | R | `set[str]` ↔ `List String`; only membership observed (mapping.md §2). |
| A4 | the backward `while` fold building `result`, each step prepending `(a, newPrefix ++ toString (i-1))` unless `preserved.contains a` | the dict comprehension `{alias: '%s%d'%(prefix,pos) for pos,alias in enumerate(alias_map) if alias not in exclude}` | I | concrete construction, transliterated by G-CONF. The position counter `i-1` ↔ `enumerate` `pos` advances for EVERY alias; the `if preserved.contains a then []` ↔ `if alias not in exclude` decides emission only. `newPrefix ++ toString (i-1)` ↔ `'%s%d' % (prefix, pos)`. |
| A5 | `out = relabeling newPrefix preserved aliases` (the `ensures`) | the `change_map` handed to `change_aliases(...)` | R + I | the produced map (`List (String × String)` ↔ `dict[str,str]`, mapping.md §2). |

Discriminating content of the change — a `preserved` alias (the base-table alias
the two merge sides share) is **omitted** from the rename map so it keeps its
current name — lives in the `if preserved.contains a then []` branch (model) ⇔
the `if alias not in exclude` clause (real). The pre-patch comprehension had no
such filter and renamed **every** alias including the shared base table; that is
what lets a renamed key equal another alias's renamed value (e.g. T4→T5 while
T5→T6), so `change_aliases`'s `assert set(change_map).isdisjoint(
change_map.values())` can fire — the reported AssertionError.
`Solution_prepatch.lean` reproduces the unfiltered construction and **fails**
`out = relabeling newPrefix preserved aliases` (G-DIFF).

## B. No axiomatized or deep-modeled callees

The modeled operation is a self-contained construction over its three inputs:
a positional scan emitting prefixed names with a membership filter. No unchanged
callee's contract is consumed (`axioms = []`) and no foreign callee is
deep-modeled (`deep_model_references = []`). The downstream `change_aliases`
(which applies the map) and `combine` (which chooses `exclude={initial_alias}`)
are unchanged/surrounding machinery, not part of the modeled op. Hence there is
no `axiom_check.py` and G-AX is `skip` (precedent: django__django-12193).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — the rename
map gaining a "hold back the shared alias" filter — is modeled **deeply** (the
spelled-out fold `relabelFrom`, step A4, an I op), not hidden behind an axiom
about the function under change. There are no consumed axioms.

## D. verify(Solution) ⇒ resolved

`buildRelabeling` verifies only if its output equals `relabeling newPrefix
preserved aliases` — the positional rename map that **omits** every preserved
alias (A4/A5). By R (`alias_map` order ↔ list order, `str`↔`String`, set↔list
membership) the verified map equals the gold `change_map` on the tested inputs;
by G-CONF the R/I transliteration agrees with `patch.diff`'s comprehension on
≥10⁵ inputs including the issue-shaped `T4/T5/T6` and base-table-preserved cases.
A relabeling that omits the shared base-table alias cannot map an existing alias
onto another's new name, so `change_aliases`'s disjointness assertion holds and
the OR-combine that triggered the bug succeeds. Therefore a model satisfying this
spec, refined by the map above, is the gold patch up to type refinement — and the
gold patch resolves (G-RESOLVE). The sole trust point is refinement fidelity
(this doc, G-EQ + G-CONF); there are no axioms to trust.
