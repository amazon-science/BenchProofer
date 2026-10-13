# refinement.md — django__django-14053

The operation-by-operation correspondence between `model.py`'s implementation
(the `collect_reports` impl region and the deep folds `first_pass_ids` /
`adj_ids` / `failing_adj_count` / `reported`) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A-consumed** (proof uses an
axiom's `Ensures`), **A-reference** (a deep model validated == a real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map below,
is behaviourally equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies cleanly at
`base_commit` and is the real correctness oracle, G-RESOLVE).

Line numbers below are POST-patch (`base_commit` + `patch.diff`), which is the
reference tree for the modelled function; base-commit line numbers are used only
for the callees the gold patch does not touch.

## A. The reporting site — `HashedFilesMixin.post_process()` (`django/contrib/staticfiles/storage.py:203`)

Gold hunk (the changed body of `post_process`):
```
+        # Adjustable files to yield at end, keyed by the original path.
+        processed_adjustable_paths = {}
+
         for name, hashed_name, processed, _ in self._post_process(paths, adjustable_paths, hashed_files):
-            yield name, hashed_name, processed
+            if name not in adjustable_paths or isinstance(processed, Exception):
+                yield name, hashed_name, processed
+            else:
+                processed_adjustable_paths[name] = (name, hashed_name, processed)
         ...
         for i in range(self.max_post_process_passes):
             ...
             for name, hashed_name, processed, subst in self._post_process(...):
-                yield name, hashed_name, processed
+                # Overwrite since hashed_name may be newer.
+                processed_adjustable_paths[name] = (name, hashed_name, processed)
                 ...
+        # Yield adjustable files with final, hashed name.
+        yield from processed_adjustable_paths.values()
```

| # | model.py impl op (`collect_reports`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `ids: List[int]`, `adj: List[int]`, `err: List[int]` (`len(ids)==len(adj)==len(err)`) | `paths` mapping keys, the `name in adjustable_paths` predicate, and the `isinstance(processed, Exception)` predicate | R | `str` file names ↔ distinct integer ids; the two predicates ↔ the two parallel 0/non-0 streams (mapping.md §2). The stream INDEX is bound to the routine's **enumeration order** — `sorted(paths, key=path_level, reverse=True)` in `_post_process` (`storage.py:263-267`, pre-existing at base_commit, untouched by the gold patch) — NOT raw `paths` iteration order (mapping.md §2 "Enumeration order"). |
| A2 | first loop, first test: `if fa == 0 or fe != 0: first = [fid] + first` | first-pass guard `if name not in adjustable_paths or isinstance(processed, Exception): yield name, hashed_name, processed` (`storage.py:236-237`) | R | **Disjunct for disjunct, with no latitude.** `fa == 0` ↔ `name not in adjustable_paths`; `fe != 0` ↔ `isinstance(processed, Exception)`; the `or` is the same `or`; the `yield` at that point in the stream ↔ appending to the first-pass segment at that enumeration position. There is **no refinement here that may drop the second disjunct**: the model's `first_pass_ids` fold contains it, postcondition (1) is a total equation on the reported sequence, and a refinement that emits only `name not in adjustable_paths` reports a strictly shorter sequence than `reported(ids, adj, err)` on any collection carrying a failing file. See "No latitude" below. |
| A2b | the SAME loop iteration handles both of a failing adjustable file's outcomes (one first-pass report from the first test, one settled report from the second) | `_post_process` yields TWO quadruples for such a file in one pass: `yield name, None, exc, False` from the `except ValueError as exc:` arm (`storage.py:300-301`) and then, falling through, the terminal `yield name, hashed_name, processed, substitutions` (`storage.py:332`) | R | per-QUADRUPLE branching in the patch ↔ per-FILE routing in the model. The exception quadruple takes the guard's second disjunct and is yielded; the terminal quadruple for the same `name` takes the `else` and is stored. So the patch's `if`/`else` on quadruples aggregates, per file, to the model's two INDEPENDENT tests — which is why the model does not write `else` for the second test. Only an adjustable file can produce the exception quadruple at all: the substitution loop is inside `if name in adjustable_paths:` (`storage.py:291`), so `url_converter` is never invoked for a plain file. That is why `failing_adj_count` conjoins `adj[0] != 0` with `err[0] != 0`, and why the model's value is insensitive to `err` on a plain file (mapping.md §2, "unreachable flag combination"). |
| A3 | first loop, second test: `if fa != 0: collected = [fid] + collected` | `else: processed_adjustable_paths[name] = (name, hashed_name, processed)` (`storage.py:238-239`) | R | dict-keyed-by-`name` collection ↔ list of adjustable ids; since file names (ids) are distinct, keying by `name` yields each adjustable id exactly once — modelled as appending it once to `collected`. By A2b every adjustable file's terminal quadruple reaches this `else`, failing or not, so the model's test is `fa != 0` unconditionally rather than the complement of A2's guard. |
| A4 | (no repeat-pass report; the `collected` sequence is pass-count-invariant) | repeat-pass body `processed_adjustable_paths[name] = (...)` with NO `yield` (`storage.py:245-247`) | R | the repeat passes overwrite values but never change the KEY set (mapping.md §2 note): the reported adjustable-name sequence is the same regardless of pass count, so the model omits the pass counter and reports `collected` once. In a repeat pass a failing file's exception quadruple is also merely stored and is then overwritten by the same file's terminal quadruple later in the same pass, so no repeat pass emits anything. |
| A5 | `result = first + collected` (first-pass segment, then settled segment) | first-pass yields ++ final `yield from processed_adjustable_paths.values()` (`storage.py:259-260`) | R | concatenation of the first-pass reports with the end-of-run adjustable reports. The ORDER WITHIN each part is a type refinement, not an identical operation: both parts come out in `_post_process`'s depth-sorted enumeration order (`storage.py:263-267`), and `processed_adjustable_paths` preserves it because dicts keep insertion order, keys are first inserted in first-pass enumeration order, and the repeat passes only overwrite existing keys. So `first`/`collected` are ordered by the enumeration index the `ids` stream carries (A1, mapping.md §2 "Enumeration order") — machine-confirmed 0 order violations against the real callee under that binding, vs 19252/30000 under the older "paths iteration order" reading. Tagged `R` because the correspondence holds only through that index binding. |
| A6 | `Assert(lemma_split_len(...))` | — (proof obligation) | I | discharges the length postcondition; no repo counterpart (a verification artefact). |

### No latitude: what a refinement of this model may NOT do

The two obligations the spec carries are independent, and the map above admits
exactly one refinement of each:

1. **Multiplicity (A3–A5).** An adjustable file is reported ONCE for its settled
   outcome, at the end, however many internal passes run — versus the pre-change
   unconditional `yield` in the first pass and in every repeat pass.
2. **Failure hand-off (A2, A2b).** A file whose examination fails is reported to
   the caller AT the position the first pass reaches it. A refinement that
   satisfies obligation 1 by holding that file back — storing its failing outcome
   under the file's key so the later settled outcome overwrites it, and emitting
   only the settled one — is **not** a refinement of A2: it drops the `fe != 0`
   disjunct, which the model's `first_pass_ids` fold and postcondition (1)
   require. Nothing in this document licenses it. It is also observably wrong at
   the caller: `collect()` is the component that interprets a failure
   (`collectstatic.py:129-134` writes `"Post-processing '%s' failed!"` and then
   `raise processed`), so a failure the routine does not hand over is a failure
   the run never surfaces.

`model_prepatch.py` reproduces the pre-change shape for obligation 1: its first
loop reports EVERY file (`first = [fid] + first` for all files) and its second
loop reports each adjustable file again (`collected`), so an adjustable file
appears twice. It therefore **fails** postcondition (1)
`ToSeq(Result()) == reported(ToSeq(ids), ToSeq(adj), ToSeq(err))` and
postcondition (2) `len(Result()) == len(ids) + failing_adj_count(...)` — exactly
the spec sensing the change (G-DIFF).

### Scope actually claimed, and what is left outside

The model's carrier is the sequence of reported file identities. Two things the
real routine does are outside it, and in neither case does this document grant a
refinement any latitude over them:

* **Per-file failure multiplicity.** `err[k]` is a 0/non-0 flag: file `k`'s
  examination fails or it does not, and a failing file contributes exactly one
  first-pass report. In the repository a file's examination runs one substitution
  per matching rewrite pattern (`storage.py:294-301`), so a file whose content
  fails under several distinct patterns emits one report per failure, at the same
  enumeration position. The model abstracts that to one. This is sound at the
  observable: `collect()` stops at the FIRST failure report it sees
  (`collectstatic.py:134`), so reports after the first are never consumed.
  axiom_check.py drives the real callee under the one-pattern-per-file binding
  mapping.md §2 states, and additionally asserts, for collections where a file
  fails, that the failure report precedes that file's settled report in the real
  stream.
* **Non-convergence.** If substitutions never settle, the routine yields
  `('All', None, RuntimeError(...))` (`storage.py:253-254`) and `collect()`
  re-raises it. The model carries no counterpart because the arm reports no file
  identity. This arm is **caller-observable** — the PASS_TO_PASS test
  `test_import_loop` asserts `collect()` raises `RuntimeError('Max post-process
  passes exceeded')` and writes `"Post-processing 'All' failed!"` — so the
  justification is NOT "unobservable, therefore free". It is that the gold patch
  does not touch the arm: it appears in `patch.diff` only as unchanged context,
  no step A1–A6 above ranges over it, and therefore **no refinement of this map
  has any licence to alter it**; it must be left exactly as the gold patch
  leaves it. axiom_check.py pins that preservation executably rather than by this
  paragraph alone: it drives the arm and asserts (i) the sentinel is emitted,
  (ii) the sentinel sits exactly between the two modelled segments, each of which
  the arm leaves equal to `first_pass_ids` / `adj_ids` — so the arm is purely
  additive on the modelled part of the stream and cannot be used to smuggle a
  change into it — and (iii) a `collect()`-faithful consumer aborts on it naming
  `'All'`. Those are the three facts `test_import_loop` reads.

## B. No kind-3 (unexpressible-changed-op) steps; the deep model is an A-reference

Every step above is R or I. The operation that genuinely *changed* — which files
are reported, how many times, and at which point a failing file is handed to the
caller — is modelled **deeply** (the spelled-out front-recursive folds
`first_pass_ids` / `adj_ids` / `failing_adj_count` / `reported` and the verified
loop in `collect_reports`), not hidden behind an axiom. There is **no consumed
axiom** (no `@ContractOnly` whose `Ensures` the proof relies on).

The deep model IS, however, an **A-reference**: `first_pass_ids` / `adj_ids` /
`failing_adj_count` / `reported` abstract the function under change itself —
`HashedFilesMixin.post_process` — so its faithfulness is a real,
executable-checkable obligation, not a mechanical-only audit. `axiom_check.py`
discharges it and is **NOT a null check**: it loads the REAL patched
`post_process` AND the REAL `_post_process` (stubbing only the per-file storage
I/O, so both the `sorted(paths, key=path_level, reverse=True)` traversal that
fixes the enumeration order and the real `except ValueError as exc` arm that
produces a failing outcome are exercised, not replaced), drives them over
boundary + exhaustive(files ≤ 5, all adjustable-subsets) + fuzz MIXED-DEPTH
collections **with and without failing files**, and asserts the yielded `name`
sequence equals `reported(ids, adj, err)` and that its length is
`len(ids) + failing_adj_count(ids, adj, err)`;
`_assert_suite_exercises_depth_sort` fails the check if the suite contains no
collection the sort actually reorders, and `_assert_suite_exercises_failures`
fails it if no collection in the failure suite actually reaches the real
`ValueError` site. Against the PRE-patch source it correctly FAILS. This matches
`meta.json` `deep_model_references` (kind `A-reference`, `checked_by`
`axiom_check.py`) and the model.py docstring.

The unchanged helpers `post_process` calls (`self.hashed_name`,
`matches_patterns`, storage `_save`/`exists`/`delete`) are NOT axiomatized: they
only produce the per-file `hashed_name` VALUE, which does not influence which
`name` is reported nor how often. `self._post_process` is the ONE callee that
does, twice over — it fixes the enumeration ORDER and it is where a failing
outcome is produced — so it is NOT stubbed; axiom_check.py runs the real one. The
trust points are thus (1) refinement fidelity (this document, G-EQ) and (2) the
A-reference faithfulness of the deep model to the real `post_process`
(axiom_check.py, G-AX).

## C. verify(model) ⇒ resolved

`collect_reports` verifies only if its output equals exactly
`reported(ids, adj, err)` = the first-pass segment (every plain id and every
failing adjustable id, once each, in enumeration order) ++ the settled segment
(every adjustable id, once each, same order) (A2/A2b/A3/A5), whose length equals
`len(ids) + failing_adj_count(ids, adj, err)` (A6, `lemma_split_len`). By R (file
names ↔ distinct ids; `name in adjustable_paths` ↔ the `adj` stream;
`isinstance(processed, Exception)` ↔ the `err` stream; the yielded triple's
`name` projection; generator-as-finite-list) a verified routine, refined per §A:

* reports each file's `name` exactly once for its settled outcome — precisely the
  F2P property `assertCountEqual(stats['post_processed'], set(stats['post_processed']))`,
  together with the membership assertions that every file is still processed; and
* hands every failing file's outcome to `collect()` at that file's enumeration
  position, so `collect()` writes `"Post-processing '%s' failed!"` and re-raises
  — precisely what the PASS_TO_PASS test *post_processing indicates the origin of
  the error when it fails* asserts (`tests/staticfiles_tests/test_storage.py:221-230`:
  `with self.assertRaises(Exception)` around `call_command('collectstatic', ...)`
  and `assertEqual("Post-processing 'faulty.css' failed!\n\n", err.getvalue())`).

Both obligations are needed: a refinement that satisfies only the first is the
implementation the earlier audit exhibited — it delivers the F2P property and
destroys the failure hand-off, so F2P passes and that PASS_TO_PASS test fails.
The spec now pins both, so a model satisfying it, refined by the map above, is
the gold patch up to type refinement — and the gold patch resolves (G-RESOLVE).

A third caller-visible obligation is in the hidden suite and is NOT in the
postcondition: `test_import_loop` reads the non-convergence arm. It is discharged
differently, and deliberately so — the arm is unchanged context in `patch.diff`,
no step A1–A6 ranges over it, so every refinement of this map carries it through
untouched; axiom_check.py additionally asserts the arm is purely additive on the
modelled part of the stream (sentinel between the two segments, each segment
equal to the model), which is what makes "untouched" checkable instead of merely
asserted. See "Scope actually claimed" above.

The trust points are refinement fidelity (this document, G-EQ) and the
A-reference faithfulness of the deep model `reported` to the real patched
`post_process` (axiom_check.py, G-AX) — there is no *consumed-axiom* soundness
obligation (no `@ContractOnly`).
