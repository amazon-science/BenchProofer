# mapping.md — django__django-14493

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 7272e1963ffdf39c1d4fe225d5425a45dd095d11`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance. There are **no axioms** in this bundle (see §3).

Repo file under change: `django/contrib/staticfiles/storage.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `passBudgetExceeded (flags : List Bool) (limit : Nat)` | the bounded refinement-pass loop and its trailing summary test inside `ManifestFilesMixin.post_process` — `django/contrib/staticfiles/storage.py:248-256` (body line 251 is the `if substitutions:` read; 261 `for i in range(self.max_post_process_passes):`) | the modeled changed behavior: what boolean the loop reports after running |
| `limit : Nat` | `self.max_post_process_passes` (`storage.py:223`, default `5`; the issue sets it to `0`) | the pass budget the bounded loop iterates over |
| `flags : List Bool` | the per-pass values of the local `substitutions` (`storage.py:262`, `substitutions = substitutions or subst`): pass `i` reports `True` iff that pass still made a substitution | the per-pass change indicators |
| `out : Bool` | the value of the local `substitutions` AT line 256 (`if substitutions:` → `yield … RuntimeError('Max post-process passes exceeded.')`) | the summary "we exhausted the budget while still changing" flag |

The pre-patch repo defect (refinement audit only, not in the consumer spec
view): `substitutions` is bound ONLY inside the `for i in range(...)` loop body
(`storage.py:262`); the trailing read at line 256 references it. When
`max_post_process_passes == 0` the loop body never runs, the name is never
bound, and CPython raises `UnboundLocalError: local variable 'substitutions'
referenced before assignment`. The gold patch adds `substitutions = False`
immediately before the loop (the `+` hunk line), pinning the summary value to
`False` in the zero-budget case.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.max_post_process_passes` (`int`, `>= 0`) | `Nat` `limit` | `n` (non-negative Python int) ↔ `limit`; `range(n)` iterates `n` times ↔ the bounded loop runs while `i < limit` |
| the sequence of per-pass `subst` outcomes (`bool` per pass) | `List Bool` `flags` | `flags[i]!` ↔ "pass `i` reported a substitution"; `len(flags) >= limit` is the modeling precondition (`require limit ≤ flags.length`): the loop only ever inspects passes `0 … limit-1`, which always exist |
| local `substitutions` after the loop (`bool`) | `Bool` `out` | `True` ↔ `out = true`. The patched semantics: `out = true` iff `limit > 0` AND every pass `0 … limit-1` still reported a change (the loop ran the full budget and `break` never fired). With `limit = 0`, `out = false` (the bug fix). |

The early-stop `if not substitutions: break` (`storage.py:266`) is modeled by
the loop guard's second conjunct `(i = 0 ∨ flags[i-1]! = true)`: the bounded
loop continues to pass `i` only when the previous pass still changed. The
trailing summary `if substitutions:` over the final `substitutions` value is
`out = overBudget flags limit`.

## 3. No axioms — pure R/I refinement

`Solution.lean` declares **no `axiom`** and uses **no `:|`-stub method**. The
modeled behavior is a self-contained control-flow/data-flow computation over the
two abstract carriers (`flags`, `limit`); the only repo callee inside the loop
(`self._post_process`) is the *source* of each per-pass `subst` value and is
**unchanged** by the patch — it is abstracted into the input `flags`, not
modeled or axiomatized. Hence:

- there is **no A-consumed axiom** and **no A-reference deep model**;
- `axiom_check.py` (G-AX) has nothing repo-specific to validate. It instead
  asserts the *modeling invariant* that the patched Python summary value equals
  `overBudget(flags, limit)` for the abstracted inputs (and documents that
  `_post_process` is unchanged), so the bundle still ships an executable G-AX
  artifact. It is stdlib-only and exits 0.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`14493`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
the impl-region loop (`passBudgetExceeded`) to Python over the repo types
(`int` budget, `list[bool]` per-pass flags) and diffs it against the behaviour
of the patched `post_process` summary computation distilled from `patch.diff`.
There are no A-tagged callees in the impl region, so the shadow is pure R/I.
