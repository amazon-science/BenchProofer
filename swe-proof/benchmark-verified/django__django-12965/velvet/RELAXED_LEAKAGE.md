# RELAXED_LEAKAGE — django__django-12965

Disposition: **KEEP with relaxed leakage** (per `RELAXED_LEAKAGE.md`).
`meta.json gates.G-LEAK.status = "relaxed"`.

## The problem_statement ↔ gold mismatch

The public `problem_statement` is a pure **symptom** report: `Model.objects.all().delete()`
used to emit `DELETE FROM <table>` but on Django 3.1 emits
`DELETE FROM <table> WHERE id IN (SELECT id FROM <table>)`. The complaint is the
subquery (a LOCK TABLES blocker and a perf regression); the requested outcome is
"don't use the subquery for this query." It names neither the deciding function
nor any part of the fix mechanism.

The gold patch fixes it inside `SQLDeleteCompiler.single_alias` — the cached
predicate that selects direct-delete vs. subquery — by **registering the query's
base table among its addressed tables before counting them**:

```python
 @cached_property
 def single_alias(self):
+    # Ensure base table is in aliases.
+    self.query.get_initial_alias()
     return sum(self.query.alias_refcount[t] > 0 for t in self.query.alias_map) == 1
```

The sole FAIL_TO_PASS, `test_fast_delete_all`, exercises exactly the full-table
delete (an **empty** `alias_map`) and asserts a single query with no `SELECT`.
Pre-patch, the empty state counts `sum(...) == 0 ≠ 1`, so `single_alias` is
False and the subquery path is taken; the fix makes the base table count, so the
empty state yields `1` and the direct path is taken.

## Why the discriminator is not public

Token scan of `instance.json` (`problem_statement` vs `hints_text`):

| token | `problem_statement` | `hints_text` |
|---|---|---|
| `single_alias` | **0** | 0 |
| `single alias` | **0** | 1 |
| `refcount` / `alias_refcount` | **0** | 0 |
| `register` / `base table` / `base_table` | **0** | 0 |
| `get_initial_alias` / `initial_alias` | **0** | 0 |
| `active` | **0** | 0 |
| `subquery` / `DELETE FROM` / `all().delete` | yes (symptom) | 0 |

(The three `alias` occurrences in `problem_statement` are in the quoted MySQL
`LOCK TABLES` docs — "use aliases instead" / "no alias on the subquery" — an
unrelated SQL-locking sense, not Django's `single_alias` / `alias_map` concept.)

The deciding concept — "the deletion is direct iff the query addresses exactly
**one live table once its primary target table is accounted for**" — and its
load-bearing edge case — "an **empty** query state still counts as one table" —
appear ONLY in `hints_text` ("prevent the query when dealing with a single
alias") and the gold/`test_patch`, never in the public `problem_statement`.

## Why faithful + non-leaking is impossible

A **faithful** spec must pin the full-delete edge case: empty reference-state
⇒ exactly one live table ⇒ direct delete. This is precisely what
`test_fast_delete_all` checks, and it is precisely the gold fix (the added
`get_initial_alias()` call modeled by `withTarget [] = [1]`). A spec that
counted the tables WITHOUT first accounting for the target table — i.e. dropped
the `withTarget` step — is exactly the prepatch: it returns False on the empty
state and fails the F2P test (`Solution_prepatch.lean` fails both `ensures`
clauses for this reason). So the target-table-accounting step is **mandatory**
for faithfulness; without it no wrong impl is excluded and `verify ⟹ correct`
breaks.

But that step's behavior — that an empty query state must still resolve to one
live table — is derivable only from `hints_text` / the gold / the hidden
`test_patch`, never from the public symptom report. The public text says only
"this query should not use a subquery"; it does not say the deciding rule is a
single-live-table count, nor that the always-present target table must be
counted. Any faithful spec therefore necessarily reveals a behavior the public
task text does not contain — the leak is in the **behavior itself**, not in
narration that could be deleted. No `problem_statement`-derivable reformulation
models the gold fix. This is the precise condition `RELAXED_LEAKAGE.md`
accepts.

## De-narration performed (disclosure minimized to the unavoidable)

Although the disclosure is unavoidable at the behavior level, the spec view was
de-narrated so it reveals the minimum and never the gold edit/diagnosis:

- Method `singleAlias` → **`directDeleteEligible`** (abstract behavior:
  direct-delete-vs-subquery, both PS-public terms), off the patched symbol
  `SQLDeleteCompiler.single_alias`.
- Parameter `refcount` → **`tableRefs`**, off the repo field `alias_refcount`.
- Deep model `activate` → **`withTarget`**, off the callee `get_initial_alias`.
- Count `numActive` → **`liveCount`**.
- Removed the bug→fix mechanism narration from both docstrings — the prior text
  "the query's base table must be registered among its active references before
  they are counted (a query with no recorded references must still count its own
  base table)" was the gold's diagnosis verbatim. The docstrings now describe
  only the abstract decision (direct delete vs subquery; account for the primary
  target table, then count live tables) without naming the patched site, the
  callee, or the diagnosis.

The spec view names no patched file/function/line, echoes no patched repo
symbol, and quotes no gold-diff line. The residual disclosure is the semantic
behavior alone, as the relaxed-leakage policy expects.

## Requirements check (RELAXED_LEAKAGE.md)

1. **Core is sound.** G-VERIFY pass (Solution.lean verifies, exit 0); G-DIFF fail
   — the prepatch (omits the target-table-accounting step) fails on BOTH the
   decision clause `direct ↔ liveCount (withTarget tableRefsOld) = 1` (diverges
   on the empty full-delete state) and the mut-frame clause
   `tableRefs = withTarget tableRefsOld`, i.e. the exact discriminating reason;
   G-EQ SOUND+TIGHT (8/8 spec-too-weak attacks rejected, non-vacuous positive
   control verifies; postconditions are grounded structural predicates on the
   input carrier `tableRefs`, no ungrounded oracle — directive 8); G-AX SOUND
   (`withTarget` deep model validated == real `Query.get_initial_alias` on 14
   real-Query observations, no consumed axioms); faithfulness FAITHFUL
   (100,010-input G-CONF, 0 disagreements; F2P observation matches);
   **G-RESOLVE**: `patch.diff` == gold verbatim, harness `resolved`.
2. **The leak is genuinely unavoidable**, established above: the
   single-live-table / count-the-target-table discriminator is demonstrably
   absent from `problem_statement` and present only in `hints_text` / gold /
   `test_patch`, and no PS-derivable reformulation models the gold fix.
3. **Documented in-bundle** (this file); `meta.json gates.G-LEAK.status =
   "relaxed"` points here. The mechanical lexical G-LEAK screen still passes (the
   de-narrated spec view echoes no patched symbol) — the leak is semantic, as the
   policy expects.

## Scope of what is disclosed

The spec view discloses: a deletion is compiled as a direct single-table delete
(rather than via a row-selecting subquery) iff the query addresses exactly one
live table once its primary target table is accounted for; in particular an
empty query state counts as one such table. The direct-delete-vs-subquery
distinction is PS-public; the single-live-table decision rule and the
empty-state edge case are the relaxed disclosure. Nothing about the patched file,
the `single_alias` / `alias_refcount` / `alias_map` / `get_initial_alias` symbols,
or the `cached_property` mechanism is named in the spec view.
