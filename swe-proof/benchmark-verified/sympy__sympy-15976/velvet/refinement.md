# refinement.md — sympy__sympy-15976

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildSymbolNode` `do` block and the deep `buildSymbol` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — none here), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The node-assembly site — `_print_Symbol` (`sympy/printing/mathml.py:745`)

Gold hunk (pre-image → post-image), the structural essence:
```
- x = self.dom.createElement('mi')          # representing node fixed to <mi> up front
- if style == 'bold': x.setAttribute(...)    # bold applied to that <mi>
  ... build mname, subs, supers ...
  if len(supers) == 0:
      if len(subs) == 0:
-         x.appendChild(createTextNode(name))           # <mi> wraps the name text
+         x = mname                                      # representing node IS the name <mi>
      else:
-         msub = createElement('msub'); ...; x.appendChild(msub)   # <mi> wraps <msub>
+         x = createElement('msub'); x.appendChild(mname); x.appendChild(join(subs))
  else:
      if len(subs) == 0:
-         msup = ...; x.appendChild(msup)               # <mi> wraps <msup>
+         x = createElement('msup'); ...
      else:
-         msubsup = ...; x.appendChild(msubsup)         # <mi> wraps <msubsup>
+         x = createElement('msubsup'); ...
+ if style == 'bold': x.setAttribute('mathvariant','bold')   # bold applied to the representing node
  return x
```

| # | Solution.lean impl op (`buildSymbolNode`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `name : List Char` | the translated base name `name` (from `split_super_sub`) | R | `str ↔ List Char` (mapping.md §2). Already-translated base name is an input; the translation is unchanged infrastructure. |
| A2 | `subs : Option Node`, `sups : Option Node` | `join(subs)` / `join(supers)` present iff `len(...)>0` | R | non-empty script list ↔ `some <rendered node>`; empty ↔ `none` (mapping.md §2). `join` is unchanged; its result node is an input. |
| A3 | `bold : Bool` | `style == 'bold'` | R | only `'bold'` changes shape; else `false` (mapping.md §2). |
| A4 | `mname := .elem "mi" false [Node.text name]` | `mname = createElement('mi'); mname.appendChild(createTextNode(name))` (`mathml.py:775-776`) | I | identical concrete construction of the base-name identifier. |
| A5 | `core := match sups, subs with …` selecting the representing node directly: `mname` / `msub[mname,sub]` / `msup[mname,sup]` / `msubsup[mname,sub,sup]` | the post-image four-arm `if/else` assigning `x = mname` / `x = createElement('msub')…` / `'msup'…` / `'msubsup'…` | I | the changed control flow modeled **deeply** and faithfully: in every arm the representing node IS the chosen container (or the bare `mname`), NOT an `<mi>` wrapping it. Child order matches the post-image (`mname`, then subs, then sups for `msubsup`). |
| A6 | `x := setBold core bold` | `if style == 'bold': x.setAttribute('mathvariant','bold')` (post-image, AFTER assembly, `mathml.py:799-800`) | I | bold styling applied to the representing node, after it is chosen — exactly the relocation the patch performs. `setBold core false = core`. |
| A7 | `return x` | `return x` | I | identical. |

Discriminating content of the change — for a scripted variable the returned
node's top tag is the script container (`msub`/`msup`/`msubsup`), NOT `mi` — is
pinned by `buildSymbol` (A5) and by the postconditions
`ensures (subs ≠ none ∧ sups = none) → out.tag = "msub"` etc. The pre-patch code
fixed `x` to an `<mi>` element and nested the container inside it, so the top tag
stayed `mi`; `Solution_prepatch.lean` reproduces that and **fails** the three
scripted-tag clauses and the structural equality `out = buildSymbol …` (G-DIFF).
The no-script clause (`out.tag = "mi"`) still holds for both, correctly: the bug
only affects scripted variables.

## B. No second site

The patch touches only `_print_Symbol`. `_print_MatrixSymbol` and
`_print_RandomSymbol` delegate to it unchanged (`mathml.py:803-805`); their
behavior changes only through this routine, so the bold MatrixSymbol P2P test
(`<mi mathvariant="bold">A</mi>`, a no-script symbol) is preserved by the
no-script arm of A5 + A6 (`bold` applied to the bare `mi`). No separate prepatch.

## B2. Termination semantics: TOTAL correctness (spec-strengthening, audit repair)

The bundle uses `set_option loom.semantics.termination "total"`
(`TotalCorrectness`), not `"partial"`. A prior audit (G-PANEL-1, 2026-08-02)
exhibited a same-spec counterexample under partial correctness: a diverging
implementation (a non-terminating body in place of the straight-line dispatch)
verified vacuously, because partial correctness constrains only terminating
executions — while its translated patch would hang the printer and fail every
test. The real `_print_Symbol` node assembly is straight-line code (one
four-way conditional plus one attribute write) that always terminates, so
total correctness is the faithful semantics: it rejects every diverging impl
(no `decreasing` measure can be discharged for a non-terminating body) while
the verified impl here is loop-free and unaffected. The `set_option`/`open`
lines are part of the frozen spec view shared byte-identical by both twins.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The operation that genuinely changed — which node
represents a scripted variable and where the bold attribute lands — is modeled
**deeply** (the spelled-out `buildSymbol` dispatch, A5/A6), not hidden behind an
axiom. There are no axiomatized callees: `split_super_sub` and `join` are
unchanged infrastructure supplied as inputs (mapping.md §3), so there is no
A-consumed contract and no A-reference deep model.

## D. verify(Solution) ⇒ resolved

`buildSymbolNode` verifies only if its output equals `buildSymbol name subs sups
bold` (A5/A6) — i.e. the representing node is the script container itself for a
scripted variable, with bold applied to it. By R (`str ↔ List Char`, script
presence ↔ `Option`, `'bold' ↔ Bool`) the verified node equals the node the
post-image `_print_Symbol` returns on the same inputs; by G-CONF the R/I
transliteration of `buildSymbol` agrees with the patched printer's observable
`(top tag, bold, child tags)` on ≥10⁵ inputs. A model satisfying this spec,
refined by the map above, is the gold patch up to type refinement — and the gold
patch resolves (G-RESOLVE). The single trust point is refinement fidelity (this
doc, G-EQ + G-CONF); there are no axioms to trust (G-AX skip).
