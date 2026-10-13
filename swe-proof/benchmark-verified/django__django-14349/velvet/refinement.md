# refinement.md — django__django-14349

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `validateUrl` `do` block, the deep `containsForbidden`/`isForbidden` model,
the pure `CallOutcome`/`liftBaseline` outcome algebra, and the
`baselineOutcome` axiom) and `patch.diff` (the gold patch). Each step is
tagged **R** (type refinement), **A** (axiomatized callee — **A-consumed** where
the proof uses the axiom's `ensures`, **A-reference** where an abstraction is
validated against the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The validator entry point — `URLValidator.__call__` (`django/core/validators.py:101`)

Gold hunks:
```
+    unsafe_chars = frozenset('\t\r\n')            # class attribute (line 94)
     def __call__(self, value):
         if not isinstance(value, str):
             raise ValidationError(...)
+        if self.unsafe_chars.intersection(value):  # the new early-reject guard
+            raise ValidationError(...)
         # ... unchanged scheme/regex/IDN/IPv6/host-length validation ...
```

| # | Solution.lean impl op (`validateUrl`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `value : List Char` | `value` arg of `__call__` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | `if containsForbidden value then return CallOutcome.rejected` | `if self.unsafe_chars.intersection(value): raise ValidationError(...)` | R + I | the **changed** screen modeled **deeply**: `containsForbidden`/`isForbidden` (pure region) ARE the per-code-point membership in `frozenset('\t\r\n')`. `return CallOutcome.rejected` ↔ `raise ValidationError` (mapping.md §2). The fold ops (`isForbidden c`, `||`, the recursion) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `intersection`-truthiness is an **A-reference** G-AX validates. |
| A3 | `else return liftBaseline baselineVerdict` | fall through to the unchanged scheme/regex/IDN/IPv6/host-length validation; its ending (return / raise `ValidationError` / another error escaping, e.g. the hostname-None `TypeError`) surfaces unchanged as the call's ending | A-reference + R | the unchanged validation is abstracted by `baselineOutcome : List Char → BaselineOutcome` (mapping.md §3.1); its three-way outcome on `value` enters as `baselineVerdict` (`require baselineVerdict = baselineOutcome value`). `liftBaseline` (pure, an identity embedding `accepts↦accepted`, `rejects↦rejected`, `crashes↦crashed`) ↔ the validation's ending becoming the call's ending. The `else` faithfully encodes that the new guard short-circuits before this validation runs — including on inputs where it would crash. |
| A4 | result `outcome : CallOutcome` | `__call__` returning `None` vs. raising `ValidationError` vs. another exception escaping | R | the F2P test observes raise/no-raise of `ValidationError` (`assertRaises(ValidationError)`); the `crashed` constructor represents the third real ending (an unrelated error escaping, e.g. `TypeError('object of type NoneType has no len()')` on `"http://?@[::1]"`-shaped inputs whose `urlsplit().hostname` is `None`, present identically pre- and post-patch); `message`/`code`/`params` payload is test-neutral and omitted (mapping.md §2). |

Discriminating content of the change — a `value` containing `\t`, `\r`, or `\n`
is refused with the designated validation failure even when the structural
validation alone would have accepted it (or crashed on it) — lives in the
`if containsForbidden value then CallOutcome.rejected` branch of the
postcondition. `Solution_prepatch.lean` omits this screen in its impl
(`return liftBaseline baselineVerdict` only) and therefore **fails**
`outcome = (if containsForbidden value then CallOutcome.rejected else
liftBaseline (baselineOutcome value))` on exactly those inputs (G-DIFF). The
F2P cases `'http://www.djangoproject.com/\n'`, `'http://[::ffff:192.9.5.5]\r'`,
`'http://\twww.djangoproject.com/'`, etc. are instances where the embedded
control char makes `containsForbidden = true`.

## B. No second site

The patch touches one function (`URLValidator.__call__`) plus the class
attribute `unsafe_chars` it reads; both are modeled in site A. No other
independently-observable behavior changes, so one failing prepatch suffices
(G-DIFF).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
forbidden-character screen — is modeled **deeply** (`containsForbidden`/`isForbidden`,
step A2, an A-reference + I), not hidden behind an axiom about the function under
change. The only axiom, `baselineOutcome` (step A3), abstracts the **unchanged**
surrounding validation, and is consumed only as a determinism/totality-onto-
three-outcomes abstraction whose result is passed through — never as an
answer-key (SPEC_GUIDE directive 8); G-AX validates its soundness against the
real unchanged body, including the real third outcome (the hostname-None
`TypeError` family, identical at base_commit and post-patch).

## D. verify(Solution) ⇒ resolved

`validateUrl` verifies only if its output equals
`if containsForbidden value then CallOutcome.rejected else liftBaseline
(baselineOutcome value)` (A2+A3). By R (`str ↔ List Char`, the three-way
`CallOutcome` ↔ return / `ValidationError` / escaping error) the verified
validator refuses exactly when a forbidden control character is present, and
otherwise surfaces the unchanged validation's ending untouched — which is the
patched `__call__`'s behavior, on the crashing inputs too. By G-AX the deep
model `containsForbidden` equals the real `frozenset('\t\r\n').intersection`
screen (A-reference) and the unchanged validation is the deterministic total
three-outcome function the axiom assumes; by G-CONF the R/I transliteration
agrees with `patch.diff`'s three-way ending on ≥10⁵ inputs (including the
crash family). Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and the one audited unchanged
callee — and the gold patch resolves (G-RESOLVE). Trust points are exactly the
two of plan §1.1: A-reference soundness (G-AX) and refinement fidelity (this
doc, G-EQ + G-CONF).
