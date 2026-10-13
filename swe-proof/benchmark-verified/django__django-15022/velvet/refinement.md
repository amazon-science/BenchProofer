# refinement.md — django__django-15022

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`searchKeepsRow` `do` block plus the pure folds `conjTerms` / `anyRecord`) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement; state
the bijection), **A-consumed** / **A-reference** (none in this bundle), or **I**
(identical concrete op). EVERY step is R or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The combination loop — `ModelAdmin.get_search_results` (`options.py:1031-1046`)

Gold hunk:
```
             orm_lookups = [construct_search(str(search_field))
                            for search_field in search_fields]
+            term_queries = []
             for bit in smart_split(search_term):
                 if bit.startswith(('"', "'")) and bit[0] == bit[-1]:
                     bit = unescape_string_literal(bit)
                 or_queries = models.Q(
                     *((orm_lookup, bit) for orm_lookup in orm_lookups),
                     _connector=models.Q.OR,
                 )
-                queryset = queryset.filter(or_queries)
+                term_queries.append(or_queries)
+            queryset = queryset.filter(models.Q(*term_queries))
```

| # | Solution.lean impl op (`searchKeepsRow` / `anyRecord` / `conjTerms`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `records : List Nat` | the related items reachable through the searched multi-valued relation that `queryset.filter(...)` joins and tests, per candidate outer row | R | multi-valued relation / multiset of related rows ↔ `List Nat` opaque identities; the decision depends only on the per-(item,word) match bits (mapping.md §2). |
| A2 | param `terms : List Nat` | `list(smart_split(search_term))` (after the quote-literal unwrap) — the loop's iteration variable `bit` | R | word list ↔ `List Nat` opaque identities (mapping.md §2). `smart_split`/`unescape_string_literal` are UNCHANGED (mapping.md §3) and produce the same words pre/post. |
| A3 | param `matchTerm : Nat → Nat → Bool` | `or_queries` for a word evaluated at one related item: `models.Q(*((orm_lookup, bit) for orm_lookup in orm_lookups), _connector=OR)` | R | the per-word OR-of-fields test at one item ↔ a total `Nat → Nat → Bool` (mapping.md §2/§3). UNCHANGED callee, abstracted as a free input. |
| A4 | `conjTerms (matchTerm r) terms` (pure, front-recursive AND) | `models.Q(*term_queries)` = AND of the per-word OR-queries, applied to one related item | I | `conjTerms` IS the conjunction `Q(t₁) AND … AND Q(tₙ)` at item `r`, modeled deeply; the fold ops (`matchTerm r t`, `&&`) are concrete, transliterated by G-CONF. Empty word list ↔ vacuous `true`. |
| A5 | `anyRecord matchTerm terms records` (pure, front-recursive OR over items), computed by the backward `while` fold accumulating `conjTerms (matchTerm r) terms || acc` | `queryset.filter(models.Q(*term_queries))` keeps a row iff SOME related item satisfies the combined AND | I | `anyRecord` IS the row-membership semantics of the single combined filter over a multi-valued relation: ∃ related item r. (r matches every word). Modeled deeply; the OR-fold ops (`conjTerms (matchTerm r) terms`, `||`, the loop) are concrete and transliterated by G-CONF. No axiom — the combination is the operation under spec. |
| A6 | `result = anyRecord matchTerm terms records` (the `ensures`) | the kept/dropped outcome of the candidate row under the patched filter | R | kept ↔ `true` (mapping.md §2). |

## B. The discriminating content — what the spec senses

The change: pre-patch, the per-word `or_queries` were applied as **chained**
`queryset = queryset.filter(or_queries)` — once per word, each adding a JOIN. Over
a multi-valued relation, chaining `.filter` means each filter is satisfied
**independently**: a row is kept iff for **every** word there exists **some**
related item matching it — and those items may **differ** per word. Post-patch the
per-word OR-queries are collected into one `models.Q(*term_queries)` AND and
applied in a **single** `queryset.filter(...)`, so a row is kept iff there exists
**one** related item matching **all** words at once.

This is a quantifier swap on the multi-valued relation:

* pre-patch (buggy):  ∀ word t. ∃ item r. `matchTerm r t`
* post-patch (fixed): ∃ item r. ∀ word t. `matchTerm r t`

The frozen spec pins the result to `anyRecord matchTerm terms records`
(= `∃ r ∈ records. conjTerms (matchTerm r) terms`, the post-patch ∃∀).
`Solution_prepatch.lean` reproduces the pre-patch skeleton — it accumulates the
words one at a time, keeping the row only if SOME item matches **that** word,
re-deciding existence per word independently
(`(terms.drop i).all (fun t => records.any (fun r => matchTerm r t))`) — and
**fails** verification on exactly the clause that the per-word ∃ aggregate equals
the per-item ∃ aggregate (G-DIFF; confirmed unsolved goal at `invariant_2`: the
rewrite `anyRecord_drop_step` finds no occurrence because the buggy accumulator is
`∀word∃item`, structurally distinct from `∃item∀word`). The two diverge precisely
when each word is matched by a different item and no single item matches all words
— the multi-valued-relation case the F2P `test_related_field_multiple_search_terms`
and the `('Mary Jonathan Duo', 1)→0` row of `test_multiple_search_fields` exercise.

A single `Solution_prepatch.lean` carries this one independently-fixed behaviour,
against the byte-identical frozen spec (G-DIFF requires `same_spec`).

The JOIN-count regression observed by `test_many_search_terms` (the `count('JOIN')
== 1` assertion) is the *performance* manifestation of the same change — chaining
`.filter` adds one JOIN per word, the single combined `.filter` adds one total. It
is a consequence of the modeled combination choice (A5: one aggregate filter vs N
chained filters), not a separately modeled quantity.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — how the per-word
OR-queries are combined (N chained filters vs one AND-combined filter) — is
modeled **deeply** (the `anyRecord` ∃-over-items of `conjTerms` ∀-over-words,
A4/A5), not hidden behind an axiom about a function under change. There are **no
consumed axioms and no A-references**: the only callees (`smart_split`,
`unescape_string_literal`, `construct_search`, the per-word/per-item `or_queries`
match, `queryset.filter`) are UNCHANGED by the patch and are abstracted as free
inputs / folded into `matchTerm` with no relied-on property (mapping.md §3), so
nothing requires G-AX validation.

## D. verify(Solution) ⇒ resolved

`searchKeepsRow` verifies only if its result equals the exact modeled decision
`anyRecord matchTerm terms records` (A5/A6) — the ∃-related-item-∀-word
membership. By R (the `List Nat` / `Nat → Nat → Bool` / `Bool` bijections,
mapping.md §2) the verified decision equals the gold-patched
`queryset.filter(models.Q(*term_queries))` row membership on every input, and by
G-CONF the R/I transliteration of the conj/any folds agrees with the patched
combination logic on ≥10⁵ checks (seed 15022, 0 disagreements). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (G-AX skips).
