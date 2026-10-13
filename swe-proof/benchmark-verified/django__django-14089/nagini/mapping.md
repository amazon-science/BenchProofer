# mapping.md — django__django-14089

Binds every `model.py` symbol to its repository counterpart at
`base_commit = d01709aae21de9cd2565b9c52f32732ea28a2d98`, states the type
abstraction, and gives the provenance of the one kind-A obligation (an
A-reference deep model checked by axiom_check.py / G-AX; there is no consumed
`@ContractOnly` axiom).

Repo file under change: `django/utils/datastructures.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `reverse_order(elements)` | the new `OrderedSet.__reversed__(self)` — `django/utils/datastructures.py:25-26` (the method inserted after `__iter__` at line 25, before `__contains__` at line 28) | the modeled changed function: the backward enumeration of the ordered collection |
| `elements` (parameter) | the keys of `self.dict` in insertion order — `OrderedSet.__init__` sets `self.dict = dict.fromkeys(iterable or ())` (`datastructures.py:11`); `__iter__` returns `iter(self.dict)` (`datastructures.py:25-26`) | the ordered contents of the collection (distinct keys, insertion order) |
| `rev(s)` *(deep model — A-reference)* | `reversed(self.dict)` — CPython builtin `reversed` over a `dict` (the body of the new `__reversed__`), materialized to a list | pure spec: the reversal of a sequence; the deep model of the new method's net effect, validated `rev == reversed(dict)` by axiom_check.py (G-AX), NOT consumed as an axiom |

The unchanged neighbours that fix the carrier semantics (read, not referenced
from the consumer spec view): `OrderedSet.__init__` (`datastructures.py:10-11`,
`self.dict = dict.fromkeys(iterable or ())` — distinct keys, insertion order)
and `OrderedSet.__iter__` (`datastructures.py:25-26`, `return iter(self.dict)`
— forward enumeration is the keys in insertion order). The collection's order
is fully carried by `self.dict`'s insertion order; the new `__reversed__`
delegates to the builtin `reversed` on that dict.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `OrderedSet` instance (a distinct-key, insertion-ordered collection backed by `self.dict`) | `List[int]` of element keys in insertion order | the dict keys in insertion order ↔ the list elements in order; `list(iter(self.dict))` ↔ `elements`; `len(self.dict)` ↔ `len(elements)`. Elements are distinct hashables; modelled as distinct `int` keys (the F2P uses `int` keys `1,2,3`). |
| `reversed(self.dict)` (a `dict_reversekeyiterator`) | `List[int]` (the materialized backward enumeration) | the iterator's yielded sequence ↔ `Result()`; `list(reversed(self.dict))` ↔ `reverse_order(elements)`. The iterator-ness (`collections.abc.Iterator`) is a guaranteed property of the builtin `reversed`; modelled as the materialized list whose order is pinned, with the Iterator property checked by G-AX (axiom_check.py). |
| a specification over the ordered contents | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`drop`/`len`/`[i]` mirror list `+`/slice/`len`/index; `rev` is the sequence reversal. |

`OrderedSet` is generic over hashables; the carrier `List[int]` is the
`int`-keyed instance the F2P test exercises (`OrderedSet([1, 2, 3])`).

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `rev` deep model ↔ `reversed(dict)` (A-reference)
**Callee:** CPython builtin `reversed(d)` over a `dict` `d`. Since Python 3.8,
`dict` (and therefore `dict.fromkeys`) supports `reversed`, yielding the keys
in reverse insertion order; the collection's image runs Python 3.9 (the
instance's `environment_setup_commit`/version 4.0 Django), where this is
available. The new `__reversed__` returns `reversed(self.dict)`. Because
`self.dict` preserves insertion order with distinct keys and `__iter__` yields
`iter(self.dict)` (the keys in insertion order), the materialized backward
enumeration is exactly the element-wise reversal of the forward enumeration:

  `list(reversed(self.dict)) == list(iter(self.dict))[::-1]`,

which is what the deep model `rev` encodes
(`rev(s) = rev(s.drop(1)) + PSeq(s[0])`). The changed operation — providing a
backward enumeration at all — is modeled **deeply** (the spelled-out
front-recursive reversal `rev` in the pure region and the verified loop in
`reverse_order` ARE the reversal); there is **no `reversed` axiom** the proof
consumes. The deep model is instead validated equal to the real callee
out-of-band: G-AX (axiom_check.py) builds `dict.fromkeys(items)` and asserts
`list(reversed(d)) == rev(list(d))`, that `reversed(d)` is a
`collections.abc.Iterator`, and that materializing it does not disturb
`list(iter(d))` (read-only), over 15 boundary + 20 000 fuzz inputs (including
duplicate inputs that collapse keys, the empty collection, and the F2P witness
`[1, 2, 3] → [3, 2, 1]`).

Docs: `reversed` — https://docs.python.org/3/library/functions.html#reversed ;
dict reverse-iteration since 3.8 —
https://docs.python.org/3/whatsnew/3.8.html (dict views are reversible).
