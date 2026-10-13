# RELAXED_LEAKAGE — sympy__sympy-15976 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

## The mismatch

The gold fix to `MathMLPresentationPrinter._print_Symbol`
(`sympy/printing/mathml.py:745`) changes WHICH node represents a scripted
variable: pre-patch, the routine created an `<mi>` element up front (bold
applied to it early) and appended the `msub`/`msup`/`msubsup` script
container INSIDE that `<mi>`; post-patch, the script container itself IS the
returned node (and the bare base-name `<mi>` when there are no scripts), with
`mathvariant="bold"` applied to that final representing node.

- **The public problem_statement is a pure visual-symptom report**: "A symbol
  ending with a number is made invisible when printing with MathML" — a
  Safari 12 rendering artifact, with a repro script and two screenshots.
  Token scan of problem_statement: ZERO hits for any of the discriminating
  vocabulary (`mi`, `msub`, `msup`, `msubsup`, subscript, superscript, wrap,
  container, element, tag, bold, mathvariant, node, child). It names only
  "MathML", "presentation", and the symptom.
- **The structural discriminator is gold/test_patch/hints-only.** The
  `<mi>`-wrapping diagnosis (`<mi><msub>...</msub></mi>`, "Removing the pair
  of `mi` tags ... works") lives solely in `hints_text` — which is excluded
  from the leakage baseline — and in the gold diff and hidden `test_patch`,
  whose F2P test (`test_presentation_symbol`) asserts, for every script
  combination, that the returned node's top `nodeName` is the script
  container (`msub`/`msup`/`msubsup`) with children `(mi, [sub], [sup])` in
  order, and that bold lands on the representing node.

The leaking content is the spec view's postconditions
`ensures (subs ≠ none ∧ sups = none) → out.tag = "msub".toList` (and the
msup/msubsup/mi siblings), the deep `buildSymbol` dispatch that pins the
representing node's shape, and the docstring describing that dispatch. From
the spec view the gold edit's intent is reconstructible.

## Why the leak is unavoidable

Faithfulness forces the structural discriminator into the spec:

- The F2P test pins the EXACT top-tag structure: `msub`/`msup`/`msubsup` as
  the top node — NOT an `mi` wrapping it — plus bold on the representing
  node. Any spec that is faithful to the post-gold behavior MUST fail the
  prepatch (G-DIFF requires it), and the prepatch produces structurally
  VALID markup (an `<mi>` wrapping the container) that differs only in that
  top-node shape. Hence the spec must pin exactly the tag/shape facts that
  reveal the fix.
- The problem_statement's actual observable — "invisible in Safari 12" — is
  a rendering-engine artifact. No tractable Lean spec over minidom
  observables can encode "renders invisibly in Safari"; the ONLY expressible
  faithful discriminator is the node structure the F2P test reads.
- A spec derivable from problem_statement alone could say at most "the
  printed markup makes the symbol visible" — not expressible — or pin
  nothing structural, admitting the prepatch (a G-DIFF/spec-too-weak
  defect). Faithful + non-leaking is provably impossible here.

This is the same faithful-must-leak shape as the dispositioned
sphinx-doc__sphinx-10466 velvet instance (ascending-sort facet): the
discriminator exists only in gold + hidden tests + hints, and the spec cannot
be both faithful and silent about it. De-narration HAS been applied where
possible: the spec-view docstring states only the abstract desired shape
(which container represents a scripted variable, where bold lands) and does
not name the patched file/function, quote diff lines, or narrate the
pre-patch wrapping bug mechanism.

## Core soundness is intact (per the recorded P2 audit, 2026-08-02)

- G-VERIFY: Solution.lean verifies (no sorry); positive control with a
  structurally-different correct impl also verifies.
- G-DIFF: `Solution_prepatch.lean` (pre-image: `<mi>` created up front, bold
  early, container nested inside) fails exactly the three scripted-tag
  clauses + the structural equality; the no-script `mi` clause correctly
  survives.
- G-EQ: SOUND/TIGHT — 12 attacks re-run, none breaks the spec (prepatch bug,
  ignore-bold, swapped child order, swapped containers, dropped scripts,
  dropped mname child all rejected); positive control verifies.
- G-PANEL-2 (faithfulness): FAITHFUL — modeled `buildSymbol` matches the
  REAL gold-patched `_print_Symbol` (base_commit 701441853…): bundled
  conformance_check.py = 100,014 renders / 0 disagreements (seed 15976), plus
  an independent adversarial probe over edge names = 0 divergences.
- G-CONF: 0 / 100,014 disagreements. G-AX: skip (zero axioms — the changed
  behavior is modeled deeply). G-RESOLVE: patch.diff is gold verbatim,
  resolves.

Only the secondary no-leakage property is relaxed, for this one documented
facet (the representing node's top tag per script combination and the bold
placement on it).
