# mapping.md — astropy__astropy-7671

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = a7141cd90019b62688d507ae056298507678c058`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of the deep model and the consumed axiom.

Repo file under change: `astropy/utils/introspection.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `meetsRequirement (have_, version, inclusive)` | `minversion(module, version, inclusive, version_path)` — `astropy/utils/introspection.py:140` (changed body lines 143–148) | the modeled changed function; the slice modeled is the version-string → verdict computation (the `have_version`/`version` comparison). The `module`→`have_version` resolution prologue (lines 124–141) is unchanged and observationally just supplies `have_`. |
| `cleanLabel (version)` *(deep model — A-reference)* | `re.match(expr, version).group(0)` with the new `if m:` guard — the patch hunk at `introspection.py:143–148` (the four added lines) | pure spec: the orderable leading numeric portion the patch extracts before comparing. Deep model of the introduced `re.match` extractor, validated `cleanLabel == real re.match` by axiom_check.py (G-AX), NOT consumed as an axiom. |
| `labelGE` *(axiom — A-consumed, opaque)* | `LooseVersion(have_version) >= LooseVersion(version)` and the `> ` variant — `introspection.py:145,147` (UNCHANGED by the patch) | the unchanged ordering callee. Opaque axiom (no `ensures`): the weakest sufficient contract is none (directive 7). G-AX confirms it is a partial bool-or-raise operation of this signature. |

The patch ADDS `import re` (line 7) and the four-line `re.match` guard; it does
NOT touch the `LooseVersion` comparison lines. The discriminating change is
purely "reduce `version` to its leading numeric portion before comparing."

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `version : str` (the required label) and `have_version : str` (the available label) | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `len(s)` ↔ `l.length`; `s[i]` ↔ `l[i]`; `str` slice `s[:k]` ↔ `l.take k`; `s[k:]` ↔ `l.drop k`; empty `str` ↔ `[]` |
| a single character `ch` | Lean `Char` | `Char.ofNat (ord ch)` ↔ `ch`; comparisons `'0' ≤ ch ≤ '9'`, `ch = '.'`, `ch = '!'`, `ch = '0'` are exact on the BMP |
| `inclusive : bool` | Lean `Bool` | identity; `true` ↔ non-strict `>=`, `false` ↔ strict `>` |
| the comparison's result | `Except CmpErr Bool` | `ok b` ↔ the comparison returned Python `bool` `b`; `error incomparable` ↔ the comparison raised `TypeError` (`'<' not supported between instances of 'int' and 'str'`). The `Except` carrier models the callee's partiality (mapping.md §3.2). |

Lean `List Char` indexing/`take`/`drop` are total and sound; the carrier is
`List Char` because the extractor is a per-code-point left-to-right parse.

### 2.1 Modeled domain: the required label is ASCII (recorded, not hidden)

`meetsRequirement` carries the precondition `∀ c ∈ version, c.toNat < 128`.
Rationale: the real extractor is `re.match` with `\d`, and on Python 3 `str`
patterns `\d` matches ANY Unicode decimal digit (category `Nd`), e.g. the
Arabic-Indic digit `'١'` — whereas the deep model's `isDigit` is the ASCII
`'0'..'9'` test. On a required label containing a non-ASCII decimal digit
(e.g. `'1١'`) the two extractors disagree (`re.match` consumes `'1١'` whole;
the model stops after `'1'`), and the downstream `LooseVersion` verdicts then
diverge. The public version grammar (PEP440 Appendix B) is ASCII, every
F2P/PASS_TO_PASS input is ASCII, and both fuzz harnesses below draw from
ASCII alphabets, so the ASCII plane is the domain the model is contracted
over; non-ASCII required labels are OUT of the modeled domain and not claimed
(same pattern as the recorded domain restrictions in sibling bundles). This is
a domain record, not a hidden weakening: within the domain the spec still pins
the full clean-before-compare behaviour, and the prepatch twin still fails on
in-domain inputs (e.g. `'0.12dev'`).

## 3. Callee provenance

### 3.1 `cleanLabel` deep model ↔ the `re.match` extractor (A-reference)
**Callee:** `re.match(expr, version)` with
`expr = r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'` (PEP440 Appendix B), and
the patch's `if m: version = m.group(0)` guard (so a non-match leaves `version`
unchanged). The changed extraction is modeled **deeply** by `cleanLabel`
(`epochLen`/`segLen`/`digitRun`/`dottedTail`) in the `pure` region; there is **no
consumed `cleanLabel` axiom**.

Grammar of `cleanLabel`, matching the anchored regex left-to-right:
- **epoch** `([1-9]\d*!)?` — `epochLen`: a nonzero-led digit run then `!`,
  accepted only when a release segment still follows (else the optional group
  is skipped — Python's regex backtracks identically).
- **release** `(0|[1-9]\d*)` — `segLen`: a lone `0`, or a nonzero-led maximal
  digit run. Mandatory: if absent at the post-epoch position the whole match
  fails and the raw string is returned (`if r = 0 then version`).
- **dotted tail** `(\.(0|[1-9]\d*))*` — `dottedTail`: maximal run of
  `.`+segment, stopping at the first `.` not followed by a valid segment.

`group(0)` is the consumed prefix `version[: e + r + d]`.

**Soundness check (G-AX):** `axiom_check.py` runs the real `re.match` extractor
on 36 boundary inputs (incl. the F2P matrix `0.12`, `0.12.1`, `0.12.0.dev`,
`0.12dev`, `1`, `1.2rc1`, epochs, leading zeros, empties, non-matches) plus
200 000 randomized fuzz strings over `0123456789.!abrcdev-+ XY`, asserting
`cleanLabel == real re.match` on every one. Imports only stdlib `re`. Exit 0 iff
sound.

### 3.2 `labelGE` ↔ `LooseVersion` comparison (A-consumed, opaque)
**Callee:** `LooseVersion(have_version) >= LooseVersion(candidate)` (and the
strict `>` under `inclusive=False`). UNCHANGED by the patch. It is **partial**:
on a candidate whose `LooseVersion` tokenization mixes `int` and `str`
components against the available label, the element-wise list comparison raises
`TypeError` (CPython bug https://bugs.python.org/issue30272) — this is exactly
the failure the issue reports. The Lean axiom `labelGE` is **fully opaque**
(no `ensures`): the weakest sufficient contract for the proof is none, so
nothing is over-claimed (directive 7). The `Except CmpErr Bool` return carries
the bool-or-raise partiality.

**Soundness check (G-AX):** because the axiom is opaque there is no contract to
refute; `axiom_check.py` instead confirms the real callee is a well-defined
partial bool-or-raise operation of this signature over 200 000 fuzzed
`(have, candidate, inclusive)` triples (never anything but a `bool` or a raise),
and witnesses that the partiality is REAL and load-bearing: it finds candidate
labels on which the raw comparison raises but the cleaned candidate compares
cleanly (incl. the canonical F2P witness `have='0.12.2'`, `version='0.12dev'`:
raw raises `TypeError`, cleaned `'0.12'` returns `True`).

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`7671`**. The R/I shadow
it builds transliterates `cleanLabel` (the R/I leg) to Python and leaves
`labelGE`'s callee as the REAL `LooseVersion` comparison (A-tagged → run real
callee, not the opaque axiom). The oracle is the patched `minversion` driven
with a synthetic module whose `__version__` is the chosen available label.
Outcomes are compared as bool-or-raise, so the shadow must agree with the oracle
on WHICH inputs raise as well as on the verdict. ≥10⁵ inputs (the F2P matrix
first), exit 0 iff zero disagreements.
