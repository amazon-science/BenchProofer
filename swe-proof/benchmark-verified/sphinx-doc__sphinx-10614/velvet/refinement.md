# refinement.md — sphinx-doc__sphinx-10614

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`buildLinkMap` `do` block, the pure `linkMap`/`refEntry` model, and the deep
`afterLastHash` model) and `patch.diff` (the gold patch). Each step is tagged
**R** (type refinement), **A** (axiomatized callee — **A-consumed** where the
proof uses the axiom's `ensures`, **A-reference** where a deep model is validated
== the real callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`); the
A-reference and this narrative are audited by **G-AX** and **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The link-map construction — `html_visit_inheritance_diagram` (`sphinx/ext/inheritance_diagram.py:411-423`)

Gold hunk (the changed loop body):
```
 for child in pending_xrefs:
     if child.get('refuri') is not None:
-        if graphviz_output_format == 'SVG':
-            urls[child['reftitle']] = "../" + child.get('refuri')
+        if not child.get('internal', True):
+            refname = child['refuri'].rsplit('#', 1)[-1]
         else:
-            urls[child['reftitle']] = child.get('refuri')
+            refname = child['reftitle']
+        urls[refname] = child.get('refuri')
     elif child.get('refid') is not None:
         if graphviz_output_format == 'SVG':
-            urls[child['reftitle']] = '../' + current_filename + '#' + child.get('refid')
+            urls[child['reftitle']] = current_filename + '#' + child.get('refid')
         else:
             urls[child['reftitle']] = '#' + child.get('refid')
```

| # | Solution.lean impl op (`buildLinkMap`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `refs : List DiagRef` | `pending_xrefs = cast(Iterable[...], node)` | R | each child node ↔ a `DiagRef` of its four touched attrs (mapping.md §1). |
| A2 | the backward `while` loop folding `refEntry … ++ acc` | `for child in pending_xrefs: …` building `urls` | I | concrete in-order iteration; `buildLinkMap` produces `linkMap` = the in-order concatenation of per-child entries. G-CONF transliterates it. |
| A3 | `refEntry`, `match c.target with some uri => …` | `if child.get('refuri') is not None: …` | R | `child.get('refuri')` ↔ `c.target : Option`, `is not None` ↔ `some` (mapping.md §2). |
| A4 | key `if c.external then afterLastHash uri else c.name`; value `uri` (verbatim) | `if not child.get('internal', True): refname = refuri.rsplit('#',1)[-1] else: refname = reftitle` then `urls[refname] = refuri` | A-reference + I | the changed branch is modeled **deeply**: `c.external` ↔ `not child.get('internal', True)` (R); the external-key recovery `afterLastHash uri` deeply models `refuri.rsplit('#',1)[-1]` (**A-reference**, G-AX-validated); the in-project key `c.name` ↔ `reftitle` (R); the URL `uri` emitted **verbatim, no `"../"` prefix** is the fix (I). |
| A5 | `match c.anchor with some aid => (c.name, (if isSvg then page else []) ++ '#' :: aid)` | `elif child.get('refid') is not None:` → `current_filename + '#' + refid` (SVG) / `'#' + refid` (else) | R + I | `refid` ↔ `c.anchor : Option`; the SVG link is `page ++ "#" ++ aid` with **no `"../"` prefix** (the fix), the non-SVG link is `"#" ++ aid` (unchanged). `'#' :: aid` ↔ `'#' + refid` (I). |
| A6 | `none/none => []` (no entry) | neither `refuri` nor `refid`: no `urls[...]` write | I | a child contributing nothing. |
| A7 | `out = linkMap isSvg page refs` returned | `urls` passed to `graph.generate_dot(name, urls, …)` | R | the produced map ↔ the assoc-list of writes (mapping.md §2). |

Read-only frame (directive 5): `refs`, `isSvg`, `page` are not `mut`; the loop
mutates only `acc` and `i`. No `mut` parameter, so no `xOld = x` obligation.

## B. The two independently-fixed behaviours (G-DIFF)

The patch fixes two observable behaviours; each has its own failing prepatch
keeping the spec byte-identical:

1. **External-target keying + verbatim target URL** (`Solution_prepatch.lean`).
   Pre-patch keys every `refuri` entry on `reftitle` (never recovering the
   external key from the URI) and, under SVG, prepends `"../"` to the target
   URL. Diverges from the spec at any `target = some _` reference — fails
   `out = linkMap …` on the discriminating `refEntry` clause (step A4).
2. **Anchor (`refid`) SVG prefix removal** (`Solution_prepatch_2.lean`).
   Pre-patch, under SVG, prepends `"../"` in front of the page path for a
   fragment-only ref (`"../" ++ page ++ "#" ++ aid`). The spec emits
   `page ++ "#" ++ aid`. Diverges at any `anchor = some _` ref under SVG —
   fails on the discriminating `refEntry` clause (step A5). This is the exact
   404-with-SVG bug in the issue title (the SVG `object`-embedded links are
   resolved relative to the SVG, so the extra `../` over-climbs).

Both prepatches verified to FAIL G-VERIFY on the `invariant_2` (fold-step) goal.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *uses a library call*
on the changed path — `refuri.rsplit('#', 1)[-1]` — is modeled **deeply**
(`afterLastHash`, step A4, an A-reference validated == the real call by G-AX),
not hidden behind an axiom. The `axioms` region is empty; there are no consumed
axioms.

## D. verify(Solution) ⇒ resolved

`buildLinkMap` verifies only if its output equals, per child in order: the
verbatim target URL keyed on `afterLastHash uri` for external refs / `name`
otherwise (A4), and the `"../"`-free fragment link for anchors (A5). By R
(`str ↔ List Char`, `Option`, `Bool`, dict ↔ assoc-list) the verified map equals
the gold loop's `urls` on the tested children; by G-AX the deep model
`afterLastHash` equals the real `rsplit('#',1)[-1]` (A-reference); by G-CONF the
R/I transliteration agrees with `patch.diff`'s behaviour over the fuzzed inputs.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the one audited callee — and the gold patch
resolves (G-RESOLVE). Trust points: the A-reference's soundness (G-AX) and the
refinement fidelity (this doc, G-EQ + G-CONF).
