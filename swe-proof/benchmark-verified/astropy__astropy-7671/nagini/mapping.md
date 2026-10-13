# mapping.md — astropy__astropy-7671

Binds every `model.py` symbol to its repository counterpart at
`base_commit = a7141cd90019b62688d507ae056298507678c058`, states the type
abstraction, and gives the provenance of each deep-model reference (the real
library callee its deep model is validated against by axiom_check.py / G-AX).

Repo file under change: `astropy/utils/introspection.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `version_meets_minimum(have, want, inclusive)` | `minversion(module, version, inclusive=True, version_path='__version__')` — `astropy/utils/introspection.py:91` (body lines 137-145) | the modeled changed function (version-requirement check) |
| `normalize(s)` *(deep model — A-reference)* | the qualifier-stripping regex added by the patch — `re.match(r'^([1-9]\d*!)?(0\|[1-9]\d*)(\.(0\|[1-9]\d*))*', version).group(0)` at `astropy/utils/introspection.py:143-148` post-patch | pure spec: the leading dotted-numeric prefix of a requested version label |
| `loose_ge(a, b)` *(deep model — A-reference)* | `LooseVersion(have_version) >= LooseVersion(version)` — `astropy/utils/introspection.py:143` | pure spec: inclusive component-wise version order |
| `loose_gt(a, b)` *(deep model — A-reference)* | `LooseVersion(have_version) > LooseVersion(version)` — `astropy/utils/introspection.py:145` | pure spec: strict component-wise version order |
| `is_numeric(s)` | (no repo symbol) — the predicate "the version label carries no non-numeric qualifier tail" | pure spec helper / proof predicate; documents that the installed version has no qualifier tail |

The `module` / `version_path` resolution (lines 124-140: `isinstance` dispatch,
`resolve_name`, `getattr`) produces the two version strings `have_version` and
`version`. This input-acquisition prologue is UNCHANGED by the patch and is
abstracted away: the model takes the two resolved version values directly as
its `have` / `want` parameters (a faithful skeleton of the changed tail of the
function, lines 142-145, plus the inserted strip at 143-148).

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| a version string `v` (e.g. `"0.12.2"`, `"0.12dev"`) | `List[int]` of parsed release segments | the leading dotted-numeric run `re.match(EXPR, v).group(0)` splits on `.` into integer components; if a non-numeric qualifier tail remains (`prefix != v`), a single sentinel `-1` is appended to mark it. So `"0.12.2"` ↔ `[0,12,2]`, `"0.12"` ↔ `[0,12]`, `"0.12dev"` ↔ `[0,12,-1]`, `"1.2rc1"` ↔ `[1,2,-1]`, `"0.12.0.dev"` ↔ `[0,12,0,-1]`. (axiom_check.py `encode()`.) |
| a version value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list; `PSeq` `+`/`take`/`drop`/`len`/`[i]` mirror list concat/slice/len/index |
| `LooseVersion(s).version` (the parsed `.version` list distutils builds) | the numeric components of the model carrier | for a qualifier-free version, `LooseVersion("0.12.2").version == [0,12,2]`, exactly the model components; distutils compares these lists with Python list `>=`/`>` (lexicographic, longer-wins-on-equal-prefix), which `loose_ge`/`loose_gt` reproduce |
| the inclusive/strict flag `inclusive` | `bool` parameter | identical |

`str` indexing/iteration is banned in Nagini, so versions are carried as
`List[int]` of parsed components; the specification is phrased over `PSeq[int]`
via `ToSeq`.

The sentinel `-1` is sound as a marker because release segments are
non-negative integers; any negative value is reserved to denote "the start of
the non-numeric qualifier tail". The model only needs to know THAT a qualifier
tail begins (so it can strip it and so an un-stripped comparison reaching it is
undefined), not the qualifier's textual content.

## 3. Deep-model references (kind A-reference — checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**: the two operations the patch
changes are modelled DEEPLY (spelled out as pure functions), and each deep
model is validated equal to the real library callee out-of-band.

### 3.1 `normalize` ↔ the qualifier-stripping regex (A-reference)
**Callee:** `re.match(r'^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*', version)`,
added by the gold patch at `astropy/utils/introspection.py:143-148`. Regex from
PEP440 Appendix B (https://www.python.org/dev/peps/pep-0440/). It matches the
leading epoch-and-release-number run and stops at the first character that is
not part of a dotted release number — exactly the leading dotted-numeric prefix.
`normalize` (the `@Pure` front-recursive prefix-until-first-`-1`) is the
parsed-component image of that prefix:

  `re.match(EXPR, "0.12dev").group(0) == "0.12"`  ↔  `normalize([0,12,-1]) == [0,12]`
  `re.match(EXPR, "1.2rc1").group(0) == "1.2"`    ↔  `normalize([1,2,-1]) == [1,2]`
  `re.match(EXPR, "0.12.0.dev").group(0) == "0.12.0"` ↔ `normalize([0,12,0,-1]) == [0,12,0]`
  `re.match(EXPR, "0.12").group(0) == "0.12"`     ↔  `normalize([0,12]) == [0,12]`

G-AX (axiom_check.py `check_normalize_vs_independent`) runs an INDEPENDENT
leading-numeric-release oracle — distutils `LooseVersion(version).version`'s
leading run of `int` components, a completely different parser from the gold
regex — on 15 boundary labels (incl. the four F2P "good" and two "bad" versions)
plus 20 000 randomized labels and asserts it equals the deep model
`normalize(encode(version))`. (Previously the reference was re-derived from the
same `re.match`+`encode`, making the check tautological; it is now an
independent parser — D2.) Additionally `check_normalize_strips` validates
`normalize`'s marker-stripping logic DIRECTLY on hand-built carriers (markers in
interior / leading / absent positions), with no `re.match`/`encode` in the loop.
`encode` now raises `Unencodable` on epoch labels (a `!` in the matched prefix)
rather than crashing on `int('1!2')` — epochs are outside the model carrier's
plain-integer-segment domain (D3).

### 3.2 `loose_ge` / `loose_gt` ↔ `LooseVersion` comparison (A-reference)
**Callee:** `distutils.version.LooseVersion`'s `>=` / `>`
(`astropy/utils/introspection.py:143,145`). For qualifier-free versions
`LooseVersion(s).version` is the list of integer release components, and its
comparison operators are Python list `>=`/`>` — lexicographic, with a longer
list greater than a shorter one of which it is a proper extension. `loose_ge`
/ `loose_gt` reproduce exactly this on the model's component lists.

The single behavioural subtlety the issue is about: distutils' comparison
RAISES `TypeError` when a position pairs an `int` with a `str` — i.e. when one
operand still carries a non-numeric qualifier (`LooseVersion('0.12.2') >=
LooseVersion('0.12dev')` raises). The deep model represents that undefined,
never-satisfied outcome as `False` at a numeric-vs-qualifier-marker position
(`(a[0] < 0) != (b[0] < 0) -> False`). Because the specification only ever
compares against the qualifier-STRIPPED requested version
(`normalize(want)`, always numeric), this case never arises on the spec path; it
matters only for the pre-patch skeleton, which compares against the raw `want`
and so is sensed as non-satisfying — exactly the bug.

**Soundness check (G-AX):** axiom_check.py `check_order` runs the REAL
`LooseVersion` `>=`/`>` on 169 boundary numeric pairs and 20 000 randomized
numeric pairs and asserts they equal the deep models `loose_ge`/`loose_gt`. It
also confirms the headline differential directly: the stripped comparison
`LooseVersion('0.12.2') >= LooseVersion('0.12')` is `True`, while the raw
`LooseVersion('0.12.2') >= LooseVersion('0.12dev')` RAISES `TypeError`. Exit 0
iff sound. It imports only the standard library `re` and
`distutils.version.LooseVersion` — the exact callees the gold patch uses; the
real evaluation interpreter for this instance (Python 3.6) ships both, and
axiom_check.py is confirmed RC=0 IN that pinned eval container.

## 4. The contract domain on `want` (directive-7 no-raise obligation)

The real gold-patched `minversion` is PARTIAL: when the requested label does not
begin with a numeric release segment (a pure / leading qualifier `"dev"`, the
empty string, a leading-dot `".1"`, or an epoch `"1!2.3"`), the regex either
fails to match (so the raw label is fed to `LooseVersion` and the `int`-vs-`str`
comparison RAISES `TypeError`/`AttributeError`) or strips to a form with no
defined release ordering. The contract therefore restricts the requested
version to the non-raising region:

  `Requires(len(ToSeq(want)) > 0 and ToSeq(want)[0] >= 0)`

i.e. `want` begins with a numeric release segment, so `normalize(want)` is a
non-empty numeric prefix. This is exactly the domain on which the real callee
returns a defined boolean; the contract promises a total result ONLY there, so
the deep model is a sound (no-raise) over-approximation rather than over-claiming
a defined answer where the real machinery is partial. axiom_check.py's
`check_end_to_end_in_domain` (real callee never raises and equals the
end-to-end deep model across the domain) and `check_out_of_domain_is_partial`
(every excluded label raises / loses a defined order) jointly certify the domain
is exactly the non-raising region.
