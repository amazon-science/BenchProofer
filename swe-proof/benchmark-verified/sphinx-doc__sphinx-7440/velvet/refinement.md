# refinement.md — sphinx-doc__sphinx-7440

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`registerGlossaryName` `do` block and the `registeredKey` deep model) and
`patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — **A-consumed** where the proof uses the axiom's
`ensures`, **A-reference** where a deep model is validated == the real callee by
G-AX), or **I** (identical concrete op). Every step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The registration-key site — `make_glossary_term` (`sphinx/domains/std.py:308`)

Gold hunk:
```
-    std.note_object('term', termtext.lower(), node_id, location=term)
+    std.note_object('term', termtext, node_id, location=term)
```

| # | Solution.lean impl op (`registerGlossaryName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `termText : List Char` | `termtext` (= `term.astext()`), the `str` key argument computed in `make_glossary_term` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | result is `registeredKey termText` — the term text **verbatim** (no normalization), as recorded by and reported from the registry | `std.note_object('term', termtext, …)` then later `get_objects()` yielding the recorded name | A-reference + I | the registry round-trip is modeled **deeply** as `registeredKey` (the identity on the term text): the recorded/reported key IS the term text. No consumed `noteObject` axiom. The impl op (return the verbatim key, `registeredKey termText`) is **I** (concrete, transliterated by G-CONF and run through the real `make_glossary_term` + `get_objects`); the equality of that deep model to the real registry round-trip is the **A-reference** G-AX validates. mapping.md §3.1. |

Discriminating content of the change — the key is the term text **as written**,
NOT case-folded — lives in `out = registeredKey termText` with
`registeredKey = id` (model) ⇔ the removal of `.lower()` before `note_object`
(real). The pre-patch code passed `termtext.lower()`; `Solution_prepatch.lean`
reproduces that (`termText.map Char.toLower`) and **fails** `out = registeredKey
termText` (G-DIFF) on any term containing an upper-case character (e.g. `TERM2`).

## B. The xref-role flag site — `'term'` role (`sphinx/domains/std.py:568`)

Gold hunk: the `'term'` entry of `StandardDomain.roles` drops `lowercase=True`:
```
-        'term':    XRefRole(lowercase=True, innernodeclass=nodes.inline,
+        'term':    XRefRole(innernodeclass=nodes.inline,
                             warn_dangling=True),
```

| # | Solution.lean construct | patch.diff op | tag | justification |
|---|---|---|---|---|
| B1 | (no construct) | drop `lowercase=True` from the term xref role | I (test-neutral) | governs how a `:term:` cross-**reference** target is lowered at resolution time (`XRefRole.create_xref_node`, `roles.py:146`); the companion edit that keeps lookups consistent with the now case-preserving registration key. No F2P/`test_glossary` assertion resolves a term reference, so it is observationally neutral for the resolved verdict and contributes no spec clause. mapping.md §3.2. |

No separate failing prepatch for site B: it changes no value any F2P test
observes (a prepatch must keep the spec byte-identical, G-DIFF, and must *fail* —
a test-neutral edit cannot). Site A's prepatch already exercises the single
observable behavioural change (the registration key's case).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — which key
string is handed to the registry — is modeled **deeply** (the spelled-out
`registeredKey` = the term text verbatim, step A2, an A-reference + I), not hidden
behind an axiom about the function under change: there is no consumed `noteObject`
axiom. There are no consumed axioms in this bundle.

## D. verify(Solution) ⇒ resolved

`registerGlossaryName` verifies only if its output equals the term text verbatim
(`registeredKey = id`, A2) — i.e. no case folding. By R (`str ↔ List Char`) and
the registry's identity-on-name contract (A-reference, G-AX: `note_object` then
`get_objects` yields the recorded name unchanged), the verified key equals what
the gold `make_glossary_term` records, namely `termtext` itself; G-CONF confirms
this end-to-end through the real patched `make_glossary_term` + `get_objects` on
≥10⁵ inputs. The companion role-flag edit (B) is test-neutral. Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and the audited registry callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: callee soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
