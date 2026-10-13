# mapping.md — pytest-dev__pytest-10356

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 3c1534944cbd34e8a41bc9e76818018fadefc9a1`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep models.

Repo file under change: `src/_pytest/mark/structures.py`. Line numbers below are
given as `base:NNN` for the pre-change file and `post:NNN` for the file with
`patch.diff` applied, because the change moves everything after the first hunk.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line) | role |
|---|---|---|
| `collectMarks (lineage : List (List Item)) (wholeLineage : Bool) : Outcome` | `get_unpacked_marks(obj, *, consider_mro=...)` — `structures.py` `base:358` / `post:358-386` | the modeled changed function: gather a class's annotations, optionally across its whole resolution order, canonicalizing the assembly on the way out |
| `attachMark (lineage : List (List Item)) (mark : Mark) : Outcome` | `store_mark(obj, mark)` — `structures.py` `base:383` (body `base:391`) / `post:406` (body `post:414`) | the modeled changed function: record a freshly-applied annotation on a class |
| `Mark` (`abbrev Mark := Int`) | `_pytest.mark.structures.Mark` — `structures.py:195` | opaque *canonical* annotation identity token; only `==` is observed (the target test compares `Mark` objects by equality) |
| `Item` (`canonical` \| `wrapped` \| `foreign`) *(pure region)* | one element of a `pytestmark` list as actually found there, classified by what `getattr(mark, "mark", mark)` yields at `post:400` | the RAW element domain — see §2 for the three-way bijection |
| `markOf : Item → Option Mark` *(deep model — pure region)* | `mark_obj = getattr(mark, "mark", mark)` then `isinstance(mark_obj, Mark)` — `post:400-401` | the annotation an element makes available; `none` exactly when the element is not (and does not carry) a `Mark` |
| `nameOf : Item → Int` *(deep model — pure region)* | `repr(mark_obj)` in `f"got {repr(mark_obj)} instead of Mark"` — `post:402` | the identity token a refusal names |
| `Outcome` (`collected ms` \| `refused n`) *(pure region)* | returning `List[Mark]` (`post:386`) vs raising `TypeError` naming the offending object (`post:402`) | the two observable results of a collection |
| `canonicalize : List Item → Outcome` *(deep model — pure region)* | `list(normalize_mark_list(mark_list))` — `post:386`, whose callee is `normalize_mark_list` at `post:389-403` (`base:366-380`, textually UNCHANGED) | element-by-element canonicalization of the assembled list, refusing the whole collection at the FIRST element that makes no annotation available |
| `flattenSeq : List (List Item) → List Item` *(deep model — pure region)* | `for item in mark_lists: mark_list.extend(item) / else append(item)` — `post:374-379` | the in-order per-source flatten the changed function now performs |
| `withMark : Outcome → Mark → Outcome` *(pure region)* | `[*get_unpacked_marks(obj, consider_mro=False), mark]` — `post:414`; a raise inside the splat aborts the assignment | extend a collection's outcome with the new annotation, propagating a refusal unchanged |
| `lineage` element / `lineage.headD []` | `x.__dict__.get("pytestmark", [])` — `post:371,373` — a single class's OWN list (NOT `getattr`, so ancestors are not folded in) | one source's own raw elements |
| `wholeLineage` | the `consider_mro` keyword — `post:361,370,372` | which sources contribute |

The pre-change behavior the patch removes (refinement audit only, not in the
consumer spec view): `get_unpacked_marks` read a single `getattr(obj,
"pytestmark", [])` attribute (`base:360`), which under attribute lookup along the
MRO returned only the *nearest* class's marks — losing annotations applied to
sibling base classes.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types. A wrong entry surfaces as spurious
G-CONF disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| a canonical annotation object `Mark` | Lean `Mark` (`= Int`) | each distinct `Mark` instance ↔ a distinct `Int` token; `m1 == m2` ↔ `n1 = n2`. Only equality / multiplicity / order is observed (the target test asserts list equality of `Mark` objects), so an opaque identity carrier is exact. |
| an element `e` of some `pytestmark` list with `getattr(e, "mark", e)` a `Mark` and `e` itself a `Mark` | `Item.canonical m` | `m` = the token of that `Mark`. `post:400` unwraps to `e` itself; `post:401` accepts it. |
| an element `e` with `e.mark` a `Mark` (`e` is a `MarkDecorator`, the shape a hand-written `pytestmark = [pytest.mark.foo]` produces) | `Item.wrapped m` | `m` = the token of `e.mark`. `post:400` unwraps to `e.mark`; `post:401` accepts it. The annotation comes OUT of the element. |
| an element `e` with `getattr(e, "mark", e)` NOT a `Mark` (any other object — a class, a string, an int, a decorator carrying a non-`Mark`) | `Item.foreign n` | `n` = the identity token of the *unwrapped* value `getattr(e, "mark", e)`, i.e. of the object `repr`'d in the `TypeError` at `post:402`. `markOf` is `none` here and only here. |
| one class's own list `cls.__dict__.get("pytestmark", [])` | `List Item` | Python `list` ↔ `List Item` elementwise via the three rows above; missing attribute ↔ `[]`. A class whose `pytestmark` is NOT a list contributes exactly one element (`post:378-379` appends it), so it maps to the singleton `[Item.…]` of that element. |
| the per-class own-list sequence `[x.__dict__.get("pytestmark", []) for x in cls.__mro__]` (class itself first) | `lineage : List (List Item)` | the i-th MRO entry's own elements ↔ `lineage[i]`; `cls.__mro__[0] is cls` so `cls`'s own elements ↔ `lineage.headD []` |
| `consider_mro: bool` keyword | `wholeLineage : Bool` | `True` ↔ `true` (whole lineage), `False` ↔ `false` (own only) |
| **the NON-class branch** (`post:380-385`): `obj` is not a `type`, so `mark_attribute = getattr(obj, "pytestmark", [])` and `mark_list` is that list, or `[mark_attribute]` if it is not a list | `lineage = [that one list]`, EITHER flag | a length-1 lineage: `flattenSeq [L] = L` under `wholeLineage=true` and `flattenSeq [(([L]).headD [])] = L` under `false`, which is exactly the fact that `consider_mro` has no effect on a non-class object. This is the branch the existing test at `testing/test_mark.py:590-602` drives (a module whose `pytestmark` is a plain class), so it is bound explicitly rather than left implicit. |
| `get_unpacked_marks(...)` returns `List[Mark]` | `Outcome.collected ms` | `ms` = the tokens of the returned `Mark`s, in order |
| `get_unpacked_marks(...)` raises `TypeError(f"got {repr(mark_obj)} instead of Mark")` | `Outcome.refused n` | `n` = the identity token of the object `repr`'d in the message. Raised at `post:402` for the FIRST offending element, because `normalize_mark_list` is a generator consumed in order and `post:386` drains it eagerly with `list(...)`. |
| `store_mark(obj, mark)`'s post-state `obj.pytestmark` | `attachMark`'s `out` | on success the new OWN list ↔ `Outcome.collected`; if the inner collection raises, the assignment at `post:414` never happens and the `TypeError` propagates ↔ `Outcome.refused`. `mark` is a canonical `Mark` by the assertion at `post:411`, which is why `attachMark`'s second parameter is `Mark` and not `Item`. |

`pytestmark` lists are finite and Lean `List` indexing is total/sound; the
carrier is `List (List Item)` because the operation flattens a sequence of
per-source lists whose elements are raw, not yet canonical.

### Why the element domain is `Item` and not `Mark`
The list a source carries is written by users and is not typed: `post:400-402` is
a real, load-bearing runtime check, and `testing/test_mark.py:590-602` asserts its
observable effect (a module-level `class pytestmark` must make collection FAIL
with a `TypeError`). Modeling the element domain as canonical `Mark`s only would
make that check invisible in the spec — the assembled list would be canonical by
construction and the canonicalization would collapse to the identity — so an
implementation that dropped the check entirely would satisfy the spec while
breaking that test. `Item` is therefore the raw domain, `Outcome` carries the
refusal, and `canonicalize` is modeled deeply. This is a WIDENING of the modeled
domain (the previously-modeled inputs are exactly the all-`canonical` sub-domain,
where every clause says what it said before); no precondition restricts it.

## 3. Deep-model provenance — checked by G-AX / axiom_check.py

### 3.1 `markOf` / `nameOf` / `canonicalize` ↔ `normalize_mark_list` (A-reference)
**Callee:** `_pytest.mark.structures.normalize_mark_list`, textually UNCHANGED
across the patch (`base:366-380` = `post:389-403`), consumed eagerly by the
changed function at `post:386`:

```python
def normalize_mark_list(mark_list):
    for mark in mark_list:
        mark_obj = getattr(mark, "mark", mark)
        if not isinstance(mark_obj, Mark):
            raise TypeError(f"got {repr(mark_obj)} instead of Mark")
        yield mark_obj
```

The Lean model transliterates this **in full**, not as a fold:

* `markOf it` ↔ `getattr(mark, "mark", mark)` followed by `isinstance(..., Mark)`
  — `some m` when the unwrapped value is a `Mark` with token `m` (covering both
  `Item.canonical`, where the unwrap is the identity, and `Item.wrapped`, where it
  is the `.mark` projection), `none` otherwise;
* `canonicalize` ↔ `list(normalize_mark_list(...))` — a front-to-back walk
  yielding one annotation per element, and `Outcome.refused (nameOf it)` at the
  FIRST element whose unwrapped value is not a `Mark` (the `raise` at `post:402`);
  the eager `list(...)` at `post:386` is what makes that refusal the observable
  result of the collection rather than something a lazy consumer might not reach.
* `nameOf` ↔ the identity of the object `repr`'d in the message, i.e. WHICH
  element the refusal names.

This is a deep model of a real sub-computation, **not** a consumed axiom and
**not** an identity fold: nothing about the callee is assumed, its refusal is
part of the modeled behaviour, and the proofs of both methods use only the
`Solution.lean` definitions.

**Soundness check (G-AX):** `axiom_check.py` runs the REAL
`normalize_mark_list` against a Python transliteration of the Lean
`markOf`/`nameOf`/`canonicalize` on: all-`Mark` lists (identity), lists holding
`MarkDecorator`s (unwrapped to `.mark`), lists holding non-`Mark` objects (must
RAISE `TypeError`), lists with SEVERAL offenders (must raise naming the FIRST),
offender-position sweeps, and randomized fuzz over all three element shapes. It
asserts both the success values and the refusal identity (that a `TypeError` is
raised and which object it names). Imports only `pytest` /
`_pytest.mark.structures`. Exit 0 iff sound.

### 3.2 `flattenSeq` ↔ the per-source flatten (deep model, R/I legs)
`flattenSeq` is the in-order concatenation performed by `post:374-379`; an empty
source `extend`s nothing and the loop continues, which is the "a source
contributing none is skipped without ending the assembly" content. It is modeled
deeply (pure region) and computed by the verified backward `while` fold in the
impl; its R/I legs are differential-tested by G-CONF, not by G-AX.

### 3.3 No A-consumed axioms
The proof of `collectMarks` closes by `loom_solve` + one drop-step rewrite over
`flattenSeq`; the proof of `attachMark` applies the generated
`collectMarks_correct` (callee-under-spec). No `axiom` is declared or consumed
(`meta.json: axioms = []`), and the functions under change are never axiomatized
(directive 7).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`10356`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`flattenSeq`, `canonicalize`, `collectMarks`, `withMark` and `attachMark` to
Python over the real repo types and diffs them against `patch.diff` behaviour —
the patched `get_unpacked_marks` / `store_mark` applied at base_commit — over
randomly generated class hierarchies (varying MRO depth, branching, and per-class
own-list content), over lists mixing all three element shapes (`Mark`,
`MarkDecorator`, and objects that are neither), and over the NON-class branch
(module-like objects whose `pytestmark` is a list, a non-list, or absent). Both
sides are compared on the SUCCESS value and on the REFUSAL (that an exception is
raised and which object it names), so a shadow that skipped the canonicalizing
step could not agree.
