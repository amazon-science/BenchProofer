# RELAXED_LEAKAGE — sphinx-doc__sphinx-8721 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file). The identical disposition
pattern is already applied and green in
`benchmark-verified/sphinx-doc__sphinx-9673/{lean,velvet}`,
`benchmark-verified/django__django-14011/velvet` and
`benchmark-verified/django__django-15252/nagini`.

## The mismatch

The gold patch (`sphinx/ext/viewcode.py` @ base 82ef497a8c) inserts TWO
early-return guards into `collect_pages`:

```python
+    if app.builder.name == "singlehtml":
+        return
+    if app.builder.name.startswith("epub") and not env.config.viewcode_enable_epub:
+        return
```

The solver-visible `problem_statement` describes ONLY the second (e-book)
behavior: its title is "viewcode creates pages for epub even if
`viewcode_enable_epub=False` on `make html epub`", and its whole body is that
scenario. Token scan of the `problem_statement` (case-insensitive,
re-verified): `singlehtml` = 0, `single` = 0, `combined` = 0. `hints_text`
is EMPTY (`""`). The instance's tests exercise only the e-book clause
(F2P `test_viewcode_epub_default`, P2P `test_viewcode_epub_enabled`); no test
touches the first guard.

The leaking lines in this bundle's spec view (frozen pure region of
`Solution.lean`): the `isCombinedFormat` definition (the exact builder-name
literal `"singlehtml"`), its disjunct in `shouldSuppress`, the corresponding
clause of `collectedPages`, and the second `ensures` of `gatedPageEmission`
that folds `isCombinedFormat` into the required suppression predicate. A
reader of the spec view alone is handed the first inserted guard — behavior
the public issue never states. The recorded G-PANEL-3 LEAKAGE finding is
factually correct about the leak's existence; this file dispositions it.

## Why the leak is unavoidable

A faithful spec of the patched gating decision MUST pin the
combined-document clause; a non-leaking spec cannot. Both horns were
actually exercised in this bundle's history:

1. **Omit the clause ⇒ unfaithful.** The migrated original of this bundle
   modeled the e-book guard only, relegating the first guard to a prose
   "modeled scope" note in mapping.md and excluding the name from the
   conformance corpus. The unified pipeline's faithfulness audit rejected
   exactly that (recorded triage, this repo,
   `experiments/triage/problems.tsv`): on input `fmt="singlehtml"`,
   `hasModules=True` (either opt-in value) the model's output is `generated`
   (emit) while the REAL patched `collect_pages` returns early and emits
   nothing — a concrete model↔repo divergence. `fmt` is a free input of the
   modeled function, so the divergent point is squarely inside the modeled
   domain; a prose scope note does not remove it.
2. **Restrict the domain ⇒ the same leak.** Excluding the divergent point
   with a `require` (or any domain predicate) needs a predicate that is true
   exactly away from the combined-document format — i.e. the predicate
   itself names the discriminator the problem_statement never states. There
   is no public vocabulary from which that predicate is derivable: the
   solver-visible text names only the e-book scenario.

So a spec derivable from the `problem_statement` alone could model only the
e-book clause and is provably unfaithful to the patched function at
`fmt="singlehtml"`; a faithful spec provably discloses the first guard.
Faithful + non-leaking is impossible here — the definition of a
`problem_statement ↔ gold` mismatch. The surrounding prose is already
de-narrated (abstract "single combined-document format" wording, no repo
file/function names, no diff narration); the residual leak is the behavior
itself plus the one exact-name literal an exact-equality test cannot avoid.

## Core soundness is intact (recorded stamps of THIS bundle, 2026-08-05 run)

- **G-GOLD / verify: pass** — `Solution.lean` verifies (lean_verify.sh
  exit 0; re-confirmed 2026-08-06).
- **G-DIFF: pass** — `Solution_prepatch.lean` (neither inserted guard;
  genuine pre-patch behavior) fails on the discriminating
  `out = collectedPages ...` goal (unsolved `generated = collectedPages fmt
  ebookOptIn hasModules generated`); `same_spec(Solution, prepatch) = True`
  (spec regions byte-identical; re-confirmed 2026-08-06).
- **G-EQ: pass (TIGHT)** — 7 attacks re-run, none breaks the spec; positive
  control verifies.
- **G-PANEL-1: pass (TIGHT)** — 7 wrong impls rejected; positive control
  verifies.
- **G-PANEL-2: FAITHFUL** — auditor's independent differential (patched
  worktree, monkeypatched sentinel, 116 cases over adversarial builder
  names × opt-in × has-modules): 0 disagreements vs the real patched
  `collect_pages`.
- **G-CONF: pass** — R/I shadow agrees with `patch.diff` behavior
  (emit-vs-suppress) on 100,018 inputs (seed 8721), 0 disagreements.
- **G-MUT: 1/1 killed. G-HYGIENE / G-INTEGRITY: pass. G-RESOLVE:**
  `patch.diff` is the gold patch verbatim.

Only the secondary no-leakage property is relaxed, for this one documented
facet (the combined-document-format suppression clause of `shouldSuppress` /
`isCombinedFormat`). The "verify ⇒ resolved" guarantee is unaffected.
