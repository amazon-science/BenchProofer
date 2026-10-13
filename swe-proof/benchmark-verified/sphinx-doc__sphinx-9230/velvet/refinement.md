# refinement.md — sphinx-doc__sphinx-9230

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`resolveParamMethod` `do` block plus the deep `severTail`/`resolveParam` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The descriptor-separation site — `DocFieldTransformer.transform` (`sphinx/util/docfields.py:301`)

Gold hunk:
```
- argtype, argname = fieldarg.split(None, 1)
+ argtype, argname = fieldarg.rsplit(None, 1)
```
within
```python
if typedesc.is_typed:
    try:
        argtype, argname = fieldarg.rsplit(None, 1)
    except ValueError:
        pass
    else:
        types.setdefault(typename, {})[argname] = [nodes.Text(argtype)]
        fieldarg = argname
```

| # | Solution.lean impl op (`resolveParamMethod`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `descriptor : List Char` | the local `fieldarg : str` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | parameter `mayCarryType : Bool` | the guard `if typedesc.is_typed:` | R | `bool` ↔ `Bool` (mapping.md §2). When false, the `try`/`except`/`else` block is skipped and the descriptor passes through untouched — modeled by the `else` branch of `resolveParam` (`typeName := none`, `name := descriptor`). |
| A3 | `severTail descriptor` — separate on the LAST whitespace run, at most once, `none` ⇔ fewer than two whitespace-separated parts | `fieldarg.rsplit(None, 1)` (the 2-tuple unpack, with `ValueError` ⇔ the `except`) | A-reference + I | the changed string op is modeled **deeply**: `severTail` (+ `rstripWs`/`tailWord`/`beforeTailWord`, pure region) IS the last-whitespace separation. No consumed axiom. The fold/strip ops are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `str.rsplit(None,1)` is the **A-reference** G-AX validates. mapping.md §3.1. |
| A4 | `some (typ, nm) ⇒ {name := nm, typeName := some typ}` | the `else:` branch: `types[...][argname] = [Text(argtype)]`; `fieldarg = argname` | R + I | a successful 2-element separation records the leading part as the type (`argtype`) and the trailing word as the name (`argname`/`fieldarg`). `ParsedParam.typeName = some typ` ⇔ "a type was recorded"; `name = nm` ⇔ the rebinding `fieldarg = argname`. mapping.md §2. |
| A5 | `none ⇒ {name := descriptor, typeName := none}` | the `except ValueError: pass` branch | R + I | when `rsplit` yields fewer than two parts the 2-tuple unpack raises `ValueError`, the body is skipped, and the descriptor is left untouched with no recorded type. mapping.md §2. |

Discriminating content of the change — separation at the LAST whitespace, not
the FIRST — lives in `severTail` taking `tailWord`/`beforeTailWord` from the
END of the string. On a descriptor whose type part itself contains whitespace
(e.g. the issue's `dict(str, str) opc_meta`), the spec demands
`severTail → some("dict(str, str)", "opc_meta")` (type kept whole), whereas the
pre-patch `split(None, 1)` separates at the first whitespace
(`("dict(str,", "str) opc_meta")`). `Solution_prepatch.lean` reproduces the
first-whitespace separation and **fails** the
`severTail descriptor = some (t,a) → out = {name := a, typeName := some t}`
clause exactly on such descriptors (G-DIFF).

## B. No additional change sites

The gold patch is a single-token edit (`split` → `rsplit`) at one site. There
are no other changed functions and no unchanged imperative callees needing a
`:|` stub. The only callee involved (`str.rsplit`) is the one whose behaviour
the change selects, and it is modeled deeply as an A-reference (§A, mapping.md
§3.1), not consumed as an axiom.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
which whitespace run the descriptor separates on — is modeled **deeply** (the
spelled-out `severTail` with reversed strip/take/drop, step A3, an A-reference +
I), not hidden behind an axiom about the operation under change. There are **no
consumed axioms** in this bundle.

## D. verify(Solution) ⇒ resolved

`resolveParamMethod` verifies only if its output equals `resolveParam descriptor
mayCarryType` — i.e. it separates on the LAST whitespace (A3) and records
`(name, type)` exactly as the gold `else:`/`except:` branches do (A4/A5). By R
(`str ↔ List Char`, `bool ↔ Bool`, the `(argname, argtype)` ↔ `ParsedParam`
bijection) the verified resolver equals the patched `fieldarg.rsplit(None, 1)`
descriptor handling on the tested `str` inputs; by G-AX the deep model
`severTail` equals the real `str.rsplit(None, 1)` (A-reference) and `wsCodes`
matches Python's whitespace classifier; by G-CONF the R/I transliteration of
`severTail`/`resolveParam` agrees with `patch.diff`'s behaviour on ≥10⁵ inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and an audited callee — and the gold patch resolves
(G-RESOLVE). The single trust point is the A-reference soundness of `severTail`
(G-AX); refinement fidelity is covered by this doc + G-EQ + G-CONF.
