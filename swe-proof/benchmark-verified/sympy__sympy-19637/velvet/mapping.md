# mapping.md — sympy__sympy-19637

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 63f8f465d48559fecb4e4bf3c48b75bf15a3e0ef`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee/flag provenance.

Repo file under change: `sympy/core/sympify.py` (the `kernS` function).

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `markerPresent (s : List Char)` | the marker-presence flag step inside `kernS` — `sympy/core/sympify.py:516` (post-patch lines 516–518) | the modeled changed code: the step that decides the flag (`hit`) reporting whether a substitution marker is present in the working string |
| `markerFlag (s : List Char)` | the value `kern in s` (membership of the marker in the working string) — `sympy/core/sympify.py:516` | pure spec: the total flag value for a working string |
| `s : List Char` | the local working string `s` consumed at the flag step (`sympify.py:516`) | the read-only input the step inspects |
| `MarkerError` (inductive) | the `UnboundLocalError` raised when the consulted marker value was never established (`kern` referenced before assignment) | reified failure leg — never produced by the gold |

The pre-patch defect (refinement audit only, not in the consumer spec view): at
`sympify.py:516` the flag assignment `hit = kern in s` sits at the outer
`if '(' in s` level, but the marker value (`kern`) is bound only inside the
nested `if ' ' in s:` branch (lines 510–515). When no marker survives into the
working string (no space remains after the paren transforms), the consulted
value was never established, so the read raises instead of yielding a flag.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `s` (Python `str`, the working string at the flag step) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; empty `str` ↔ `[]` |
| a single Python character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; on the BMP this is total and exact |
| the substitution marker | the distinguished code point `' '` (space, U+0020) | the gold replaces every space in `s` with a freshly-chosen kern that is guaranteed absent from `s` beforehand (`while kern in s: kern += choice(...)`), then `s = s.replace(' ', kern)`. Therefore **`kern in s` (post-patch) holds iff `s` contained a space at the flag step** — the marker membership `kern in s` is observationally `' ' in s` evaluated on the working string as it stood before the replace. The model uses the space code point directly as the marker, so `markerFlag s = s.contains ' '` is exactly the post-patch `hit` (mapping.md §3). |
| `hit : bool` (the flag) | `Bool` carried in `Except.ok` | `True` ↔ `Except.ok true`, `False` ↔ `Except.ok false`; the `UnboundLocalError` path ↔ `Except.error MarkerError.markerUnavailable` (never produced by the gold). |

Lean `List Char` indexing/membership is total and sound; the carrier is
`List Char` because the operation is per-code-point membership.

## 3. The marker / flag identity (why `markerFlag s = s.contains ' '`)

Post-patch `kernS` computes the flag only inside the space branch:

```python
if ' ' in s:
    # get a unique kern
    kern = '_'
    while kern in s:                       # kern is chosen ABSENT from s
        kern += choice(string.ascii_letters + string.digits)
    s = s.replace(' ', kern)               # every space becomes kern
    hit = kern in s                        # <-- post-patch: inside the branch
else:
    hit = False                            # <-- post-patch: total
```

The `while kern in s` loop guarantees `kern` is absent from `s` **before** the
replace; `s.replace(' ', kern)` then inserts `kern` exactly where the spaces
were. Hence after the replace, `kern in s` is `True` iff `s` had at least one
space, i.e. iff `' ' in s` (evaluated at the top of the branch). And the `else`
branch is reached precisely when `' ' in s` is `False`, where the flag is
`False`. So across both branches the post-patch flag equals `' ' in s` on the
working string — which is exactly `markerFlag s = s.contains ' '`. The model
uses the space code point as the marker directly (a faithful re-expression that
avoids modeling the random kern choice, which is observationally irrelevant to
the flag). No axiom is consumed: the membership is a concrete per-code-point op.

This is a **control-flow / totality** change (error-vs-success), not a
value-table change: the gold makes the flag step total (always `Except.ok`),
whereas the pre-patch surfaces a failure on the no-marker path.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`19637`** so the
consumer-side verdict is reproducible. The R/I shadow transliterates the
`markerPresent` `do` block (the membership branch — pure R/I, no A-tagged
callee) to Python and diffs against the patch.diff behaviour of the flag step in
`kernS` replayed on the same working strings. There are no axioms in this bundle
(no `axiom_check.py` / G-AX): the only callee-like op is concrete membership.
