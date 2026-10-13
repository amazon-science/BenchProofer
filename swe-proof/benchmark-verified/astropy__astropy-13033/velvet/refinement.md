# refinement.md — astropy__astropy-13033

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`requiredColumnsError` `do` block plus the deep `errorMessage`/`renderColumnList`
model) and `patch.diff` (the gold patch). Each step is tagged **R** (type
refinement; state the bijection), **A-consumed**, **A-reference**, or **I**
(identical concrete op). EVERY step is R, A, or I; no kind-3.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the single A-reference leg (`renderedName`, §B) is mechanically refuted
by **G-AX** (`axiom_check.py`); this narrative is audited by **G-EQ**.
Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The changed site — the mismatch-arm message of `_check_required_columns`

Gold hunk (post-image of the `elif self.colnames[:len(required_columns)] !=
required_columns:` arm, plus the nested helper it introduces):

```python
def as_scalar_or_list_str(obj):
    if not hasattr(obj, "__len__"):
        return f"'{obj}'"
    elif len(obj) == 1:
        return f"'{obj[0]}'"
    else:
        return str(obj)
...
raise ValueError("{} object is invalid - expected {} "
                 "as the first column{} but found {}"
                 .format(self.__class__.__name__, as_scalar_or_list_str(required_columns),
                         plural, as_scalar_or_list_str(self.colnames[:len(required_columns)])))
```

| # | Solution.lean impl op (`requiredColumnsError`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `className : List Char` | `self.__class__.__name__` (a `str`) | R | `str` ↔ `List Char` (mapping.md §2). On the tested classes (`TimeSeries`) it is a simple name. |
| A2 | param `required : List (List Char)` | `required_columns` (the `list[str]` required as leading columns) | R | `list[str]` ↔ `List (List Char)` (mapping.md §2). In the mismatch arm `required_columns` is `self._required_columns` (non-relaxed) or its `colnames`-length prefix (relaxed); both are `list[str]`. |
| A3 | param `present : List (List Char)` | `self.colnames` (the present column names) | R | `list[str]` ↔ `List (List Char)`. |
| A4 | `let found := present.take required.length` | `self.colnames[:len(required_columns)]` | I (under R) | `xs[:k]` ↔ `xs.take k` (mapping.md §2); identical slice, the very prefix the helper is applied to on the "found" side. |
| A5 | `renderColumnList required` (= `quoted x` if a single name, else `bracketList`) | `as_scalar_or_list_str(required_columns)` | I (deeply modeled) + A-reference leaf | the changed rendering, modeled **deeply**: `as_scalar_or_list_str` for a list returns `f"'{obj[0]}'"` when `len==1` else `str(obj)`; `renderColumnList [x] = quoted x` (verbatim single-quoting, matching the f-string exactly — no escaping on either side) and otherwise `bracketList xs` = `[` + `, `-joined per-element `renderedName` + `]`, exactly CPython's `list.__str__` composition, with the per-element rendering (`repr` of a `str`) kept as the opaque A-reference `renderedName` (mapping.md §2/§3; refuted by G-AX). The `not hasattr(obj,"__len__")` scalar arm never fires here (both args are lists), so it is out of the modeled domain (mapping.md §2). R/I skeleton transliterated by G-CONF (adversarial names included). |
| A6 | `renderColumnList found` | `as_scalar_or_list_str(self.colnames[:len(required_columns)])` | I (deeply modeled) + A-reference leaf | same rendering applied to the present-prefix; same justification as A5. |
| A7 | `plural := if required.length > 1 then ['s'] else []` | `plural` (`'s' if len(required_columns) > 1 else ''`, computed earlier in the method, lines 73) | I (under R) | identical pluralization predicate; `required.length` ↔ `len(required_columns)`. The patch does NOT change this line; it is reproduced in the model because it is part of the assembled message. |
| A8 | `className ++ " object is invalid - expected " ++ … ++ " but found " ++ foundStr` | the `"{} object is invalid - expected {} as the first column{} but found {}".format(...)` template | I (under R) | identical literal template and field order; `str` concat ↔ `List` `++`. The literal text changed from `expected '{}'`/`found '{}'` (quotes around a scalar) to `expected {}`/`found {}` (the rendered collection supplies its own quoting) — captured by A5/A6 moving the quoting into `renderColumnList`. |

Discriminating content of the change: when `required.length > 1`, the expected
side renders the **whole collection** `['time', 'a']` (resp. the found side
`['time', 'b']`) rather than only the first element quoted (`'time'` / `'time'`).
This lives in `renderColumnList required` / `renderColumnList found` taking the
`bracketList` arm for length ≠ 1. `Solution_prepatch.lean` reproduces the
pre-patch message (only `required.head` and `present.head`, each `quoted`) and
**fails** `out = errorMessage …` on exactly that clause: the verifier's residual
goal is `quoted (required.head?.getD []) … = renderColumnList required …`, which
is false when `required.length ≥ 2` (G-DIFF). The F2P test
`test_required_columns` adds precisely a 2-required-column case
(`['time', 'a']` vs `['time', 'b']`) asserting the bracketed-list message.

## B. One A-reference leaf; no consumed axiom

The single changed operation — the scalar-vs-list rendering
(`as_scalar_or_list_str`) — is modeled **deeply** in the `pure` region
(`quoted`, `joinRendered`, `bracketList`, `renderColumnList`), not hidden
behind an axiom about the function under change (directive 7: never axiomatize
the operation the patch changes). What IS abstracted is one pre-existing
platform builtin the multi-name arm calls into: the canonical per-element
rendering `str(list)` applies to each element (`repr` of a `str`) — quote
delimiter switching, backslash/control/non-printable escaping per CPython's
rules. That builtin is UNCHANGED by the patch; committing to a concrete Lean
approximation of it would diverge from reality on names embedding
quote/escape/control characters. It is therefore the `opaque renderedName`
(axioms region), an **A-reference** whose binding to the real `repr` is
validated executably by **G-AX** (`axiom_check.py`: byte-for-byte
`str(list)`-composition and round-trip legs over adversarial + fuzzed names,
pinned seed 13033). No `axiom` about `renderedName` is consumed — the Velvet
proof never inspects its behaviour, so there is no axiom-soundness trust point
beyond the executable G-AX validation.

## C. No kind-3 (inexpressible-changed-op) steps

Every step above is R, I, or the single A-reference leaf of §B. The changed
string-rendering operation is fully expressible (concrete `List Char`
operations over the abstract per-element leaf), so it is modeled deeply, not
hidden. The unchanged surrounding control flow (the `_required_columns_enabled`
early return, the `_required_columns is not None` guard, the relax bookkeeping,
the empty-`colnames` branch, and the prefix-equality comparison
`self.colnames[:len(required_columns)] != required_columns` that *selects* this
arm) is **not** modeled: the patch leaves it byte-identical and it is reached
identically pre- and post-patch. Modeling only the message string is faithful
because the patch's only behavioural effect is the message that arm raises.

## D. verify(Solution) ⇒ resolved

`requiredColumnsError` verifies only if its output equals `errorMessage` — the
exact template with the collection-rendering on both the expected and the found
sides and the prefix slice on the found side (A4–A8). By R (`str ↔ List Char`,
`list[str] ↔ List (List Char)`, and the `str(list)`/`f"'{x}'"` ↔
`bracketList`/`quoted` correspondence — exact for EVERY name via the
`renderedName := repr` A-reference binding) the verified message equals the
`str` the patched `_check_required_columns` mismatch arm raises; by G-CONF the
transliteration agrees with the **real patched** method (driven in-container)
on ≥10⁵ fuzzed inputs including adversarial names, and by G-AX the A-reference
binding agrees with the real builtin byte-for-byte on 50k+ adversarial/fuzzed
cases. No `axiom` is consumed. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The trust points are refinement fidelity (this doc,
G-EQ + G-CONF) and the executable A-reference binding (G-AX).
