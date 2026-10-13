# refinement.md — sphinx-doc__sphinx-8459

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `recordParamTypes` `do` block and the pure `paramEntry`/`recordedTypes`/
`returnEntry` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** / **A-reference**),
or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `record_typehints()` (`sphinx/ext/autodoc/typehints.py:23`)

Gold hunk:
```
-            sig = inspect.signature(obj)
+            sig = inspect.signature(obj, type_aliases=app.config.autodoc_type_aliases)
```
The only edit: the signature renderer is invoked with the **configured** alias
map `app.config.autodoc_type_aliases` instead of the default empty `{}`. The
surrounding loop (record each annotated parameter's `typing.stringify` result,
record the return annotation last) is unchanged.

| # | Solution.lean impl op (`recordParamTypes`) | patch.diff / repo op | tag | justification |
|---|---|---|---|---|
| A1 | params `params : List Param`, `retAnnot : Option SourceType` | `sig.parameters.values()` / `sig.return_annotation` | R | ordered param list ↔ `List Param`; `param.empty`/`sig.empty` ↔ `none` (mapping.md §2). |
| A2 | `aliases : Aliases` (read-only input) | `app.config.autodoc_type_aliases` | R | the configured alias map ↔ `List (List Char × List Char)` (mapping.md §2). The gold edit is precisely *that this value is consulted* (see "discriminating content" below). |
| A3 | `renderType : Aliases → SourceType → TypeStr` (free input) | `inspect.signature(obj, type_aliases=·)` ∘ `typing.stringify(·)` | R | the two UNCHANGED renderer callees, modeled as a universally-quantified free input — no axiom, no deep model (mapping.md §3). G-CONF leaves them as the **real** callees applied to `aliases`. |
| A4 | `result := returnEntry (renderType aliases) retAnnot` (initial), then prepend each `paramEntry`; backward `while` fold | the loop body `typehints.py:31-35`: `for param in sig.parameters.values(): if annotated: annotation[name] = stringify(param.annotation)` then `annotation['return'] = stringify(return_annotation)` | I | the backward fold computes exactly the forward concatenation `recordedTypes (renderType aliases) params ++ returnEntry (renderType aliases) retAnnot`; ordered iteration, skip-unannotated, and the `'return'` key appended last are the I-ops G-CONF transliterates. |
| A5 | `paramEntry`: `some a => [(name, render a)]`, `none => []` | `if param.annotation is not param.empty: annotation[name] = …` (else nothing recorded) | I | unannotated parameters contribute no entry; annotated ones bind `name → render annot`. |
| A6 | `returnEntry`: `some a => [("return".toList, render a)]`, `none => []` | `if sig.return_annotation is not sig.empty: annotation['return'] = …` | I | the return entry is keyed by the constant `'return'` and present iff a return annotation exists. |

Discriminating content of the change — the renderer is applied to the
**configured** `aliases` (`renderType aliases`), not the default empty map
(`renderType []`) — lives in the spec's `ensures` (`recordedTypes (renderType
aliases) … ++ returnEntry (renderType aliases) …`). The pre-patch called
`inspect.signature(obj)` with the default empty `type_aliases`, i.e. applied
`renderType []`; `Solution_prepatch.lean` reproduces that and **fails**
`out = recordedTypes (renderType aliases) params ++ returnEntry (renderType
aliases) retAnnot` (G-DIFF), because for any configured alias that changes a
rendered string `renderType aliases ≠ renderType []`.

## B. No axioms, no deep-model references

The renderer (`inspect.signature` + `typing.stringify`) is the only callee, and
it is **unchanged** by the patch. It is modeled as a **free input** — the spec
is universally quantified over it — which is strictly weaker than an axiom and
cannot over-claim. Therefore:

- No `axiom` is shipped; `axiom_check.py` is intentionally **absent**, so G-AX
  returns `skip` (no soundness obligation about a real callee to discharge).
- No A-consumed or A-reference rows exist. Every step above is **R** or **I**.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely *changed* — *which alias map
the renderer is given* — is expressed directly: the spec applies the free
renderer to the configured `aliases` argument. There is no operation Velvet
cannot express here, and no axiom hides the changed behavior.

## D. verify(Solution) ⇒ resolved

`recordParamTypes` verifies only if its output equals the ordered mapping
produced by applying the renderer **to the configured `aliases`** for every
annotated parameter in order, with the return entry last (A4–A6). By R
(`str ↔ List Char`, ordered-param ↔ `List Param`, `dict ↔ assoc list`,
`autodoc_type_aliases ↔ aliases`) the verified body equals the patched
`record_typehints` — which calls `inspect.signature(obj,
type_aliases=app.config.autodoc_type_aliases)` then `typing.stringify` in the
same order — on the tested inputs; by G-CONF the R/I transliteration of the loop
agrees with `patch.diff`'s behaviour over the fuzzed `(callable, alias-map)`
inputs. The F2P test
`test_autodoc_typehints_description_and_type_aliases` observes exactly that the
recorded type strings honour the configured alias (`myint`), which the spec
pins via `renderType aliases`. Therefore a model satisfying this spec, refined
by the map above, is the gold patch up to type refinement — and the gold patch
resolves (G-RESOLVE). The single trust point is refinement fidelity (this doc +
G-CONF); there is no axiom-soundness trust point (no axioms).
