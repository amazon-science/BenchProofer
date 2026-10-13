# refinement.md — sphinx-doc__sphinx-8593

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `collectMemberDocs` `do` block plus the deep `buildMembers` / `lookupDocs` /
`joinNL` model) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed** / **A-reference**),
or **I** (identical concrete op). EVERY step is R, A, or I.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1). This bundle has **no axioms**, so there is no A leg and no G-AX.

Claim: any impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The member-collection site — the new `ModuleDocumenter.get_module_members`

Gold hunk (`sphinx/ext/autodoc/__init__.py`, new method): for each `name in
dir(self.object)`, build `ObjectMember(name, value, docstring="\n".join(
attr_docs.get(('', name), [])))`; then add annotation-only members the same way.
The pre-patch path used the importer-level `get_module_members(module)` which
returned bare `(name, value)` tuples with **no** docstring.

| # | Solution.lean impl op (`collectMemberDocs`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `names : List Int` | `dir(self.object)` (the candidate roster) | R | each `str` name ↔ a distinct `Int` (mapping.md §2). G-CONF drives both sides on the identical `dir(obj)` roster. |
| A2 | parameter `attrDocs : List (Int × List (List Int))` | `attr_docs` restricted to `('', name)` keys (`self.analyzer.attr_docs`, or `{}` when no analyzer) | R | the per-name doc-line table; `str` line ↔ `List Int` codes (mapping.md §2). Unchanged input carrier (mapping.md §3). |
| A3 | `lookupDocs n attrDocs` | `attr_docs.get(('', name), [])` | I | the recorded doc lines for `name`, `[]` if absent; transliterated 1:1 by G-CONF (`shadow_lookup_docs`). |
| A4 | `joinNL (lookupDocs n attrDocs)` | `"\n".join(attr_docs.get(('', name), []))` | I | the changed op restored by the fix: assemble the member's documentation text by joining its lines with `'\n'`. Modeled **deeply** (`joinNL`, pure region); transliterated 1:1 by G-CONF (`shadow_join_nl`). |
| A5 | `{ name := n, doc := … } :: result` (backward `while` fold building the ordered list) | `members[name] = ObjectMember(name, value, docstring=…)` (insertion-ordered dict) | I | one entry per name in roster order; the backward fold reproduces insertion order. The `value`/`object`, `class_`, `skipped` fields are unmodeled R-identities (mapping.md §2) — not observed by the metadata decision. |
| A6 | `out = buildMembers attrDocs names` (the postcondition) | the returned `members.values()` | R + I | the result is exactly the per-name expansion attaching each member's assembled doc text. G-CONF projects each side to `(name, doc)` and diffs. |

Discriminating content of the change — each member now CARRIES the documentation
text assembled from its recorded lines, instead of carrying none — lives in
`doc := joinNL (lookupDocs n attrDocs)` (model) ⇔ `docstring="\n".join(
attr_docs.get(('', name), []))` (real). `Solution_prepatch.lean` reproduces the
pre-patch behaviour (`doc := []` — the bare-tuple collector dropped the doc text)
and **fails** `out = buildMembers attrDocs names` (G-DIFF) on any name with
recorded documentation lines. That dropped doc text is precisely why downstream
`filter_members` → `extract_metadata` never saw `:meta public:` / `:meta private:`
on module data members.

## B. Behaviour-preserving plumbing — R-identities (not separately modeled)

The gold patch also edits surrounding code that is order/value-preserving for the
tested behaviour and therefore modeled as R-identities (mapping.md §2.1):

- **B1 — annotation-only loop.** The new method's second loop adds
  `inspect.getannotations(self.object)` names not already collected, with the
  SAME `docstring="\n".join(attr_docs.get(('', name), []))`. This is the same
  per-name doc-attachment over a second name source; the `buildMembers` fold
  covers it (G-CONF feeds any annotation-only names through the same roster).
- **B2 — `get_object_members` rewiring.** It now calls
  `self.get_module_members()` and returns `list(members.values())` /
  marks `member.skipped` by `member.__name__ not in self.__all__`. In the F2P
  scenario (no `__all__`) it returns the collected members unchanged, an
  order-preserving R-identity over the collected list. (The `__all__`/skipped
  selection logic is the subject of the **sibling** instance sphinx-8595, not
  this fix; here it is untouched behaviour.)
- **B3 — importer `get_module_members(module)`.** Only a deprecation
  `warnings.warn(...)` is added; it is no longer on the resolving path and emits
  no observable difference for the tests. Pure R-identity.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. The one operation that genuinely *changed* — attaching to
each collected member the documentation text assembled from its recorded lines —
is modeled **deeply** (the spelled-out `lookupDocs` + `joinNL` + the verified
backward fold, steps A3–A6), not hidden behind an axiom about the function under
change. There are **no consumed axioms and no deep-model references**: the two
values read from elsewhere (`dir(self.object)`, `self.analyzer.attr_docs`) are
unchanged callees whose OUTPUT is consumed as data, so they are modeled as the
input carriers `names` / `attrDocs` (mapping.md §3), bridged by G-CONF.

## D. verify(Solution) ⇒ resolved

`collectMemberDocs` verifies only if its output equals the exact per-name
expansion that attaches `joinNL (lookupDocs n attrDocs)` to each member (A4, A6).
By R (`str ↔ Int` names, `str ↔ List Int` doc lines, the unmodeled R-identity
fields, the B-plumbing identities) the verified collector equals the gold method
`docstring="\n".join(attr_docs.get(('', name), []))` on the tested inputs; by
G-CONF the R/I transliteration of `buildMembers`/`lookupDocs`/`joinNL` agrees with
the real patched `ModuleDocumenter.get_module_members` on ≥10⁵ inputs. Therefore a
model satisfying this spec, refined by the map above, is the gold patch up to type
refinement — and the gold patch resolves (G-RESOLVE). The sole trust point is
refinement fidelity (this doc, G-EQ + G-CONF); there are no axioms (no G-AX).
