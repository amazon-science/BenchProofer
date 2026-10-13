# mapping.md — sphinx-doc__sphinx-9711

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 81a4fd973d4cfcb25d01a7b0be62cdb28f82406d`, states the type
abstraction, and gives the provenance of the deep-model reference (the version
comparator) the deep model is validated against by G-AX.

Repo file under change: `sphinx/extension.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `verify_requirement(reqversion, extversion, ext_known)` | the per-extension body of `verify_needs_extensions(app, config)` — `sphinx/extension.py:42`, decision at body line 54 | the modeled changed function: the single-extension version-requirement decision |
| `version_gt(a, b)` *(deep model — A-reference)* | `packaging.version.Version` ordering — `Version(reqversion) > Version(extension.version)`, introduced by the patch at `sphinx/extension.py:56` (post-patch); imported at module top (post-patch) | release-number ordering: the version comparison whose semantics the change fixes; deep-modelled, validated `version_gt == Version(..) > Version(..)` by axiom_check.py (G-AX), NOT a consumed axiom |
| `version_gt_from(a, b, i)`, `seg(s, i)` | helpers spelling out the segment-wise integer comparison | pure spec: the body of the release-number ordering |
| `RequirementUnfulfilled` (exception) | `sphinx.errors.VersionRequirementError`, raised at `sphinx/extension.py:55` | the out-of-band abort the guard signals when the requirement is not met |
| `reqversion: List[int]` | the dict value `reqversion` in `config.needs_extensions[extname]` (a dotted release string) | required minimum version |
| `extversion: List[int]` | `extension.version` (the loaded extension's reported version string) | loaded version |
| `ext_known: bool` | `extension.version != 'unknown version'` (`sphinx/extension.py:54`, first disjunct) | whether the loaded version is reported at all |

The pre-patch decision the change replaces (for the refinement audit, not
referenced from the consumer spec view):
`sphinx/extension.py:54`
`if extension.version == 'unknown version' or reqversion > extension.version:`
— a **textual** `>` between the two version *strings*. The patch replaces the
`reqversion > extension.version` string comparison with
`Version(reqversion) > Version(extension.version)` (release-number ordering),
keeping the `'unknown version'` guard.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a dotted release *string* (e.g. `"3.10"`) as a release **number** | `List[int]` of release segments (`[3, 10]`) | the string `s` split on `.` into integer segments `seg_k`; `Version(s).release == tuple(segments)`; segment `k` ↔ `extversion[k]` / `reqversion[k]`; `len` ↔ number of segments. The point of the fix is exactly that a segment is the *integer* (ten), not the two characters '1','0'. |
| release value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `version_gt` is phrased over `PSeq[int]`. |
| `Version(s) > Version(t)` (`packaging`) | `version_gt(ToSeq(req), ToSeq(ext))` | segment-wise integer comparison with a missing trailing segment counting as zero — equal to `packaging`'s release ordering on dotted release numbers (G-AX, §3). |
| `extension.version == 'unknown version'` | `ext_known: bool` (False when unknown) | the loaded version's presence is a boolean; its *string content* is irrelevant once known, so it is abstracted to a flag plus the segment list. |
| `raise VersionRequirementError(__(...))` | `raise RequirementUnfulfilled()` + `Exsures(RequirementUnfulfilled, …)` | a builtin/real exception type in an `Exsures` crashes the Nagini translator (SPEC_GUIDE §2), so a user-defined exception stands in; the message string is observationally irrelevant to the F2P test (it asserts only that *a* `VersionRequirementError` is raised). |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
(release segments) throughout; the specification is phrased over `PSeq[int]`.

## 3. Deep-model reference provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `version_gt` deep model ↔ `packaging.version.Version` ordering (A-reference)
**Callee:** `packaging.version.Version`. The changed comparison operation is
modelled **deeply** by the `@Pure` comparator `version_gt` (with `version_gt_from`
and `seg`) in the `pure` region; there is **no consumed `@ContractOnly` axiom**.
The deep model is validated equal to the real comparator out of band by
axiom_check.py (G-AX).

`packaging.version.Version` parses a version string and compares by its
`release` tuple (among other fields); for a plain dotted release number
(`N(.N)*`, no epoch / pre / post / dev / local) the comparison is the
left-to-right comparison of the integer release segments, a missing trailing
segment treated as zero:

```python
Version("3.10") > Version("3.9")    # True  (10 > 9)
Version("0.6")  > Version("0.10")   # False (6 < 10)
Version("3")    > Version("3.0")    # False (3.0.0… == 3)
```

which is exactly what `version_gt` / `version_gt_from` / `seg` encode
(segment-wise integer compare, zero-pad the shorter). G-AX asserts
`version_gt(a, b) == (Version(va) > Version(vb))` on 19 boundary inputs (the
issue's `0.6`/`0.10`, the F2P test's `3.9`/`3.10`/`3.11`, equal, prefix /
zero-pad, the bare `10 vs 9` inversion the issue describes) plus 200 000
randomized fuzz pairs over 1..4 segments / values 0..99. Zero mismatches.
Docs: https://packaging.pypa.io/en/stable/version.html.

**Modelled domain & the gold's fallback.** The gold patch wraps the comparison
in `try: … except InvalidVersion: <textual fallback>`. The modelled domain is
*valid dotted release numbers* — precisely the inputs the requirement check
compares for the tested behaviour (F2P uses `3.9`/`3.10`/`3.11`; the issue uses
`0.6`/`0.10`; real extension versions are PEP 440 release numbers). For such
inputs `Version()` never raises `InvalidVersion`, so the modelled release-number
ordering path IS the executed path and the `except InvalidVersion` text fallback
is never taken. The fallback exists only to preserve the *old* string behaviour
for genuinely-unparseable version strings (a degenerate compatibility tail
outside the tested behaviour and outside the issue); it is not part of the
modeled, fixed behaviour. axiom_check.py confirms every tested input stays in
the valid-release domain.
