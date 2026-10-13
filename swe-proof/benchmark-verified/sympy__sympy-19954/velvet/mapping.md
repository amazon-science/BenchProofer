# mapping.md — sympy__sympy-19954

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 6f54459aa0248bf1467ad12ee6333d8bc924a642`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records callee
provenance and the pinned fuzz seed.

Repo file under change: `sympy/combinatorics/perm_groups.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `pruneParallelSystems (blocks numBlocks repBlocks removeFlags)` | the per-orbit prune of the three parallel lists inside `PermutationGroup.minimal_blocks` — `sympy/combinatorics/perm_groups.py:2197-2208` (post-patch `2197-2209`) | the modeled changed operation |
| `blocks`    | local `blocks` list — `perm_groups.py:2174` (`blocks = []`) | one of the three index-aligned parallel lists (block-system descriptors) |
| `numBlocks` | local `num_blocks` list — `perm_groups.py:2175` (`num_blocks = []`) | parallel list (numbering tuples) |
| `repBlocks` | local `rep_blocks` list — `perm_groups.py:2176` (`rep_blocks = []`) | parallel list (representative sets) |
| `removeFlags` | the per-position "this system is non-minimal, drop it" decision computed by the inner `for i, r in enumerate(rep_blocks)` comparison loop — `perm_groups.py:2198-2206` | read-only input: which positions the (unchanged) minimality comparison marks for removal |
| `keepByMask`  | the three post-patch list-comprehensions — `perm_groups.py:2207-2209` | pure spec: drop the flagged positions from one list |
| `numKept`     | (no single repo symbol) length of any mask-filtered list | pure spec: count of kept positions; used to prove alignment |

The pre-patch repo constructs the change removes (refinement audit only, not in
the consumer spec view): the in-loop `del num_blocks[i], blocks[i]`
(`perm_groups.py:2201`), the `to_remove` accumulator (`:2197`, `:2202`), and the
value-based `rep_blocks = [r for r in rep_blocks if r not in to_remove]`
(`:2208`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `blocks` — Python `list` of block-system descriptors (each a `list[int]`) | `List Int` | each descriptor is an opaque, distinct identifier `Int`; `blocks[k]` ↔ `(l : List Int)[k]`; `len(blocks)` ↔ `l.length`. Only POSITION and identity matter to the prune — never the internal structure of a descriptor — so an `Int` token per descriptor is a faithful, total carrier. |
| `num_blocks` — Python `list` of numbering `tuple`s | `List Int` | one opaque `Int` per tuple (same justification: the prune treats each entry as an indivisible positional element). |
| `rep_blocks` — Python `list` of representative `set`s | `List Int` | one opaque `Int` per set. The prune never inspects a set's contents (post-patch); the pre-patch value test `r not in to_remove` is over set identity, modeled by `Int` equality. |
| the per-position removal decision | `List Bool` | `removeFlags[i] = True` ⇔ the comparison loop marked position `i` for deletion (`len(r) > len(rep) and rep.issubset(r)`); `False` otherwise. One flag per position, `len == len(blocks)`. |
| the three returned lists | `(List Int) × (List Int) × (List Int)` | the three rebound locals `(blocks, num_blocks, rep_blocks)` after the prune, in that order. |

The three input lists are index-aligned (equal length) on entry — `blocks`,
`num_blocks`, `rep_blocks` are only ever `.append`-ed together
(`perm_groups.py:2211-2213`), so they share a length; the `require` clauses pin
this, and the comparison loop produces exactly one flag per position.

## 3. Callee provenance

**No axioms and no deep-model references.** The operation under specification —
dropping the flagged positions from the three parallel lists — is modeled
DEEPLY by `keepByMask` (pure region) and is transliterated wholesale by G-CONF
(R/I). It calls no unchanged repo/library function whose behaviour the proof
must assume: the only inputs are the three lists and the per-position flags, all
modeled directly. The minimality comparison that *produces* the flags
(`perm_groups.py:2198-2206`) is UNCHANGED by the patch and lies outside the
modeled slice; its output is the read-only input `removeFlags`. Hence
`axiom_check.py` is a `skip` stub (`meta.json gates.G-AX.status = "skip"`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`19954`** so the
consumer-side verdict is reproducible. The shadow transliterates `keepByMask`
applied to all three lists (the post-patch list-comprehensions); the oracle is
`patch.diff`'s behaviour — the three list-comprehensions at
`perm_groups.py:2207-2209` run on the same `(blocks, num_blocks, rep_blocks,
removeFlags)`. Every R/I op is concrete; there is no A-tagged callee to leave
real.
