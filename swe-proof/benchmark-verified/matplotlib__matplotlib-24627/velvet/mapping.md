# mapping.md — matplotlib__matplotlib-24627

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 9d22ab09d52d279b125d8770967569de070913b2`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the modeled site. Repo file under change:
`lib/matplotlib/axes/_base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `clearAxes (children : List Artist)` | `_AxesBase.__clear(self)` — `lib/matplotlib/axes/_base.py:1271` (body line 1311, `self._children = []`) | modeled changed function: the per-axes clear routine, reached by the public `Axes.clear()` / `Axes.cla()` (`_base.py:1395` / `:1404`) |
| `Artist` (`hasAxes`, `hasFigure`) | a matplotlib `Artist` viewed through its `.axes` and `.figure` attributes only (`lib/matplotlib/artist.py`) | pure spec: an attached child seen through the two links the issue names |
| `deparent` | the per-child body `chld.axes = chld.figure = None` (post-patch loop body) | pure spec: unset both links of one artist |
| `deparentAll` / the `while` fold | the post-patch loop `for chld in old_children: chld.axes = chld.figure = None` | pure spec: deparent every formerly-attached child, in order |

The pre-patch repo behaviour the change removes (refinement audit only, not in
the consumer spec view): `__clear` rebound `self._children = []` (emptying the
axes' own list) but never touched the artists that had been in it, so each one
kept `.axes`/`.figure` pointing back at the now-cleared axes — observable as
`l.axes is <Axes>` after `a.cla()` in the reproduction.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| the sequence of artists attached to the axes before the clear (`self._children`, a `list` of `Artist`) | `List Artist` | the i-th attached artist ↔ `children[i]`; `len` ↔ `.length`; order preserved; empty list ↔ `[]` |
| one artist's `.axes` / `.figure` attribute, observed AFTER the clear | the corresponding field of the returned `Artist` (`hasAxes` / `hasFigure`) | `attr is None` ↔ field `= false`; `attr is not None` ↔ field `= true`. The clear sets both to `None` ⇔ both fields `false`. |
| the result of clearing: each formerly-attached artist's post-clear `(.axes, .figure)` state, in order | `List Artist` (the `out` of `clearAxes`) | the i-th returned artist's `(hasAxes, hasFigure)` ↔ the i-th former child's `(.axes is not None, .figure is not None)` after `cla()` |

Only the **set/unset** status of `.axes` and `.figure` is modeled, because that
is the entire observable contract of the fix (the F2P test asserts `art.axes is
None` / `art.figure is None`, and the bug left them `is ax` / `is fig`). The
identity of the axes/figure object, the artists' other attributes, and the
order-irrelevant collection rebuild are not part of the contract and are not
modeled. G-CONF feeds artist counts and checks the boolean set/unset status of
both links on each former child.

## 3. Site provenance (the modeled change — checked by G-CONF, not G-AX)

### 3.1 `clearAxes` ↔ `_AxesBase.__clear`
**Repo:** `lib/matplotlib/axes/_base.py:1271`. Pre-patch body does
`self._children = []` — it discards the axes' reference to its children but
leaves each child's `.axes`/`.figure` set. Post-patch:
```python
old_children, self._children = self._children, []
for chld in old_children:
    chld.axes = chld.figure = None
```
i.e. it deparents every formerly-attached child (unsets BOTH links).

G-CONF constructs a REAL axes via `plt.subplots()`, attaches a fuzzed number of
real artists (`ax.plot(...)`, `ax.imshow(...)`), records them, calls
`ax.clear()`, and asserts each recorded artist now has `.axes is None` and
`.figure is None` — matching the `deparentAll` semantics of `clearAxes`. The
public `Axes.clear()`/`Axes.cla()` both reach `__clear` (the `_subclass_uses_cla`
dispatch at `_base.py:1395`/`:1404` routes to it); G-CONF drives the public
`clear()` entry point.

### 3.2 The non-deparenting statements around the edit — not modeled
The surrounding statements `__clear` runs (`self._mouseover_set = ...`,
`self.child_axes = []`, resetting the various `None` sentinels, regridding,
etc.) are untouched by the patch, observe nothing the F2P test discriminates,
and carry no bug→fix delta. They are intentionally omitted from the model. The
only modeled behaviour is the deparenting loop the patch adds. No axiom, no
method, no G-AX obligation corresponds to them.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`24627`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `clearAxes`/`deparentAll`/`deparent` (all pure R/I — there are no
A-tagged callees in the impl region, so `conf_skip = false`) to the boolean
"both links unset" semantics, and runs the REAL patched `clear()` as the oracle
(attach-artists-then-clear-then-read-`.axes`/`.figure`).

## 5. Axioms — none

This bundle declares zero consumed axioms and zero A-reference deep models of an
unchanged callee. The only modeled behaviour is the *changed* clear routine's
deparenting of former children, validated by G-CONF against the real patched
code, not by an axiom (refinement.md §C; `axiom_check.py` asserts the inventory
is empty).
