# refinement.md — sphinx-doc__sphinx-9258

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`splitUnionTypeField` `do` block plus the deep model `splitTokens`/`stepLen`/
`delimLen` it folds over) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement; state the bijection), **A-consumed** (proof uses an
axiom's `ensures`), **A-reference** (a deep model validated == the real callee by
G-AX), or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `make_xrefs()` (`sphinx/domains/python.py:304`)

Gold hunk (the only change the patch makes):
```
- delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\.\.\.)'
+ delims = r'(\s*[\[\]\(\),](?:\s*or\s)?\s*|\s+or\s+|\s*\|\s*|\.\.\.)'
```
i.e. the delimiter set used to split-and-classify a type field gains the
`\s*\|\s*` (vertical-bar) alternative. The rest of `make_xrefs`
(`re.split` → `filter(None, …)` → per-piece `delims_re.match` classification →
`make_xref` per content piece) is unchanged.

| # | Solution.lean impl op (`splitUnionTypeField`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `target : List Char` | `target: str` arg of `make_xrefs` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | the `while` fold over `stepLen true rest` / `delimLen true rest`, emitting one `⟨rest.take L, delimLen true rest == 0⟩` Token per step — i.e. the deep model `splitTokens true target` | `re.split(delims, target)` → `filter(None, …)` → per-piece `delims_re.match` classification, under the **post-patch** `delims` | A-reference + I | the changed operation (the split+classify under the new delimiter set) is modeled **deeply**: `splitTokens`/`stepLen`/`delimLen`/`contentLen` (pure region) and the verified loop ARE the maximal-munch scan. The fold ops (`take`, `drop`, `++`, `==`, the loop) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `re` engine under the new `delims` is the **A-reference** G-AX validates (mapping.md §3.1). No consumed split axiom. |
| A3 | each emitted Token `⟨piece, linked⟩` with `linked = (delimLen true == 0)` | per kept piece: `delims_re.match(piece)` true ⇒ verbatim separator node (`linked = false`); false ⇒ `make_xref(…, piece, …)` node (`linked = true`) | R + I | classification is the parity of the capturing-group `re.split` output; `splitTokens` reproduces it with `linked = (delimLen == 0)` (**I**). The `linked = true` Token carries, verbatim, the sub-target string `make_xrefs` hands to `make_xref` — the `re.split` piece, unmodified between the split and the call (**R** at the call boundary, mapping.md §2/§3.2, re-checked by G-AX §3.2). `make_xref`'s own downstream rendering (incl. its pre-existing `.`/`~` short-name display handling) is outside the modeled boundary and unchanged by the patch; on the F2P pieces (no such prefix) the rendered node text coincides with the boundary string. |
| A4 | `result` returned (`List Token`) | `results` list of docutils nodes returned | R | order-preserving node↔Token bijection (mapping.md §2): each kept piece ↔ one node; the F2P test reads each node's text and whether it is a `pending_xref` (link) vs a `literal_emphasis` (separator). |

Discriminating content of the change — the vertical-bar `|` becomes a recognized
separator, so `int | str` splits into `int`, ` | `, `str` (three pieces: two
linked references and one verbatim separator) instead of the single content run
`int | str`. This lives in `delimPipe true` / `delimLen true`'s pipe branch
(model) ⇔ the `\s*\|\s*` alternative of the post-patch `delims` (real). The
pre-patch regex lacked it; `Solution_prepatch.lean` reproduces that by folding
with `stepLen false`/`delimLen false` (pipe NOT a separator) and **fails**
`out = splitUnionType target` (= `splitTokens true`) at the discriminating step
(G-DIFF).

## B. No consumed axiom

The `axioms` region is empty. The unchanged per-token callee `make_xref`
(`python.py:285`) is handled as an **R-refinement at the call boundary** (§A row
A3, mapping.md §3.2), not an axiom: the modeled Token text is the sub-target
string handed to `make_xref` — the `re.split` piece, unmodified between the
split and the call. G-AX §3.2 re-checks that boundary R-claim. `make_xref`'s
downstream rendering is outside the modeled boundary and unchanged by the patch.
The unchanged `re` engine is the **A-reference** of row A2 (deep-modeled,
validated == real by G-AX §3.1), not a consumed axiom.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
the delimiter-set split+classify — is modeled **deeply** (the spelled-out
maximal-munch scan `splitTokens`, step A2, an A-reference + I), not hidden behind
an axiom about the function under change. There is no consumed split/classify
axiom.

## D. verify(Solution) ⇒ resolved

`splitUnionTypeField` verifies only if its output equals `splitUnionType target`
= `splitTokens true target` (A2/A3) — the full maximal-munch scan with the
vertical bar as a recognized separator. By R (`str ↔ List Char`, node↔Token,
`make_xref` text-preservation) the verified token stream equals the post-patch
`make_xrefs` node stream on the tested type fields; by G-AX the deep model
`splitTokens true` equals the real `re` split+classify under the post-patch
`delims` (A-reference); by G-CONF the R/I transliteration of the fold agrees with
`patch.diff`'s behaviour on ≥10⁵ inputs. Therefore a model satisfying this spec,
refined by the map above, is the gold patch up to type refinement and the audited
A-reference — and the gold patch resolves (G-RESOLVE). Trust points are exactly
the two of plan §1.1: A-reference soundness (G-AX) and refinement fidelity (this
doc, G-EQ + G-CONF).
