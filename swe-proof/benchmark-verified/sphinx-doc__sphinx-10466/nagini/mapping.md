# mapping.md — sphinx-doc__sphinx-10466

Binds every `model.py` symbol to its repository counterpart at
`base_commit = cab2d93076d0cca7c53fac885f927dde3e2a5fec`, states the type
abstraction, and records that the changed operation is modelled deeply (no
axiomatized callee).

Repo file under change: `sphinx/builders/gettext.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `canonical_positions(recorded)` | the position list built inside `Catalog.__iter__` — `sphinx/builders/gettext.py:58-62` (the `positions = ...` assignment on line 60) | the modeled changed behaviour: from the recorded occurrences of a message, produce the reported position list |
| `dedup_sort(s)` *(deep model — A-reference)* | the `sorted(set(...))` applied to the projected `(source, line)` pairs in the patched `__iter__` (`sphinx/builders/gettext.py:60-61` post-patch) | pure spec: the ordered set (deduplicated, strictly ascending) of a sequence; the deep model of the real `sorted(set(...))`, validated `dedup_sort == sorted(set(...))` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `ins(x, s)` | one ordered-set insertion step of `sorted(set(...))` | pure spec helper: insert one key into a strictly-sorted sequence, dropping it if already present |
| `insert_sorted(xs, key)` | the imperative skeleton of one `ins` step | verified loop computing `ins` |
| `recorded: List[int]` | `self.metadata[message]` projected to its `(source, line)` pairs (the comprehension target `(source, line) for source, line, uuid in self.metadata[message]`) | the recorded occurrences of one message, in scan order, with duplicates |
| `Result()` of `canonical_positions` | `positions`, passed to `Message(message, positions, uuids)` (`gettext.py:62`) | the reported position list for the message |

The pre-patch repo expression the change replaces (for the refinement audit, not
referenced from the consumer spec view): `positions = [(source, line) for
source, line, uuid in self.metadata[message]]` (`gettext.py:60`) — the verbatim
projection that keeps duplicates and scan order.

Out of model scope (unchanged by the patch, observably independent): the
sibling `uuids = [uuid for source, line, uuid in self.metadata[message]]`
(`gettext.py:61`) is untouched by the gold patch and is not modeled. Its
construction does not depend on `positions`; the F2P test asserts only on
`.text` and `.locations`. `Message.__init__` (`gettext.py:33-36`) merely stores
`locations = positions`; it is the identity on the list content the test reads.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a position `(source: str, line: int)` tuple | a single `int` key | the positions occurring in one message form a finite set of comparable tuples; under the unique strictly-monotone, equality-preserving enumeration of that universe (`tuple -> its index in the sorted-distinct universe`) each tuple ↔ one integer key. Python tuple comparison `(s1,l1) < (s2,l2)` (lexicographic) ↔ integer `<`; tuple equality ↔ integer `==`. Because the modeled operation (`sorted` + `set`) uses ONLY `<` and `==` on the elements, an order- and equality-preserving carrier is observationally exact (validated in axiom_check.py §check 2). |
| `list` of `(source, line)` positions (`self.metadata[message]` projected) | `List[int]` of keys | element-wise under the tuple↔int bijection; `len`, list `+`, scan order, and duplicate multiplicity all preserved |
| a `list` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror list `+`/slice/`len`/index |
| `sorted(set(positions))` (the patched expression) | `dedup_sort(ToSeq(keys))` | the ordered set: deduplicate (drop repeats) then arrange strictly ascending. `set(...)` ↔ deduplication; `sorted(...)` ↔ strict ascending order; the composition is `dedup_sort` |

`str` indexing/iteration is banned in Nagini, so a `(source, line)` position is
not modelled as a character sequence + int; it is modelled by its order/equality
identity (an integer key), which is all the `sorted`/`set` operation observes.

## 3. Callee provenance

### 3.1 `dedup_sort` deep model ↔ `sorted(set(...))` (A-reference)
**Operation:** CPython `sorted(set(positions))` on a list of `(source, line)`
tuples. The changed operation (the addition of deduplication + sort) is the
operation under specification, so it is modelled **deeply** by the `@Pure`
construction `dedup_sort` (built from `ins`) in the `pure` region; there is **no
`@ContractOnly` axiom** the proof consumes. The deep model is validated equal to
the real operation out-of-band by axiom_check.py (G-AX):

  * `set(xs)` removes duplicate elements; `sorted(...)` returns a new list in
    ascending order (`<`). Hence `sorted(set(xs))` is the strictly-increasing
    list of the distinct elements of `xs` — exactly what `dedup_sort` computes
    (`ins` inserts each element at its sorted slot, dropping it if already
    present; `dedup_sort` folds `ins` over the sequence).
  * `set`/`sorted` use only element `==`/`<`. Modelling each `(source, line)`
    position by an order- and equality-preserving integer key therefore loses
    nothing: `sorted(set(positions))` corresponds element-for-element to
    `dedup_sort(keys)` under the tuple↔int bijection (§2).

Python docs: `sorted` returns a new sorted list using `<`
(https://docs.python.org/3/library/functions.html#sorted); `set` is an
unordered collection of distinct hashable objects
(https://docs.python.org/3/library/stdtypes.html#set). Both are referentially
transparent on the finite tuple inputs here.

**Soundness check (G-AX):** `axiom_check.py` runs the real `sorted(set(...))` on
boundary inputs (empty, all-duplicate, reversed, already-sorted, mixed) plus
20 000 randomized integer-key fuzz inputs and asserts `dedup_sort == sorted(set
(...))` everywhere. It then validates the integer-key abstraction for actual
`(source, line)` positions — including the exact F2P scenario — on 1 boundary +
20 000 fuzz position lists, asserting the decoded ordered set of keys equals the
real ordered set of tuples. stdlib-only (`random`); exit 0 iff sound.
