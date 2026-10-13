# RELAXED-LEAKAGE ACCEPTANCE: matplotlib__matplotlib-21568

**Disposition: ACCEPTED under the relaxed-leakage policy (project decision
2026-06-14).** `meta.json` records the top-level `relaxed_leakage: true` flag,
which (with this file present) makes the G-LEAK gate record
`status = "relaxed"` (`src/swebench_unified/gates/leak.py`). In this unified
repo the policy lives in the binding spec-construction rules,
`prompts/nagini/spec_guide.md` directive 6 ("**Exception — relaxed-leakage:**
... for a proven `problem_statement <-> gold` mismatch where the gold's tested
discriminator exists only in `hints_text`/gold internals, so a *faithful* spec
MUST name it ... KEEP the instance with the leak allowed"). (The
`RELAXED_LEAKAGE.md` cited by an earlier revision of this file was a
source-repo-only doc that does not exist here — see `prompts/README.md` on
dangling source-repo refs.)

## Why the leak is genuinely unavoidable (not lazy de-narration)

The behavior the gold actually fixes — and that the F2P test measures — IS the
leaked discriminator. There is no way to pin it without naming it.

### The gold protects three specific code points

Gold patch (`lib/matplotlib/dates.py`, `_wrap_in_tex`):

```python
def _wrap_in_tex(text):
    p = r'\\.\\d'
    ...
    # The general approach to escaping special characters in mathmode does not
    # work in TeX.
    text = ret_text.replace('-', '{-}').replace(':', '{:}').replace(' ', r'\;')
    return '$\\mathdefault{' + text + '}$'
```

The discriminator is exactly the per-code-point substitution
`-` -> `{-}`, `:` -> `{:}`, `' '` -> `\;`. The prepatch protected only `-`; the
colon and the space passed through unchanged, producing the wrong (run-together)
math-mode spacing the issue reports.

### That discriminator is absent from the solver-visible problem_statement

Token check against `problem_statement` (solver-visible) vs. `hints_text` /
`test_patch` (never shown to the consumer):

| token / concept              | problem_statement | hints_text | test_patch |
|------------------------------|:-----------------:|:----------:|:----------:|
| `_wrap_in_tex`               | absent            | present    | absent     |
| `mathdefault`                | absent            | present    | present    |
| `{-}` / `{:}` / `\;`         | absent            | present    | present    |
| `.replace`                   | absent            | present    | absent     |
| `dates.py`                   | absent            | absent     | present    |
| "spaced binary operator(s)"  | absent            | absent     | absent     |
| `usetex` / "spacing"         | present           | present    | present    |

The `problem_statement` says only that "the spacing for a datetime axis when
using `usetex=True` is unclear" and asks to "have the spacing from version 3.3
in a tex format." It names none of the three characters, none of the brace/space
tokens, not the patched symbol `_wrap_in_tex`, not `mathdefault`, and not the
`.replace`-chain mechanism. The entire fix vocabulary (the monkey-patch with the
exact `.replace('-','{-}').replace(':',r'{:}').replace(' ',r'\;')` chain and the
`_wrap_in_tex` symbol) appears ONLY in `hints_text`; the patched file path and
the `{-}`/`{:}`/`\;` tokens appear ONLY in `hints_text` and the hidden
`test_patch`.

### Any faithful, G-DIFF-failing spec must name it

To satisfy G-EQ / faithfulness, `model.py` must pin the gold's actually-tested
behavior: the result is the per-code-point protection with `-` -> `{-}`,
`:` -> `{:}`, `' '` -> `\;`. The F2P discriminator is precisely the colon and the
space cases (the prepatch already had `-`); a spec tight enough to FAIL G-DIFF on
the prepatch (`model_prepatch.py`, which reverts to `-`-only) and to pin the F2P
output MUST state the colon and space tokens. There is no
`problem_statement`-derivable ("usetex"/"spacing") reformulation that models the
gold fix, because the public issue is about an unclear-spacing symptom while the
gold is about three specific character substitutions — different vocabularies.
The behavior itself is the leak. This is a genuine PS<->gold mismatch, not lazy
docstring narration.

Note: the spec view correctly still avoids the patched path/symbol names
(`_wrap_in_tex`, `dates.py`, `mathdefault`) — model identifiers
(`protect_codepoints`, `protected_seq`, `tok_dash`/`tok_colon`/`tok_space`)
describe behavior, not the edit. Only the unavoidable token/mechanism vocabulary
(`{-}`, `{:}`, `\;`, the per-code-point substitution) is present, and that is the
tested behavior.

## Re-verify snapshot (soundness intact — this is a relaxed-leak, not a defect-in-spec)

- G-VERIFY: PASS — `model.py` verifies, no flags, <300s.
- G-DIFF: PASS — `model_prepatch.py` FAILS on the postcondition
  `ToSeq(Result()) == protected_seq(ToSeq(text))` (loop invariant, line 109): the
  `-`-only prepatch cannot discharge the colon/space protection. same_spec=True.
- same_spec: TRUE — spec regions (axioms/pure/pre/post/invariants) byte-identical
  between `model.py` and `model_prepatch.py`; only `impl` differs.
- Static gates (G-INTEGRITY / G-HYGIENE / G-LEAK-mechanical): pass.
- G-AX: A-reference mode (zero consumed `@ContractOnly` axioms; the changed
  protection is modeled deeply as `protected_seq`). `axiom_check.py` validates the
  deep model == real gold `_wrap_in_tex` protection over boundary + fuzz inputs,
  RC=0.

The mechanical G-LEAK screen passes (no diff lines/patched-path/patched-symbol
narration), but it is lexical and blind to this semantic token/mechanism leak;
the adversarial reconstruction test (G-PANEL attacker 3) independently
re-verifies the disposition. Per the panel recording convention above, its
honest recording for this properly-dispositioned facet is NO-LEAKAGE (pass) +
note; LEAKAGE is reserved for a NEW leak beyond the facet or a broken
disposition.

## Conclusion

No prescribed code fix exists for the leakage axis. Per the relaxed-leakage policy
the correct action is to KEEP this instance in the verified set with the leak
documented: `meta.json` carries the top-level `relaxed_leakage: true` flag (so
the G-LEAK gate records status `"relaxed"`), with this file as the recorded
rationale. The `verify => correct` guarantee is fully intact.
