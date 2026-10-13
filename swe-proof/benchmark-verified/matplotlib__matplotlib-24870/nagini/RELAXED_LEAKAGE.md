# RELAXED-LEAKAGE ACCEPTANCE: matplotlib__matplotlib-24870

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision
2026-06-14).** This instance is a `problem_statement <-> gold` MISMATCH on its
SECOND facet: the gold has two coupled behaviours for a boolean (two-valued)
field with no explicit levels —

  * a LINE contour defaults to a single level at the midpoint (`[.5]`), and
  * a FILLED contour defaults to the three bracketing levels (`[0, .5, 1]`).

The LINE facet is fully PUBLIC — the `problem_statement` literally shows
`plt.contour(boolean_2d_array, levels=[.5])` and says "the only choice that
makes sense is to have a single level at 0.5". The FILLED facet's discriminating
vocabulary (`contourf`, the three-level list `[0, .5, 1]`, the "Filled contours
require at least 2 levels" rule) lives ONLY in `hints_text` / the gold internals
/ the hidden `test_patch`, NEVER in the solver-visible `problem_statement`. The
F2P `test_bool_autolevel` asserts BOTH facets (`plt.contourf(z).levels.tolist()
== [0, .5, 1]` for all four filled forms), so a *faithful* spec MUST pin the
filled three-level behaviour, which only a hints/gold-derived spec can. The
verification CORE is fully SOUND (G-VERIFY/G-DIFF/G-EQ/G-AX/faithfulness clean,
G-RESOLVE resolves), so this is a relaxed-leak, not a defect-in-spec.

Per the project's relaxed-leakage policy (see RELAXED_LEAKAGE.md), such
PS<->gold-mismatch instances are KEPT in the verified set with the
hints/gold-derived discriminator allowed in the spec view, rather than excluded.
The "verify => correct" guarantee is UNAFFECTED (the core is sound and the gold
resolves); only the no-leakage property is relaxed, and only for the FILLED
facet (the line facet is public and does not leak).

---

## Why the FILLED leak is genuinely unavoidable (not lazy de-narration)

The behaviour the gold actually fixes for `contourf` — and that the F2P test
measures — IS the leaked discriminator. There is no way to pin it without naming
the three-level / "at least two levels" filled default.

### The gold special-cases the filled two-valued default

Gold patch (`lib/matplotlib/contour.py`, the `self.levels is None` block):

```python
if args:
    levels_arg = args[0]
elif np.issubdtype(z_dtype, bool):
    if self.filled:
        levels_arg = [0, .5, 1]     # <-- the filled facet
    else:
        levels_arg = [.5]           # <-- the line facet (PUBLIC)
else:
    levels_arg = 7  # Default, hard-wired.
```

The line facet (`[.5]`) is exactly what the public issue requests. The filled
facet (`[0, .5, 1]`) exists because `contourf(bool_array)` without it raises
"Filled contours require at least 2 levels" — a constraint stated ONLY in the
hints. The F2P test pins it: `plt.contourf(z).levels.tolist() == [0, .5, 1]`.

### The filled discriminator is absent from the solver-visible problem_statement

Token check against `problem_statement` (solver-visible) vs. `hints_text` /
`test_patch` (never shown to the consumer):

| token / concept                    | problem_statement | hints_text | test_patch |
|------------------------------------|:-----------------:|:----------:|:----------:|
| `contourf`                         | absent            | present    | present    |
| `[0, .5, 1]` (filled levels)       | absent            | present    | present    |
| "Filled" / "at least 2 levels"     | absent            | present    | absent     |
| `levels=[.5]` / `[.5]` (line)      | present           | absent     | present    |
| `.5` (the single level)            | present           | present    | present    |
| `bool` / boolean field             | present           | present    | present    |
| `np.issubdtype`                    | absent            | absent     | absent     |
| `_process_contour_level_args`      | absent            | absent     | absent     |
| `z_dtype` / `dtype`                | absent            | absent     | absent     |

The `problem_statement` is an [ENH] asking only to autodetect bool arrays and
default the LINE contour to `[0.5]`. It never mentions `contourf`/filled, the
three-level list, or the "at least two levels" rule. The hint adds the second
facet ("I tried your code with `contourf()`, but that raises 'Filled contours
require at least 2 levels'. ... the natural levels would be `[0, .5, 1]`").

### Any faithful, G-DIFF-failing spec must name the filled facet

The model's spec view discloses, in its docstring (model.py lines 24-26), "for a
filled contour: the three levels `[zmin, midpoint, zmax]` ... a filled contour
requires at least two levels", and the post-conditions pin
`Implies(two_valued and filled, len(Result()) == 3)` /
`Result()[0] == zmin and Result()[2] == zmax` / `len(Result()) >= 2`. These are
load-bearing: the F2P test checks `plt.contourf(z).levels.tolist() == [0, .5, 1]`
for all four filled forms; dropping them lets a wrong `contourf` impl verify.
There is no `problem_statement`-derivable reformulation of the filled facet
because the public issue is about the LINE case only. The behaviour itself is
the leak — a genuine PS<->gold mismatch on the second (filled) facet, not lazy
docstring narration.

Note: the spec view correctly still avoids the patched path/symbol names
(`_process_contour_level_args`, `np.issubdtype`, `z_dtype`, `contour.py`) — model
identifiers (`choose_default_levels`, `two_valued`, `filled`, `mid`) describe
behaviour, not the edit. Only the unavoidable filled-facet behaviour (three
levels / "at least two levels") is disclosed, and that is the tested behaviour.

## Re-verify snapshot (soundness intact — this is a relaxed-leak, not a defect-in-spec)

- G-VERIFY: PASS — `model.py` verifies with `--float-encoding=real`, ~40s < 300s.
- G-DIFF: PASS — `model_prepatch.py` (the always-multi-level prepatch) FAILS on
  the postcondition `Implies(two_valued and not filled, len(Result()) == 1)`.
  same_spec=True.
- same_spec: TRUE — axioms/pure/pre-conditions/post-conditions byte-identical
  between `model.py` and `model_prepatch.py`; only `impl` differs.
- Static gates (G-INTEGRITY / G-HYGIENE / mechanical G-LEAK): pass. The
  mechanical G-LEAK screen is lexical and blind to this semantic facet leak; the
  adversarial reconstruction (G-PANEL attacker 3) is the binding judgment and it
  confirms the filled facet leak is real but unavoidable.
- G-AX: A-consumed axiom `auto_levels` (len>1 on a WELL-RESOLVED range). After
  refinement the axiom is scoped to the well-resolved regime (the real selection
  collapses to a single tick at unresolvable ranges, e.g. `(1e-300,2e-300) ->
  [1e-300]`, measured in the 3.6 image); `axiom_check.py` runs RC=0 in the
  canonical 3.6 eval image: every well-resolved boundary/fuzz range gives >1
  level and the collapse witnesses are correctly guard-excluded.

## Conclusion

No prescribed code fix exists for the leakage axis (the filled facet's tested
behaviour is itself the leak). Per the relaxed-leakage policy the correct action
is to KEEP this instance in the verified set with the leak documented and
`meta.json gates.G-LEAK.status = "relaxed"`. The `verify => correct` guarantee is
fully intact.
