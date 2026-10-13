# Relaxed-leakage rationale — sphinx-doc__sphinx-9602

This bundle takes the project's **relaxed-leakage** disposition for ONE facet
of its specification — the **B1 quoting** behaviour. The core is fully sound
and `verify ⟹ correct` is unaffected; only the secondary no-leakage property is
relaxed for that one facet, because faithful + non-leaking is provably
impossible for it.

**Where the policy lives.** `meta.json` records the top-level
`relaxed_leakage: true` flag, which (with this file present) makes the G-LEAK
gate record `status = "relaxed"` (`src/swebench_unified/gates/leak.py`). In
this unified repo the policy is the binding spec-construction rule,
`prompts/nagini/spec_guide.md` directive 6 ("**Exception — relaxed-leakage:**
… for a proven `problem_statement ↔ gold` mismatch where the gold's tested
discriminator exists only in `hints_text`/gold internals, so a *faithful* spec
MUST name it … KEEP the instance with the leak allowed"). (An earlier revision
of this file cited `RELAXED_LEAKAGE.md`, a source-repo-only doc that does
not exist here — see `prompts/README.md` on dangling source-repo refs.)

## The problem_statement ↔ gold mismatch

**Public `problem_statement`** (verbatim title: "Nitpick flags Literal annotation
values as missing py:class"): every example is a **boolean** Literal —
`Literal[True]`, `typing.Literal[True]`, `typing.Literal[False]`. The reported
symptom is purely the nitpick `py:class` warning: a Literal *value* is treated as
a cross-referenced class and fails `-n -W`. The expected behaviour stated is only
"`Literal[True]` … should not trigger the nitpick warning." `hints_text` is
**empty**.

**Gold patch** fixes this with three coupled hunks in
`sphinx/domains/python.py::_parse_annotation`:
1. render a constant value with its textual representation (`repr`) instead of
   the bare value;
2. wrap each text node inside a `Literal[...]` subscript so the resolver leaves
   it as plain text;
3. unwrap those nodes (plain text) and cross-reference only the remaining
   non-blank text nodes.

**Hidden `test_patch`** (`tests/test_domain_py.py::test_parse_annotation_Literal`,
the sole FAIL_TO_PASS) asserts on **`typing.Literal[0, 1, 'abc']`** that the
string value renders as **`"'abc'"`** — i.e. *with* surrounding quotes (the B1
effect of hunk 1).

## Why the B1 facet is an unavoidable leak

- The B1 discriminator — a **string** Literal value rendered WITH surrounding
  quotes — is observable only on a string argument such as `'abc'`. That string
  appears **only in the hidden F2P test**.
- The public `problem_statement` uses **only boolean** Literals (`True`/`False`),
  for which `repr(True) == str(True) == "True"`: the quoting is **invisible**. A
  solver reading only the public issue has no way to know that string values must
  be quoted; the issue is framed entirely around the missing-`py:class` warning,
  not around how a value's text is rendered.
- A **faithful** spec MUST pin the quoting: without
  `Ensures(Implies(is_str, ToSeq(Result()) == quote() + ToSeq(value) + quote()))`
  the buggy `render_literal_value` (model_prepatch_2.py, hunk 1 reverted) would
  *verify*, and a non-quoting implementation would satisfy the spec yet fail the
  F2P assertion `"'abc'"` — breaking `verify ⟹ correct`.
- But pinning the quoting necessarily reveals a behaviour (string values carry
  quotes) that is **absent from the public issue** — it lives only in the gold
  diff and the hidden test. Therefore **faithful + non-leaking is impossible for
  the B1 facet**, by the construction of the public task text vs. the gold fix.

This is not lazy de-narration: the spec view names no patched symbol, quotes no
diff line, and narrates no fix mechanism. The *behaviour itself* (string quoting)
is the leak, and it is mandatory for faithfulness.

## What does NOT relax (B2 is PS-derivable)

The **B2** facet — an enumerated Literal value stays plain text rather than
becoming a class cross-reference — IS directly derivable from the public issue
("values like `Literal[True]` end up failing because `True` is not a class …
should not trigger the nitpick warning"). The spec's `resolve_subscript`
postcondition pins exactly this, and it leaks nothing. Only the B1 quoting
sub-behaviour, invisible on the public boolean examples, takes the relaxation.

## Soundness is intact

- **G-VERIFY** pass (model.py verifies, 62s, no flags).
- **G-DIFF** fail: model_prepatch.py (B2) fails the resolve-pipeline
  postcondition; model_prepatch_2.py (B1) fails the string-quoting postcondition.
- **G-EQ** sound/tight; **G-AX** sound (both A-references validated, the
  `render_literal_value == repr` equality checked over exactly its `Requires`
  domain); **G-RESOLVE** patch.diff == gold verbatim, resolves the F2P + P2P.

`verify ⟹ correct` holds. Only no-leakage relaxes, for the B1 facet only.
