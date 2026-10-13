# refinement.md — sphinx-doc__sphinx-11445

Operation-by-operation correspondence between `implementation_placePreamble`
(Solution.lean impl region) and `patch.diff` (the POST-PATCH `prepend_prolog`).
Tags: **R** type refinement, **A-consumed** proof uses an axiom, **A-reference**
deep model validated == real callee, **I** identical concrete op.

Post-patch Python (sphinx/util/rst.py):

```python
FIELD_NAME_RE = re.compile(Body.patterns['field_marker'])

def prepend_prolog(content: StringList, prolog: str) -> None:
    if prolog:
        pos = 0
        for line in content:
            if FIELD_NAME_RE.match(line):
                pos += 1
            else:
                break

        if pos > 0:
            content.insert(pos, '', '<generated>', 0)
            pos += 1

        lineno = 0
        for lineno, line in enumerate(prolog.splitlines()):
            content.insert(pos + lineno, line, '<rst_prolog>', lineno)

        content.insert(pos + lineno + 1, '', '<generated>', 0)
```

| # | Lean impl op | patch.diff / post-patch Python op | tag |
|---|---|---|---|
| 1 | `if preamble = [] then return body` | `if prolog:` guard (empty ⇒ no mutation) | R |
| 2 | `for line in body do if isFieldLine line.toList then pos := pos+1 else break` | `for line in content: if FIELD_NAME_RE.match(line): pos += 1 else: break` | A-reference |
| 3 | `let head := body.take pos` | lines `content[:pos]` left in place | I |
| 4 | `let tail := body.drop pos` | lines `content[pos:]` shifted after insertions | I |
| 5 | `let sep := if pos > 0 then [""] else []` | `if pos > 0: content.insert(pos, '', ...); pos += 1` (blank after header) | R |
| 6 | `head ++ sep ++ preamble ++ [""] ++ tail` | insert each `prolog.splitlines()` line at `pos+lineno`, then one blank at `pos+lineno+1` | R |

Notes:

- **The classifier (step 2) is the fix and is modeled DEEPLY**, so its
  underlying matcher is an **A-reference**, not a consumed axiom: `isFieldLine` /
  `fieldMarkerScan` is a faithful transliteration of
  `re.compile(Body.patterns['field_marker']).match`, validated byte-for-byte
  against the REAL compiled docutils regex by G-CONF (the oracle below imports
  `docutils.parsers.rst.states.Body` and compiles the actual pattern). SPEC_GUIDE
  §3 forbids axiomatizing the operation the patch changes; there is no `axiom`
  and **G-AX skips**. The `field_marker` grammar is the unchanged docutils
  primitive the post-patch code now *consults*; modeling it deeply (rather than
  axiomatizing `re.match`) is what lets the prepatch's loose classifier produce
  the actual bug.
- **Trusted boundary.** `fieldMarkerScan`/`isFieldLine` is the refinement leg's
  trusted classifier: both spec and impl consult it, so its faithfulness to the
  real `field_marker` grammar is established EMPIRICALLY by G-CONF LEG 1 (diffed
  == the REAL compiled docutils regex over the structured cases + 1e5 fuzzed
  lines), not by a Lean refinement theorem. This is the A-reference contract
  (SPEC_GUIDE §3): the classifier is the unchanged docutils primitive the patch
  newly consults, validated against the real callee rather than axiomatized.
- **R vs I.** Step 1 is **R** (Python truthiness of a `str` ⇒ `preamble = []`;
  `''.splitlines() == []`; the preamble is modeled up to `splitlines()`
  observational equivalence — a quotient, not a bijection, but lossless for this
  function which observes `prolog` only via truthiness + `splitlines()`). Step 2 is **A-reference** (the classifier). Step 5 is
  **R**: the conditional header-separator blank line. Step 6 is **R**: the
  Python code threads `StringList.insert` mutations at computed positions; under
  the line-list refinement this is exactly `preamble ++ [""]` spliced at `pos`.
  Steps 3–4 are **I**: the leading lines and the trailing body are concatenated
  verbatim.
- **Frame (directive 5).** Every output component is pinned: the leading `pos`
  lines equal `body.take pos`, the trailing lines equal `body.drop pos`, the
  preamble lines appear in order, and the blank separators are exactly placed.
  No result component is left unconstrained.
- **The bug → the prepatch.** Pre-patch the classifier was
  `docinfo_re = re.compile(':\\w+:.*?')`, which matches ANY line opening
  `:word:` regardless of trailing text — so a leading role-heading like
  `:mod:`foo`` is counted (`pos ≥ 1`) and the preamble is inserted AFTER it,
  splitting the heading from its underline. `Solution_prepatch.lean` reproduces
  exactly this loose `:word:` head-test (`looseFieldHead`) in its impl region
  (spec region byte-identical). On the F2P input
  `[":mod:`foo`", "----------", "", "hello"]` the buggy impl yields
  `[":mod:`foo`", "", <prolog…>, "", "----------", …]` whereas the spec demands
  the prolog FIRST (`pos = 0`); the carried `correct_placePreamble` therefore
  cannot close (G-DIFF). Verified concretely: a throwaway `native_decide` example
  confirms `implementation_placePreamble ≠ placePreambleSpec` on that input.
- **G-CONF** mechanically refutes the R/I/A-reference legs: a faithful in-process
  replica of the POST-PATCH `prepend_prolog` (oracle, using the REAL docutils
  `field_marker` regex) is diffed against the op-for-op shadow of
  `implementation_placePreamble` (using the transliterated `fieldMarkerScan`)
  over the structured F2P/P2P inputs + 10⁵ fuzzed (body, preamble) pairs
  (seed 11445). The classifier transliteration is additionally fuzzed against the
  real regex on ≥10⁵ random lines.
