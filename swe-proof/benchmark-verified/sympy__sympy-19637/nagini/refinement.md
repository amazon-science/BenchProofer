# refinement.md — sympy__sympy-19637

The operation-by-operation correspondence between `model.py`'s implementation
(the `compute_processing_signal` impl region) and `patch.diff` (the gold patch).
Each step is tagged **R** (type refinement), **A** (axiomatized callee — split
into **A-consumed**, proof uses the axiom's `Ensures`/`Requires`, and
**A-reference**, a deep model validated == the real callee by axiom_check.py /
G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The `hit` computation inside `kernS` (`sympy/core/sympify.py:510-516`)

Gold hunk (move `hit = kern in s` inside the `if ' ' in s:` block; add the
`else: hit = False`):
```
             while kern in s:
                 kern += choice(string.ascii_letters + string.digits)
             s = s.replace(' ', kern)
-        hit = kern in s
+            hit = kern in s
+        else:
+            hit = False
```
The surrounding context: `hit = False` is set at `sympify.py:471` before the
outer guard `if '(' in s and not quoted:` (`sympify.py:473`); the inner branch
`if ' ' in s:` (`sympify.py:510`) is the only place the local `kern` is
assigned (`sympify.py:512-514`).

| # | model.py impl op (`compute_processing_signal`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `entered: bool` | the outer guard `'(' in s and not quoted` (`sympify.py:473`) | R | the guard's truth value ↦ a boolean (mapping.md §2). When false, `kern` is never assigned, so `entered` false ⟹ `key` absent (the precondition `Implies(not entered, key is None)`). |
| A2 | parameter `key: Optional[bool]` | the local `kern`, assigned only inside `if ' ' in s:` (`sympify.py:512-514`), and its membership `kern in s` | R | **presence** `key is None` ↔ `kern` never bound (no substitution performed); **value** `key_member(key)` ↔ `kern in s` (mapping.md §2). The `str` content of `kern` is abstracted to its single observable, the membership boolean. |
| A3 | `hit = False` (the default before the guard) | `hit = False` at `sympify.py:471` | I | identical initial assignment of the signal to false. |
| A4 | `if entered:` … (the body) | `if '(' in s and not quoted:` … (the body) | R | the outer guard branch (A1). |
| A5 | `if key is not None: hit = key_member(key)` | the inner branch `if ' ' in s:` … then `hit = kern in s` **moved inside it** (the gold's `+            hit = kern in s`) | R + I | **the fix (part 1).** The signal is read from the created key's membership ONLY when a key was created — i.e. inside the substitution branch. `key is not None` ↔ `' ' in s` was true and `kern` was assigned; `key_member(key)` ↔ `kern in s`. Reading membership is guarded by `key is not None`, the formal face of "`kern` must be bound before use." |
| A6 | `else: hit = False` | the gold's added `+        else:` `+            hit = False` | R + I | **the fix (part 2).** When no key was created (no substitution performed), the signal is false — there is no key to test. Identical assignment; `key is None` ↔ the `' ' in s` branch was not taken. |
| A7 | `return hit` | the value `hit` carried out of the guard block (used at `sympify.py:523,525,529`) | R | the boolean signal handed to the post-processing decision. |

The discriminating content of the change — `hit = kern in s` must be read ONLY
when `kern` was actually assigned (inside `if ' ' in s:`), with `hit = False`
otherwise — lives in steps A5/A6. The pre-patch placed `hit = kern in s`
**outside** the `if ' ' in s:` block (`sympify.py:516`), so on the path
`'(' in s and not quoted` true but `' ' in s` false, `kern` was never bound and
the read is `UnboundLocalError`. `model_prepatch.py` reproduces that exactly: it
reads `key_member(key)` unconditionally inside the `entered` branch (outside the
`key is not None` guard), and **fails** verification because `key_member`'s
precondition `key is not None` cannot be established when `entered and key is
None` — the formal face of reading the unbound `kern`. That is exactly the spec
sensing the change (G-DIFF), and the exact F2P observation: `kernS("(2*x)/(x-1)")`
has `(` and is unquoted (enters the guard) but, after the structural rewrite,
contains no space (no `kern` created), so the pre-patch reads the unbound `kern`
and crashes; the gold sets `hit = False` and returns `2*x/(x-1)`.

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R or I. The operation that genuinely *changed* — restricting
the `hit = kern in s` read to the branch where `kern` is bound and defaulting
`hit = False` otherwise — is modelled **directly** by the guarded
`if key is not None: hit = key_member(key) else: hit = False` over the
`Optional[bool]` binding state (steps A5/A6). There is **no consumed axiom** and
**no A-reference deep model**: the surrounding callees (`str.split`,
`str.replace`, `str.find`, `random.choice`, `sympify`, `Symbol`, `subs`) are
UNCHANGED and are not the source of the `UnboundLocalError`; the model abstracts
the *outcome* of the substitution (`key`'s presence and membership) and pins
only the `hit`-computation delta, which is the whole change.

## C. verify(model) ⇒ resolved

`compute_processing_signal` verifies only if (a) it never inspects a key that
was not created — `key_member`'s precondition `key is not None` is unprovable on
the entered-but-no-substitution path unless the read is guarded (this is what
`model_prepatch.py` fails on), (b) the signal equals the created key's
membership in the entered-and-substituted case and is false otherwise
(`Result() == expected_signal(entered, key)`), and (c) an absent key forces the
signal false (`Implies(key is None, not Result())`), and (d) it terminates —
the precondition carries a `MustTerminate` obligation (total correctness), so
an implementation that diverges instead of returning the signal (satisfying
the value postconditions only vacuously) is rejected. By R (the outer guard ↦
`entered`; the local `kern` ↦ `Optional[bool]` by presence and membership; the
`hit` assignments ↦ identical boolean assignments) the verified function equals
the patched `kernS` `hit`-computation on the tested inputs: on the F2P input
`"(2*x)/(x-1)"` the guard is entered (`(` present, unquoted) but no space
survives the rewrite, so no `kern` is created (`key is None`); the patched code
takes `else: hit = False` and the model returns `False`, both avoiding the
unbound read; the pre-patch read the unbound `kern`. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). There is no axiom trust
point (no consumed `@ContractOnly`); the sole trust point is refinement
fidelity (this document, G-EQ).
