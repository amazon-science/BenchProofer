# RELAXED_LEAKAGE — sphinx-doc__sphinx-10466 (lean)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

Policy: `prompts/lean/spec_guide.md` directive 6 — "**Exception —
relaxed-leakage:** for a proven `problem_statement ↔ gold` mismatch where a
faithful spec MUST name the discriminator, keep the instance with the leak
allowed". The gate honors it mechanically
(`src/swebench_unified/gates/leak.py`) via the `relaxed_leakage` meta flag plus
this file, **even when the lexical screen passes** — which is this bundle's
situation, and the reason the mechanism exists.

## The leaking facet

The spec view states the ORDER of the reported positions. `problem_spec_dedupSort`'s
first conjunct is `List.Sorted lexLt result`; the `pure` region's `lexLe` / `lexLt`
encode lexicographic order on `(source, line)`; and the docstrings say the positions
are listed "in ascending order". The gold hunk at `sphinx/builders/gettext.py:60-61`
is

```python
positions = sorted(set((source, line) for source, line, uuid in self.metadata[message]))
```

so the spec view names the `sorted(...)` half of that hunk. That half is **not**
in the public `problem_statement`. This file dispositions exactly that facet, and
the sections below are the measurements it rests on.

## The mismatch (problem_statement ↔ gold)

Token scan of `problem_statement` ONLY (`hints_text` excluded, per the leakage
standard), re-run from the frozen instance row:

| ordering term | problem_statement | hints_text |
|---|---|---|
| `sort` | 0 | 8 |
| `sorted` | 0 | 1 |
| `order` | 0 | 3 |
| `ordering` / `ascending` / `descending` | 0 | 0 |
| `alphabet` / `lexicograph` | 0 | 0 |
| `arrange` / `reorder` / `canonical` / `stable` | 0 | 0 |
| `position` | 0 | 1 |

Zero hits for every ordering term in the public statement. The de-duplication
vocabulary, by contrast, IS public: `duplicat` ×3, `unique` ×2, `set(` ×1,
`loc_set` ×2, "no duplications" ×1. The ordering content is reachable only
through `hints_text` (out of scope) and the gold diff.

Two further public-side facts point the same way:

* The reporter's own proposed fix, quoted in the statement, is
  `loc_set = set(locations)` / `return list(loc_set)`. `list(set(...))` is
  order-arbitrary — a solver following the statement writes de-duplication with
  no order at all.
* The statement's own sample `.pot` block is not in ascending order
  (`.../vector/vector_rotate.rst:38` precedes `.../modeling/hair.rst:0`), so
  ascending order cannot even be inferred from the displayed expected output.

The GRADED TEST, however, does demand the order. The sole FAIL_TO_PASS test,
`tests/test_build_gettext.py::test_Catalog_duplicated_message`, records four
occurrences and then asserts LIST EQUALITY:

```python
assert msg1.locations == [('/path/to/filename', 1),
                          ('/path/to/filename', 2),
                          ('/path/to/yetanother', 1)]
```

A list-equality assertion grades order. So the instance grades a property its
public statement does not mention: that is the `problem_statement ↔ gold`
mismatch this relaxation is about.

## Why the leak is unavoidable — measured

The standard this corpus enforces is `verify ⟹ correct`: every implementation
that satisfies the spec must RESOLVE the instance (pass FAIL_TO_PASS, keep
PASS_TO_PASS passing). The candidate de-leaked spec replaces the ordering
conjunct with plain repeat-freeness and changes nothing else:

```
-  List.Sorted lexLt result ∧
+  result.Nodup ∧
   (∀ p : String × Int, p ∈ result ↔ ∃ u : String, (p.1, p.2, u) ∈ triples)
```

That weakening keeps rejecting the PRE-patch implementation (`return pairs` is
not `Nodup` on a repeated position), so the prepatch-rejection test alone does
not detect the problem. It nevertheless breaks `verify ⟹ correct`, measured
at two levels.

**(a) Lean — the de-leaked spec admits a non-resolving implementation.**
`scripts/lean_verify.sh` exit 0 on a file whose rival is
`(triples.map (fun t => (t.1, t.2.1))).dedup.reverse` — de-duplicated, NOT
sorted ascending (Python: `list(dict.fromkeys(...))[::-1]`):

* `deleaked_admits_rival : ∀ triples, problem_spec_deleaked triples (implementation_rival triples)`
  — closed from `List.nodup_dedup` and `List.mem_reverse`/`List.mem_dedup`, so
  the rival satisfies the de-leaked spec at EVERY input, not just one.
* `shipped_rejects_rival : ¬ problem_spec_dedupSort W (implementation_rival W)`
  for `W = [("a",1,"u1"), ("a",2,"u2")]` — the shipped ordering conjunct is
  exactly what excludes it.
* `rival_on_F2P` (by `decide`): on the FAIL_TO_PASS test's own four
  occurrences the rival returns
  `[("/path/to/yetanother",1), ("/path/to/filename",2), ("/path/to/filename",1)]`,
  and `deleaked_admits_a_list_the_graded_assertion_rejects` closes both halves:
  the de-leaked spec admits that list AND it is not the list the graded
  assertion demands.

**(b) The harness — that implementation does not resolve.** Three candidate
patches applied at `base_commit` and graded through the normal oracle
(`swebench_unified.harness.run_resolve`, official SWE-bench harness, prebuilt
instance image). All three applied cleanly and all three runs completed:

| candidate | `positions = ...` | de-leaked spec | resolved | FAIL_TO_PASS | PASS_TO_PASS |
|---|---|---|---|---|---|
| gold (control) | `sorted(set(...))` | satisfies | **true** | 1 pass / 0 fail | 6 pass / 0 fail |
| insertion-order dedup | `list(dict.fromkeys(...))` | satisfies | true | 1 pass / 0 fail | 6 pass / 0 fail |
| **descending dedup** | `sorted(set(...), reverse=True)` | **satisfies** | **false** | **0 pass / 1 FAIL** | 6 pass / 0 fail |

The failing test is `tests/test_build_gettext.py::test_Catalog_duplicated_message`
(`resolved: false`, `completed: true`, `patch_successfully_applied: true`,
"patch did not resolve in 1 attempts (consistent — not flaky)"). On that test's
input the descending candidate returns exactly the list `rival_on_F2P` computes,
which the list-equality assertion rejects. So an implementation satisfying the
de-leaked spec fails the graded test: `verify ⟹ correct` does not hold without
the ordering conjunct.

The middle row is why the weaker prepatch-rejection test is not sufficient here.
First-seen de-duplication happens to agree with ascending order on the graded
input, so it resolves; the de-leaked spec, however, admits far more than
first-seen order, and the rows differ on exactly the property the statement never
mentions.

**(c) The statement's own fix is a coin flip under the de-leaked spec.**
`list(set(...))`, the implementation the public statement proposes, satisfies the
de-leaked spec at every input, and whether it passes the graded assertion depends
on string-hash randomization: over `PYTHONHASHSEED` 0–9 on the FAIL_TO_PASS
input it produces the asserted list for 5 seeds and a different permutation for
the other 5 (seeds 1, 2, 4, 6, 8 fail). Under the de-leaked spec a "verified"
implementation resolves the instance about half the time.

**Conversely, the shipped spec is FUNCTIONAL.** `scripts/lean_verify.sh` exit 0
on `shipped_functional`:

```
theorem shipped_functional (triples) (r1 r2)
    (h1 : problem_spec_dedupSort triples r1)
    (h2 : problem_spec_dedupSort triples r2) : r1 = r2
```

(via `List.perm_ext_iff_of_nodup` on the membership biconditional plus
`List.eq_of_perm_of_sorted`, with `lexLt` irreflexive and transitive). The
shipped postcondition pins the output to a single list, so every implementation
satisfying it returns precisely what the gold returns, and therefore resolves.
The ordering conjunct is what buys that: strict ascending order is the property
that turns "the right set of positions" into "the one list the graded assertion
accepts".

A faithful, sound spec for this instance therefore cannot avoid naming the
ordering discriminator — the statement asks only for de-duplication, the graded
assertion additionally grades order, and a spec silent on order admits
implementations that fail it.

## What was NOT done

No clause was weakened and no prose was edited. `Solution.lean` and
`Solution_prepatch.lean` are byte-unchanged by this repair (their spec regions
remain byte-identical under `swebench_unified.markers.same_spec`), so every
retained attack, every rival rejection and every mechanical verdict recorded
against those bytes still describes the artifact that ships. The de-narration
route is not available here either: the leak is in the postcondition and in the
`pure` helpers it quantifies over, not in narration around them, so removing
comments would not remove it.

## Core soundness

Recorded gate verdicts for these bytes:

- G-VERIFY pass — `Solution.lean` verifies in 6.0s, 1 `correct_*` theorem
  closed, axioms clean.
- G-DIFF pass — `Solution_prepatch.lean` fails to verify: the spec still sees
  the bug.
- G-GOLD pass — gold-faithful impl verifies; prepatch fails.
- G-CONF pass — 120007 differential cases against the real patched expression,
  0 mismatches (seed 1046620250630).
- G-MUT pass — killed 10/10.
- G-PBT pass — SOUND, 7 spec cases behaved as expected.
- G-EQ pass — 11 admissible attacks re-run of 11 submitted, none breaks the
  spec; positive control verifies.
- G-RESOLVE pass, G-HYGIENE pass, G-INTEGRITY pass, G-AX skip (no consumed
  callee axioms; every op modeled deeply).

Criterion 1 (core sound) holds on that record; criterion 2 (the leak is
genuinely unavoidable) is the measured argument above; this file is criterion 3
(in-bundle documentation).

## Scope of this disposition

**The facet covered.** Exactly one: the spec view names the ORDER of the
reported positions — the `List.Sorted lexLt` conjunct, the `lexLe`/`lexLt`
helpers that define that order, and the docstring phrase "in ascending order".
What the disposition rests on is the token scan (0 ordering hits in the public
statement), the list-equality assertion in the graded test, the two Lean files
(the de-leaked spec admits `dedup.reverse`; the shipped spec is functional), and
the three-row resolve table.

**What is outside it.** Nothing here speaks to any other leaking line. The
de-duplication half of the hunk is public vocabulary and is not part of this
disposition; a spec-view identifier echoing a patched repo symbol, narration of
the bug→fix mechanism, or any leak elsewhere in the spec view is untouched by
the argument above.

**What would break it.** Two checkable things. Core soundness — the gate record
in the section above. And unavoidability, which is refuted by exhibiting a spec
that is BOTH silent on order (so derivable from the public statement) AND
rejects every implementation that fails the graded assertion. The claim here is
not that no such spec can exist in principle; it is the measured fact that the
one candidate weakening admits `sorted(set(...), reverse=True)`, and that
candidate loses `tests/test_build_gettext.py::test_Catalog_duplicated_message`
in the harness.

**On re-checking.** Every number above is reproducible rather than asserted. The
token scan re-runs from the frozen row's `problem_statement`. The two Lean files
re-run under `scripts/lean_verify.sh` (both exit 0); their content is stated
above in full enough form to re-derive. The resolve table re-runs by applying
each one-line variant of `patch.diff` through
`swebench_unified.harness.run_resolve` for this instance. The hash-seed sweep
re-runs with `PYTHONHASHSEED` 0–9 over the FAIL_TO_PASS input. A reader who
measures something different from what these tables record has found something
this file gets wrong.
