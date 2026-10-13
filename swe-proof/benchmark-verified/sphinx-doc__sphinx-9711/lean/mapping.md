# mapping.md — sphinx-doc__sphinx-9711

## Symbol binding (base_commit 81a4fd973d4cfcb25d01a7b0be62cdb28f82406d)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_verifyExtensionVersions` | `verify_needs_extensions(app, config)` | `sphinx/extension.py:41` |
| `problem_spec_verifyExtensionVersions` | post-condition of the same function | `sphinx/extension.py:41-58` |
| `problem_pre_verifyExtensionVersions` | admissibility of the version strings (see "Admitted domain") | — |
| `parseVersion` / `verGt` | `packaging.version.Version(_)` construction + `>` (`__gt__`) | newly used by the patch (`from packaging.version import InvalidVersion, Version`) |
| `stringGt` | Python `str.__gt__` (the lexicographic fallback) | `sphinx/extension.py:54` original / patch `except InvalidVersion` branch |
| `entryUnmet` / `requirementUnmet` | the patch's `fulfilled` flag, negated | patch hunk in `verify_needs_extensions` |

## Type bijection (used by G-CONF and G-AX)

| Python | Lean | notes |
|---|---|---|
| `config.needs_extensions : Dict[str,str]` joined with `app.extensions.get(extname)` | `entries : List (String × Option String)` | each entry = `(reqversion, loadedVersion?)`. `none` ⇔ `app.extensions.get(extname) is None` (extension not loaded → warn+continue). `some v` ⇔ a loaded `Extension` whose `.version` is `v` (which may be the literal `"unknown version"`). Insertion order of the dict = list order. |
| function raises `VersionRequirementError` for extension #k (first failing) | `result = some k` | `k` = 0-based position in `entries` of the first extension whose version check fails. |
| function returns `None` (no raise) | `result = none` | every loaded extension is fulfilled. |
| `config.needs_extensions is None` (early `return`) | modeled as `entries = []` (caller passes empty list) — no behavior to pin | the `is None` guard is unchanged framing; an empty entry list yields `result = none`. |

## Callee provenance + the deep model (the fix's core)

The patch replaces the string comparison `reqversion > extension.version` with a
**semantic version** comparison `Version(reqversion) > Version(extension.version)`,
falling back to the original string comparison when either string is not a valid
version (`except InvalidVersion`).

`packaging.version.Version` is an UNCHANGED external callee that the patch newly
*uses*. Because the comparison **is** the fixed behavior, it is modeled **deeply**
(A-reference), not axiomatized (SPEC_GUIDE §3, §0.7). The model reads a version
string into an ordering key and compares keys:

- `parseVersion s` = `some key` when `s` is a readable version, `none` otherwise
  (`none` models `InvalidVersion`). Reading a version, in order:
  - a leading and trailing run of blank code points is ignored (`blankChars` is
    the same class the callee's surrounding `\s*` tolerates);
  - ASCII letter case is folded, so tag spellings are case-insensitive
    (`RC` and `rc` name the same tag);
  - an optional leading `v` is dropped (`"v1"` reads as `1`);
  - an optional `<digits>!` era marker ("epoch") is read, defaulting to `0`;
  - the release is a `.`-separated run of non-empty decimal digit groups;
  - then optional qualifier tags, each with an optional separator (`.`, `-`, `_`)
    and an optional number: a pre-qualifier (`a`/`alpha`, `b`/`beta`,
    `c`/`rc`/`pre`/`preview`), a revision tag (`post`/`rev`/`r`, or the bare
    `-N` form), and a development tag (`dev`);
  - an optional `+` build tag ("local version"): non-empty word/number segments
    separated by single separators;
  - anything left over rejects the string.
- `verGt a b` compares the keys in the order `epoch`, release, qualifier tags,
  build tag:
  - trailing zero release components are dropped, so `1`, `1.0` and `1.0.0`
    share a key;
  - release components compare numerically, and a proper prefix is smaller;
  - a version with no pre-qualifier but a development tag ranks below every
    pre-qualifier; one with neither ranks above them all; a revision tag ranks
    above no tag; the tag numbers break ties;
  - in the build tag, word segments order before numeric ones, words compare
    alphabetically and numbers numerically, and a proper prefix is smaller.
- `stringGt a b := decide (a > b)` models Python `str.__gt__`: both are
  lexicographic by Unicode code point.
- Decision per `(req, ver)` (`requirementUnmet`, = the patch's `not fulfilled`):
  - `ver == "unknown version"` → fails (raise) — unchanged behavior;
  - else if both `parseVersion req` and `parseVersion ver` are `some` → `verGt`;
  - else (either unreadable → `InvalidVersion`) → `stringGt req ver`.

### Admitted domain (`problem_pre_verifyExtensionVersions`, binding for G-AX / G-CONF)

The correctness theorem is guarded by one admissibility hypothesis: **every
version string an entry mentions is ASCII text**. Everything ASCII is admitted —
including strings that are not readable versions at all (those are ordered as raw
text) and the `"unknown version"` sentinel — so the whole decision procedure,
both the version branch and the string-fallback branch, is claimed over ASCII
input.

The restriction excludes exactly one class: a string carrying a code point
outside ASCII that a case-folding table maps onto an ASCII letter. There are four
such code points for an ASCII letter class (U+0130, U+0131, U+017F, U+212A).
Released revisions of the callee disagree about them — some scope their
case-insensitive tag matching to ASCII and refuse such a string, others accept it
and keep the non-ASCII spelling in the ordering key, where it then sorts *above*
the ASCII spelling of the same tag. The two readings give different end-to-end
verdicts on the same inputs, so no single model can be faithful to both, and the
spec deliberately claims neither. The boundary is drawn at ASCII rather than at
that four-code-point class because ASCII is the version grammar's own character
set and is stable across revisions, which makes the hypothesis checkable by
inspection of an input rather than by knowing which revision is installed.

This is a genuine narrowing of what the cell proves, and it is stated rather than
hidden: on any ASCII configuration the theorem is unconditional, and on a
configuration mentioning a non-ASCII version string the theorem says nothing.

### G-AX validation
`axiom_check.py` runs the REAL callee in the instance environment and measures
the deep model against it over ASCII inputs only, asserting that every string it
checks is ASCII (so no admitted input is skipped) and that every string in its
documented exclusion list is non-ASCII (so the exclusion cannot absorb an
admitted input). Four properties, over a boundary pool (exhaustive, and
exhaustive pairwise) plus fuzz: the accept sets coincide (`parseVersion` is
`some` exactly when the callee does not raise), the orders coincide on strings
both accept, the raw-string fallback coincides where the callee rejects, and the
composed per-entry decision `requirementUnmet` coincides with the patched block's
own decision. The excluded class is exercised too, but only as a reported
observation, never as a pass/fail.

## Flag deps
None.

## G-CONF fuzz seed
`pinned_seed = 9711`
