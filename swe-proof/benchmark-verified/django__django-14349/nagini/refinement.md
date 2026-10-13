# refinement.md — django__django-14349

The operation-by-operation correspondence between `model.py`'s implementation
(the `validate_url` impl region plus the live `downstream_validate` axiom) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — split into **A-consumed**, where the proof uses the
axiom's `Ensures`/`Exsures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold patch
on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

The patch edits `URLValidator` in `django/core/validators.py`: it adds a class
attribute and inserts one early rejection at the top of `__call__`.

Gold hunks:
```
@@ class URLValidator(RegexValidator):
     schemes = ['http', 'https', 'ftp', 'ftps']
+    unsafe_chars = frozenset('\t\r\n')

@@ def __call__(self, value):
         if not isinstance(value, str):
             raise ValidationError(self.message, code=self.code, params={'value': value})
+        if self.unsafe_chars.intersection(value):
+            raise ValidationError(self.message, code=self.code, params={'value': value})
         # Check if the scheme is valid.
         scheme = value.split('://')[0].lower()
         ...
```

## A. The forbidden-character screen — `URLValidator.__call__` (`validators.py:101`)

| # | model.py impl op (`validate_url`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value: List[int]` | `value` argument of `__call__` (a `str`) | R | `str` ↔ `List[int]` of code points (mapping.md §2). `str` indexing is banned in Nagini; the loop reads `value[i]` ↔ the i-th code point. |
| A2 | the `while i < len(value)` loop testing `is_forbidden(value[i])` | `if self.unsafe_chars.intersection(value):` with `unsafe_chars = frozenset('\t\r\n')` | R + I | `frozenset('\t\r\n').intersection(value)` is truthy ⟺ some character of `value` is in `{TAB,LF,CR}` ⟺ `Exists k. is_forbidden(value[k])` with `is_forbidden(c) ≡ c∈{9,10,13}` (mapping.md §2). The explicit scan over code points is the type-refined spelling of the set-intersection membership test; the decision (found-or-not) is the identical concrete branch. |
| A3 | `raise InvalidValue()` on a found forbidden code point | `raise ValidationError(self.message, code=self.code, params={'value': value})` | R | `InvalidValue` ↔ `ValidationError` (mapping.md §2: user-defined exception stands in for the builtin-carrying error; only the raise/no-raise control flow is observed). The message/code/params payload is not behaviour the F2P tests inspect (they assert `ValidationError` is raised). This raise is INDEPENDENT of `accepted` — exactly the patch's early, unconditional rejection. |
| A4 | `downstream_validate(accepted)` after the loop | the remainder of `__call__` (scheme check, `super().__call__`, IDN retry, IPv6 recheck) — byte-for-byte unchanged | A-consumed | `downstream_validate` is the weakest contract on the unchanged downstream chain the proof needs: normal completion ⇒ `accepted`, rejection ⇒ `Exsures(InvalidValue, not accepted)`. The proof consumes both clauses to discharge the screen's own postcondition on the no-forbidden-char path. G-AX confirms it against the real `URLValidator` downstream (mapping.md §3.1). The patch places this chain strictly AFTER the new check, so its operation and position are identical pre- and post-patch. |
| A5 | `Requires(MustTerminate(2))` on `validate_url` (consumed by the scan loop's decreasing measure `len(value) - i` and by `downstream_validate`'s own `Requires(MustTerminate(1))`) | `__call__` is a bounded, straight-line computation: the `intersection` membership test plus the downstream chain always deliver a verdict — return or raise, never diverge (every F2P/P2P test observes an answer) | I | a total-correctness obligation, not an operation: it pins the fact that the real `__call__` ANSWERS. Nagini is a partial-correctness verifier by default, so without it a same-spec impl that inserts an infinite loop (e.g. `while True: pass` after the screen — a real patch shape that hangs `test_validators` into the harness timeout and does NOT resolve) satisfies every `Ensures`/`Exsures` vacuously. The axiom's `MustTerminate(1)` states the unchanged downstream chain likewise always returns/raises (exercised on every axiom_check.py input), letting the deferral discharge the caller's obligation. |

The discriminating content of the change: the post-patch rejects a value that
carries any of TAB/LF/CR **before and independently of** the rest of validation,
so such a value is rejected even when the rest of validation would accept it.
That "even when otherwise accepted" case is precisely the bpo-43882 scenario the
issue reports: on Python with the bpo-43882 fix, `urlsplit` strips TAB/LF/CR, so
a URL like `http://www.django\rproject.com/` reaches the (unchanged) downstream
validation already stripped and is **accepted** there — yet it must be rejected.

`model_prepatch.py` reproduces the literal pre-patch body (no screen; straight
`downstream_validate(accepted)`) and **fails** verification on the normal-
completion postcondition
`Forall k. not is_forbidden(value[k])`: for an input with `Exists k. is_forbidden(value[k])`
AND `accepted == True`, the pre-patch returns normally instead of raising, which
the spec forbids. That is exactly the spec sensing the change (G-DIFF). The
verifier reports the failure on this clause
(`Postcondition of validate_url ... not is_forbidden(value[k]) might not hold`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A, or I. The operation that genuinely *changed* — the
addition of the forbidden-character screen — is modelled **directly** as the
explicit code-point scan + early raise (A1–A3), a refinement of the
`frozenset('\t\r\n').intersection(value)` membership test, NOT hidden behind an
axiom about the function under change. The only consumed axiom,
`downstream_validate` (**A-consumed**), covers the **unchanged** downstream
validation chain the new code still defers to — never the operation under
change. There is no **A-reference** deep model and no dead axiom: the axiom's
`Ensures`/`Exsures` are consumed by `validate_url`'s postcondition on the
no-forbidden-char path.

## C. verify(model) ⇒ resolved

`validate_url` verifies only if (a) it raises on EVERY value carrying a forbidden
code point, independent of `accepted` (A1–A3) — so a value the downstream would
accept is still rejected — and (b) on a forbidden-char-free value it defers
exactly to the downstream verdict (A4). By R (`str` ↔ `List[int]`,
`intersection` truthiness ↔ the existential, `ValidationError` ↔ `InvalidValue`)
the verified screen equals the gold
`if self.unsafe_chars.intersection(value): raise ValidationError(...)` placed
before the unchanged validation; by G-AX the real downstream `URLValidator`
meets the `downstream_validate` axiom (A-consumed). Therefore a model satisfying
this spec, refined by the map above, is the gold patch up to type refinement and
the one audited callee — and the gold patch resolves (G-RESOLVE). The trust
points are exactly the two of PLAN §1.1: axiom soundness (G-AX) and refinement
fidelity (this document, G-EQ).
