# mapping.md — django__django-14053

Binds every `model.py` symbol to its repository counterpart, states the type
abstraction, and records callee provenance. There is **no consumed axiom**
(no `@ContractOnly` whose `Ensures` the proof relies on): the changed behaviour
is selection/structure logic over the input streams, modelled deeply. The deep
model (`first_pass_ids` / `adj_ids` / `failing_adj_count` / `reported`) is,
however, an **A-reference**: it abstracts the function under change itself
(`HashedFilesMixin.post_process`), so `axiom_check.py` is a real discriminating
A-reference check — it loads the patched `post_process` and asserts its yielded
`name` sequence equals `reported(ids, adj, err)` (see §3), matching `meta.json`
`deep_model_references`.

Repo file under change: `django/contrib/staticfiles/storage.py`.

Reference tree and line numbers. For the modelled function the reference is
`base_commit = 179ee13eb37348cd87169a198aec18fedccc8668` **with `patch.diff`
applied**, and every `storage.py:NNN` below is a POST-patch line. For callees the
gold patch does not touch (`_post_process`) the base and patched trees agree, and
the cited lines are the same in both.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line, patched tree) | role |
|---|---|---|
| `collect_reports(ids, adj, err)` | `HashedFilesMixin.post_process(self, paths, dry_run, **options)` — `django/contrib/staticfiles/storage.py:203` (changed hunk body lines 230-260) | the modeled changed function: the multi-pass routine that yields one report triple per file to `collectstatic`'s `collect()` |
| `ids` (param) | the keys of the `paths` mapping passed to `post_process`, **listed in the order `_post_process` enumerates them** — `sorted(paths, key=path_level, reverse=True)`, i.e. deepest-directory-first, Python's stable sort breaking ties by `paths` iteration order (`storage.py:263-267`; the sort PRE-EXISTS at base_commit and is untouched by the gold patch, appearing in `patch.diff` only as context) | the distinct file identities, in enumeration order |
| `adj` (param) | the membership predicate `name in adjustable_paths`, where `adjustable_paths = [path for path in paths if matches_patterns(path, self._patterns)]` (`storage.py:225-228`) | per-file 0/non-0 flag: non-0 ⇔ the file is adjustable (matched a content-rewrite pattern) |
| `err` (param) | the predicate `isinstance(processed, Exception)` on the outcome `_post_process` reports for that file — non-0 ⇔ examining the file raised, which `_post_process` surfaces as `yield name, None, exc, False` from its `except ValueError as exc:` arm (`storage.py:300-301`) | per-file 0/non-0 flag: non-0 ⇔ the file's examination fails instead of settling |
| `first_pass_ids(ids, adj, err)` | the first-pass branch `if name not in adjustable_paths or isinstance(processed, Exception): yield name, hashed_name, processed` (`storage.py:236-237`) | pure spec: the ids reported while the first pass runs — plain files, plus any file whose examination fails, at its enumeration position |
| `adj_ids(ids, adj)` | the keys of `processed_adjustable_paths` (`storage.py:231,239,246-247,259-260`), i.e. the adjustable files collected once and yielded at the end via `yield from processed_adjustable_paths.values()` | pure spec: the adjustable ids, each collected and reported once |
| `failing_adj_count(ids, adj, err)` | how many files satisfy `name in adjustable_paths and isinstance(processed, Exception)` — the files reported in BOTH parts (yielded from the guard at `storage.py:237`, and stored by the same pass's terminal quadruple so the final `yield from` emits them too) | pure spec: the number of extra reports a failing examination adds |
| `reported(ids, adj, err)` | the full sequence of `name` values `post_process` yields back to `collect()` | pure spec: the first-pass segment then the settled segment |
| `lemma_split_len` | — | proof lemma (no repo counterpart): each file lands in the first-pass segment, or the settled segment, or — exactly when it is adjustable and fails — in both |

The pre-patch repo construct the change replaces (for the refinement audit, not
referenced from the consumer spec view): the unconditional `yield name,
hashed_name, processed` in BOTH the first pass and every repeat pass, so an
adjustable file is yielded in the first pass and once more in each repeat pass —
the multiple-yield the F2P test forbids. Note what the pre-patch code did NOT do:
it never withheld a failing file's outcome, because it yielded every quadruple
`_post_process` produced, exception quadruples included. The failure hand-off is
therefore a **preservation** obligation — a property the routine had before the
change and still has after it — not part of the change itself.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| the `paths` mapping (keys = file names, unique) | `ids: List[int]` of distinct file-identity codes, in the routine's **enumeration order** | `name` ↔ `ids[k]`; one list entry per `paths` key; key uniqueness ↔ distinct `ids` entries. The index `k` orders the files as `_post_process` visits them — `sorted(paths, key=path_level, reverse=True)` (`storage.py:263-267`), NOT raw `paths` iteration order. See "Enumeration order" below. |
| `name in adjustable_paths` (a membership predicate over the same files) | `adj: List[int]` parallel stream, `adj[k] != 0` ⇔ `ids[k]` is adjustable | aligned index-for-index with `ids` (`len(ids) == len(adj)`); 0 ⇔ plain, non-0 ⇔ adjustable |
| `isinstance(processed, Exception)` — the file's examination raised rather than settling | `err: List[int]` parallel stream, `err[k] != 0` ⇔ examining `ids[k]` fails | aligned index-for-index with `ids` (`len(ids) == len(err)`); 0 ⇔ settles, non-0 ⇔ fails. This stream is what the repair added: without it the operand the patched first-pass guard branches on has no carrier at all, and a routine that withholds a failing file cannot be told apart from one that hands it over. |
| the yielded triple `(name, hashed_name, processed)` | the `name` component only — `List[int]` of reported ids | the observables both hidden test sets inspect are per-`name`: the F2P reads `stats['post_processed']`, a list of `name`s, and the failure-path PASS_TO_PASS reads whether `collect()` re-raised and which `name` it named in `"Post-processing '%s' failed!"`. Projecting to `name` keeps both, because `hashed_name` carries no identity and `processed`'s only identity-relevant content — is it an `Exception`? — is carried by the `err` stream instead. |
| the generator's lazy `yield` stream | the eagerly materialised `List[int]` the model returns | a generator that is fully consumed by `collect()` is observationally its finite output list; the F2P property (no name yielded twice for a settled outcome) and the failure-hand-off property (a failing file's report appears in the first-pass segment) are both properties of that finite list |
| `self.max_post_process_passes` repeat passes (`storage.py:243`) | folded into the single `adj_ids` collection | each repeat pass only OVERWRITES `processed_adjustable_paths[name]` — the SEQUENCE of reported adjustable names is pass-count-invariant, so the model needs no explicit pass counter; the modeled output is the fixpoint the passes converge to (note below) |

**Why the pass count drops out.** Post-patch, the repeat-pass loop body is
`processed_adjustable_paths[name] = (name, hashed_name, processed)` with NO
`yield` (`storage.py:245-247`); the final `yield from
processed_adjustable_paths.values()` (`storage.py:259-260`) emits each key once.
The keys of `processed_adjustable_paths` are exactly the adjustable names
(established in the first pass and only re-keyed, never added or removed, by the
repeat passes, because `paths` is restricted to `adjustable_paths` at
`storage.py:241`). Hence the reported adjustable-name sequence equals `adj_ids`
independent of how many passes run. (Pre-patch, by contrast, EACH pass `yield`s,
so the name multiplicity grows with the pass count; the prepatch model reproduces
this with a first-pass-reports-all loop plus one repeat-pass report, which already
exceeds multiplicity 1 and fails the spec.)

**Enumeration order (load-bearing R-step — the `ids` index is NOT `paths`
iteration order).** `post_process` never enumerates `paths` itself; every file it
reports comes to it from `self._post_process`, which iterates
`sorted(paths, key=path_level, reverse=True)` where
`path_level(name) = len(name.split(os.sep))` (`storage.py:263-267`) —
deepest-directory-first, with Python's stable sort breaking ties by `paths`
iteration order. That sort PRE-EXISTS at `base_commit` and the gold patch does not
touch it (it appears in `patch.diff` only as unchanged context), so it is a
standing property of the modelled function, not a patch artefact. The model's
`ids`/`adj`/`err` streams are therefore bound to that **enumeration order**:
`ids[k]` is the k-th file `_post_process` visits. Under this binding the real
callee's reported-`name` sequence is exactly
`first-pass-in-enumeration-order ++ adjustable-in-enumeration-order` =
`reported`: machine-confirmed 0 order violations in 40000 mixed-depth random
collections, and 0/20000 driving the REAL `_post_process` (not a stub) with only
storage I/O replaced. Under the previously documented "paths iteration order"
reading the same fuzz shows 19252/30000 ORDER MISMATCHES — that reading was false,
and this row is the correction. The postcondition itself is *parametric* in the
enumeration order (it constrains which files are reported and how often, relative
to the order the streams present them), so binding `ids` to the real enumeration
order realigns the abstraction without weakening the contract.
`conformance_check.py` and `axiom_check.py` both drive the REAL depth-sorted
traversal over MIXED-DEPTH names, so the ordering is actually exercised (an
earlier revision used same-depth pools like `f0..f5`/`a,b,c`, on which the depth
sort is a no-op — which is why they were green while the order diverged).

**Where a failing file's report lands (load-bearing R-step, and the reason the
model routes each file with two INDEPENDENT tests rather than an if/else).** The
patch branches per QUADRUPLE, the model routes per FILE. `_post_process` can
produce two quadruples for one file in one pass: the `except ValueError as exc:`
arm yields `name, None, exc, False` (`storage.py:300-301`) and then execution
falls through to the terminal `yield name, hashed_name, processed, substitutions`
(`storage.py:332`). In the patched first pass the exception quadruple takes the
guard's `isinstance(processed, Exception)` disjunct and is YIELDED at that file's
enumeration position; the terminal quadruple for the same `name` takes the `else`
and is STORED. Aggregated per file, an adjustable failing file is therefore
reported twice — once in the first-pass segment and once in the settled segment —
which is exactly `first_pass_ids` ∋ id and `adj_ids` ∋ id, and exactly the `+1`
`failing_adj_count` contributes. In a repeat pass both quadruples are merely
stored, the terminal one last, so no repeat pass emits anything and the stored
value is the settled one.

**Unreachable flag combination (stated, not exploited).** Only an adjustable file
can fail: the substitution loop that can raise lives inside
`if name in adjustable_paths:` (`storage.py:291`), so `url_converter` is never
invoked for a plain file and a plain file's `processed` is never an `Exception`.
The precondition nevertheless admits `adj[k] == 0` with `err[k] != 0`. That
combination is unreachable under the bridge, and the model's value there
coincides with `err[k] == 0` (a plain file is in the first-pass segment either
way; `adj_ids` ignores `err`; `failing_adj_count` requires `adj[k] != 0`). So the
spec claims nothing about a state the callee can occupy, and it does not need a
precondition carve-out to stay faithful. `axiom_check.py` asserts this
explicitly: binding `err` to the raw error set and binding it to the reachable
subset give the same `reported`.

**Domain: the failure arm is IN, non-convergence is OUT.** The model covers the
**convergent** domain, with failing examinations INCLUDED. What remains outside is
one arm:
- **Non-convergence arm.** If substitutions never settle, `post_process` yields
  `('All', None, RuntimeError(...))` (`storage.py:253-254`). `'All'` is not a file
  identity, so the carrier has no counterpart for it, and `collect()`
  (`management/commands/collectstatic.py:129-134`) re-raises on it, aborting
  before anything further is recorded. This arm IS caller-observable — the
  PASS_TO_PASS test `test_import_loop`
  (`staticfiles_tests.test_storage.TestCollectionManifestStorage`) asserts that
  `call_command('collectstatic', ...)` raises `RuntimeError('Max post-process
  passes exceeded')` and that stderr carries `"Post-processing 'All' failed!"` —
  so it is not "unobservable and therefore free". It is out of the CARRIER, and
  what keeps it safe is a different argument: the gold patch does not touch it (it
  appears in `patch.diff` only as unchanged context), so it is preserved by
  construction under any refinement of the map in refinement.md §A, which grants
  no step over it. `axiom_check.py` pins that preservation EXECUTABLY rather than
  by prose alone: `check_nonconvergence_arm_out_of_domain` asserts the arm emits
  the sentinel, that the sentinel sits exactly BETWEEN the two modelled segments
  (both of which it leaves byte-equal to `first_pass_ids` and `adj_ids`, so the
  arm is purely additive on the modelled part of the stream), and that a
  `collect()`-faithful consumer aborts on it naming `'All'` — the three facts
  `test_import_loop` reads.

The earlier revision of this document ALSO placed the exception arm out of domain
and argued it was sound to omit because `collect()` raises before recording. That
argument covered only the F2P observable. It is not sound for the failure-path
PASS_TO_PASS observable, which asserts that `collect()` DOES raise — a routine
that never hands the failure over makes `collect()` not raise at all, and no
clause over a carrier that cannot see a failure can forbid that. Hence the `err`
stream: the arm is now in the carrier and in the postcondition.

**Per-file failure multiplicity (scope, stated).** `err[k]` is a flag, so a
failing file contributes exactly one first-pass report. In the repository a
file's examination runs one substitution per matching rewrite pattern
(`storage.py:294-301`), so a file whose content fails under several distinct
patterns emits one report per failure, at the same enumeration position. The
model abstracts that to one. This is sound at the observable: `collect()` stops at
the FIRST failure report (`collectstatic.py:134`), so later ones are never
consumed. `axiom_check.py` binds one rewrite pattern per file (so the counts agree
exactly) and additionally asserts, on every collection carrying a failure, that
the failure report PRECEDES that file's settled report in the real stream.

`str` is not indexed anywhere; file names are abstracted to integer identity
codes, so no `str`-indexing surface is touched (Nagini-safe).

## 3. Callee provenance (kind-A) — A-reference deep model of `post_process`

There is **no consumed axiom** (no `@ContractOnly` whose `Ensures` the proof
relies on). But the deep model `first_pass_ids` / `adj_ids` /
`failing_adj_count` / `reported` IS an **A-reference**: it is a deep model of the
function under change itself — `HashedFilesMixin.post_process` — not of an
unchanged callee. The changed operation is the control-flow restructuring of which
files `post_process` yields, how many times, and at which point a failing file is
handed over (selection/structure logic over `paths` / `adjustable_paths` / the
per-file outcome), modelled deeply by the front-recursive folds and the matching
impl loop.

Because the deep model abstracts a REAL repository generator, G-AX has a genuine
discriminating obligation: confirm the deep model is faithful to the patched
`post_process`'s yielded `name` sequence. `axiom_check.py` discharges it — it is
**NOT a null check**. It loads the REAL patched `post_process` AND the REAL
`_post_process` straight out of `django/contrib/staticfiles/storage.py` (stubbing
only the per-file storage I/O — `open`/`_save`/`exists`/`delete`/`hashed_name`/
`clean_name`/`hash_key`/`url_converter` — so both the depth-sorted traversal of
"Enumeration order" and the real `except ValueError as exc` arm are exercised
rather than replaced), drives them over boundary + exhaustive(files ≤ 5, all
adjustable-subsets) + fuzz MIXED-DEPTH collections **with and without failing
files**, and asserts the yielded `name` sequence equals `reported(ids, adj, err)`,
that its length is `len(ids) + failing_adj_count(ids, adj, err)`, and that on any
collection carrying a failure the failure report precedes that file's settled
report. Two guards refuse a vacuous suite:
`_assert_suite_exercises_depth_sort` fails if no collection is genuinely reordered
by the sort, and `_assert_suite_exercises_failures` fails if no collection
actually reaches the real `ValueError` site. Run against the PRE-patch source it
correctly FAILS (the pre-patch yields an adjustable name multiple times). This
matches `meta.json` `deep_model_references` (kind `A-reference`, `checked_by:
axiom_check.py`).

The unchanged helpers `post_process` calls (`self.hashed_name`,
`matches_patterns`, storage `_save`/`exists`/`delete`) are NOT axiomatized: they
only compute the per-file `hashed_name` VALUE, which influences neither which
`name` is reported nor how often. `self._post_process` is the ONE callee that
does, twice over — it fixes the enumeration ORDER, and it is where a failing
outcome is produced — so it is NOT stubbed; axiom_check.py runs the real one.
axiom_check.py supplies the remaining helpers as stubs, exercises the failure arm
IN-domain (asserting equality with `reported`, not divergence from it), and
exercises the one remaining out-of-domain arm (forced non-convergence), asserting
it emits the `'All'` sentinel and aborts the caller. So the A-reference check
validates the in-domain faithfulness and documents the scope of the abstraction.
