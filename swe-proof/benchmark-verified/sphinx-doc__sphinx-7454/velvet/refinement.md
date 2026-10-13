# refinement.md — sphinx-doc__sphinx-7454

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`referenceForName` `do` block plus the deep `desiredKind` model) and `patch.diff`
(the gold patch). Each step is tagged **R** (type refinement; state the
bijection), **A** (axiomatized callee — none here), or **I** (identical concrete
op). EVERY step is R, A, or I; there is no kind-3 (inexpressible-changed-op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the narrative is audited by **G-EQ**. Claim: any impl verifying against
this frozen spec, refined per the map below, is behaviourally equal to the gold
patch on the observed inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The cross-reference builder — `make_xref` inside `_parse_annotation`

Gold hunk (`sphinx/domains/python.py:73-75`):
```
 def make_xref(text: str) -> addnodes.pending_xref:
+    if text == 'None':
+        reftype = 'obj'
+    else:
+        reftype = 'class'
+
     return pending_xref('', nodes.Text(text),
-                        refdomain='py', reftype='class', reftarget=text)
+                        refdomain='py', reftype=reftype, reftarget=text)
```

| # | Solution.lean impl op (`referenceForName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `name : List Char` | `text: str` arg of `make_xref` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via the single-name annotation → lone `pending_xref` path; `"None" ↔ "None".toList`. |
| A2 | `let kind := if name = "None".toList then .valueRef else .classRef` | `if text == 'None': reftype = 'obj' else: reftype = 'class'` | R + I | the changed selection, modeled **deeply** (no axiom). The control flow is identical (a two-arm conditional on `text == 'None'`); the values refine by the finite bijection `'class' ↔ classRef`, `'obj' ↔ valueRef` (mapping.md §2). |
| A3 | `{ kind, domain := "py".toList, target := name, label := name }` | `pending_xref('', nodes.Text(text), refdomain='py', reftype=reftype, reftarget=text)` | R + I | the node constructor; its four observed fields map field-for-field. `domain ↔ refdomain='py'` (constant), `target ↔ reftarget=text`, `label ↔ nodes.Text(text)`, `kind ↔ reftype`. `pending_xref`/`nodes.Text` are constructors, captured structurally — no callee contract owed (mapping.md §3). |
| A4 | `return result` (`TypeReference`) | the node returned by `make_xref` | I | identity; the returned node IS the result record under the field bijection. |

Discriminating content of the change — the `None` token gets `reftype='obj'`
instead of `'class'` — lives in `desiredKind "None".toList = .valueRef` (model) ⇔
the new `if text == 'None': reftype = 'obj'` branch (real). The pre-patch builder
emitted `reftype='class'` for every token including `None`;
`Solution_prepatch.lean` reproduces that (`kind := .classRef` unconditionally)
and **fails** the clauses `out.kind = desiredKind name`, `name = "None" → out.kind
= .valueRef`, and `out.kind = .valueRef ↔ name = "None"` (G-DIFF, confirmed:
errors on `ensures_1/_3/_4`).

## B. The unchanged frame (directive 5)

`name` is **not** `mut`; the postconditions pin the unchanged frame exactly:
`out.domain = "py".toList` (the domain never varies), `out.target = name` and
`out.label = name` (the token is echoed verbatim into both the link target and
the shown text — the gold patch leaves `nodes.Text(text)` and `reftarget=text`
untouched). A wrong impl that altered the domain, target, or shown text — or that
flipped the kind for any other name — cannot verify (G-PANEL attacker 1; the
`↔` clause makes `valueRef` reachable by `None` and ONLY `None`).

## C. No kind-3, no axioms

Every step is R or I. The one operation that genuinely *changed* — the choice of
the reference kind — is modeled **deeply** (the spelled-out `desiredKind` dispatch,
step A2), not hidden behind an axiom about the function under change. There are no
consumed axioms and no A-reference deep models of outside callees: `pending_xref`
and `nodes.Text` are pure constructors whose observed effect is the four record
fields. Hence `G-AX = skip` (no `axiom_check.py`); `conf_skip = false` (the impl
region is pure R/I content that G-CONF transliterates).

## D. verify(Solution) ⇒ resolved

`referenceForName` verifies only if its output's `kind` equals `desiredKind name`
(`= valueRef` iff `name = "None"`, A2) with the domain/target/label frame pinned
(B). By R (`str ↔ List Char`, `'class'/'obj' ↔ classRef/valueRef`, the field
bijection) the verified builder equals the patched `make_xref` on every name
token; by G-CONF the R/I transliteration agrees with the real patched
`_parse_annotation` on ≥10⁵ inputs (including `None` and `None`-near-misses), 0
disagreements. Therefore a model satisfying this spec, refined by the map above,
is the gold patch up to type refinement — and the gold patch resolves
(G-RESOLVE). The single trust point is refinement fidelity (this doc, G-EQ +
G-CONF); there are no axioms to trust (G-AX skip).
