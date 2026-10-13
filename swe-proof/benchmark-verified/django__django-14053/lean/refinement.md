# refinement.md — django__django-14053

Operation correspondence between `implementation_postProcess` (Solution.lean) and
the gold `patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses
an axiom's property), **A-reference** (deep model validated == real callee by
G-AX), **I** (identical concrete op).

## Modeled function: `HashedFilesMixin.post_process`

The patch changes how `post_process` consumes the record stream from the
unchanged inner processor `self._post_process(...)`: instead of `yield`-ing every
record from every pass, it now (1) yields immediately only the non-adjustable
files and error records of the first pass, (2) collects adjustable-file results
into an insertion-ordered dict keyed by original name (overwriting on later
passes), and (3) yields that dict's values once at the end — after
`self.hashed_files.update(hashed_files)` (`storage.py:257` post-patch), the point
at which the accumulated name mapping becomes visible to the caller. The record
stream itself (`firstPass`, `laterPasses`) is the modeled INPUT (see mapping.md);
the modeled output is the yielded item sequence **split at that point**, because
`post_process` is a generator and its caller (`collectstatic.collect`) stops
consuming at the first item carrying an exception — so whether an item is handed
over before or after the mapping is committed is observable to the caller, not an
internal detail. Hence `OutReport := List OutItem × List OutItem`: `.1` is what
reaches the caller while the passes are still running, `.2` is what is withheld
until after the commit.

| # | `implementation_postProcess` op | `patch.diff` counterpart | tag | justification |
|---|---|---|---|---|
| 1 | inputs `adjustable : List String`, `firstPass : List PassRecord`, `laterPasses : List (List PassRecord)` | `adjustable_paths`; the record stream of the first `self._post_process(...)` loop; the record streams of the `range(max_post_process_passes)` loops | R | type bijection in mapping.md. The unchanged producer's records are an input. `subst` is not part of the reported item (`toItem` drops it) but is kept on the record as `rewrote`, because it is what decides whether the run continues and hence whether the guarded terminal item is reported — a caller-visible consequence (row 4). |
| 2 | `for r in firstPass do if (! adjustable.contains r.name) ‖ r.isError then early := early ++ [r.toItem] else collected := upsertItem collected r.name r.toItem` | the patched first-pass loop (`storage.py:236-239` post-patch): `if name not in adjustable_paths or isinstance(processed, Exception): yield name, hashed_name, processed; else: processed_adjustable_paths[name] = (name, hashed_name, processed)` | I | identical control flow. `adjustable.contains r.name` ↔ `name in adjustable_paths`; `r.isError` ↔ `isinstance(processed, Exception)`; appending to `early` — the component handed over *before* the commit — ↔ `yield` reached while the loop is still running; `upsertItem` ↔ dict insert/overwrite. |
| 3 | `for pass in laterPasses do unsettled := pass.any (fun r => r.rewrote); for r in pass do collected := upsertItem collected r.name r.toItem` | the patched later-pass loop: `substitutions = False` then `for ... subst in self._post_process(...): processed_adjustable_paths[name] = (name, hashed_name, processed)  # Overwrite since hashed_name may be newer` / `substitutions = substitutions or subst`, and `if not substitutions: break` | I | identical: every later-pass record overwrites the collected entry in place (or appends if new), and `substitutions` is re-initialized to `False` at the top of each pass and then accumulated over that pass's records — so `unsettled := pass.any (fun r => r.rewrote)` is that same per-pass disjunction, and after the loop both hold the LAST executed pass's value. The early `break` and the `max_post_process_passes` bound determine only *which* passes execute, i.e. the *length* of `laterPasses` (mapping.md: `laterPasses` is by construction the executed passes), so they are reflected in the input shape rather than the impl body; what they do NOT determine is the final value of `substitutions`, which is why the flag is on the record. |
| 4 | `unsettled` after the later-pass loop, and `if unsettled then [allowanceItem] else []` appended to the pre-commit component | `if substitutions: yield 'All', None, RuntimeError('Max post-process passes exceeded.')` (`storage.py:243-244` at base_commit, unchanged by the patch and left *before* the commit while the adjustable items move *after* it) | I | the loop falls through with `substitutions` true exactly when the allowance of passes was used up while the run was still rewriting; the guarded item is then handed over, and — because the patch moved the adjustable items past the commit but left this one where it was — it lands on the pre-commit component. Its payload is a fixed error item naming no single source file, ↔ `allowanceItem`. |
| 5 | `return (early ++ (if unsettled then [allowanceItem] else []), collected.map (·.2))` | `self.hashed_files.update(hashed_files)` (`storage.py:257` post-patch, context) then `yield from processed_adjustable_paths.values()` (`storage.py:260` post-patch) | I | the pair is the modeled output, not a re-ordering: `.1` is exactly the set of items the generator has already handed to its caller by the time control reaches `self.hashed_files.update(hashed_files)`, and `.2 = collected.map (·.2)` is exactly what the single trailing `yield from` produces after it — each collected adjustable item once, in insertion order; `collected.map (·.2)` ↔ `.values()`. The split point is `storage.py:257`; no item is on the far side of it that the real generator yields on the near side, and vice versa. Measured: fuzzing the verbatim post-patch body over 20000 randomized record streams (draining the generator item-by-item and reading the commit flag between items) gave 0 mismatches against this pair, with the guarded item exercised on 5023 of them. |
| 6 | the split of the return type `OutReport` itself | the *position* of `yield from processed_adjustable_paths.values()` — after `self.hashed_files.update(hashed_files)` rather than before it | R | a generator's consumer observes item order relative to the callee's side effects: `collectstatic.collect` raises on the first item whose `processed` is an exception and never resumes the generator, so an item yielded before `storage.py:257` is delivered with the shared mapping still holding its pre-call contents, and an item yielded after it is delivered only once the mapping has been committed. Modeling the output as one flat list would erase this distinction, making a full-buffer restructure (all items emitted after the commit) indistinguishable from the real function. |

## Measured: the pair is exactly the discriminating granularity

The split point in row 6 is not a modeling preference; it is where the oracle
changes its answer. Three variants of the post-patch body were written by hand
and each was graded by the resolve oracle on this instance (`run_resolve`,
timeout 3600s, up to 3 attempts). Each was materialized the way the oracle
consumes one — a single diff against `base_commit 179ee13eb3` carrying the gold
edit AND the variant, since `run_resolve` applies it to a clean checkout at
base_commit, not to the patched tree:

| variant of the post-patch `post_process` body | modeled `OutReport` | resolve oracle |
|---|---|---|
| **commit-relative staging destroyed**: buffer *every* item — the first pass's non-adjustable files and its `Exception` items included — and `yield from` the whole buffer after `self.hashed_files.update(hashed_files)`. The flat item sequence is gold's, item for item. | `([], everything)` | **NOT resolved**, 3/3 attempts, consistent (not flaky): F2P passes, and the P2P test asserting what the shared store holds after a failed run fails, because `collectstatic` aborts on the error item only after the mapping was committed. |
| **the pair itself, reconstructed as data**: compute `early` and `processed_adjustable_paths` first, then `yield from early`, then commit, then `yield from ...values()`. Nothing is computed lazily any more. | gold's pair | **resolved**, 1 attempt. Buffering per se is not the defect: the model is insensitive to *when* an item's value is computed and sensitive only to which side of the commit it is handed over on — exactly what `OutReport` encodes. |
| **finer than the pair**: keep the first pass's plain items back until the pass loop has ended, but still hand them over *before* the commit — so the pre-commit component's items arrive interleaved differently with the passes than gold's do. | gold's pair | **resolved**, 1 attempt. A model that pinned the position of each hand-over *within* the pre-commit phase (a 3-or-more-component schedule) would therefore reject a correct implementation. The pair is not too fine. |

The first row is why one flat list is too weak (it cannot see that rival at all)
and the third is why anything finer than two components is too strong. Row 6's
type is the unique granularity between them.

`problem_pre_postProcess laterPasses : laterPasses ≠ []` is a faithfulness
precondition, not a domain restriction against any rival: `substitutions` is bound
*inside* the `for i in range(self.max_post_process_passes)` loop while the
`if substitutions:` guarding row 4's item is *outside* it, so an invocation allowed
zero passes raises `UnboundLocalError` and produces no report to describe. Every
allowance of one or more passes is admissible, including one whose passes report
nothing at all (`laterPasses = [[]]`). `correct_postProcess` closes without using
the hypothesis.

Every op is R or I. There is **no consumed axiom** and **no opaque callee** (the
`axioms` region is empty): the modeled orchestration computes purely over its
input record lists, so `correct_postProcess` discharges by structural reasoning
about the two `for` loops and `upsertItem` (no callee contract needed). The
unchanged producer `_post_process` is an input, not an axiomatized callee, so
there is **no A-reference** either — G-AX is a skip.

## Out-of-scope gold-patch content

The gold patch touches only `post_process`; `_post_process` and all other methods
are unchanged. There is exactly one independently-observable fixed behavior
(duplicate yields for the same file), so one triple and one prepatch suffice.
`patch.diff` is gold verbatim.
