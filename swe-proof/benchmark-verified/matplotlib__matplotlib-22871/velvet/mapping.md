# mapping.md — matplotlib__matplotlib-22871

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a7b7260bf06c20d408215d95ce20a1a01c12e5b1`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of each callee.

Repo file under change: `lib/matplotlib/dates.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `offsetSelection (initShow) (stats)` | the level/offset-suppression decision loop inside `ConciseDateFormatter.format_ticks` — `lib/matplotlib/dates.py:797-806` | the modeled changed operation |
| `colVaries col` | `len(np.unique(tickdate[:, level])) > 1` — `dates.py:799-800` (post-patch `len(unique) > 1`) | a component's column takes more than one distinct value across the ticks |
| `colHasOne col` | `np.any(unique == 1)` — `dates.py:802` (added by the patch) | the value one occurs among the component's values |
| `suppressOffset level col` | the `level < 2 and np.any(unique == 1)` guard — `dates.py:802` | the offset-suppression condition |
| `offsetDecision initShow stats` | the whole `for level in range(5, -1, -1): …` loop — `dates.py:797-808` | the deep model of the changed decision; chosen `level` + final `show_offset` |
| `offsetSelection`'s `chosenLevel` / `showOffset` outputs | the `level` and `show_offset` locals after the loop — `dates.py:797-808` | consumed downstream at `dates.py:840-846` |

The upstream that PRODUCES the integer columns — `num2date(value)` →
`.timetuple()[:6]` → `np.array` → `tickdate[:, level]` (`dates.py:778-779`) — is
**unchanged** and is not modeled; it is reproduced verbatim by the real repo in
the conformance bridge (§3, refinement.md §B). The downstream that CONSUMES the
decision — `tickdatetime[-1].strftime(offset_formats[level])` else `''`
(`dates.py:840-846`) — is likewise unchanged and is applied verbatim to the
shadow's `(level, show_offset)` by the conformance bridge.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `show_offset` (a `bool`, `dates.py:795`) | `initShow : Bool` | identity on booleans |
| one date component's column across the ticks — `tickdate[:, level]`, an `int64` numpy column | `List Int` | `[int(x) for x in tickdate[:, level]]` ↔ a `List Int`; `len` ↔ `.length`; membership ↔ `List.contains` |
| the components in scan order — the loop variable `level ∈ {5,4,3,2,1,0}` paired with its column | `stats : List (Nat × List Int)` | `[(level, column) for level in (5,4,3,2,1,0)]`, the SAME finest→coarsest order as `range(5, -1, -1)` |
| `len(np.unique(c)) > 1` | `colVaries c` | "more than one distinct value" ↔ `c.any (· != c.headD 0)`; both are false on an empty/one-element column and true exactly when two entries differ |
| `np.any(unique == 1)` | `colHasOne c` | "the value 1 appears" ↔ `c.contains 1`; `np.unique(c)` is the set of `c`'s values, so `1 ∈ unique(c) ⇔ 1 ∈ c` |
| the chosen `level` (an `int`) and final `show_offset` (a `bool`) | `Nat × Bool` | componentwise identity |

Note `colVaries`/`colHasOne` read only the SET of distinct values of the column
(`np.unique`), so modeling them on the raw `List Int` is faithful: `np.unique`
neither adds nor removes membership facts, and `> 1 distinct` ⇔ `some entry
differs from the first`.

## 3. Callee provenance (kind-I / unchanged — checked by G-CONF, not G-AX)

There are **no axiomatized callees and no `:|` stubs**, hence **no G-AX**. The
changed operation — the offset-display decision — is modeled **deeply** in the
`pure` region (`colVaries`, `colHasOne`, `suppressOffset`, `offsetDecision`) and
the verified `while` loop IS that scan. The two callees the surrounding code uses
are genuinely **unchanged** and are exercised by the real repo in the
conformance bridge, not modeled:

- **`num2date` / `datetime.timetuple` / `np.unique`** (the column producer,
  `dates.py:778-800`): unchanged upstream. The conformance shadow derives its
  integer columns from the SAME real `num2date(value).timetuple()[:6]` the
  patched code uses (an I-reference run via the real repo), so the bijection in
  §2 is exercised on real data.
- **`datetime.strftime` / `offset_formats` indexing** (the offset renderer,
  `dates.py:840-846`): unchanged downstream. The conformance shadow renders its
  `(level, show_offset)` decision through the SAME real `strftime` call, so the
  observable compared is the exact F2P observable `get_offset()`.

The pre-patch repo behaviour the change removes (refinement audit only, not in
the consumer spec view): the suppression guard was `if level < 2:` with no
`np.any(unique == 1)` condition (`dates.py:801` pre-patch) — i.e.
`suppressOffset = decide (level < 2)`, dropping the `colHasOne` factor.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`22871`** so the
consumer-side verdict (§11.3) is reproducible. It builds the R/I shadow of
`offsetDecision`/`offsetSelection` in Python (all ops I/R-tagged; no A-tagged
callee to leave as a real callee — the unchanged `num2date`/`strftime` are run
by the real repo on both sides) and diffs the resulting offset string against the
real patched `ConciseDateFormatter.get_offset()` over ≥10⁵ fuzzed tick sets
(sub-second to multi-year spans, plus the three F2P spans and the issue example).
