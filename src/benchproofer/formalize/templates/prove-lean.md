## How these proofs usually go

For an implementation written as `Id.run do let mut acc := init; for x in xs do acc := upd;
return acc`:

* **Plain accumulation** (no branch in the loop body): `unfold` the implementation and
  `simp [List.range_eq_range']` reduces the loop to a `List.foldl` or a `Finset.range` fold;
  finish with the closed-form lemma. `simp` already knows how `Std.Range.forIn`, `Id.run`
  and `mut` desugar -- do not cite those lemmas by name.
* **A conditional loop body** (the general case):
  1. State a helper lemma about the cleaned `forIn` form, generalized over the accumulator:
     `Id.run (forIn xs init (fun x r => if cond then .yield … else .yield …)) = <foldl spec>`.
  2. Prove it by `induction xs generalizing init with | nil => rfl | cons a as ih => rw
     [List.forIn_cons]; simp only [Id.run, bind] at ih ⊢; by_cases h : cond <;> simp only
     [h, if_true, if_false, ih]`.
  3. In the claim, rewrite the desugared body (`do pure PUnit.unit; pure (ForInStep.yield
     …)`) into the helper's clean body with `have h2 : … = … := rfl`, then `rw [h2,
     helper]`. Strip an early-`return` guard with `simp only [Id.run, h, if_false]`.
* `simp only [Id.run]; trace_state` prints the exact desugared goal, which is what the
  `rfl` step has to match.

Lemmas that exist here: `List.forIn_cons`, `List.forIn_nil`, `List.foldl_cons`,
`List.filter_cons`, `List.range_succ`, `List.range_eq_range'`, `List.sum_append`,
`List.sum_eq_foldl`, `List.length_cons`, `Finset.sum_range_succ`,
`Finset.sum_range_id_mul_two`, `List.mem_cons`, `List.mem_cons_self`,
`List.mem_cons_of_mem`, `List.not_mem_nil`. Names that do not: `List.forIn_eq_foldl`,
`List.foldl_eq_sum`, `range'_eq_range`; `Id.bind_eq` and `Id.pure_eq` are deprecated in
favor of `Id.run_bind` and `Id.run_pure`.
