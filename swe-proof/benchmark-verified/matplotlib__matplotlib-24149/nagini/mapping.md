# mapping.md — matplotlib__matplotlib-24149

Binds every `model.py` symbol to its repository counterpart at
`base_commit = af39f1edffcd828f05cfdd04f2e59506bb4a27bc`, states the type
abstraction, and gives the provenance of each axiom (callee source + the exact
behaviour the axiom encodes).

Repo file under change: `lib/matplotlib/axes/_axes.py` (the static helper
`Axes._convert_dx`). The two callees are in `lib/matplotlib/cbook/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `select_position_x0(seq)` | the `x0` representative-selection block of `Axes._convert_dx` — `lib/matplotlib/axes/_axes.py:2181-2184` (the inner `try: x0 = cbook._safe_first_finite(x0)`) | first modeled changed function (hunk 1) |
| `select_position_xconv(seq)` | the `xconv` representative-selection block of `Axes._convert_dx` — `lib/matplotlib/axes/_axes.py:2186-2189` (the inner `try: x = cbook._safe_first_finite(xconv)`) | second modeled changed function (hunk 2) |
| `first_finite(s)` *(axiom — A-consumed)* | `cbook._safe_first_finite` — `lib/matplotlib/cbook/__init__.py:1709-1749` (list path: `next(val for val in obj if safe_isfinite(val))`) | unchanged callee: first finite element selector |
| `first_unconditional(s)` *(axiom — A-consumed)* | `cbook.safe_first_element` — `lib/matplotlib/cbook/__init__.py:1699-1706` (delegates to `_safe_first_finite(obj, skip_nonfinite=False)`; list path returns `next(iter(obj))`) | unchanged callee: first element unconditionally |
| `any_finite(s)` *(deep model)* | the existence-of-a-finite-element condition implicit in the `_safe_first_finite` generator (`val for val in obj if safe_isfinite(val)` is non-empty) — `lib/matplotlib/cbook/__init__.py:1749` | pure spec: whether the no-StopIteration branch applies; drives the fallback choice |
| `first_finite_value(s)` *(deep model)* | the VALUE the `_safe_first_finite` generator yields: `next(val for val in obj if safe_isfinite(val))` = the first finite element — `lib/matplotlib/cbook/__init__.py:1749` | pure spec: the selected element's value/identity, used to PIN postcondition (1) and the `first_finite` axiom to the input's actual first finite element (closes the directive-8 ungrounded-marker hole) |

The pre-patch repo state the change repairs (for the refinement audit, not
referenced from the consumer spec view): each inner `try` in `_convert_dx`
caught only `(TypeError, IndexError, KeyError)` and had **no** `except
StopIteration` clause, so when `_safe_first_finite` raised `StopIteration` (all
elements non-finite) it propagated out of `_convert_dx` and crashed `Axes.bar`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a coordinate sequence (`x0` / `xconv`, a Python list or numpy 1-D array of floats, possibly containing NaN) | `List[int]` of per-element finiteness flags | `seq[k] != 0` ↔ `safe_isfinite(value_k)` is `True` (i.e. the k-th coordinate is a finite, non-`None` value); `seq[k] == 0` ↔ the k-th coordinate is non-finite (NaN) or `None`; `len(seq)` ↔ the number of coordinates |
| the selected representative coordinate (a float, finite or NaN) | the selected flag `int` returned by the function | `Result() != 0` ↔ the chosen representative is finite; `Result() == 0` ↔ it is non-finite |
| sequence value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `len`/`[i]`/`drop` mirror list `len`/index/tail |

`_convert_dx` is only reached when `xconv.size != 0` (it returns early on an
empty array, `_axes.py:2166-2168`), so both modeled functions require a
**non-empty** sequence (`len(seq) > 0`); the all-non-finite-but-non-empty case
(e.g. `[np.nan]`) is therefore in-domain — it is exactly the regression input.

Both modeled functions also carry `Requires(MustTerminate(2))` — a
total-correctness obligation. The real selection is bounded, loop-free code
(a `try/except` around a single generator step over a finite sequence): it
always returns. Under partial-correctness semantics an implementation that
computes the right representative and then diverges before returning would
satisfy the value postconditions only vacuously while its faithful real patch
hangs `Axes.bar` (and every F2P/P2P test) — the same-spec rival the batch
G-PANEL-1 audit exhibited (atk_4). The obligation forces every loop in a
candidate implementation to declare a strictly decreasing termination measure,
closing that vacuous-nontermination hole.

The only behaviour the F2P test (`test_bar_all_nan`) observes about the
representative is whether the selection **succeeds and produces a (possibly
non-finite) value** rather than crashing; the model carries finiteness, which is
the sole discriminating property of the choice. Coordinate magnitudes are
irrelevant to the change, so the integer-flag carrier (not interpreted floats)
is the faithful, sufficient abstraction.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `first_finite` ↔ `cbook._safe_first_finite` (A-consumed)
**Callee:** `lib/matplotlib/cbook/__init__.py:1709-1749`. For a list/array
(neither `np.flatiter` nor `collections.abc.Iterator`) and the default
`skip_nonfinite=True`, the body is:

```python
return next(val for val in obj if safe_isfinite(val))
```

where `safe_isfinite(val)` is `False` for `None`, `np.isfinite(val)` for a
scalar, and `True` otherwise. Hence:
- it returns the **first finite element** when one exists — so the returned
  element is finite (`Result() != 0`); and
- it raises **`StopIteration`** when the generator is empty, i.e. when **no**
  element is finite — exactly the negation of `any_finite`.

The axiom encodes what the proof needs while staying grounded in the input:
`Requires(any_finite(s))` (the no-raise domain — the guard the patched code now
establishes before the call) and `Ensures(Result() == first_finite_value(s))`
(the chosen element is THE first finite element of the input — its value/identity,
which in particular implies it is finite/non-zero). It is the **weakest** sound
contract that still pins the result to a *property produced by applying the
selector to the input* rather than to a bare derived flag: an earlier
`Ensures(Result() != 0)` was dischargeable by any finite constant (directive-8
ungrounded-marker hole — a constant-echo impl `rep = 1` verified yet, refined,
failed the unit-conversion P2P `test_bar_timedelta` because the representative's
actual value/type is load-bearing downstream). Pinning to `first_finite_value(s)`
(a structural fold over the carrier, §3.4) closes that hole while remaining
sound (G-AX: the real callee returns exactly this element). The axiom is
`@Pure @ContractOnly` (used inside the model's `if`/`Ensures`).

### 3.2 `first_unconditional` ↔ `cbook.safe_first_element` (A-consumed)
**Callee:** `lib/matplotlib/cbook/__init__.py:1699-1706`, which delegates to
`_safe_first_finite(obj, skip_nonfinite=False)`. For a list/array the
`skip_nonfinite is False` path returns `next(iter(obj))` — i.e. the **first
element unconditionally**, regardless of finiteness. The axiom encodes
`Requires(len(s) > 0)` and `Ensures(Result() == s[0])` — the weakest sound
contract: a non-empty sequence's first element. This is the fallback the patch
reaches when `_safe_first_finite` raises (all-non-finite input).

### 3.3 `any_finite` deep model (drives the choice; NOT a consumed callee)
`any_finite` is a `@Pure` front-recursive fold spelling out "the sequence
contains at least one finite element" — the condition that decides whether
`first_finite` applies (no raise) or the `first_unconditional` fallback is taken.
It mirrors the existence/non-existence of an element satisfying `safe_isfinite`
in the real generator. It is part of the spec, not an axiom about a callee; its
correspondence to the real finiteness predicate is the R-refinement of §2 and is
exercised by axiom_check.py alongside the two axioms.

### 3.4 `first_finite_value` deep model (the selected element's identity; NOT a consumed callee)
`first_finite_value` is a `@Pure` front-recursive fold (under `Requires(any_finite(s))`)
spelling out "**the** first finite element of the sequence" — the leftmost
element whose flag is non-zero. It is the structural witness postcondition (1)
and the `first_finite` axiom are pinned to (`Result() == first_finite_value(s)`),
so the selected representative's value/identity — not merely its finiteness — is
grounded in the input carrier. It mirrors the VALUE the real
`next(val for val in obj if safe_isfinite(val))` generator yields. Like
`any_finite` it is part of the spec, not an axiom about a callee; its
correspondence to the real first-finite element is exercised by axiom_check.py
(the real `_safe_first_finite` returns exactly the value at the first-finite
index, observable because the materialized finite flags are distinct floats).
This closes the directive-8 ungrounded-marker hole the batch05 G-EQ panel found
(attack 4: a constant-echo `rep = 1` formerly verified the weaker
`Ensures(Result() != 0)` yet, refined, failed the value/type-sensitive
unit-conversion P2P `test_bar_timedelta`).

**Soundness check (G-AX):** `axiom_check.py` imports the REAL `matplotlib.cbook`
(the very module the gold patch calls) plus `numpy`, materializes each finiteness
flag pattern as a concrete coordinate list (finite flag → a **distinct** finite
float so the selected element's identity is observable; zero flag → `float('nan')`),
and asserts over 11 boundary patterns + 20 000 fuzz sequences:
- under `any_finite`, the real `_safe_first_finite` returns normally with the
  **first finite** element — exactly the value at the first-finite index, the
  element `first_finite_value` selects (the `first_finite` axiom — load-bearing,
  version-robust, identity-pinning);
- on a non-empty sequence, `safe_first_element` returns the **first** element
  (the `first_unconditional` axiom — version-robust);
- in the **base_commit (matplotlib 3.6)** callee the eval container pins,
  `_safe_first_finite` **raises `StopIteration`** on an all-non-finite sequence
  (the negation of `any_finite`) — confirming the axiom's `Requires` is the
  weakest sound guard and witnessing the exact regression. (A later matplotlib
  refactor absorbed the fallback into the callee; the check detects the installed
  version and adapts the explanatory raise-witness, while the load-bearing
  Ensures checks hold unconditionally.) Exit 0 iff sound.

## 4. Conformance check (G-CONF)

`conformance_check.py` runs the contract-stripped impl regions of both modeled
functions (shadow; @ContractOnly callees delegated to the real
`cbook._safe_first_finite` / `cbook.safe_first_element` across the flag/float
bridge of §2) against the REAL patched selection sites of
`Axes._convert_dx` (oracle; each site isolated by pinning the other side to
`0.0` with `dx = 0.0` and an identity `convert`). Inputs: 30 boundary flag
patterns (including +/-inf materializations), all 2046 finite/non-finite
patterns of lengths 1..10, and 60000 fuzz patterns — each fed to both sites
(>= 124000 checks). **Pinned fuzz seed: 24149.**
