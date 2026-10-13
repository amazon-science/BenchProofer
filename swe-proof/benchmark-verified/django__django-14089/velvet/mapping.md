# mapping.md — django__django-14089

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = d01709aae21de9cd2565b9c52f32732ea28a2d98`, states the type
abstraction (R-refinements), and gives the provenance of the one kind-A
obligation (an **A-reference** deep model checked by `axiom_check.py` / G-AX;
there is **no** consumed axiom — the `axioms` region is empty).

Repo file under change: `django/utils/datastructures.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reverseEnum (elements, demand) → out` | the new `OrderedSet.__reversed__(self)` — `django/utils/datastructures.py` (the method inserted after `__iter__` at line 25-26, before `__contains__` at line 28) | the modeled changed function: the backward enumeration of the ordered collection, observed through the single handle it hands back |
| `elements` (parameter) | the keys of `self.dict` in insertion order — `OrderedSet.__init__` sets `self.dict = dict.fromkeys(iterable or ())` (`datastructures.py:10-11`); `__iter__` returns `iter(self.dict)` (`datastructures.py:25-26`) | the ordered contents of the collection (distinct keys, insertion order) |
| `revSeq (s)` *(deep model — A-reference)* | `reversed(self.dict)` — CPython builtin `reversed` over a `dict` (the body of the new `__reversed__`), materialized to a list | pure spec: the reversal of a sequence; the deep model of the new method's net effect, validated `revSeq == list(reversed(dict))` by `axiom_check.py` (G-AX), NOT consumed as an axiom |
| `out.1 : Option Int` (C0) | `next(h, None)` where `h` is the object the new method hands back — the answer the handle gives to a single-element request put **to the handle itself** | `some e` ⇔ the handle yields the element `e` on its own; `none` ⇔ it has nothing to give (`StopIteration`, i.e. the collection is empty). A handle that must first be converted into something else before one element can be taken from it has no `some` to give here, and is the observable this clause excludes |
| `out.2.1`, `out.2.2.1` (C1, C2) | the elements the SAME handle `h` yields to `demand` further single `next(h)` calls, and then everything left in it (`list(h)`) | the further single draws ↔ `out.2.1`; the subsequent drain ↔ `out.2.2.1`. Both are measured against what the handle has left after answering the first request, hence `(revSeq elements).tail` |
| `out.2.2.2.1` (C3) | `list(h)` a SECOND time, on the same now-spent handle | `[]` ⇔ the handle is one-shot: a consumer cannot obtain the elements twice from it. A re-readable container would answer with the same elements again |
| `out.2.2.2.2.1 : Option Int` (C4) | `h2[0]` where `h2 = reversed(OrderedSet(items))` is a SECOND, FRESH handle obtained from the same unchanged collection — a request for the element AT A POSITION, put to a handle that still holds every element it will ever give | `none` ⇔ the handle refuses: it has no positions to be read at, only the place it has currently reached. In gold `h2` is a `dict_reversekeyiterator`, which is not subscriptable, so `h2[0]` raises `TypeError` — the refusal. An object that ANSWERS it (a `list`, a `tuple`, or the legacy `__getitem__` sequence-protocol shape) gives `some e` here and is excluded by this clause even when every element it enumerates is correct |
| `out.2.2.2.2.2.1 : List Int` (C5) | `list(h3)` where `h3 = reversed(OrderedSet(items))` is a THIRD, FRESH handle that has NOT been advanced first — the whole enumeration taken in one drain | `revSeq elements` ⇔ a consumer who only drains the handle it was handed gets the complete backward enumeration in that order. This is literally the failing test's own call, `list(reversed(OrderedSet([1, 2, 3]))) == [3, 2, 1]`, and it is the one observation C0–C3 cannot make: all four of those look at a handle the single-element request has ALREADY stepped |
| `out.2.2.2.2.2.2 : List Int` (C6) | the elements collected from `h4 = reversed(OrderedSet(items))`, a FOURTH, FRESH handle, by asking it for the element at position 0, then 1, then 2, ... and stopping at the first refusal — each request put through the object's OWN element-at-position access (`operator.getitem(h4, j)`), which is the access path an index-driven traversal itself uses | `[]` ⇔ the handle serves NO position, so a consumer trying to collect it position by position walks away with nothing. In gold `h4` is a `dict_reversekeyiterator`, whose type implements no element-at-position access at all, so the very first request raises `TypeError` and the collection is empty. This is strictly stronger than C4 and is the clause that makes the refusal a fact about the OBJECT rather than about one question: C4 asks a single position and can be declined by an object that nonetheless serves the 0, 1, 2, ... sequence (an object whose positional access is relative to how far it has been advanced, or which distinguishes its caller, does exactly that), whereas an object that refuses this whole sequence cannot supply its elements by position to anyone |

`elements` is bound to the FORWARD enumeration as it exists at `base_commit` —
i.e. before the change — so it is an input the change does not touch, and every
clause is stated as a function of it. The unchanged neighbours that fix the
carrier semantics (read, not referenced
from the consumer spec view): `OrderedSet.__init__` (`datastructures.py:10-11`,
`self.dict = dict.fromkeys(iterable or ())` — distinct keys, insertion order)
and `OrderedSet.__iter__` (`datastructures.py:25-26`, `return iter(self.dict)`
— forward enumeration is the keys in insertion order). The collection's order
is fully carried by `self.dict`'s insertion order; the new `__reversed__`
delegates to the builtin `reversed` on that dict.

## 2. Type abstraction (R-refinements)

| repo reality | Lean carrier | bijection |
|---|---|---|
| `OrderedSet` instance (a distinct-key, insertion-ordered collection backed by `self.dict`) | `List Int` of element keys in insertion order | dict keys in insertion order ↔ list elements in order; `list(iter(self.dict))` ↔ `elements`; `len(self.dict)` ↔ `elements.length`. Elements are distinct hashables; modelled as distinct `Int` keys (the F2P uses `int` keys `1,2,3`). |
| the object the changed method hands back (in gold, a `dict_reversekeyiterator`) | the 7-tuple `Option Int × List Int × List Int × List Int × Option Int × List Int × List Int` — the answers four consumers get: one handle interrogated `next(h, None)`, `demand` further `next(h)` calls, `list(h)`, `list(h)` again; a second, fresh handle asked `h2[0]`; a third, fresh handle asked `list(h3)`; a fourth, fresh handle collected position by position (`0`, then `1`, then `2`, until refused) | four handles from the same unchanged collection, seven observations. **Iterator-ness is carried by these observations, not by the carrier type**: `out.1 = some e` says the object advanced ITSELF one element (so it is the traversal, not a container a traversal must be derived from), `out.2.2.2.1 = []` says it was spent by being drained (so it is one-shot), `out.2.2.2.2.1 = none` says a bare read at a position does not produce an element, `out.2.2.2.2.2.1 = revSeq elements` says the enumeration is already there for a consumer who only drains it (so it is not a traversal that exists only once stepped), and `out.2.2.2.2.2.2 = []` says NO position is served at all, so the elements are not obtainable by position by anyone and advancing is the only channel. A `list`, a `tuple`, or a view object whose `__iter__` returns a fresh or shared iterator fails the first observation, because `next()` on it raises `TypeError` rather than yielding an element — `none`, not `some`. |
| `reversed(...)`/`iter(...)` element ordering | `revSeq : List Int → List Int` | `revSeq` is the sequence reversal (`revSeq (c::cs) = revSeq cs ++ [c]`); it mirrors `list(...)[::-1]`. `elements.drop i`/`elements[i-1]!`/`elements.length` mirror Python slice/index/`len`. |

`OrderedSet` is generic over hashables; the carrier `List Int` is the
`int`-keyed instance the F2P test exercises (`OrderedSet([1, 2, 3])`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `revSeq` deep model ↔ `reversed(dict)` (A-reference)
**Callee:** CPython builtin `reversed(d)` over a `dict` `d`. Since Python 3.8,
`dict` (and therefore `dict.fromkeys`) supports `reversed`, yielding the keys
in reverse insertion order; the instance's image runs Python 3.x (Django 4.0),
where this is available. The new `__reversed__` returns `reversed(self.dict)`.
Because `self.dict` preserves insertion order with distinct keys and `__iter__`
yields `iter(self.dict)` (the keys in insertion order), the materialized
backward enumeration is exactly the element-wise reversal of the forward
enumeration:

  `list(reversed(self.dict)) == list(iter(self.dict))[::-1]`,

which is what the deep model `revSeq` encodes
(`revSeq (c::cs) = revSeq cs ++ [c]`). The changed operation — providing a
backward enumeration at all — is modeled **deeply** (the spelled-out
front-recursive reversal `revSeq` in the `pure` region and the verified loop in
`reverseEnum` ARE the reversal); there is **no `reversed` axiom** the proof
consumes. The deep model is instead validated equal to the real callee
out-of-band: G-AX (`axiom_check.py`) builds `dict.fromkeys(items)` and asserts
`list(reversed(d)) == revSeq(list(d))`, that `reversed(d)` is a
`collections.abc.Iterator`, and that materializing it does not disturb
`list(iter(d))` (read-only), over boundary + 20000 fuzz inputs (including
duplicate inputs that collapse keys, the empty collection, and the F2P witness
`[1, 2, 3] → [3, 2, 1]`).

**Scope of this lane, and what it deliberately does NOT carry.** G-AX here
checks a fact about the VALUE model: that `revSeq` is the same sequence the real
reversal primitive yields. It does not, and cannot, constrain what a candidate
implementation of the changed method hands back — a check run against gold's own
choice of callee says nothing about a rival that chose a different one. So the
self-advancing, one-shot, index-free nature of the returned handle is **not**
delegated here. It is BEHAVIOUR of the changed operation, and the frozen spec
states it directly, in four clauses:

* `out.1 = (revSeq elements).head?` (C0) — the handle answers a single-element
  request itself, with an element rather than a refusal, whenever the collection
  is non-empty. So it has a working `__next__`.
* `out.2.2.2.1 = []` (C3) — once drained it is spent.
* `out.2.2.2.2.1 = none` (C4) — a FRESH handle refuses a positional read, so no
  element can be taken from it by index at the position asked about.
* `out.2.2.2.2.2.1 = revSeq elements` (C5) — a FRESH handle that is only drained,
  never advanced, still yields the whole backward enumeration. So `iter()` on it
  works and gives everything.
* `out.2.2.2.2.2.2 = []` (C6) — a FRESH handle collected position by position,
  0 then 1 then 2 until it refuses, yields NOTHING. So it serves no position at
  all, and advancing it is the only channel that ever produces an element.

Together C0, C6 and C5 are what make the returned object an **iterator** rather
than merely something that enumerates correctly, and they do it without naming a
type. C5 says `iter()` succeeds and delivers the whole enumeration; `iter()` can
succeed in exactly two ways, through `__iter__` or through the legacy
`__getitem__` sequence protocol; C6 rules out the second, because a
`__getitem__`-driven iteration obtains its elements by asking for position 0,
then 1, then 2, until refused — and C6 says that exact sequence of requests,
put through the object's own element-at-position access, yields nothing, while
C5 says a drain yields everything. The two cannot both hold of a legacy
sequence-protocol object, so `__iter__` exists. Note that C4 alone does NOT
close this: it asks about ONE position, and declining a single bare read is
consistent with serving the 0, 1, 2, ... sequence, so C4 bounds the shape
without determining it and C6 is what carries the argument. C0 says `__next__`
exists and works; and
`collections.abc.Iterator.__subclasshook__` is exactly
`_check_methods(C, '__iter__', '__next__')` — which is the failing test's first
assertion. A candidate that hands back a container-like view — every enumerated
value correct, but nothing to give until the consumer derives a further traversal
from it — satisfies the value model and still violates C0. The
`collections.abc.Iterator` assertion in `axiom_check.py` therefore stands as a
cross-check on the primitive gold happens to call, not as the bearer of the
obligation; see `refinement.md` §B for the closure argument and its one measured
residue (the empty collection, where neither C4 nor C6 can discriminate and the
failing test does not look).

Docs: `reversed` — https://docs.python.org/3/library/functions.html#reversed ;
dict reverse-iteration since 3.8 —
https://docs.python.org/3/whatsnew/3.8.html (dict views are reversible).

## 4. G-CONF fuzz seed

`conformance_check.py` is pinned to **seed 14089**, N = 100000 fuzz inputs over
`(items, demand)` (plus 15 boundary cases: the empty collection at two demands,
the singleton, the F2P witness `[1, 2, 3]` at demand 0/1/2/7 — including
`demand` exactly draining the remainder and `demand` past the end — a
duplicate-collapsing input, and a 40-element collection at demand 0/39/40). The
R/I shadow of `reverseEnum`'s impl region is the backward append loop
transliterated to Python (`dict.fromkeys` for the carrier), followed by the same
seven observations the impl reads off it: `result[0] if result else None`,
`remaining[:j]`, `remaining[j:]`, `remaining[k:]` with `j`/`k` advanced by the
transliterated loops, then `None` for the positional read, `result` for the
fresh drain and `[]` for the position-by-position collection. The oracle is FOUR
handles from the patched
`OrderedSet.__reversed__` (gold patch applied) over the same unchanged
collection: the first interrogated `next(h, None)`, `demand` further `next(h)`
calls, `list(h)`, `list(h)` again; the second asked `h2[0]`, with `TypeError`
(and `IndexError`/`KeyError`) read as the refusal `None`; the third asked
`list(h3)` with no prior advance; the fourth collected position by position via
`operator.getitem(h4, j)` for j = 0, 1, 2, ... until it refused. So the
mechanical refutation covers the self-advancing, one-shot, index-free and
already-populated observations as well as the enumerated sequence — a candidate
handing back a container, a re-readable object, an indexable one or one that is
empty until stepped disagrees with the shadow on the first, fourth, fifth, sixth
or seventh component, and one whose elements are reachable by position only
through the 0, 1, 2, ... sequence (so that a single bare read is declined)
disagrees on the seventh alone. conf_skip = **false** (the impl region is pure
R/I — a reversal loop plus tuple/list observations, no consumed axiom).
