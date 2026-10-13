# refinement.md — django__django-14089

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `reverseEnum` impl region and the deep `revSeq` model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (the proof uses an axiom's `ensures`), **A-reference** (a deep
model validated == the real callee by `axiom_check.py` / G-AX), or **I**
(identical concrete operation). The claim: *any implementation that verifies
against this frozen spec, refined per the map below, is behaviourally equal to
the gold patch on the tested inputs, so it resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The backward-enumeration site — new `OrderedSet.__reversed__`

Gold hunk (`django/utils/datastructures.py`, inserted after `__iter__`):
```
+    def __reversed__(self):
+        return reversed(self.dict)
```

The gold method has two observable consequences, and the F2P test asserts both:
the object it hands back **enumerates the elements backwards** (`list(s) ==
[3, 2, 1]`) and that object **is a self-advancing, single-use traversal**
(`isinstance(s, collections.abc.Iterator)`). The frozen spec makes seven
observations, through four handles drawn from the same unchanged collection.
One handle is interrogated four ways — `out.1` (C0: its own answer to one
single-element request), `out.2.1` (C1: `demand` further single draws),
`out.2.2.1` (C2: what that same handle has left), `out.2.2.2.1` (C3: what it
yields when asked again). Two further handles are each asked one question, and
each is **fresh**, i.e. still holding every element it will ever give:
`out.2.2.2.2.1` (C4: the element AT A POSITION) and `out.2.2.2.2.2.1` (C5: yield
everything, with no prior advance). A fourth fresh handle is asked to give up its
elements POSITION BY POSITION: `out.2.2.2.2.2.2` (C6: collect `0`, then `1`, then
`2`, until refused). The rows below refine each observation.
C0, C3, C5 and C6 are what carry the second consequence; see §B.

| # | Solution.lean impl op (`reverseEnum`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `elements : List Int` | the receiver `self`, whose ordered contents are `self.dict`'s keys in insertion order | R | `OrderedSet`'s ordered contents ↔ `List Int` of distinct element keys in insertion order (mapping.md §1, §2). `self.dict = dict.fromkeys(iterable or ())` and `__iter__` returns `iter(self.dict)`, so the forward enumeration is exactly `elements`. |
| A2 | `result = revSeq elements`, the reversal of the forward enumeration, computed by the backward loop that appends each element from the end (`result := result ++ [elements[i-1]!]`, `i` from `length` down to `0`) — the sequence all seven observations are read off | the sequence `reversed(self.dict)` enumerates | A-reference | the changed operation — providing a backward enumeration — is modeled **deeply**: `revSeq` (the spelled-out front-recursive reversal in the `pure` region) and the verified loop in `reverseEnum` ARE the reversal. There is no consumed `reversed` axiom — the proof never depends on one. Instead the deep model is validated **== the real callee** out-of-band: G-AX (`axiom_check.py`) builds `dict.fromkeys(items)` and asserts `list(reversed(d)) == revSeq(list(d))`. Because `self.dict` keeps insertion order with distinct keys, `reversed(self.dict)` yields the keys in reverse insertion order — exactly the element-wise reversal of `iter(self.dict)` (mapping.md §3.1). The model loop and the real callee enumerate the same sequence. |
| A3 | `let given := result.head?` — the handle's own answer to one single-element request, returned as `out.1` and pinned by C0 to `(revSeq elements).head?` | `next(h, None)` where `h` is the object the new method hands back — i.e. `h.__next__()`, put to that object itself | R + I | `reversed(self.dict)` is a `dict_reversekeyiterator`, so `h.__next__()` is defined and answers with the first key of the backward enumeration, raising `StopIteration` only when the dict is empty. `Option Int` ↔ "an element, or a refusal": `some e` ↔ `next(h)` yielded `e`; `none` ↔ the request was refused. `result.head?` is exactly that — `some` of the first element of the backward enumeration, `none` iff it is empty. Gold satisfies this because the request is answered *by the handed-back object*, with no further traversal derived from it first (§B). |
| A4 | `let remaining := result.tail`; the counting loop on `j`; `let drawn := List.take j remaining` (`out.2.1`, C1) and `let firstDrain := List.drop j remaining` (`out.2.2.1`, C2) | `demand` further single `next(h)` calls on the SAME `h`, then `list(h)` on that same `h` | R + I | one iterator carries one position. After A3 answered, `h` stands one element in, so everything later is measured against `(revSeq elements).tail` — hence `remaining`. `next(h)` repeated `demand` times yields the next `min(demand, len(remaining))` elements and stops early once the traversal is spent (the loop guard `j < demand ∧ j < remaining.length`, `done_with j = demand ∨ j = remaining.length` — asking past the end simply yields fewer, matching `StopIteration` ending the draws); `list(h)` afterwards drains from the position those draws left, which is `List.drop j remaining`. `drawn ++ firstDrain = remaining` in the model ⇔ no element of `h` is repeated or skipped across the boundary between the two ways of asking. |
| A5 | `let secondDrain := List.drop k remaining`, where the third loop has driven `k` to `remaining.length` (`out.2.2.2.1`, C3, pinned to `[]`) | `list(h)` a SECOND time, on the same now-drained `h` | R + I | a Python iterator that has raised `StopIteration` keeps doing so: `dict_reversekeyiterator` is spent, not restartable, so the second `list(h)` is `[]`. The model mirrors this by carrying the drain's own progress in `k` and reading the remainder from there — `List.drop remaining.length remaining = []`. A re-readable object (a list, a tuple, a view whose iteration restarts) answers with the elements over again and is excluded here. |
| A6 | `out` is built from freshly-computed lists; `elements` is read-only (never mutated — Lean is functional, the parameter is not `mut`) | `reversed(self.dict)` returns a fresh iterator and does not mutate `self.dict` | R + I | the new method only reads `self.dict`; the functional carrier (no `mut` on `elements`, directive 5) mirrors that. G-AX confirms materializing `reversed(d)` leaves `list(iter(d))` unchanged (read-only). |
| A7 | `let positional : Option Int := none` (`out.2.2.2.2.1`, C4, pinned to `none`) | `h2[0]`, where `h2` is a SECOND object obtained by calling the new method again on the same unchanged collection — a request for the element at a position, put to a handle that has not been advanced | R + I | `Option Int` ↔ "an element, or a refusal", the same refinement A3 uses. `reversed(self.dict)` is a `dict_reversekeyiterator`; it implements no `__getitem__`, so `h2[0]` raises `TypeError: 'dict_reversekeyiterator' object is not subscriptable`, which is the refusal `none`. Measured on gold at `[1,2,3]`, `[4]`, `[5,6,7,8]` and `[]` — every case `None`. The model's `none` is therefore the honest constant: gold refuses this request over the whole domain. What the clause excludes is any carrier that answers a bare positional read with an element. It bounds the shape but does not by itself close the legacy sequence-protocol route — an object may decline this one read and still serve the `0, 1, 2, …` request sequence; A9/C6 is the observable that closes that route. See §B. |
| A8 | `let freshDrain := result` (`out.2.2.2.2.2.1`, C5, pinned to `revSeq elements`) | `list(h3)`, where `h3` is a THIRD object from the same unchanged collection, drained with no prior advance — literally the F2P's own call, `list(reversed(OrderedSet([1, 2, 3])))` | R + I | `iter(h3)` on a `dict_reversekeyiterator` returns the object itself, and draining it walks the whole backward enumeration, so `list(h3) == list(reversed(self.dict))` = the reversal of the forward enumeration = `revSeq elements` (A2; G-AX validates that sequence equality). This is the one observation C0–C3 cannot make: each of those looks at a handle the C0 request has ALREADY stepped, so all four are blind to a carrier whose enumeration only comes into being once it has been advanced. |
| A9 | `let byPosition : List Int := []` (`out.2.2.2.2.2.2`, C6, pinned to `[]`) | the elements a consumer collects from `h4` — a FOURTH object from the same unchanged collection — by asking for the element at position `0`, then `1`, then `2`, and so on until refused, each request put through the object's OWN element-at-position access (`operator.getitem(h4, j)`) | R + I | this is the access path an index-driven traversal itself uses, asked in the order it uses. `dict_reversekeyiterator` implements no element-at-position access at all — its type has no `mp_subscript` and no `sq_item` — so the very FIRST request raises `TypeError` and the collection stops empty. Measured on gold over the whole G-CONF domain (boundary + 100000 fuzz inputs): every case `[]`, including the empty collection, the singleton and the F2P witness. The model's `[]` is therefore the honest constant. What the clause excludes is any carrier whose elements are obtainable by position, INCLUDING one that declines an isolated bare read (A7) while still serving the `0, 1, 2, …` sequence — the refusal here is a fact about the object rather than about one question, which is why this row and not A7 closes the legacy sequence-protocol route (§B). |

The discriminating content of the change — the backward enumeration is the
**reversal** of the forward enumeration, not the forward order over again —
lives in A2, surfacing through C0/C1/C2/C5 (`(revSeq elements).head?`, the two
halves of `(revSeq elements).tail`, and the whole of `revSeq elements`) ⇔ the new
`reversed(self.dict)` (real). Before the patch there was no `__reversed__` (and
`OrderedSet` exposes no `__getitem__`/sequence protocol), so
`reversed(OrderedSet(...))` could not produce a reverse-ordered traversal;
`Solution_prepatch.lean` reproduces the faithful pre-patch skeleton — the only
traversal available hands the elements back in **forward** (`__iter__`) order,
observed the same seven ways — and **fails** the frozen postconditions, which is
exactly the spec sensing the change (G-DIFF). Measured:
`Solution_prepatch.lean:166:26: error: unsolved goals`, four residual goals, all
of them `ensures` cases and no tactic error, among them
`case «ensures_7: out.1 = (revSeq elements).head?»`
and
`case «ensures_2: out.2.2.2.2.2.1 = revSeq elements»`
— the forward-order handle answers the single-element request with the *first*
element instead of the last, and a consumer who only drains what it was handed
gets the forward order rather than the backward one.

## B. Where the iterator-ness obligation is discharged

The F2P test asserts `isinstance(reversed(OrderedSet([1, 2, 3])),
collections.abc.Iterator)` alongside the value assertion. This leg is **not**
delegated out-of-band, and it is **not** a kind-3 (unexpressible) step: the
frozen spec states it, as behaviour of the changed operation, in C0, C3, C5
and C6.

What the seven observations force of the object `h` the method hands back:

1. **It answers a single-element request itself.** C0 says `out.1 = some e`
   whenever the collection is non-empty. Under A3's refinement `out.1` is what
   `next(h, None)` returns — the result of `h.__next__()`. An object with no
   `__next__` (a `list`, a `tuple`, a keys view, any container from which a
   consumer must first derive a further traversal) refuses that request with
   `TypeError`, so the observation is a refusal, `none`, and C0 fails on every
   non-empty collection.
2. **Iterating it is possible and resumes from its own position.** C1 and C2
   measure `demand` further draws and then a drain of *that same* object, and
   their conjunction pins `out.2.1 ++ out.2.2.1 = (revSeq elements).tail`: the
   drain must begin exactly where the single draws stopped. An object whose
   iteration restarts from the beginning re-yields the already-drawn elements
   and breaks C2.
3. **It is single-use.** C3 says the second drain is `[]`. A re-readable
   snapshot answers with the same elements a second time and breaks C3.
4. **An element cannot be taken from it at a position.** C4 says a handle still
   holding everything refuses `h2[0]`. So a bare read at a position does not
   produce an element.
5. **Its enumeration is there before it is advanced.** C5 says a handle that is
   only drained, never stepped, yields the whole backward enumeration. So
   `iter()` on the handed-back object succeeds and delivers everything.
6. **No element is reachable by position at all.** C6 says a consumer that
   collects position by position — asking the object's own element-at-position
   access for `0`, then `1`, then `2`, until it refuses — walks away with
   NOTHING. So element access is available only by advancing the object. This is
   strictly stronger than point 4 and is what that point cannot deliver on its
   own: refusing one bare read is a fact about that request, whereas refusing
   the whole `0, 1, 2, …` sequence is a fact about the object.

Points 1 and 2 are the two methods Python's `Iterator` ABC requires:
`collections.abc.Iterator.__subclasshook__` is exactly
`_check_methods(C, '__iter__', '__next__')` (`_collections_abc.py`, read at the
installed interpreter), and `_check_methods` returns `NotImplemented` — i.e.
`issubclass` is `False` for an unregistered class — as soon as one of the two is
absent. The closure argument therefore runs: C5 says `iter(h)` succeeds and
delivers the whole enumeration; `iter()` can succeed in exactly two ways, through
`__iter__` or through the legacy `__getitem__` sequence protocol; C6 rules out
the second, because legacy iteration obtains its elements by asking the object's
own element-at-position access for `0`, then `1`, then `2`, until it refuses —
which is precisely the sequence of requests C6 pins to yield NOTHING, while C5
says a drain yields everything; the two are inconsistent for a legacy-protocol
carrier, hence `__iter__` exists. C0 says `__next__` exists and answers. Both
methods present ⇒ `isinstance(h, collections.abc.Iterator)`.

**Why C4 cannot carry this step, and C6 must.** An earlier form of this argument
put C4 in C6's place, reasoning that legacy iteration "must answer `h[0]` with
the first element whenever the enumeration is non-empty", so a refusal of that
one read excludes the protocol. That inference does not hold, and the gap is a
real one rather than a technicality: what the protocol requires is that the
`0, 1, 2, …` REQUEST SEQUENCE be served, and an object is free to distinguish
that sequence from an isolated bare read of position `0` — by answering
positions relative to how far it has already been advanced, or by inspecting its
caller. Such an object refuses `h2[0]`, satisfying C4 exactly as gold does, and
still hands `list()` the full enumeration through the index protocol, so it
reproduces every one of C0–C5 while having no `__iter__` and therefore failing
the F2P `isinstance` assertion. Carriers of this shape were built in CPython and
measured: they match gold on all six of the older observations across every
input tried, and `isinstance(handle, collections.abc.Iterator)` is `False` where
gold's is `True`. C6 closes it because it asks through the object's own
element-at-position access, in the same `0, 1, 2, …` order an index-driven
traversal uses, so no carrier can serve the protocol while refusing C6: serving
the protocol IS what C6 observes. C4 is retained — it is true of gold over the
whole domain (A7) and it independently excludes the plainly indexable carriers —
but it bounds the shape rather than determining it.

**Why C4 and C5 are in the spec, measured rather than argued.** C0–C3 alone do
*not* close this leg — the earlier form of this document claimed C2 ∧ C3 squeezed
the legacy-protocol loophole shut, and direct measurement refutes that claim. Two
carriers were built in CPython and observed exactly as A3–A8 prescribe, over
`([1,2,3], demand ∈ {0,1,7})`, `([4], 0)`, `([], 0)` and `([5,6,7,8], 2)`:

| carrier | shape | C0..C3 vs gold | C4 | C5 | F2P `isinstance` | F2P `list(s) == [3,2,1]` |
|---|---|---|---|---|---|---|
| gold `reversed(dict.fromkeys(items))` | `dict_reversekeyiterator` | — | `None` | `[3, 2, 1]` | True | True |
| `Sneaky` | `__next__` plus the legacy `__getitem__` protocol, **no** `__iter__`; `__getitem__` ignores the index and hands back the next element, raising `IndexError` once spent | **identical on every case** | `3` | `[3, 2, 1]` | **False** | True |
| `LazyIter` | `__iter__` and `__next__`, but `__iter__` yields nothing until the object has been advanced at least once | **identical on every case** | `None` | `[]` | True | **False** |

`Sneaky` is a working index-driven traversal: legacy iteration walks `h[0]`,
`h[1]`, … and, because each call hands back the next element, the drain yields
precisely the remainder and then stops — so C2 holds, and the drain that follows
finds nothing, so C3 holds too. It reproduces all four old observations and is
**not** an `Iterator`. `LazyIter` reproduces all four as well, because every one
of them is made *after* the C0 request has stepped the object; a consumer who
only drains what it was handed gets `[]`, and the F2P value assertion fails. C4
rejects the first (`3 ≠ none`) and C5 rejects the second
(`[] ≠ revSeq elements`), and the reject lane measures exactly this:
`properties.py` carries a rival refuted by C4 alone and a rival refuted by C5
alone, each attribution read off that rival's own `case «ensures_N: ...»` header.

**The residue, stated honestly.** Three things in this section are **R** steps —
facts about the Python carrier protocol, argued here, not discharged by the Lean
proof — and they are the only residue of this leg.

* The protocol facts themselves: that `next()` on an object without `__next__`
  raises, that `iter()` succeeds only via `__iter__` or legacy `__getitem__`, and
  that the subclass hook is `_check_methods(C, '__iter__', '__next__')`.
* **Neither C4 nor C6 discriminates at the empty collection.** With no
  elements, a legacy-protocol carrier's first positional request raises
  `IndexError`, so the bare read is `none` and the position-by-position
  collection is `[]` — both agreeing with gold (measured: `Sneaky` at
  `items=[]` gives `positional = None`, `byPosition = []`). The clauses are
  universally quantified over `elements`, so a *single* carrier of that shape is
  still refuted — at every non-empty collection — and the failing test's own
  input is `[1, 2, 3]`. What is not excluded is a carrier that is only ever
  handed empty collections, where the F2P assertion is not made either.
* **C4 and C6 are deliberately stronger than the ABC.** An object that is a
  genuine iterator *and additionally* supports subscripting would satisfy the
  F2P and still fail them. That direction is sound — it shrinks the admitted
  set, so `verify ⇒ resolved` is preserved — and it is the price of stating
  "elements are obtainable only by advancing, never by position" as an
  observation rather than as a type name. Refusing positional access is
  behaviour of the object the changed operation hands back, and gold refuses it
  — both the isolated read and the whole `0, 1, 2, …` sequence — over the entire
  measured domain (A7, A9).

Accordingly the `isinstance(reversed(d), collections.abc.Iterator)` assertion in
`axiom_check.py` is retained as a **cross-check on the primitive gold itself
calls**, not as the bearer of the obligation. That check ranges over `reversed`
applied to a real `dict`; it is a fact about gold's own choice of callee and says
nothing about a candidate that chose a different one, so it could never
constrain a candidate implementation. The constraint on a candidate is
C0 ∧ C3 ∧ C5 ∧ C6, in the frozen spec. See mapping.md §1 (the `out.1`,
`out.2.2.2.1`, `out.2.2.2.2.2.1` and `out.2.2.2.2.2.2` rows) and §3.1 ("Scope of
this lane").

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — handing back a self-advancing, single-use backward traversal — is
modeled **deeply** on both legs: its enumerated sequence by the spelled-out
reversal `revSeq` (step A2, an **A-reference**), and its traversal behaviour by
the seven observations of four handles (steps A3–A5, A7, A8, A9, R + I,
constrained by the frozen clauses C0–C6 per §B). Neither leg is hidden behind an axiom about the
function under change: there is **no consumed `reversed` axiom** and the model's
`axioms` region is empty. The builtin `reversed(dict)` appears only as the
**A-reference** that G-AX validates the deep sequence model against.

## D. verify(model) ⇒ resolved

`reverseEnum` verifies only if all seven clauses hold. C0 ∧ C1 ∧ C2 ∧ C5 force
the enumerated sequence to be the exact reversal of the forward enumeration (A2)
— an impl that preserves the order, drops, duplicates, reorders, restarts, or is
empty until stepped fails one of them — and C0 ∧ C3 ∧ C5 ∧ C6 force the handle to
be the self-advancing, one-shot, position-free traversal (A3, A5, A8, A9, §B),
with C4 (A7) bounding the shape alongside them. By R
(`OrderedSet` contents ↔ `List Int`; `self.dict` insertion order ↔ `elements`)
the verified sequence equals what `reversed(self.dict)` enumerates on the tested
inputs; by G-AX the deep model `revSeq` equals the real `reversed(dict)`
(A-reference); and by §B the object a verifying candidate hands back satisfies
both F2P assertions — the values `list(s) == [3, 2, 1]` (C5 is that call
directly) and `isinstance(s, collections.abc.Iterator)` (C0 ∧ C5 ∧ C6 through the
subclass hook). Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement and the audited callee — and the gold
patch resolves (G-RESOLVE). The trust points are exactly deep-model soundness for
the sequence leg (G-AX) and the three carrier-protocol R steps of §B; refinement
fidelity is this document (G-EQ); the R/I leg is mechanically refuted by G-CONF,
whose oracle makes all seven observations against the patched
`OrderedSet.__reversed__`.
