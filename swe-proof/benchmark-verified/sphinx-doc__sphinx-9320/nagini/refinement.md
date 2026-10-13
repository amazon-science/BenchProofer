# refinement.md — sphinx-doc__sphinx-9320

The operation-by-operation correspondence between `model.py`'s implementation
regions and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement), **A** (axiomatized callee — split into **A-consumed**, where the
proof uses the axiom's `Ensures`, and **A-reference**, where a deep model is
validated == the real callee by axiom_check.py / G-AX), or **I** (identical
concrete operation). The claim: *any implementation that verifies against this
frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## Gold patch (two hunks, `sphinx/cmd/quickstart.py`)

```
+def is_path_or_empty(x: str) -> str:
+    if x == '':
+        return x
+    return is_path(x)
...
 d['path'] = do_prompt(__('Please enter a new root path (or just Enter to exit)'),
-                              '', is_path)
+                              '', is_path_or_empty)
```

## A. The new re-prompt validator — `validate_path_allowing_empty` ↔ `is_path_or_empty`

| # | model.py impl op (`validate_path_allowing_empty`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `x: List[int]` | `x: str` argument of `is_path_or_empty` | R | `str` ↔ `List[int]` code points (mapping.md §2). |
| A2 | `if len(x) == 0:` | `if x == '':` | R | empty `str` ⇔ zero-length code-point sequence (mapping.md §2). |
| A3 | `result = list(x); return result` (empty branch) | `return x` | R/I | return the (empty) response unchanged; `list(x)` is the identity copy of the code-point carrier. |
| A4 | `return validate_strict(x)` (non-empty branch) | `return is_path(x)` | I (calls modeled fn) | `validate_strict` is the model of the UNCHANGED `is_path`; it is itself a modeled function (its spec, not an axiom, is consumed) — §B. |

The discriminating content of the change lives in the **empty branch** (A2/A3):
the new validator returns `''` instead of raising. The frozen postcondition
`Exsures(ValidationRejected, ... len(x) > 0)` (a rejection only for a non-empty
response) and the normal clause `is_empty(ToSeq(x)) == (len(Result()) == 0)`
pin this. The pre-patch validator (`is_path` directly, no empty branch) sends
the empty response into `validate_strict`, which raises with `len(x) == 0` —
`model_prepatch.py` reproduces that (drops the empty branch) and **fails** on
exactly `Exsures(... len(x) > 0)` (G-DIFF).

## B. The strict validator — `validate_strict` ↔ `is_path` (unchanged, modeled)

| # | model.py impl op (`validate_strict`) | repo op (`is_path`, lines 91-95) | tag | justification |
|---|---|---|---|---|
| B1 | `expand_home(ToSeq(x))` | `path.expanduser(x)` (line 92) | A-consumed | unchanged stdlib callee; weakest fact `expanduser('')==''` (mapping.md §3.1). |
| B2 | `path_is_dir(...)` | `path.isdir(x)` (line 93) | A-consumed | unchanged stdlib callee; weakest fact `isdir('') is False` (mapping.md §3.2). |
| B3 | `if not path_is_dir(...): raise ValidationRejected()` | `if not path.isdir(x): raise ValidationError(...)` (lines 93-94) | R | `ValidationRejected` ↔ `ValidationError` (mapping.md §2); the message string is not behaviourally observed by the F2P test. |
| B4 | `expanded = expand_home_value(x)` | `x = path.expanduser(x)` (line 92) | R | the callee REBINDS its argument to the expanded path; `expand_home_value` is the value-producing face of the same callee, tied by its Ensures to the pure `expand_home` (a `PSeq` cannot be materialized as a `List` in an impl). |
| B5 | `return expanded` | `return x` (line 95) | R/I | `:95` returns the REBOUND name, i.e. the home-expanded response — not the response as typed. |

The strict validator's rejection is **domain-guarded** in the frozen spec:
`Exsures(ValidationRejected, ... and not path_is_dir(expand_home(ToSeq(x))))`
permits a raise ONLY when the expanded response is not an existing directory.
Together with the normal-return clauses (`path_is_dir(expand_home(ToSeq(x)))`
and `ToSeq(Result()) == expand_home(ToSeq(x))`) this pins the validator's
behaviour on BOTH sides: a response naming an existing directory MUST be
accepted and returned in its home-expanded form, and a response naming a
non-directory MUST be rejected. An impl that raises on every
input (or on any existing-directory input) cannot discharge the Exsures guard
and does not verify.

`is_path` is **unchanged** by the patch, so `validate_strict` is modeled
faithfully and its spec (not an axiom) is consumed by the new validator. The
two A-consumed axioms are about the filesystem callees `is_path` calls, which
the patch also does not change.

## C. The consuming abort decision — `abort_on_empty_reprompt` ↔ the `ask_user` loop

Gold context (`ask_user`, lines 218-228 — UNCHANGED control flow, only the
validator argument at line 226 changes):
```
d['path'] = do_prompt(__('Please enter a new root path (or just Enter to exit)'),
                      '', is_path_or_empty)      # was: is_path
if not d['path']:
    sys.exit(1)
```

| # | model.py impl op (`abort_on_empty_reprompt`) | repo op | tag | justification |
|---|---|---|---|---|
| C1 | `validated = validate_path_allowing_empty(x)` | `d['path'] = do_prompt(..., '', is_path_or_empty)` | R + (calls modeled fn) | `do_prompt` returns the value its validator accepts (its `try: x = validator(x); break` loop, lines 151-156); when the validator accepts the empty response, `do_prompt` returns `''`. The model abstracts `do_prompt` to "the validator's accepted value", which is exactly what the loop assigns to `d['path']`. |
| C2 | `aborts = len(validated) == 0; return aborts` | `if not d['path']: sys.exit(1)` | R | `not d['path']` ⇔ empty validated value (a `str` is falsy iff empty, for the path strings here); the abort (`sys.exit(1)`) happens exactly then. `True` models "operation aborts". |

The behaviour the F2P test `test_exits_when_existing_confpy` observes: with an
existing `conf.py` present and an empty re-prompt response, `ask_user` raises
`SystemExit`. In the model that is `abort_on_empty_reprompt([]) == True` —
provable ONLY because the new validator returns the empty value (does not
raise). Pre-patch, the validator raises on the empty response, so the
`do_prompt` loop never returns and `sys.exit(1)` is never reached (the observed
bug: it re-prompts forever with "Please enter a valid path name").

## D. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — adding the empty-response branch to the re-prompt validator — is
modeled **directly** (A2/A3, the `if len(x) == 0: return x` branch in
`validate_path_allowing_empty`), not hidden behind an axiom. The two consumed
axioms (`expand_home`, `path_is_dir`) cover **unchanged** stdlib callees inside
the unchanged strict validator; there is no `is_path`/`is_path_or_empty` axiom
the proof consumes (both are modeled functions). No A-reference deep model is
needed.

## E. verify(model) ⇒ resolved

`validate_path_allowing_empty` verifies only if the empty response validates to
the empty string WITHOUT raising (A2/A3, the frozen `Exsures(... len(x) > 0)` +
`is_empty == (len(Result())==0)` clauses), `validate_strict` verifies only if
it returns an existing-directory response unchanged and rejects exactly the
non-directory responses (B3/B4: the domain-guarded Exsures plus the
normal-return clauses partition the input space), and `abort_on_empty_reprompt`
verifies only if it aborts exactly on the empty validated value (C2). By R
(`str` ↔ `List[int]`, empty ⇔ length 0, `ValidationError` ↔ `ValidationRejected`)
the verified validator equals `is_path_or_empty` and the verified abort
decision equals the `ask_user` loop's `if not d['path']: sys.exit(1)` on the
tested inputs; by G-AX the two stdlib callees meet the axioms the strict
validator stands on. Therefore a model satisfying this spec, refined by the map
above, is the gold patch up to type refinement and audited callees — and the
gold patch resolves (G-RESOLVE). The trust points are exactly the two of
PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this document, G-EQ).
