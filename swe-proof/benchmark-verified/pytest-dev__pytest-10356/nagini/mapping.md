# mapping.md — pytest-dev__pytest-10356

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 3c1534944cbd34e8a41bc9e76818018fadefc9a1`, states the type
abstraction, and gives the provenance of the deep-model reference (callee
source + the exact behaviour validated by G-AX).

Repo file under change: `src/_pytest/mark/structures.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `unpacked_tokens(chain, consider_chain)` | `get_unpacked_marks(obj, *, consider_mro=True)` — `src/_pytest/mark/structures.py:358` (post-patch signature lines 358-386) | the modeled changed function (mark collector) |
| `consider_chain: bool` | the new keyword-only parameter `consider_mro: bool = True` | controls whether the whole ancestor chain (MRO) or only the class itself is read |
| `chain: PSeq[PSeq[int]]` | `[x.__dict__.get("pytestmark", []) for x in obj.__mro__]` (each element normalised by `normalize_mark_list`) — post-patch body line 372 | the ordered per-class own-mark lists along the method-resolution order |
| `chain[0]` | `obj.__dict__.get("pytestmark", [])` (normalised) — post-patch body line 370, the `consider_mro=False` branch | the class's own directly-attached marks |
| `concat_chain(chain)` *(deep model — A-reference)* | the `for item in mark_lists: mark_list.extend/append(item)` concatenation over the MRO own-lists, then `normalize_mark_list` — post-patch body lines 373-381 | pure spec: MRO-ordered concatenation of every member's own marks; deep model of the changed collection, validated `== get_unpacked_marks` by axiom_check.py (G-AX), NOT a consumed axiom |

The unchanged callee `normalize_mark_list` (`structures.py:366-380`) maps a list
of `Mark`/`MarkDecorator` to a list of `Mark` (extracting `.mark`); it is
order- and length-preserving on already-`Mark` items, so under the refinement it
is the identity on the token-identifier sequence (see §2). The caller
`store_mark` (`structures.py:383`, body line 391 pre / 414 post) is the site that
passes `consider_mro=False` post-patch; it is not separately modeled (its only
behavioural role is fixing each class's OWN `__dict__["pytestmark"]` to exactly
the class's own marks, which is precisely `chain[0]` — validated by G-AX, where
classes are built through the real decorator/`store_mark` path).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a class `obj` (a `type`) | the chain `PSeq[PSeq[int]]` = its MRO own-mark lists | `obj.__mro__[k]` ↔ `chain[k]`; `len(obj.__mro__)` ↔ `len(chain)`; the class itself is `obj.__mro__[0]` ↔ `chain[0]` |
| one class's own `pytestmark` list (a `List[Mark]`, or a single mark wrapped to a 1-list) | `PSeq[int]` of token identifiers | each `Mark` ↔ a distinct `int` (its `name`); list order ↔ `PSeq` order; the `if not isinstance(...,list): [x]` wrap ↔ a length-1 `PSeq` |
| `normalize_mark_list(mark_list)` | identity on the token-identifier sequence | preserves order and length on `Mark` items (yields each `mark_obj` once, in order); the F2P marks are all proper `Mark`s, so observationally the identity on the name sequence |
| the post-patch `mark_lists` → `mark_list` extend/append concatenation | `concat_chain` fold | `+` of `PSeq` mirrors `list.extend`; MRO order preserved |

Rich `Mark`/`type` objects are reduced to integer token identifiers and a
sequence of per-class own-lists because Nagini bans `str` indexing and rich
objects; the only observable the F2P test compares is the ordered list of marks
(`all_marks == [xfail("c").mark, xfail("a").mark, xfail("b").mark]`), which the
integer-identifier sequence captures faithfully.

## 3. Deep-model reference (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `concat_chain` deep model ↔ `get_unpacked_marks` (A-reference)
**Callee:** `_pytest.mark.structures.get_unpacked_marks(obj, consider_mro=...)`
(the patched function itself, on the class branch). The changed collection
operation is modeled **deeply** by the `@Pure` fold `concat_chain` in the `pure`
region; there is **no consumed `@ContractOnly` axiom**. Post-patch source:

```python
def get_unpacked_marks(obj, *, consider_mro=True):
    if isinstance(obj, type):
        if not consider_mro:
            mark_lists = [obj.__dict__.get("pytestmark", [])]
        else:
            mark_lists = [x.__dict__.get("pytestmark", []) for x in obj.__mro__]
        mark_list = []
        for item in mark_lists:
            if isinstance(item, list):
                mark_list.extend(item)
            else:
                mark_list.append(item)
    else:
        ...   # non-class branch: single attribute, unchanged
    return list(normalize_mark_list(mark_list))
```

For a class, with `consider_mro=True` this is exactly the MRO-ordered
concatenation of each member's own `__dict__["pytestmark"]` (each class's OWN
marks, because `store_mark` now stores with `consider_mro=False`, so a class's
own dict holds only its directly-applied marks). That is `concat_chain(chain)`.
With `consider_mro=False` it is just the class's own list, i.e. `chain[0]`.

**Soundness check (G-AX):** `axiom_check.py` builds class hierarchies through the
REAL pytest decorator path (`pytest.mark.X(cls)` → `store_mark`), then asserts,
at the ordered per-mark-name level (no value-membership proxy):

  * `get_unpacked_marks(C)` (names) `== concat_chain([own_marks(m) for m in C.__mro__])`
  * `get_unpacked_marks(C, consider_mro=False)` (names) `== own_marks(C)` (= `chain[0]`)

over the explicit F2P shape `C(A,B)` (each decorated: result `["c","a","b"]`,
class-only `["c"]`), boundary shapes (single, undecorated, linear, multi-mark,
diamond, mixed-empty), and ~4000 randomised class DAGs. The F2P shape is
enumerated and the check fails loudly if skipped. Imports only the stdlib plus
the package under test. Exit 0 iff sound.

The discriminating content of the change — walking the FULL MRO so a class with
two decorated ancestors keeps BOTH ancestors' marks — lives in
`Result() == concat_chain(chain)` (model) ⇔ the
`[x.__dict__.get("pytestmark", []) for x in obj.__mro__]` concatenation (real).
The pre-patch read a single MRO-resolved attribute and lost the other
ancestors' marks; `model_prepatch.py` reproduces that (`return chain[0]`) and
**fails** the postcondition `Implies(consider_chain, Result() == concat_chain(chain))`
(G-DIFF).
