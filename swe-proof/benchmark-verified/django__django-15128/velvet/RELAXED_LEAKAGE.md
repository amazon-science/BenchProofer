# Relaxed-leakage argument — django__django-15128

**Disposition: RELAXED** (per `RELAXED_LEAKAGE.md`). This is a
`problem_statement ↔ gold` mismatch: the gold's *tested* discriminator lives only
in `hints_text` / the gold diff / the hidden `test_patch`, and — proven
in-container below — the sole property the public `problem_statement` *does*
state (the `change_aliases` keys-disjoint-from-values constraint) is **not** a
faithful discriminator for the gold fix. A spec that is faithful (rejects the
modeled-op prepatch, so no wrong impl verifies) MUST name the hints-only
mechanism; a spec restricted to `problem_statement`-public vocabulary cannot pin
the gold behavior. Faithful + non-leaking is therefore provably impossible.

This supersedes two prior failed dispositions (verdict.md): the round-0 bundle
claimed NO-LEAKAGE while narrating the merge purpose; the round-1 refinement
de-narrated the docstrings but kept the mechanism and again claimed NO-LEAKAGE.
Both were wrong about the *direction* of the fix — they (and the audit) assumed a
PS-derivable "disjoint keys/values" outcome spec was available. It is not, and
the experiment below shows why.

## 1. What the modeled operation actually is

The modeled op (`buildRelabeling` / `relabeling`) is the rename-map dict
comprehension at the end of `Query.bump_prefix`, gold-patched:

```python
self.change_aliases({
    alias: '%s%d' % (self.alias_prefix, pos)
    for pos, alias in enumerate(self.alias_map)
    if alias not in exclude          # <-- the gold's added discriminator
})
```

with `combine` now calling `rhs.bump_prefix(self, exclude={initial_alias})`. The
modeled spec pins exactly the `if alias not in exclude` emission filter: the
strings in `preserved`/`exclude` are held back from the rename map while the
position counter still advances for every alias.

## 2. The public problem_statement describes a DIFFERENT property and proposes a DIFFERENT fix

Token scan (lower-cased counts; `problem_statement` = PS, `hints_text` = HT):

| token | PS | HT |
|---|---:|---:|
| exclude | 0 | 4 |
| initial | 0 | 5 |
| bump_prefix | 0 | 10 |
| prefix | 0 | 26 |
| preserve | 0 | 0 |
| shared | 0 | 0 |
| base table | 0 | 0 |
| relabel / rename | 0 | 0 |
| adjust | 0 | 3 |
| "starting point" | 0 | 1 |
| keys | 3 | 1 |
| values | 3 | 2 |
| isdisjoint / disjoint | 0 | 1 |
| AssertionError | 4 | 1 |
| KeyError | 0 | 1 |

The PS reports the SYMPTOM — `Query.change_aliases raises an AssertionError`,
`change_map = {'T4':'T5','T5':'T6'}`, "change_map's keys intersect with
change_map's values" — and proposes a SPECIFIC, DIFFERENT remedy:

> "Maybe alias_map of rhs can be provided to Query.join and Query.table_alias,
> and **suffix (number) of the new alias might be incremented until it is not in
> rhs.alias_map**."

That is a `table_alias`/`join` suffix-bump, NOT the gold's
`bump_prefix(..., exclude=...)`. The gold's actual mechanism — bump the rhs
prefix and hold back the shared base/initial alias from renaming — appears ONLY
in `hints_text`:

> Simon Charette: "change the alias_prefix of the rhs … so it doesn't conflict"
> … "have **bump_prefix adjust all the aliases but the initial one so it can
> still be used as the merge starting point**."

`exclude`/`initial`/`bump_prefix`/`prefix`/`preserve`/`base table` are all
PS=0 — present only in hints/gold.

## 3. Decisive: the PS-derivable "disjoint keys/values" property is SPEC-TOO-WEAK (it does not discriminate the gold fix)

The prior audit asserted three times that an outcome-framed spec — "the produced
rename map's keys are disjoint from its values" — is PS-derivable and would make
the leak avoidable. **This is false, and I refuted it in-container.**

The comprehension keys every new name on the `enumerate` **index** (`pos` =
0,1,2…), not on the alias's original number. So the produced map's *values*
(`prefix0, prefix1, …`) are structurally disjoint from its *keys* (the original
aliases) regardless of whether the filter is present:

In-container, gold map vs modeled-op-prepatch map (filter removed):

```
exclude={'T4'}: GOLD     disjoint=True  map={'T5':'U1','T6':'U2'}
                PREPATCH disjoint=True  map={'T4':'U0','T5':'U1','T6':'U2'}
exclude={'T5'}: GOLD     disjoint=True  map={'T4':'U0','T6':'U2'}
                PREPATCH disjoint=True  map={'T4':'U0','T5':'U1','T6':'U2'}
```

Both the gold map AND the unfiltered prepatch map satisfy
`set(keys).isdisjoint(values)` in EVERY case. **The disjointness outcome the PS
describes does not separate the gold from the prepatch of the modeled op.** A
spec framed on that property would verify against the unfiltered impl — it is
spec-too-weak and would fail G-EQ/G-DIFF.

Why is disjointness still satisfied without the filter? Because the public
`AssertionError` is fixed not by the modeled comprehension but by the *act of
calling `bump_prefix` at all* — bumping `self.alias_prefix` to a fresh value via
`prefix_gen`. That is unchanged `bump_prefix` machinery (the call is new; the
prefix-generation is not), downstream of which the index-keyed names trivially
avoid the keys. Confirmed in-container by hunk-isolation on the F2P
(`test_conflicting_aliases_during_combine`, the sole FAIL_TO_PASS):

| variant | modeled-op filter | F2P outcome |
|---|---|---|
| base (no gold) | n/a (no bump_prefix call) | `AssertionError` (disjointness) — the **publicly reported** bug |
| gold minus the `bump_prefix(...)` call | n/a | still `AssertionError` (disjointness) — so the disjointness fix = *calling bump_prefix* |
| gold, but `if alias not in exclude` removed | renames base alias too | **`KeyError: 'U0'`** — a DIFFERENT failure |
| gold (full) | omits base alias | **PASS** |

## 4. What the modeled `exclude`/`preserved` filter actually fixes — a hints-only failure mode

The modeled discriminator fixes the THIRD-row failure: with the base/initial
alias also renamed, the merge loses its shared starting point and `combine`'s
`join` lookup raises `KeyError: 'U0'` (the base alias the merge algorithm expects
to find on both sides is gone). This is precisely the hint:

> "The alias merging algorithm that Query.combine uses requires that both query
> share the same initial alias in order to work otherwise you'll get a
> **KeyError**. You'll want to find a way to have bump_prefix adjust all the
> aliases **but the initial one** so it can still be used as the merge starting
> point."

So the gold's tested discriminator is "hold back the shared base/initial alias
from the rename map" — a KeyError-avoidance / merge-correctness property whose
vocabulary (`exclude`, `initial`, `base table`, `shared`, "starting point",
`KeyError`) is entirely absent from `problem_statement` and present only in
`hints_text` / gold / `test_patch`.

## 5. Conclusion: faithful + non-leaking is provably impossible

- A **faithful** spec must reject the modeled-op prepatch (which renames the base
  alias and fails the F2P with KeyError). The only property that does so is the
  preserve-the-`exclude`-subset filter — the gold mechanism.
- A **non-leaking** spec (directive 6, judged against `problem_statement` only)
  may use only the PS-public vocabulary, whose strongest expressible behavioral
  property is the disjointness-of-keys/values outcome. §3 proves that property is
  satisfied by the prepatch too, so it cannot be faithful.
- The two requirements are mutually exclusive. The public task text (disjointness
  symptom + a suffix-increment proposal) and the gold fix (exclude the shared
  base alias when bumping the prefix) are **about different things**.

This is not a de-narration gap. The round-1 refinement already neutralized the
*purpose* prose; the residual "leak" is the *behavior itself* — the modeled
filter — which is mandatory for faithfulness and unexpressible in PS-public
terms. Per `RELAXED_LEAKAGE.md` this is exactly the KEEP-with-relaxation
case.

## 6. Core soundness (all re-confirmed; unchanged by this disposition)

- **G-VERIFY** pass: `Solution.lean` verifies (exit 0, ~2s).
- **G-DIFF** pass: `Solution_prepatch.lean` (unfiltered comprehension) fails
  verify (exit 1) on the discriminating goal
  `(a, newPrefix++…) :: rest = (if a ∈ preserved then [] else [(a,…)]) ++ rest`
  — unprovable exactly when a preserved alias is present.
- **G-EQ** SOUND + TIGHT (prior audit, re-confirmed): 7 same-spec impl attacks
  all rejected; non-vacuity control verifies; postcondition grounded entirely in
  the input carriers (`aliases`/`newPrefix`/`preserved`), no opaque oracle.
- **G-AX** VACUOUS: `axioms=[]`, `deep_model_references=[]`, no `axiom_check.py`.
- **G-CONF** pass: R/I shadow agrees with the gold comprehension over 100010
  inputs (seed 15128), incl. issue-shaped T4/T5/T6 and base-preserved cases.
- **G-RESOLVE** pass: `patch.diff` == gold; harness reports `resolved`.
- **F2P** `test_conflicting_aliases_during_combine`: PASS post-gold; pre-gold
  `AssertionError`; modeled-op prepatch `KeyError` (§3 table) — all reproduced
  in-container in this round.

Only the secondary no-leakage property is relaxed; the headline
`verify ⟹ correct` contract is fully intact.
