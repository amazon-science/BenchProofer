# refinement.md — django__django-12155

Modeled function: `implementation_normalizeIndent` / `problem_spec_normalizeIndent`
/ `correct_normalizeIndent`.

The patch removes the hand-rolled docstring de-indent routine and replaces the
call with the standard-library PEP 257 docstring cleaner. The MODELED behavior is
the indentation normalization the patched code now performs. The Lean impl is a
skeleton of that normalization (the standard algorithm) operating on the
line-list carrier; the buggy pre-patch leg is the old routine's margin
computation.

Type-only refinement (mapping.md): a Python docstring `str` ↔ a `List (List Char)`
obtained as `s.expandtabs().split('\n')` (each line a `List Char`); the normalized
line-list rejoins with `'\n'`. The split/join and tab-expansion happen at the
boundary and are bridged in `conformance_check.py`.

| # | `implementation_normalizeIndent` op | patch.diff counterpart (post-patch behavior via `inspect.cleandoc`) | tag |
|---|---|---|---|
| 0 | `isSpaceChar c` (membership in `whitespaceCodes`, the 29 `str.isspace()` code points) | cleandoc's `str.lstrip()` / `not line` blank test act on the full whitespace set, not the ASCII space | A-reference |
| 1 | `for line in lines.drop 1` accumulating `margin := min leadingWs` over non-blank lines | cleandoc: `margin` = min indentation over `lines[1:]` (PEP 257; lines after the first) | A-reference |
| 2 | `isBlank line` guards the margin update (blank lines skipped) | cleandoc skips lines that are all-whitespace (`not line.lstrip()`) when computing margin | A-reference |
| 3 | `lstripWs first` — first line fully left-stripped | cleandoc: `lines[0] = lines[0].lstrip()` | A-reference |
| 4 | `line.drop m` for each following line | cleandoc: `lines[i] = lines[i][margin:]` for `i>=1` | A-reference |
| 5 | `margin = none ⇒ following lines untouched` | cleandoc: no non-blank line after first ⇒ margin stays unset, lines kept | A-reference |
| 6 | `dropTrailingEmpty out` (drop trailing `[]` lines) | cleandoc: `while lines and not lines[-1]: lines.pop()` | A-reference |
| 7 | `dropLeadingEmpty out` (drop leading `[]` lines) | cleandoc: `while lines and not lines[0]: lines.pop(0)` | A-reference |
| 8 | line/character carrier (`List (List Char)` ↔ `str.expandtabs().split('\n')`) | tab-expansion + split-into-lines at the boundary | R |

Every op is R or A-reference. There is no I-only op besides the carrier
correspondence and no A-consumed axiom: the normalization is modeled deeply and
validated == the real `inspect.cleandoc` by G-CONF (≥10⁵ fuzzed inputs).

Discriminating behavior (G-DIFF): op 1's margin domain. Post-patch (Solution.lean)
the margin is measured over `lines.drop 1`; pre-patch
(`Solution_prepatch.lean`) it is measured over all of `lines` including the
first. When the first line is flush-left (zero leading whitespace) the pre-patch
margin collapses to 0, so the indented following lines are NOT dedented — the
exact bug in the issue (`'firstline\n\n    second line'` keeps the 4-space
indent), so its `correct_normalizeIndent` cannot close against the frozen spec.
