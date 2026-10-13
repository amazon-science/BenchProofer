# mapping.md — django__django-14493

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 7272e1963ffdf39c1d4fe225d5425a45dd095d11`, states the type
abstraction, and records that this bundle relies on NO axiomatized library
callee.

Repo file under change: `django/contrib/staticfiles/storage.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `run_passes(pass_changed, max_passes)` | `HashedFilesMixin.post_process(self, paths, dry_run=False, **options)` — `django/contrib/staticfiles/storage.py:224`; specifically the pass loop + post-loop flag read at lines 263-275 | the modeled changed function: the refinement-pass loop whose post-loop flag must be defined for every pass count, including zero |
| `max_passes` (param) | `self.max_post_process_passes` — class attribute default `5` (`storage.py:46`); the issue sets it to `0` in a subclass | the configurable pass count `range(self.max_post_process_passes)` iterates over |
| `pass_changed` (param, `List[int]`) | the per-pass aggregate of the inner generator `self._post_process(...)`'s `subst` outputs: `substitutions = substitutions or subst` over one pass (`storage.py:266-269`) | read-only per-pass change/no-change outcomes; `pass_changed[i] != 0` ⇔ pass i produced at least one substitution |
| `substitutions` (local) | `substitutions` local in `post_process` (`storage.py:265` inside the loop; the patch adds the pre-loop init at the new line) | the boolean flag consulted by `if substitutions:` after the loop (`storage.py:274`) |
| `all_changed(flags, n)` *(deep model — pure)* | the loop's net effect on `substitutions`: True iff ≥1 pass ran and every pass that ran reported a change (the loop breaks the first time a pass reports none) | pure spec of the post-loop flag value; modeled deeply, NOT axiomatized |
| `lemma_unfold`, `lemma_change_free_kills` | (proof-only lemma methods) | discharge the one-step unfold and the change-free-kills-the-prefix facts about `all_changed`; no repo counterpart |

The post-loop consumer is `if substitutions:` (`storage.py:274`), which yields the
`RuntimeError('Max post-process passes exceeded.')` sentinel when the flag is
True. Modeling the loop's exact post-loop flag value (`all_changed`) pins both
the well-definedness (the bug) and the value the consumer reads.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `range(self.max_post_process_passes)` iterating a non-negative count | `max_passes: int` with `0 <= max_passes <= len(pass_changed)` | `i` ranges over `[0, max_passes)` identically; the zero-pass case `max_post_process_passes == 0` ⇔ `max_passes == 0` |
| the inner generator `self._post_process(paths, …)` yielding `(name, hashed_name, processed, subst)` quadruples, aggregated per pass by `substitutions = substitutions or subst` | one read-only flag `pass_changed[i] ∈ {0,1}` per pass i | `pass_changed[i] != 0` ⇔ "pass i produced at least one substitution" (the OR of that pass's `subst` values). The inner per-file work is irrelevant to the bug — only the per-pass aggregate boolean reaches the post-loop read. |
| `substitutions` Python bool | model `bool` local | identity |
| early `break` when `not substitutions` (`storage.py:271-272`) | the loop's `if not substitutions: return False` | identical control flow: once a pass reports no change the loop stops and the post-loop flag is False |

The carrier `List[int]` (with the specification phrased over `PSeq[int]` via
`ToSeq`) is used because the abstract per-pass outcomes are a fixed sequence the
loop scans; `List[bool]` would serve equally but `List[int]`/`PSeq[int]` is the
project's standard sequence carrier.

## 3. Axiom / callee provenance

**None.** This bundle declares no `@ContractOnly` axiom and no A-reference deep
model of an external library callee. The changed behaviour is purely the
definite-assignment + early-stop semantics of an in-function loop, modeled
deeply by `all_changed` and the verified `run_passes`. The post-loop read
`if substitutions:` and the loop body call no library function whose contract
the proof must assume.

`axiom_check.py` therefore performs the FAITHFULNESS check that corresponds to
G-AX for a deep model: it executes a byte-faithful reference of the real
`post_process` pass loop (post-patch, with the pre-loop initialisation) and
asserts model.py's closed form `all_changed`/`run_passes` equals the real
post-loop `substitutions` value over exhaustive small + boundary + 50000
randomized cases, and that the pre-patch loop (no initialisation) raises
`UnboundLocalError` exactly when `max_post_process_passes == 0`. stdlib-only.
