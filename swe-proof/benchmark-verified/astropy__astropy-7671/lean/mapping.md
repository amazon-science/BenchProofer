# mapping.md — astropy__astropy-7671

## Modeled function

| Lean | Python | file:line @ base_commit |
|---|---|---|
| `implementation_versionAtLeast` / `problem_spec_versionAtLeast` / `correct_versionAtLeast` | `minversion(module, version, inclusive, version_path)` — version-comparison return | `astropy/utils/introspection.py:91-145` (changed region: the `version` normalization inserted at hunk `@@ -139,6 +140,14 @@`, plus the `inclusive` comparison at lines 142-145) |

The gold patch adds, just before the comparison:

```python
expr = '^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'
m = re.match(expr, version)
if m:
    version = m.group(0)
```

i.e. the required-version string is reduced to its leading release-number prefix
before the comparison. The comparison itself (`LooseVersion(have) >= / >
LooseVersion(version)`) is UNCHANGED by the patch.

## Type bijection (Lean ↔ Python) — used by G-CONF and G-AX

| Lean | Python | note |
|---|---|---|
| `haveVersion : List Char` | `have_version : str` (resolved module `__version__`) | the available version string; produced by unchanged module-resolution code (framed as input) |
| `version : List Char` | `version : str` | the required-minimum version argument — the only value the patch transforms |
| `inclusive : Bool` | `inclusive : bool` | `True` ⇒ `>=`, `False` ⇒ `>` |
| `result : Option Bool` | return value `bool`, or the call RAISING | `none` <-> `LooseVersion.__ge__/__gt__` raises `TypeError`; `some b` <-> it returns `b`. The ordering is genuinely partial (bpo-30272), so the result carrier is `Option`; see "Partiality" below |
| `releasePrefix version : Option (List Char)` | `re.match(expr, version)` then `.group(0)` (`None` ⇒ no match) | deep model of the inline regex; **A-reference**, validated by G-CONF |
| `normalizeVersion version : List Char` | `version = m.group(0) if m else version` | the value fed to the comparison |
| `orderable a b : Bool` | whether `LooseVersion(a) >= LooseVersion(b)` COMPLETES (`True`) or raises `TypeError` (`False`) | the ordering's DOMAIN, as a total question: a Python probe of the pair that returns a verdict rather than propagating the exception. Opaque; no consumed `_prop`; **A-reference**, exercised end-to-end by G-CONF (both directions of the raise/value bridge) |
| `versionGe a b (h : orderable a b = true) : Bool` | `LooseVersion(a) >= LooseVersion(b)`, applied only where it completes | UNCHANGED callee, carried as an operation ON ITS DOMAIN: the evidence argument `h` is the fact that this pair is one the comparison answers at, so the application is inexpressible without it. Opaque signature, no consumed `_prop`; **A-reference** (left as the real callee in G-CONF) |
| `versionGt a b (h : orderable a b = true) : Bool` | `LooseVersion(a) > LooseVersion(b)`, applied only where it completes | UNCHANGED strict callee, same domain carrier; opaque signature; **A-reference** |

## Partiality of the comparison callee (why the ordering is carried on its domain)

`LooseVersion.__ge__` / `__gt__` are PARTIAL. On a pair whose release numbers run
out against a residual non-numeric qualifier they raise `TypeError` rather than
returning a verdict — bpo-30272, which is the defect the issue report exhibits:

| pair | result |
|---|---|
| `LooseVersion('0.12.2') >= LooseVersion('0.12dev')` | RAISES `TypeError` |
| `LooseVersion('0.12.2') >= LooseVersion('0.12')` | `True` |
| `LooseVersion('0.12') >= LooseVersion('0.12dev')` | `False` (no raise — the `.3`-style extra component is what triggers it) |

Modeling this as a total `Bool` was a real defect, and an audit found the
counterexample it admits: an implementation may apply the comparison to the
UN-REDUCED required string, discard the answer through a construct Lean proves
irrelevant, and still satisfy a value-only postcondition — while the real code
evaluates that call and raises. Over `Bool` such an implementation is
EXTENSIONALLY EQUAL to the gold one (provable by `funext`), so no value-level
clause could separate them; the fix has to be in the carrier, not in an extra
value clause.

Making the ordering total-but-`Option Bool`-valued does not fix that. It reports
where the comparison has no verdict, but it still lets an implementation APPLY
the comparison anywhere and then drop the `none` on the floor — the discarded
application remains a pure subterm, and `funext` still equates the two functions.
A later audit found exactly that evasion (the discarded call folded in as
`xor raw raw`).

What the bundle carries instead is the ordering as WHAT A PARTIAL OPERATION IS: an
operation on its DOMAIN. `orderable a b` is the total question of whether the pair
is one the comparison answers at — in Python, a probe that returns a verdict
instead of propagating the exception — and `versionGe` / `versionGt` take the
answer to that question as an argument. There is then no term at all naming the
comparison's value at a pair whose commensurability has not been settled first, so
"the call happened on the raw string" is not something an implementation can do
invisibly: it must first ask a question that always completes, and a decision that
hangs on THAT answer is a different function (rejected by the battery's
`weak-definedness-leak`), while asking it and discarding the result is
behavior-preserving and admitted (`pos-guarded-raw-probe`). The result carrier
stays `Option Bool`, and its `none` <-> raises bridge is validated in both
directions by G-CONF (a raise on one leg and a value on the other is a
disagreement), which is what makes the spec's definedness clause an observed
property of the real callee rather than an assumption about it.

## Callee provenance + flag deps

- `versionGe` / `versionGt` bind to `distutils.version.LooseVersion`'s `>=` / `>`
  (stdlib, unchanged by the patch), and `orderable` binds to whether that same
  comparison completes on the pair. Opaque signatures only — the proof consumes
  NO property of them (they appear identically in spec and impl and cancel), so
  there is no `_prop` axiom; in particular NOTHING constrains where `orderable`
  is `true`, so the domain carrier is a signature choice and not an assumption
  about the callee. They are A-reference rows (G-CONF leaves them as the real
  callee).
- The regex (`releasePrefix`) is modeled DEEPLY (a total recursive scanner), not
  axiomatized. It is the changed op ⇒ A-reference, validated by G-CONF against the
  real inline-regex behavior of the patched `minversion`.
- Flag dependency: `inclusive` selects `>=` vs `>`; G-CONF fuzzes both values.
- Module-argument dispatch / `resolve_name` / `getattr` are UNCHANGED and not part
  of the fixed behavior (the F2P test passes a real `ModuleType`); they are framed
  as the production of `have_version` (a string input). Not modeled.

## Regex semantics (the discriminator) — verified against Python `re`

`^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*` matched with `re.match`:
- optional **epoch** `[1-9]\d*!` (used only if followed by a release digit; the
  alternative `0!…` does NOT match the epoch — leading `0` is excluded);
- mandatory **release number** `(0|[1-9]\d*)` (a single `0`, or a non-zero-leading
  digit run);
- zero or more `.`-separated release numbers.
Match is anchored at start; if the string does not begin with a release-number
start there is no match and `version` is left unchanged. `m.group(0)` is the
longest such prefix under `re`'s left-to-right greedy+backtrack rule (the only
backtrack point is the optional epoch).

**The character classes are NOT uniform, and the model must not treat them as
such.** For a `str` pattern `re` applies the default `UNICODE` flag, so `\d`
matches any character of the Unicode decimal-number category `Nd` (Arabic-Indic
`٠`-`٩`, Devanagari, fullwidth `０`-`９`, astral digits, …), while the classes
written as the literals `0` and `[1-9]` are plain ASCII characters and are NOT
Unicode-aware. Consequences, each observed against the real patched `minversion`
in the instance image (Python 3.6.13, `unidata_version` 9.0.0):

| required `version` | `m.group(0)` | why |
|---|---|---|
| `1٥5` | `1٥5` (whole string kept) | `\d*` matches U+0665, so the release number extends over it |
| `٥1` | *no match* | the leading class is ASCII `0`/`[1-9]`; U+0665 cannot START a release number |
| `1!٥` | `1` | the epoch is abandoned — the char after `!` must be an ASCII release-number start |
| `1٥!5` | `1٥!5` | epoch body is `\d*` (Unicode), and `5` after `!` is ASCII ⇒ epoch taken |
| `1²5` | `1` | U+00B2 is numeric but category `No`, not `Nd` ⇒ `\d` rejects it |

So `Nd` is exactly `\d` (checked exhaustively over all 0x110000 code points in
the image: 580 characters, both sets equal), and `str.isdigit()` is the WRONG
proxy — it is wider than `\d` (708 characters; it accepts the superscripts).
The Lean model therefore gates the *continuation* of a release number on
`isDecimalDigit` (an explicit `Nd` code-point range table, 54 ranges) and the
*leading* character on ASCII `c.isDigit`/`= '0'`. `releasePrefix` reproduces
`re.match` on this whole boundary; the G-CONF fuzz alphabet now includes
non-ASCII `Nd` digits from several scripts and planes plus numeric-but-not-`Nd`
characters, so the region that exposes the asymmetry is actually exercised.

## G-CONF fuzz seed

`SEED = 20240627` (pinned in `conformance_check.py` and `meta.json`).
