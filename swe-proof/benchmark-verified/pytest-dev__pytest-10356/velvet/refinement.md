# refinement.md — pytest-dev__pytest-10356

Operation-by-operation correspondence between `Solution.lean`'s impl regions (the
`collectMarks` and `attachMark` `do` blocks) and its deep models (`flattenSeq`,
`markOf`/`nameOf`/`canonicalize`, `withMark`) on one side, and `patch.diff` (the
gold patch) on the other. Each step is tagged **R** (type refinement; state the
bijection), **A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a
deep model validated == the real callee by G-AX), or **I** (identical concrete
op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE). Line numbers are
`base:NNN` (pre-change) and `post:NNN` (patched), per mapping.md §1.

## A. The collection site — `get_unpacked_marks()` (`base:358` / `post:358-386`)

Gold hunk (pre → post): the single-attribute read `getattr(obj, "pytestmark", [])`
(`base:360`) is replaced by a two-branch read. For a **class** (`post:369`): the
in-order concatenation of `x.__dict__.get("pytestmark", [])` over every `x in
obj.__mro__` when `consider_mro` is true (`post:373`), or just the class's own
`obj.__dict__.get("pytestmark", [])` when false (`post:371`), flattened by
`post:374-379`. For a **non-class** (`post:380-385`): `mark_attribute =
getattr(obj, "pytestmark", [])`, used as-is if it is a list and wrapped in a
singleton otherwise. Both branches then exit through
`return list(normalize_mark_list(mark_list))` (`post:386`).

`collectMarks (lineage) (wholeLineage)` models this. `lineage` is the per-source
own-element sequence (for a class, along `obj.__mro__`, class first; for a
non-class, the single list — a length-1 lineage, mapping.md §2), and
`wholeLineage` ↔ `consider_mro`.

| # | Solution.lean op (`collectMarks`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | params `lineage : List (List Item)`, `wholeLineage : Bool` | `obj` and the `consider_mro` keyword (`post:358-362`) | R | `obj.__mro__` own-element lists ↔ `lineage` (class first); `consider_mro` ↔ `wholeLineage` (mapping.md §2). G-CONF builds `lineage` from the real `__mro__`. |
| A2 | `let selected := if wholeLineage then lineage else [lineage.headD []]` | `mark_lists = [x.__dict__.get("pytestmark", []) for x in obj.__mro__]` (`post:373`) vs `[obj.__dict__.get("pytestmark", [])]` (`post:371`) | I | the branch selecting whole-MRO sources vs the class's own only; transliterated by G-CONF. `lineage.headD []` ↔ `obj.__dict__.get("pytestmark", [])` since `obj.__mro__[0] is obj`. |
| A3 | the backward `while` fold computing `gathered = flattenSeq selected` | the `for item in mark_lists: mark_list.extend(item) / else append(item)` flatten (`post:374-379`) | I (deep model) | `flattenSeq` (pure region) and the verified loop ARE the in-order concatenation; an empty source contributes nothing and does not end the assembly, matching `extend([])`. Concrete, transliterated by G-CONF; no axiom. |
| A4 | `return canonicalize gathered` and the clause `out = canonicalize (flattenSeq (...))` | `return list(normalize_mark_list(mark_list))` (`post:386`), callee `post:389-403` | A-reference (deep, full fidelity) | `canonicalize` transliterates the callee in full: unwrap each element (`getattr(mark, "mark", mark)`, `post:400`), demand the result be a `Mark` (`post:401`), and otherwise REFUSE the whole collection naming that element (`raise TypeError(f"got {repr(mark_obj)} instead of Mark")`, `post:402`). The walk is front-to-back and `list(...)` drains it eagerly, so the FIRST offender is the one named. Validated `== real callee` on success values AND on the refusal identity by G-AX (mapping.md §3.1). |
| A5 | the NON-class leg: `lineage = [mark_list]` (a length-1 lineage), for either flag | `mark_attribute = getattr(obj, "pytestmark", [])`; `mark_list = mark_attribute` if a list else `[mark_attribute]` (`post:380-385`) | R | a length-1 lineage gives the same result under both flag values, which is exactly the fact that `consider_mro` has no effect on a non-class object. A non-list attribute becomes a single raw element (mapping.md §2). This leg is exercised by G-CONF over module-like objects and is the leg the existing test at `testing/test_mark.py:590-602` drives. |

Two pieces of discriminating content live in
`ensures out = canonicalize (flattenSeq (if wholeLineage then lineage else
[lineage.headD []]))`:

1. **Breadth (A2/A3).** When `wholeLineage` is true the result keeps annotations
   applied to ANY class in the lineage, not just the nearest.
   `Solution_prepatch_1.lean` reproduces the pre-change read (only the class's own
   list contributes, even when the whole lineage is requested) and **fails** the
   postcondition (G-DIFF, measured: exit 1 with a real unsolved goal). This is the
   behavior the target test `test_mark_mro` observes:
   `get_unpacked_marks(C)` must equal `[xfail("c").mark, xfail("a").mark,
   xfail("b").mark]` (all three, MRO order), not just `C`'s own.
2. **The canonicalizing gate (A4).** The outcome on an assembly containing an
   element that makes no annotation available is pinned to `refused`, naming the
   first such element. This is why the element carrier is the RAW domain `Item`
   and the result carrier is `Outcome`: an earlier revision of this spec modeled
   the element domain as canonical `Mark`s and folded `normalize_mark_list` as the
   IDENTITY, which made the check at `post:401-402` invisible — an impl that
   returned the assembled list unchecked satisfied that spec, and its faithful
   counterpart (`return list(mark_list)` in place of `post:386`) breaks
   `testing/test_mark.py::TestFunctional::test_mark_with_wrong_marker`, which
   asserts a module-level `class pytestmark` makes collection fail with a
   `TypeError`. Widening the modeled element domain and making the refusal an
   observable outcome closes that; the previously-modeled inputs are exactly the
   all-`canonical` sub-domain, so nothing was narrowed and no precondition was
   added.

## B. The storage site — `store_mark()` (`base:383`/`391`, `post:406`/`414`)

Gold hunk:
```
- obj.pytestmark = [*get_unpacked_marks(obj), mark]
+ obj.pytestmark = [*get_unpacked_marks(obj, consider_mro=False), mark]
```

`attachMark (lineage) (mark)` models this: the class's new own list is the
canonicalization of its existing OWN elements (collected WITHOUT the lineage),
extended with `mark`; and if that canonicalization refuses, nothing is stored and
the refusal is the observable result.

| # | Solution.lean op (`attachMark`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | `let own ← collectMarks lineage false` | `get_unpacked_marks(obj, consider_mro=False)` (`post:414`) | I (callee-under-spec) | calls the modeled `collectMarks` with `wholeLineage=false`; `prove_correct` applies the generated `collectMarks_correct`, so `own = canonicalize (lineage.headD [])`. The `consider_mro=False` argument is the exact gold change. |
| B2 | `return withMark own mark` | the `[*..., mark]` list-splat append | I | `withMark` appends `mark` to a collected sequence (`++ [mark]` ↔ `[*L, mark]`) and propagates a refusal UNCHANGED — matching the fact that a `TypeError` raised inside the splat aborts the assignment at `post:414` before `obj.pytestmark` is rebound, so the class's stored list is left as it was and the error is what the caller sees. |
| B3 | `ensures out = withMark (canonicalize (lineage.headD [])) mark` | the post-state of `obj.pytestmark`, or the propagated `TypeError` | R | `obj.pytestmark`'s new OWN list ↔ `Outcome.collected`; a propagated refusal ↔ `Outcome.refused` (mapping.md §2). Pins that storing an annotation (i) never absorbs ancestors' annotations into the class's own attribute and (ii) never silently drops an offending element already sitting in that attribute. |
| B4 | `mark : Mark` (canonical, not `Item`) | `assert isinstance(mark, Mark), mark` (`post:411`) | R | the annotation being recorded is canonical by that assertion, so the second parameter is the canonical carrier; only the EXISTING list may hold raw elements. |

Discriminating content: the new own list must be the class's OWN annotations plus
the new one — NOT the whole-MRO collection plus the new one (which the old
`get_unpacked_marks(obj)` would now return post-A, double-counting ancestors'
annotations into the class's stored attribute). `Solution_prepatch_2.lean`
reproduces that (`collectMarks lineage true`) and **fails**
`out = withMark (canonicalize (lineage.headD [])) mark` (G-DIFF, measured: exit 1
with a real unsolved goal). This is exactly why the gold patch passes
`consider_mro=False` here: without it, every `@pytest.mark.X` decoration would
re-absorb inherited annotations into the decorated class's `__dict__`, corrupting
the per-class own-list invariant that site A's MRO walk relies on.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operations that genuinely *changed* — the
MRO-aware flatten (A2/A3) and the `consider_mro=False` storage (B1) — are modeled
**deeply** (`flattenSeq` fold + the `collectMarks`/`attachMark` methods), not
hidden behind an axiom about a function under change. The one UNCHANGED callee on
the path (`normalize_mark_list`, A4) is also modeled **deeply and at full
fidelity**, refusal included, rather than folded away: nothing is assumed about
it, and G-AX validates the model against the real callee on all three element
shapes and on the refusal identity. There are **no A-consumed axioms**
(`meta.json: axioms = []`).

## D. verify(Solution) ⇒ resolved

`collectMarks` verifies only if its output equals the canonicalization of the
exact in-order assembly of the selected sources — with the whole-lineage branch
keeping every ancestor's annotations (A2/A3) and the canonicalizing gate refusing,
with the first offender named, on any assembled element that makes no annotation
available (A4). `attachMark` verifies only if it extends the canonicalization of
the class's OWN list (B1, via `collectMarks_correct` at `wholeLineage=false`) and
propagates a refusal unchanged (B2). By R (`Mark ↔ Int`, `Item ↔ the raw element
classification`, `Outcome ↔ return-value-or-`TypeError``, `list ↔ List`, `__mro__`
own-lists ↔ `lineage`, the non-class branch ↔ a length-1 lineage) and the A4
fidelity of `canonicalize` (G-AX), the verified methods equal the patched
`get_unpacked_marks` / `store_mark` on the tested inputs — both on the values they
return and on when they fail; by G-CONF the R/I transliteration agrees with
`patch.diff`'s behaviour over the fuzzed class hierarchies, mixed-element lists
and non-class objects; the gold patch resolves (G-RESOLVE). Trust points are
exactly the two of plan §1.1: callee soundness (G-AX: `canonicalize` == the real
`normalize_mark_list`, refusal included) and refinement fidelity (this doc, G-EQ +
G-CONF).
