# Relaxed-leakage disposition — sympy__sympy-15976

This instance is a documented **problem_statement ↔ gold mismatch**: the gold fix's
tested discriminator is a presentation-MathML *structural taxonomy* that appears
ONLY in `hints_text` and the hidden `test_patch`/gold diff, never in the
solver-visible `problem_statement`. Per `RELAXED_LEAKAGE.md` it is KEPT with
the leakage bar relaxed; `verify ⟹ correct` is unaffected. All three requirements
of the policy hold and are recorded below.

## 1. Core is sound (verify ⟹ correct holds)

- **G-VERIFY PASS** — `model.py` verifies (RC=0, ~25s < 300s, no flags).
- **G-DIFF PASS** — `model_prepatch.py` (the prepatch root-`<mi>`-wrapper skeleton:
  `x = MNode(TAG_MI, [...])` always, with the structural element as its lone child)
  shares the spec byte-identically (same_spec True) and **FAILS** on
  `node_tag(Result()) == root_tag_for(has_subs, has_supers)` at line 154 — for any
  name with a sub/superscript the buggy root tag is `mi`(=1) where the structural
  root (`msub`/`msup`/`msubsup`) is required. This is the exact named counterexample
  from the prior verdict; it no longer verifies.
- **G-EQ SOUND/TIGHT** — 6 adversarial wrong impls (swapped root kind, missing bold,
  wrong child order, group-kind ignoring multiplicity, dropped base-name child, the
  prepatch CE) are all rejected each on the precise clause it violates; a
  structurally-different correct positive control (children appended incrementally,
  root from `root_tag_for` directly) verifies non-vacuously. Directive-8 echo-cheat
  is closed: an impl taking the tag from `root_tag_for` but hardcoding wrong `ctags`
  is still rejected by the independent `node_ctags(...) == child_tags_for(...)`
  clause — the pure functions are input-grounded structural predicates (functions of
  `has_subs`/`has_supers`/`subs_multi`/`supers_multi`), not an opaque answer-key
  oracle; no echo discharge exists.
- **G-AX SOUND (consumed portion VACUOUS; `axioms=[]`)** — both A-references
  (`split_super_sub` UNCHANGED; the post-fix `_print_Symbol` structural construction)
  re-validated against the real base_commit sympy (701441853569): `axiom_check.py`
  exits 0 over 13 named (all F2P) + 4000 fuzz, checking root `nodeName`, the
  element-child `nodeName` sequence, the no-extra-`mi` invariant, and bold placement,
  with flags derived from the REAL `split_super_sub`. Discrimination confirmed:
  routing the PRE-patch builder through the same check FAILS on `x^2` (real `mi` vs
  expected `msup`).
- **Faithfulness CLEAN** — `patch.diff == gold` verbatim (2040 B). On the real
  worktree F2P `test_presentation_symbol` FAILS pre-patch and PASSES post-gold; P2P
  `test_print_matrix_symbol` passes. Spec output maps under the declared
  R-refinement (`nodeName↔tag`, `childNodes[i].nodeName↔ctags[i]`,
  `mathvariant↔bold`) onto the post-gold assertions for every F2P case including the
  first-failing input `x2`. `refinement.md` is all R / A-reference / I — no kind-3,
  no consumed (dead) axiom.
- **G-RESOLVE** — `patch.diff == gold`, applies cleanly at base_commit, harness run
  by orchestrator (expected-pass; gold resolves).

## 2. The leak is genuinely unavoidable (the behavior itself is the leak)

The entire behavioral content of `problem_statement` is the SYMPTOM: "A symbol
ending with a number is made invisible when printing with MathML" (a variable like
`x2` renders invisible in Safari). It contains NONE of the tested structural
discriminator. Token scan of `problem_statement` (lowercased), all counts **0**:

    mi 0 · msub 0 · msup 0 · msubsup 0 · mrow 0 · subscript 0 · superscript 0 ·
    wrap 0 · nest 0 · child 0 · root 0 · identifier 0 · element 0 · outermost 0 ·
    remove 0 · extra 0 · tag 0 · nodeName 0

The actual fix and what the F2P test pins is purely structural: the renderer must
NOT wrap the structural element in an outer `<mi>` — the root must be the
structural element itself (`mi`/`msub`/`msup`/`msubsup` chosen from sub/super
presence), with the base-name identifier and any sub/super groups as its depth-one
direct children. That diagnosis — the extra `<mi>` wrapper, the `<msub>` subscript,
the "when they are removed the symbol renders" insight — lives ONLY in
`hints_text`:

  > "It looks like an extra set of `<mi></mi>` tags are present, when they are
  >  removed: `<msub><mi>r</mi><mi>2</mi></msub>` the rendered output has the
  >  symbol in it."
  > "Removing the pair of `mi` tags around `<msub><mi>x</mi><mi>2</mi></msub>`
  >  works."

and in the hidden `test_patch`/gold diff. The F2P `test_presentation_symbol` pins
the exact DOM tree (`nodeName == 'msub'`, ordered `childNodes`), so any **faithful**
spec — one whose prepatch fails G-DIFF and that rejects every wrong impl in G-EQ —
MUST name that four-way root taxonomy and the depth-one child placement.

De-narrating to opaque int tag-codes does not help: the spec would still have to
describe the sub/super-driven four-way root choice and the name-as-direct-child
placement — concepts the `problem_statement` never mentions. The *behavior itself*
is the leak; faithful + non-leaking is provably impossible here. (The batch09
refinement already removed the worst, narrative form: the negative "no extra
identifier wrapper / not nested one level deeper / never the single child of an
enclosing identifier / NOT always an identifier wrapper / outermost node" prose. The
residual structural vocabulary — the element-kind taxonomy and the depth-one child
contract — is the irreducible behavioral content, not bug/fix narration, and is what
remains relaxed.)

## 3. Documented in-bundle

This file is the in-bundle record. `meta.json` carries
`gates.G-LEAK.status = "relaxed"` pointing here. The mechanical
`swebench_nagini.gates` G-LEAK lexical screen still PASSES (no patched path
`mathml.py`, no symbol `_print_Symbol`, no `fix`/`bug`/`Safari`/`invisible`, no
negation/wrapper smells) — the leak is semantic, not lexical, exactly as the policy
anticipates. The instance is appended to the central `RELAXED_LEAKAGE.md` scope
list (becomes 18 / 360).
