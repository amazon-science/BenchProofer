# mapping.md — symbol binding & type bijection (django__django-14089)

## Modeled function
- **Lean** `implementation_reversed : List Int → List Int`
- **Python** `OrderedSet.__reversed__(self)` —
  `django/utils/datastructures.py:28-29 @ patched` (newly added method); the
  enclosing carrier `OrderedSet` lives at `django/utils/datastructures.py:5-35
  @ base_commit`.

`OrderedSet` is an insertion-ordered set backed by a `dict` (`self.dict`, whose
keys are the members in insertion order; the values are all `None`). The fix adds

```python
def __reversed__(self):
    return reversed(self.dict)
```

so that `reversed(an_ordered_set)` yields the members in the reverse of their
insertion order. `reversed(self.dict)` iterates the dict's keys (the ordered
distinct members) from last to first. At `base_commit` no `__reversed__` exists,
so `reversed(OrderedSet(...))` raised `TypeError` — the behavior the F2P test
`test_reversed` now pins (`list(reversed(OrderedSet([1,2,3]))) == [3,2,1]`).

The observable behavior is purely the ELEMENT ORDER produced by reverse
enumeration, so the modeled function takes the carrier's ordered members `xs`
and returns them reversed.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `self.dict` keys, in insertion order (the ordered distinct members) | `xs : List Int` | the carrier's ordered members; `Int` stands in for an arbitrary hashable member. Distinctness is a property of the carrier, not used by the reversal. |
| the iterator produced by `reversed(self.dict)`, materialized in order | `result : List Int` | per-element order; `reversed` over an insertion-ordered dict yields keys last→first |

A Python `dict` (3.7+) preserves insertion order and `reversed(dict)` yields its
keys in reverse insertion order. Since `OrderedSet.dict` is built by
`dict.fromkeys(iterable)`, its keys are exactly the distinct members in first-seen
order; `reversed` of it is therefore the reversal of that ordered-key list —
modeled exactly as `xs.reverse` (R/I), not axiomatized.

## Callee provenance
- `reversed(self.dict)` is the **changed op** (the whole added method). The
  built-in `reversed` over an order-preserving dict is the order-reversal of the
  dict's key sequence; it is modeled deeply as `List.reverse` (an accumulator
  prepend-fold in the impl), NOT axiomatized. No UNCHANGED callee property is
  consumed. The axioms region is empty; G-AX is a skip stub.

## Flag dependency
None. `__reversed__` is unconditional; there is no flag branch.

## Scope note
`reversed()` on the object returns an *iterator*; the F2P test materializes it
with `list(...)` and also asserts it is a `collections.abc.Iterator`. The
iterator-ness is a Python protocol artifact of returning `reversed(self.dict)`;
the only data-level observable is the produced element order, which is what
`problem_spec_reversed` pins. The members' equality/hash semantics (set
distinctness) are a property of how `xs` is formed and are orthogonal to the
reversal.

## G-CONF fuzz seed
Pinned seed: **14089**. ≥10^5 fuzzed inputs over member-list alphabets
(including duplicates, which the carrier dedups, and empty / singleton lists).
