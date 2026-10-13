# refinement.md — sphinx-doc__sphinx-10323

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`assembleBlock` `do` block, plus the deep `removeIndent`/`addPrefix`/`addSuffix`/
`joinLines` models) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A-reference** (deep model validated == the real callee by
G-AX), or **I** (identical concrete op). There are no **A-consumed** axioms.

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs and this narrative are audited by **G-EQ**. Claim: any
impl verifying against this frozen spec, refined per the map below, is
behaviourally equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The filter-composition site — `LiteralIncludeReader.read` (`code.py:219-231`)

Gold hunk (the ordered `filters` list):
```
                       self.start_filter,
                       self.end_filter,
                       self.lines_filter,
+                      self.dedent_filter,
                       self.prepend_filter,
-                      self.append_filter,
-                      self.dedent_filter]
+                      self.append_filter]
```
i.e. the indentation-removal filter is moved to run BEFORE the
before-/after-line-insertion filters instead of after them.

| # | Solution.lean impl op (`assembleBlock`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `body : List (List Char)` | the `lines` value reaching the `dedent`/`prepend`/`append` segment of the `filters` pipeline (output of `pyobject`/`start`/`end`/`lines` filters) | R | `List[str]` (each keeping its `'\n'`) ↔ `List (List Char)` (mapping.md §1, §2). The upstream selection filters are unchanged by the patch and abstracted into `body`. |
| A2 | parameters `prefixText`, `suffixText`, `indent` | `self.options['prepend']`, `self.options['append']`, `self.options['dedent']` | R | option carriers: `str`↔`List Char` (absent↔`[]`), `optional_int`↔`Option Nat` (absent↔`none`) (mapping.md §2). |
| A3 | `let trimmed := removeIndent indent body` (runs FIRST) | `self.dedent_filter` placed at the head of the reordered trio (`+ self.dedent_filter` before `prepend`) | A-reference + I | the indentation-removal is modeled **deeply** by `removeIndent`/`removeIndentLine` (pure region); the equality of that model to the real `dedent_lines` is the **A-reference** G-AX validates (mapping.md §3.1). Its position FIRST in the `do` block mirrors `dedent_filter` now preceding `prepend`/`append`. |
| A4 | `let withHead := addPrefix prefixText trimmed` | `self.prepend_filter` (now applied AFTER dedent) | A-reference + I | `addPrefix` is the deep model of `prepend_filter` (mapping.md §3.2); applied to the already-trimmed body, so the prepended line is NOT trimmed. |
| A5 | `let withTail := addSuffix suffixText withHead` | `self.append_filter` (applied last) | A-reference + I | `addSuffix` is the deep model of `append_filter` (mapping.md §3.3); the appended line is likewise exempt from trimming. |
| A6 | `return joinLines withTail` | `''.join(lines)` (`code.py:233`) | I | concatenation of the assembled lines; `str` `''.join` ↔ `List` `++`-fold `joinLines`. |

Discriminating content of the change — indentation removal applies to the **body
only**, the before/after lines being exempt — lives in the ORDER of the `do`
block: `removeIndent` before `addPrefix`/`addSuffix`. The pre-patch order applied
`removeIndent` LAST, over the body WITH the added lines already in place, stripping
their leading whitespace too. `Solution_prepatch.lean` reproduces that order and
**fails** `out = joinLines (addSuffix … (addPrefix … (removeIndent indent body)))`
on exactly that clause (G-DIFF): its goal reduces to
`joinLines (removeIndent indent (addSuffix … (addPrefix … body))) =
 joinLines (addSuffix … (addPrefix … (removeIndent indent body)))`, which is false
whenever a prepended/appended line has leading characters that `removeIndent` would
strip — precisely the F2P scenario (`prepend: 'class Foo:'`, `dedent: 2`, expected
`class Foo:` preserved, not `ass Foo:`).

## B. No additional change sites

The patch edits a single contiguous hunk (the `filters` list order). There is no
second independently-observable behavior; one prepatch suffices for G-DIFF.

## C. No A-consumed axioms; no kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The operation that genuinely *changed* — the
relative order of indentation-removal vs boundary-line insertion — is expressed
**directly** by the order of the `do` block (A3 before A4/A5), not hidden behind an
axiom. The three filters themselves are unchanged library routines, modeled deeply
(`removeIndent`/`addPrefix`/`addSuffix`) and validated against the real callees by
G-AX (A-reference); none is consumed as an axiom whose `ensures` the proof relies
on. `meta.json axioms = []`, `deep_model_references` lists the three.

## D. verify(Solution) ⇒ resolved

`assembleBlock` verifies only if its output equals
`joinLines (addSuffix suffixText (addPrefix prefixText (removeIndent indent body)))`
— i.e. indentation removed from the body BEFORE the boundary lines are added (A3–A6).
By R (`List[str] ↔ List (List Char)`, the option carriers) the verified assembly
equals the patched `read()`'s `dedent → prepend → append → ''.join` pipeline on the
modeled inputs; by G-AX the three deep models equal the real `dedent_lines` /
`prepend_filter` / `append_filter` (A-reference); by G-CONF the R/I transliteration
agrees with `patch.diff`'s behaviour on ≥10⁵ fuzzed option configurations.
Therefore a model satisfying this spec, refined by the map above, is the gold patch
up to type refinement and audited callees — and the gold patch resolves
(G-RESOLVE). The one trust point is refinement fidelity (this doc, G-EQ + G-CONF)
plus deep-model soundness (G-AX); there are no consumed axioms.
