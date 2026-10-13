# refinement.md — django__django-15277

The operation-by-operation correspondence between `model.py`'s implementation
(the `build_char_validators` impl, the deep `compare_length` model, and the
end-to-end `clean_charfield` impl) and `patch.diff` (the gold patch). Each step
is tagged **R** (type refinement), **A** (axiomatized callee — split into
**A-consumed**, where the proof uses an axiom's `Ensures`, and **A-reference**,
where a deep model is validated == the real callee by axiom_check.py / G-AX),
or **I** (identical concrete operation). The claim: *any implementation that
verifies against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## The change site — `CharField.__init__` (`django/db/models/fields/__init__.py:1010-1013`)

Gold hunk:
```python
-        self.validators.append(validators.MaxLengthValidator(self.max_length))
+        if self.max_length is not None:
+            self.validators.append(validators.MaxLengthValidator(self.max_length))
```

| # | model.py impl op (`build_char_validators`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| 1 | parameter `max_length: Optional[int]` | `self.max_length` (an `int` or `None`) | R | `Optional[int]` ↔ field `max_length` (mapping.md §2): positive `int` ↔ `int`, `None` ↔ `None`. |
| 2 | `validators = []` (the list being assembled) | `self.validators` (the field's validator list, before the append) — specifically its length-validator slot | R | the model abstracts the validator list to the `List[Optional[int]]` of its `MaxLengthValidator` limits; the other (default) validators are unchanged by the patch and unobserved (mapping.md §2). |
| 3 | `if max_length is not None:` | `if self.max_length is not None:` | I | identical concrete guard on `None`. |
| 4 | `validators.append(max_length)` | `self.validators.append(validators.MaxLengthValidator(self.max_length))` | R + A-reference | constructing a `MaxLengthValidator(max_length)` ↔ appending its sole behaviour-relevant datum, the limit `max_length` (R, mapping.md §2). That the appended validator's behaviour is fully captured by its limit — it compares `len(value) > limit` and is undefined on `None` — is the A-reference validated by G-AX against the real `MaxLengthValidator` (refinement step 5 / mapping.md §3.1). |
| 5 | (deep model) `compare_length(value_length, limit)` returns `value_length > limit`, undefined (raises `LimitComparisonError`) when `limit is None` | `MaxLengthValidator.compare(a, b)` returns `a > b`, raising `TypeError` when `b is None` (`validators.py:390-391`, run via `BaseValidator.__call__`) | A-reference | the changed operation's *consequence* — the length comparison — is modeled **deeply** (spelled out as `value_length > limit` with a `None`-raise), NOT behind a consumed axiom. G-AX asserts `v.compare(a,b) == (a > b)` over fuzz and that `MaxLengthValidator(None)` raises `TypeError` on a comparison (mapping.md §3.1). `LimitComparisonError` ↔ that `TypeError` (R: user-defined exception, builtin `Exsures` is banned, mapping.md §2). |
| 6 | (end-to-end) `clean_charfield` builds the list then runs each comparison in a loop; no `Exsures` ⇒ provably never raises | `Field.clean` → `run_validators` → each `MaxLengthValidator.__call__` (`fields/__init__.py:664-673,617-631`) | R + A-reference | running the assembled validators ↔ the loop over assembled limits (R). `run_validators` swallows only `ValidationError` (`:625`), so the broken comparison's `TypeError` would propagate out of `clean` exactly as the model's un-caught `LimitComparisonError` does (mapping.md §3.3); G-AX confirms the real `CharField().clean(...)` returns normally post-patch. |

The discriminating content of the change — assembling NO length validator when
`max_length is None`, so no later comparison meets an absent limit — lives in
the guard (step 3) and is observed by `build_char_validators`'s postcondition
`Forall k. Result()[k] is not None` together with
`Implies(max_length is None, len(Result()) == 0)`. The pre-patch code drops the
guard (`model_prepatch.py`: `validators.append(max_length)` unconditionally), so
when `max_length is None` the assembled list carries a `None` limit; the
postcondition `Forall k. Result()[k] is not None` then **fails** — exactly the
spec sensing the change (G-DIFF). Downstream this is the `TypeError` the F2P
test (`test_output_field_does_not_create_broken_validators`) observes: with the
guard, `clean_charfield` is provably non-raising; without it, the `None` limit
reaches `compare_length`, which raises.

## verify(model) ⇒ resolved

`build_char_validators` verifies only if it assembles no `None`-limit validator
AND preserves the validator when a maximum is supplied (steps 3-4, posts); by R
(`Optional[int]` ↔ `max_length`, validator ↔ its limit) this is exactly the
gold-patched assembly statement. `clean_charfield` verifies only if running the
assembled validators provably never raises (step 6) — the F2P behaviour. The
deep model `compare_length` is validated == the real `MaxLengthValidator`
comparison by G-AX (A-reference, step 5), and the assembled-list shape and the
non-raising `clean` are validated against the real `CharField` by G-AX
(mapping.md §3.2-3.3). Therefore a model satisfying this spec, refined by the
map above, is the gold patch up to type refinement and audited callees — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN
§1.1: axiom soundness (here, A-reference soundness — G-AX) and refinement
fidelity (this document — G-EQ).

## No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. There is no consumed `@ContractOnly`
axiom: the changed operation (the guarded assembly and its length-comparison
consequence) is modeled **deeply**, not hidden behind an axiom about the
function under change. The real `MaxLengthValidator` / `CharField` appear only
as the **A-references** that G-AX validates the deep model against.
