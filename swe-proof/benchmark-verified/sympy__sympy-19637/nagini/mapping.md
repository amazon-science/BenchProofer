# mapping.md — sympy__sympy-19637

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 63f8f465d48559fecb4e4bf3c48b75bf15a3e0ef`, states the type
abstraction, and (there being no consumed axiom) records that no callee is
axiomatized.

Repo file under change: `sympy/core/sympify.py` (the function `kernS`).

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `compute_processing_signal(entered, key)` | the assignment of the local `hit` inside `kernS` — `sympy/core/sympify.py:471` (`hit = False`), the outer guard `sympify.py:473` (`if '(' in s and not quoted:`), the inner substitution branch `sympify.py:510-515` (`if ' ' in s:` … `s = s.replace(' ', kern)`) and `sympify.py:516` (`hit = kern in s`) | the modeled changed control flow: how the `hit` flag is computed from the substitution key `kern` |
| `key_member(key)` | the membership test `kern in s` (`sympify.py:516`) — defined only when the local `kern` has been assigned | pure spec: the created key's membership in the rewritten text, legal only when a key exists |
| `expected_signal(entered, key)` | the value `hit` is required to hold after the guard block | pure spec: the correct `hit` |

The pre-patch repo construct the change fixes (for the refinement audit, not
referenced from the consumer spec view): line 516 `hit = kern in s` sits
**outside** the `if ' ' in s:` block, so on the path
`'(' in s and not quoted` true but `' ' in s` false, the local `kern` was never
assigned and the read raises `UnboundLocalError: local variable 'kern'
referenced before assignment` (the issue title). The gold moves
`hit = kern in s` *inside* `if ' ' in s:` and adds `else: hit = False`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `'(' in s and not quoted` (the outer guard at `sympify.py:473`) | `entered: bool` | the outer guard's truth value. When false, `kern` is never assigned anywhere in the block, so `entered` false ⟹ `key` absent (the model precondition `Implies(not entered, key is None)`). |
| the local `kern` (a `str`), assigned only inside `if ' ' in s:` (`sympify.py:512-514`) | `key: Optional[bool]` | **presence**: `key is None` ↔ `kern` was never assigned (the `' ' in s` branch was not taken, i.e. no substitution performed); `key is not None` ↔ `kern` was created. **value**: when present, `key` carries the boolean `kern in s` (`sympify.py:516`). The actual character content of `kern` is irrelevant to the bug — only whether it was assigned and whether it occurs in `s` matter — so `kern`'s `str` content is abstracted to its single observable, the membership boolean. |
| `kern in s` (`sympify.py:516`) | `key_member(key)` | the membership test, modelled as a `@Pure` accessor with precondition `key is not None`: in Python the read is legal only after `kern` has been bound; reading it unbound is the `UnboundLocalError`. The precondition is the formal face of "name must be bound before use." |
| `hit` (the local boolean signal; `sympify.py:471,516`) | `Result()` of `compute_processing_signal` | the flag controlling whether the later kern-substitution post-processing runs (`sympify.py:523,525,529-541`). Same boolean; abstracted from the surrounding `sympify`/`subs` machinery, which is unchanged and not the source of the bug. |

`str` indexing/iteration is banned in Nagini; here the `str` `kern` and `s`
never need to be modelled as code-point lists because the only observables the
bug touches are **(a)** whether `kern` was assigned and **(b)** the boolean
`kern in s`. Both are captured by `Optional[bool]` — a tighter, faithful
abstraction than a `List[int]` carrier (refinement.md §A).

## 3. Callee provenance

None. There is **no `@ContractOnly` axiom** and **no A-reference deep model**.
The changed operation is the placement of `hit = kern in s` relative to the
`if ' ' in s:` guard and the missing `else: hit = False` — pure local control
flow over the binding state of `kern`. The surrounding callees the F2P test
exercises (`s.split`, `str.replace`, `str.count`, `str.find`, `random.choice`,
`sympify`, `Symbol`, `subs`) are UNCHANGED and are not the source of the
`UnboundLocalError`; the model abstracts the *outcome* of the substitution
(whether a `kern` was created and its membership) and pins only the
`hit`-computation delta, which is the whole change. `axiom_check.py` therefore
records "no axioms" and verifies the abstraction's defining property against the
real `kernS` control flow (G-AX no-op soundness check).

## G-CONF

`conformance_check.py` is the differential refinement check: the `# impl-start` /
`# impl-end` region of `model.py` (plus the two `@Pure` helpers it calls), copied
**verbatim** with only the contract calls (`Requires`, `Ensures`,
`MustTerminate`) and the `@Pure` decorators deleted, diffed against the **real
patched** `sympy.core.sympify.kernS` (`sympy/core/sympify.py:440`; the flag
computation at `:471,473,510-516`).

* **Oracle — called, not transliterated.** The real `kernS` is invoked on a real
  input `str` under `sys.settrace`; the tracer halts the real frame at
  `for i in range(2):` — the first statement after the guard block, where `hit`
  is final — and reads the real function's own locals. Halting there keeps the
  unchanged downstream `sympify`/`subs` machinery out of the comparison, so
  arbitrary fuzz strings can be driven through the real flag computation. The
  script also refuses to report agreement unless the installed source has the
  gold shape (`hit = kern in s` nested inside `if ' ' in s:` with an `else:`
  arm), so a green verdict can never mean "the oracle was the pre-patch code".
* **Bridge (§2 inverted, concrete → abstract).** From the observed real frame:
  `entered = ('olds' in locals)` (the guard block's own local, cross-checked
  against `'(' in s and not quoted`); `key = None` when `kern` is unbound in the
  frame (no substitution key created), else `key = (locals['kern'] in
  locals['s'])`, the real membership test. Generating concrete-first makes every
  input Requires-satisfying by construction, and `Implies(not entered, key is
  None)` is *asserted* on every observation rather than assumed.
* **Inputs / seed.** `SEED = 19637` (pinned as a module constant),
  `N_INPUTS = 100_000` real strings: boundary cases first (empty, singleton,
  quoted, the F2P witness `"(2*x)/(x-1)"`, the `test_kernS` expressions,
  key-collision inputs that force the `while kern in s` growth loop, unmatched
  parens as domain-excluded), then seeded fuzz over a paren/operator/quote
  alphabet with parentheses balanced. The **abstract** domain is finite (4
  admissible carrier points) and is additionally enumerated exhaustively against
  `expected_signal`; the run further requires a real-string witness for each of
  the three repo-reachable states `(False, None)`, `(True, None)`, `(True, True)`
  and reports `(True, False)` as unreachable-hence-unwitnessed (a fresh `kern` is
  unique and then spliced in, so `kern in s` is necessarily true).
* Exit 0 iff zero disagreements; a disagreement prints the input, the bridged
  carrier and both signals.
