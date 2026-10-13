# refinement.md — sphinx-doc__sphinx-10323

The operation-by-operation correspondence between `model.py`'s implementation
(the `assemble` impl region, the deep `trim_block` model) and `patch.diff` (the
gold patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses the axiom's `Ensures`,
and **A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The fix — the filter pipeline order in `read()` (`sphinx/directives/code.py:219`)

Gold hunk (the `filters` list inside `read()`):
```
                        self.lines_filter,
+                       self.dedent_filter,
                        self.prepend_filter,
-                       self.append_filter,
-                       self.dedent_filter]
+                       self.append_filter]
```

The pipeline applies its filters left-to-right (`for func in filters: lines =
func(lines, ...)`). The change moves the per-line left-margin trim
(`dedent_filter`) from the LAST stage to BEFORE the leading-line insertion
(`prepend_filter`) and trailing-line append (`append_filter`). Behaviourally:
the trim is applied to the included text only; the author-supplied leading and
trailing lines are inserted afterwards and emitted verbatim.

`model.py.assemble` is the skeleton of the post-fix pipeline restricted to the
three relevant stages (trim, prepend, append) — the earlier stages
(pyobject/start/end/lines selection) are upstream of the change and produce
`included`; `assemble`'s `included` parameter is their output.

| # | model.py impl op (`assemble`) | patch.diff op (post-fix `read()` pipeline) | tag | justification |
|---|---|---|---|---|
| A1 | parameters `included: PSeq[PSeq[int]]`, `lead`, `trail: PSeq[int]`, `n: int` | the `lines` list flowing through the filters, the `prepend`/`append` option strings, the `dedent` width | R | `List[str]` lines ↔ `PSeq[PSeq[int]]` content lines (newline as implicit separator); `str` option ↔ `PSeq[int]`; `int` ↔ `int` (mapping.md §2). |
| A2 | `trimmed` built by the backward fold matching `trim_block(included, n)` (each element `included[i].drop(n)`) | `dedent_filter(lines)` run on the included text only (now the FIRST of the three stages) | A-reference | the changed-position per-line trim is modeled **deeply**: `trim_block` (each line content `PSeq.drop(n)`, with the per-element lemma `trim_block_at`) IS the per-line trim. There is no consumed trim axiom — the proof never depends on one. The deep model is validated **== the real callee** out-of-band: G-AX (axiom_check.py) runs `dedent_lines` per line and asserts `trim_block == dedent_lines` (rendered). The real callee `dedent_lines`' body is `line[dedent:]` (+ newline-special-case absorbed by the separator), exactly `content.drop(n)` (mapping.md §3.1). |
| A3 | `result = (emit(lead) + trimmed) + emit(trail)` — the supplied leading line prepended and the supplied trailing line appended, to the ALREADY-trimmed block | `prepend_filter` (`if prepend: lines.insert(0, prepend + '\n')`) then `append_filter` (`if append: lines.append(append + '\n')`), run AFTER `dedent_filter` | I + R | list `insert(0, ·)` / `append(·)` ↔ `PSeq` front/back concatenation (I on the concrete list ops; R on the `str`↔`PSeq[int]` line carrier). Both filters are GUARDED on the option being truthy, so an empty option contributes no line: that presence rule is modeled by the `@Pure` `emit` (a one-line block when the line has content, no line when it is empty) rather than assumed away, and it is validated against the real filters by G-AX. Because they run after the trim (the moved order), `lead`/`trail` are NOT passed through `trim_block` — exactly what `assemble` encodes (`lead`/`trail` enter `result` untrimmed). |
| A5 | `trimmed` is built unconditionally, before and independently of `emit(lead)`/`emit(trail)` | `dedent_filter`'s own guard is `if 'dedent' in self.options:` — the trim stage depends on the trim option ALONE and is independent of the two author filters | I | the two author filters' guards do not gate the trim stage in the real pipeline, so the included text is trimmed whether or not an author line is supplied. `assemble` encodes that by computing `trimmed` before either author line enters, with no guard on `lead`/`trail`; the postcondition `len(lead) == 0 and len(trail) == 0 -> Result() == trim_block(included, n)` and the `len(lead) == 0` branch of the per-included-line clause pin it, and they are non-vacuous because the precondition admits the absent-author-line states (mapping.md §2.1). |
| A4 | `result` returned (a `PSeq[PSeq[int]]`) | `''.join(lines), len(lines)` — the assembled text `read()` returns | R | rendering the model block `c ↦ c + '\n'` and joining equals the real `''.join(lines)` (mapping.md §2, G-AX end-to-end check §3.2); `len(lines)` ↔ `len(Result())`. |

The discriminating content of the change — the leading/trailing author lines are
emitted **verbatim** rather than left-margin-trimmed, while the included text is
trimmed **unconditionally** — lives in the primary postcondition
`Result() == (emit(lead) + trim_block(included, n)) + emit(trail)` (the trim wraps
the included text only) and its derived clauses: `Result()[0] == lead` when a
leading line is supplied (with `Result()[0] != lead.drop(n)` pinning that this
verbatim line is observably different from a trimmed one),
`Result()[len(Result())-1] == trail` when a trailing line is supplied, the
per-included-line clause in BOTH author-line regimes (`Result()[i+1] ==
included[i].drop(n)` with a leading line, `Result()[i] == included[i].drop(n)`
without), the length clause
`len(Result()) == len(emit(lead)) + len(included) + len(emit(trail))`, and the
unconditional-trim clause `len(lead) == 0 and len(trail) == 0 -> Result() ==
trim_block(included, n)`.

Those last three are what make the trim's INDEPENDENCE from the author filters
observable (A5). Without them the spec constrains only the both-author-lines-
supplied regime, and an implementation may make the entire trim stage contingent
on an author line being present: it satisfies every clause where an author line
exists, and the absent-author-line states are unconstrained — so it verifies while
failing the repo's dedent-only tests (`test_LiteralIncludeReader_dedent`,
`test_LiteralIncludeReader_tabwidth_dedent`, which set `dedent` and set neither
`prepend` nor `append`). That is why the precondition must ADMIT those states
(`n >= 0`, nothing required of `lead`/`trail`) rather than exclude them; excluding
them would make the states unreachable and every clause about them vacuous
(mapping.md §2.1). `properties.py`'s `pos-live-no-author-line` and
`pos-live-zero-width` are the liveness controls, and
`rival-trim-only-if-lead-present`, `rival-trim-only-if-both-present`,
`rival-no-trim-when-no-author-line`, `rival-blank-for-absent-author-line` and
`rival-zero-width-substitution` are the rejected rivals in that regime.

The pre-patch order trimmed everything; `model_prepatch.py` reproduces that
(assemble FIRST, then trim the whole block, so `Result() ==
trim_block((emit(lead) + included) + emit(trail), n)` and position 0 becomes
`lead.drop(n)`) and **fails** the primary postcondition (and the derived
`Result()[0] == lead`), which is exactly the spec sensing the change (G-DIFF).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The one operation that genuinely
*changed* — the position of the per-line trim relative to the leading/trailing
line insertion — is modeled **directly** by `assemble`'s control flow (trim the
included text, then prepend/append), and the two facts that make that position
observable are modeled too: the author-line presence rule (`emit`, A3) and the
trim's independence from the author filters (A5). The per-line trim function itself is
**unchanged** by the patch (`dedent_lines` is not touched); it is modeled
**deeply** as `trim_block` (step A2, an **A-reference**) and validated == the real
`dedent_lines` by G-AX, not hidden behind a consumed axiom. There is **no
consumed `@ContractOnly` axiom** in this bundle.

## C. verify(model) ⇒ resolved

`assemble` verifies only if it TERMINATES (the `MustTerminate(2)` obligation in
the precondition rules out vacuous partial-correctness proofs by divergence —
mapping.md §2.2; the real `read()` always returns its assembled text) and if, on
the WHOLE domain (`n >= 0`, any author lines including absent ones):

  * each SUPPLIED author line appears verbatim (A3, `len(lead) >= 1 ->
    Result()[0] == lead`, `len(trail) >= 1 -> Result()[len(Result())-1] ==
    trail`), and an ABSENT one contributes no line (A3's presence rule, via the
    length clause in terms of `emit`); AND
  * every included line is trimmed (A2), in BOTH author-line regimes — the
    offset-1 and offset-0 per-included-line clauses; AND
  * the trim is not contingent on an author line at all (A5, `len(lead) == 0 and
    len(trail) == 0 -> Result() == trim_block(included, n)`).

Those three together are what carry the claim beyond the F2P regime. Covering the
F2P regime alone is **not** sufficient: an implementation correct there but
skipping the trim when no author line is supplied fails the repo's dedent-only
P2P tests, so the spec has to constrain that regime as well, which is why the
domain includes it (mapping.md §2.1) and why the clauses above are stated with the
author lines' presence as a free variable rather than assumed.

By R (`List[str]` ↔ `PSeq[PSeq[int]]` content lines, `''.join` render) and I
(the concrete guarded `insert`/`append` list ops), the verified `assemble` equals the
post-fix `read()` pipeline on the tested inputs; by G-AX the deep model
`trim_block` equals the real `dedent_lines` (A-reference) and the real end-to-end
`read()` pipeline in the gold order equals `assemble`'s semantics — including the
author-line presence rule and the trim's unconditional reach, checked across all
four presence combinations (mapping.md §3.2). Therefore a model satisfying this spec, refined by the map above, is the
gold patch up to type refinement and the audited callee — and the gold patch
resolves (G-RESOLVE: F2P `test_LiteralIncludeReader_dedent_and_append_and_prepend`
plus the 41 P2P tests). The trust points are exactly the two of PLAN §1.1: axiom
soundness (here, the A-reference deep-model soundness, G-AX) and refinement
fidelity (this document, G-EQ).
