# refinement.md — scikit-learn__scikit-learn-26323

Operation-by-operation correspondence between `implementation_setOutput`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `set_output` body in
`ColumnTransformer`). Tags: **R** type refinement, **A-consumed** proof uses an
axiom, **A-reference** deep model validated == real callee, **I** identical
concrete op.

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `let mut outTransformers := []` | initialize the (implicit) per-child iteration over the contained transformers | I |
| 2 | `for trans in transformers do outTransformers := … ++ [setOutput transform trans]` | `for trans in transformers: _safe_set_output(trans, transform=transform)` — apply the chosen container to each contained transformer (sentinels untouched) | R |
| 3 | `let outRemainder := setOutput transform remainder` | `if self.remainder not in {"passthrough", "drop"}: _safe_set_output(self.remainder, transform=transform)` — **the added lines (the fix)**; the sentinel guard is subsumed by `setOutput` being a no-op on a sentinel (same coincidence as op 2's membership filter) | R |
| 4 | `return (outTransformers, outRemainder)` | `return self` (the configured composite: contained transformers + remainder) | I |

Notes:

- **Every step is R or I — no A.** Applying the output container to one
  transformer (`_safe_set_output`) is modeled DEEPLY by the pure helper
  `setOutput`: an estimator records the new container value, a reserved sentinel
  (`passthrough`/`drop`) carries no configuration and is returned unchanged. Per
  SPEC_GUIDE §3 a deeply-modeled changed op is NOT axiomatized; the `axioms`
  region is empty and **G-AX skips**.
- **R on op 2**: the contained collection is the patch's `chain(self.transformers,
  getattr(self, "transformers_", []))` flattened to the `trans` elements with the
  two reserved sentinels still present. The membership filter `if trans not in
  {"passthrough","drop"}` in the generator and the `setOutput` no-op on a sentinel
  coincide: applying `setOutput` to a sentinel returns it unchanged, exactly as
  skipping `_safe_set_output` on a filtered-out sentinel would. The collection
  itself (built upstream from the constructor args and fit bookkeeping) is
  orthogonal to the fix and enters as the grounded input `transformers : List
  Transformer`.
- **R on op 3 is the fix.** Pre-patch, `set_output` propagates the container only
  to the contained transformers; the fall-back `remainder` estimator is never
  configured. Post-patch adds `if self.remainder not in {"passthrough","drop"}:
  _safe_set_output(self.remainder, transform=transform)`. The Lean impl applies
  `setOutput transform remainder` directly: the real `if` guard is subsumed by
  `setOutput` being a no-op on a sentinel — exactly the same coincidence that
  subsumes op 2's membership filter — so the guarded and unguarded forms are
  extensionally equal. (An earlier revision mirrored the guard line-for-line;
  since the spec is functional, both forms verify, and the guardless form makes
  plain that a guarded same-spec variant is a positive control, not a
  spec-too-weak witness.) G-CONF diffs this guardless shadow against the
  guarded post-patch oracle, mechanically confirming the subsumption.
- **The discriminating clause** is `result.2 = setOutput transform remainder`. The
  pre-patch impl (`Solution_prepatch.lean`) returns `outRemainder = remainder`
  unconfigured; when `remainder = est id output` with `output ≠ transform`, this
  differs from `setOutput transform remainder = est id transform`, so the prepatch
  `correct_setOutput` is unprovable on that clause. This is exactly the bug the
  issue reports (the remainder estimator's output container is ignored) and what
  the F2P test `test_remainder_set_output` observes.
- **Directive 5 (frame):** both output components are pinned to the inputs —
  `result.1` to `transformers.map (setOutput transform)` and `result.2` to
  `setOutput transform remainder`. No output component is left free.
- **G-CONF** mechanically refutes the R/I legs (no A legs): the Python shadow of
  the impl is diffed against an in-process replica of the POST-PATCH `set_output`
  behavior over ≥1e5 fuzzed inputs.
