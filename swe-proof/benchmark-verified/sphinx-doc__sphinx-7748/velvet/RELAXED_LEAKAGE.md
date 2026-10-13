# RELAXED_LEAKAGE — sphinx-doc__sphinx-7748 (velvet)

**Disposition: KEEP with relaxed leakage.**
`meta.json relaxed_leakage = true` (G-LEAK records status `"relaxed"`).

In this unified repo the relaxed-leakage policy lives in the binding
spec-construction rules, `prompts/velvet/spec_guide.md` directive 6
("**Exception — relaxed-leakage:** for a proven `problem_statement ↔ gold`
mismatch where a faithful spec MUST name the discriminator, keep the instance
with the leak allowed (`meta.json gates.G-LEAK.status = "relaxed"`)"); the
G-LEAK gate honors it mechanically (`src/swebench_unified/gates/leak.py`,
via the `relaxed_leakage` meta flag + this file).

This disposition was prescribed by the bundle's recorded P2 audit
(`verdict.md`, sub-review 3): leakage verdict **RELAXED** — "no lexical leak
(mechanical G-LEAK correctly passes), but a semantic leak of the gold's tested
discriminator that is unavoidable for a faithful spec" — with the single
recorded defect being precisely that this file and the meta flag were missing.

## The mismatch

The gold fix to `DocstringSignatureMixin._find_signature`
(`sphinx/ext/autodoc/__init__.py`) replaces the "examine only `doclines[0]`,
take the first matching signature, then `break`" scan with a per-line loop
whose discriminating clause is a **trailing backslash continuation marker**:

```python
if line.endswith('\\'):
    multiline = True
    line = line.rstrip('\\').rstrip()
else:
    multiline = False
...
if multiline:
    continue     # keep collecting subsequent signatures
else:
    break        # the matched signature is the last one
```

Two facets:

- **(a) Collecting multiple signatures — fully public.** The
  problem_statement says overloaded-method signatures are placed "at the
  start of the docstring", that `autodoc_docstring_signature` "can only pick
  up the first one", and asks "to be able to pick up all of them". This
  facet does NOT leak.
- **(b) The trailing-continuation-marker gating — gold/test_patch-only.**
  Token scan of problem_statement for `continuation` / `backslash` / `\` /
  `trailing` / `marker` / `multiline` / `blank` / `stop` = 0 hits. From the
  PS alone one would derive "collect ALL leading signature lines (until a
  blank/non-signature line)" — but the gold `break`s after the first
  matched signature UNLESS that line ends in `\`. The mechanism lives only
  in the gold diff (`line.endswith('\\')` / `multiline`) and the hidden
  test_patch, whose F2P docstring is exactly
  `B.overloaded_method(arg1)\` ␣-continuation style:
  `E(foo: int, bar: int, baz: int) -> None \` followed by
  `E(foo: str, bar: str, baz: str) -> None`. hints_text also never names
  the marker (and is excluded from the leakage baseline anyway).

The leaking element is the spec view's `LineInfo.cont` field and the
`collectSigs` docstring (abstracted — no literal repo tokens):

- `* cont — the line carries a trailing continuation marker, indicating a
  further signature follows;`
- `a signature line is collected, and collection carries on past it only
  when that line bears a trailing join marker (otherwise that signature is
  the last one)`

realized by `collectSigs`'s
`if l.cont then l.sig :: collectSigs ls else [l.sig]`.

## Why the leak is unavoidable

Faithfulness forces the continuation-marker facet into the spec:

- The gold oracle `break`s after the first matched signature unless the
  line carries the trailing `\`. A spec derivable from the PS alone —
  "collect all leading signature lines" — disagrees with the patched
  oracle on every docstring whose first signature line lacks the marker
  but is followed by further signature lines, and would fail G-CONF
  (the R/I shadow is diffed against the REAL patched `_find_signature`
  on >10^5 inputs) and admit wrong implementations (spec-too-weak).
- The prepatch (`Solution_prepatch.lean`) fails verification EXACTLY on
  the `l.cont` clause (G-DIFF) — the continuation gating IS the
  discriminating content of the change; a spec silent about it cannot
  reject the prepatch for the right reason.
- The G-EQ panel's attack set confirms tightness requires it: attack 2
  (ignore `cont`, always continue past a match) and attack 6 (invert
  `cont`) are wrong implementations that a marker-silent spec would
  admit; both are rejected only because the spec pins the `cont` gating.
- Hence faithful + non-leaking is provably impossible here; the spec
  discloses the discriminator abstractly ("trailing continuation/join
  marker" — no `endswith`, no literal backslash, no repo symbol), which
  is the minimal disclosure faithfulness demands.

This is the same faithful-must-leak shape as the dispositioned
sphinx-doc__sphinx-10466 (ascending sort of deduplicated positions) and
sphinx-doc__sphinx-9673 instances: the discriminator exists only in gold +
hidden tests, and the spec cannot be both faithful and silent about it.

## Core soundness is intact (per the recorded P2 audit + gates)

- G-VERIFY: Solution.lean verifies (4.0 s), proof closes without sorry.
- G-DIFF: `Solution_prepatch.lean` (stop after first match, ignoring
  `cont`) fails for the right reason — exactly the `l.cont` clause.
- G-EQ: SOUND / TIGHT — 7 spec-too-weak attacks (incl. the prepatch bug,
  ignore-cont, invert-cont, no-blank-stop, echo-[], drop-isSig,
  reversed order) all rejected under `same_spec=True`; a structurally
  distinct correct impl (positive control) verifies.
- G-PANEL-2 (faithfulness): FAITHFUL — spec model matches the real
  patched `_find_signature` on the exact F2P input, G-CONF 0/100,011
  (seed 7748), independent 400k adversarial differential fuzz 0
  disagreements, exhaustive class-config enumeration 0 drift.
- G-AX: rc 0 — the `LineInfo` A-reference bridge equals the real
  unchanged callees (py_ext_sig_re + str.endswith/rstrip + valid_names
  membership) on 31 boundary lines x 2 documenter configs + 40k fuzz.
- G-RESOLVE: resolved (1 attempt, not flaky). G-MUT: 19/20 killed
  (survivor is a vacuous non-terminating mutant under partial
  correctness, not a spec hole).

Only the secondary no-leakage property is relaxed, for this one documented
facet (the trailing-continuation-marker gating of multi-signature
collection). No literal repo file/symbol/diff-line token leaks (mechanical
G-LEAK screen verified 0 hard failures).
