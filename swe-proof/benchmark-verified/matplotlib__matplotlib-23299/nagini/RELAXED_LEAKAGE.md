# RELAXED-LEAKAGE ACCEPTANCE: matplotlib__matplotlib-23299

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision
2026-06-14).** `meta.json` records the top-level `relaxed_leakage: true` flag,
which (with this file present) makes the G-LEAK gate record
`status = "relaxed"` (`src/swebench_unified/gates/leak.py`). In this unified
repo the policy lives in the binding spec-construction rules,
`prompts/nagini/spec_guide.md` directive 6 ("**Exception — relaxed-leakage:**
... for a proven `problem_statement <-> gold` mismatch where the gold's tested
discriminator exists only in `hints_text`/gold internals, so a *faithful* spec
MUST name it ... KEEP the instance with the leak allowed"). (The
`RELAXED_LEAKAGE.md` cited by an earlier revision of this file was a
source-repo-only doc that does not exist here.)

## Why this is not a code fix (the leak is the behavior, not narration)

The soundness axes are clean and were re-verified here (see "Re-verify snapshot"
below) — the bundle is *sound*. The mechanical G-LEAK screen also passes (no
diff line, no patched path `lib/matplotlib/__init__.py`, no patched symbol
`rc_context`/`rcParams`, no surface bug->fix narration). The relaxation is
needed because the **semantic** discriminator the spec must pin to be faithful
is itself absent from the public issue and present only in `hints_text`/gold.

### The gold took a deeper angle than the public symptom report

Gold patch (`lib/matplotlib/__init__.py`, the `rc_context` snapshot site):

```python
-    orig = rcParams.copy()
+    orig = dict(rcParams.copy())
+    del orig['backend']
     try:
         ...                       # body: yield (+ rc_file / rcParams.update(rc))
     finally:
         dict.update(rcParams, orig)   # revert the snapshot
```

The discriminator is **the distinguished `'backend'` key being removed from the
revert snapshot**, so a backend value resolved inside the context survives the
exit-time `dict.update` revert instead of being overwritten with the stale
entry sentinel.

### That discriminator is absent from the solver-visible problem_statement

- The `problem_statement` frames the ENTIRE defect as a SYMPTOM:
  "`get_backend()` clears figures from `Gcf.figs` if they were created under
  `rc_context`." Token check (case-insensitive over the PS): `rc_context`,
  `get_backend`, `Gcf` all appear in `problem_statement` (the symptom surface).
- The gold's actual trigger vocabulary does NOT appear in `problem_statement`:
  `revert`=absent, `restore`=absent, `preserve`=absent, `survive`=absent,
  `snapshot`=absent, `reset`=absent, `copy`=absent, `del`=absent,
  `re-resolve`=absent, `sentinel`=absent. None of the snapshot/revert mechanism
  is in the public issue.
- The diagnosis IS in `hints_text` (the consumer never sees it): "the
  `rcParams['backend']` in the auto-sentinel … is stashed by rc_context … the
  context manager sets it back to the sentinel on the way out … `get_backend()`
  re-resolves the backend." `re-resolve` and `sentinel` are `hints_text`-only.
- A `problem_statement`-only solver sees a `Gcf.figs`/`get_backend` symptom and
  would reach for the figure-manager / backend-resolution path, never for the
  `rc_context` snapshot exclusion that the gold actually edits.

### Any faithful spec must pin the leaked discriminator

To satisfy G-DIFF / G-EQ / faithfulness, `model.py` must pin the gold's actual
behavior: the distinguished key's body-set value SURVIVES the context exit
(`params[key_resolved()] == new_resolved`) while ordinary keys are REVERTED
(`params[key_other()] == entry_other`). That survive-vs-revert behavior IS the
gold's tested discriminator (F2P `test_no_backend_reset_rccontext`): the test
sets `rcParams['backend']` inside `rc_context()` and asserts it is unchanged
after exit. There is no PS-derivable (`Gcf.figs`/`get_backend`-symptom)
reformulation that still models the gold fix, because the gold fix is the
snapshot-revert change, not a `Gcf`/figure-manager change. The prepatch (which
keeps `'backend'` in the snapshot and reverts it) FAILS exactly this clause —
proving the discriminator is load-bearing and unavoidable.

## Re-verify snapshot (soundness intact — this is a relaxation, not a defect-in-spec)

- G-VERIFY: PASS — `model.py` verifies, 19.68s, no flags (< 300s).
- G-DIFF: PASS — `model_prepatch.py` FAILS at `model_prepatch.py:97:13`
  (`Postcondition ... Assertion (params[key_resolved()] == new_resolved) might
  not hold`), the named counterexample (prepatch keeps the distinguished key in
  the snapshot and reverts it on exit, so the body-set value does not survive).
- same_spec: TRUE — spec regions (axioms/pure/pre/post) AND the module docstring
  are byte-identical between `model.py` and `model_prepatch.py`; only `impl`
  differs.
- Static gates (G-INTEGRITY / G-HYGIENE / G-LEAK-mechanical): pass.
- G-AX: legitimately vacuous (zero `@ContractOnly` axioms; the snapshot/drop/
  revert is modeled deeply over a real `Dict[int,int]`; the CPython dict
  primitives are an A-reference validated by `axiom_check.py`). RC=0.
- G-RESOLVE: `patch.diff` == gold verbatim (646 B), applies at `base_commit`;
  resolves F2P `test_no_backend_reset_rccontext` + P2P. Docker oracle by
  orchestrator.

The mechanical G-LEAK screen passes (no diff lines/paths/narration), but it is
lexical and blind to this semantic PS<->gold-mismatch leak; the adversarial
mismatch reconstruction above (G-PANEL attacker 3) independently re-verifies
the disposition. Per the panel recording convention above, its honest
recording for this properly-dispositioned facet is NO-LEAKAGE (pass) + note;
LEAKAGE is reserved for a NEW leak beyond the facet or a broken disposition.

## Conclusion

No prescribed *code* fix exists for the leakage axis: the bundle cannot be made
both faithful and PS-only-non-leaking, because the public task text (a
`Gcf.figs`/`get_backend` symptom) and the gold fix (the `rcParams` snapshot
exclusion of `'backend'`) are about different things. Per the relaxed-leakage
policy this instance is KEPT in the verified set: `meta.json` carries the
top-level `relaxed_leakage: true` flag (so the G-LEAK gate records status
`"relaxed"`), with this file as the recorded rationale. The verification core
is sound and the gold resolves, so `verify => correct` is unaffected; only the
secondary no-leakage property is relaxed for this documented instance.
