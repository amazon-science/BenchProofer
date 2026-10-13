# refinement.md — astropy__astropy-7671

Operation correspondence between `implementation_versionAtLeast` and the gold
`patch.diff`. Tags: **R** (type refinement), **A-consumed** (proof uses an
axiom's property), **A-reference** (deep model validated == real callee by
G-AX/G-CONF), **I** (identical concrete op).

No axioms are consumed. The CHANGED operation (reducing the required-version
string to its leading release-number prefix) is modeled DEEPLY as the total
recursive scanner `releasePrefix` / `normalizeVersion` — an **A-reference**,
differential-tested by G-CONF, not axiomatized. The opaque comparison callees
(`versionGe` / `versionGt`, and `orderable`, the total question of whether the
comparison completes on a pair) carry NO consumed property: they occur identically
in the spec and the impl and so cancel in the proof, and nothing constrains where
`orderable` holds; they are A-reference rows (left as the real `LooseVersion`
comparison in the end-to-end G-CONF differential). Every row below is R,
A-reference, or I.

## The gold patch

Inserts, immediately before the comparison:

```python
expr = '^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'
m = re.match(expr, version)
if m:
    version = m.group(0)
```

leaving the subsequent `LooseVersion(have_version) >= / > LooseVersion(version)`
comparison UNCHANGED. The pre-patch code performed the comparison on the
un-reduced `version`, which raised `TypeError` for strings like `1.14dev`.

## `implementation_versionAtLeast` ↔ patched `minversion`

| Lean op | patch.diff / source counterpart | tag | note |
|---|---|---|---|
| `let mut ver := version` | local rebinding of `version` | I | the value to be (maybe) reduced |
| `if let some p := releasePrefix ver then ver := p` | `m = re.match(expr, version); if m: version = m.group(0)` | A-reference | the EDITED op: reduce to the leading release-number prefix; modeled deeply by `releasePrefix` (optional epoch `[1-9]\d*!`, mandatory release number `(0\|[1-9]\d*)`, dotted release numbers), `none` ⇒ leave unchanged. The digit classes are modeled NON-uniformly, matching `re`: a release number's continuation (`\d*`) is any Unicode `Nd` character (`isDecimalDigit`, an explicit code-point range table), while its leading character (the `0`/`[1-9]` literals) is ASCII-only — see mapping.md's table. Validated == the real inline regex (`m.group(0)`/no-match) by G-CONF (50k regex cross-check + end-to-end) over an alphabet that includes non-ASCII `Nd` digits and numeric-but-not-`Nd` characters |
| `if h : orderable haveVersion ver = true then ... else return none` | the comparison either completes on the pair or raises `TypeError` (bpo-30272), which propagates out of `minversion` | A-reference | the ordering's DOMAIN, asked as a total question before the ordering is applied: `orderable` ↦ whether `LooseVersion(have_version) >= LooseVersion(version)` completes. In Python this is not an extra statement but the fact that the comparison either returns or raises; the `else` leg is the raise. No consumed property — nothing in the proof constrains where `orderable` holds |
| `return some (versionGe haveVersion ver h)` | `if inclusive: return LooseVersion(have_version) >= LooseVersion(version)` | A-reference | unchanged comparison; `versionGe` ↦ `LooseVersion.__ge__`, carried as an operation on its domain (the evidence `h` is the fact that this pair is one it answers at, so the application cannot be written without it); no consumed property (identical in spec+impl) |
| `return some (versionGt haveVersion ver h)` | `else: return LooseVersion(have_version) > LooseVersion(version)` | A-reference | unchanged strict comparison; `versionGt` ↦ `LooseVersion.__gt__`, same domain carrier |

### Type refinement (R) underlying the above
- `version : List Char` ↔ Python `str` (per-character regex scan ⇒ `List Char`,
  Lean indexing total/sound). `haveVersion : List Char` ↔ resolved
  `module.__version__ : str` (produced by unchanged module-resolution code —
  framed as an input string; not part of the fixed behavior).
- `inclusive : Bool` ↔ Python `bool`; `result : Option Bool` ↔ the `bool` return
  when the comparison yields one, and `none` when it RAISES. The comparison callee
  is partial (bpo-30272), so it is carried as an operation on its DOMAIN —
  `versionGe/Gt a b (h : orderable a b = true) : Bool`, with `orderable` the total
  question of whether the comparison completes — and the RESULT carrier is
  `Option Bool` because that partiality reaches `minversion`'s own return. See the
  partiality section of mapping.md.
- `releasePrefix`'s `Option` result ↔ the regex match/no-match (`m` truthy vs
  `None`); `m.group(0)` ↔ the consumed-prefix `List Char`.

## Spec adequacy (verify ⟹ correct)
`problem_spec_versionAtLeast` pins the result to the comparison of `haveVersion`
against `normalizeVersion version` — i.e. it forces the prefix reduction to have
happened. The pre-patch impl compares against the RAW `version`; on a required
string with a trailing qualifier (`0.12dev`, the new F2P case) `normalizeVersion
version ≠ version`, so the prepatch's result equals
`versionGe/Gt haveVersion version`, which the spec does not permit unless it
happens to coincide — and the discriminating F2P inputs (`'0.12dev'` reduces to
`'0.12'`) make the two differ in observable behavior.

WHERE the behavior answers is pinned too, and that is a second, independent
obligation rather than a restatement of the first. The spec's conditional is on the
REDUCED pair: the result carries a verdict exactly when the ordering answers there,
and none exactly when it does not. So an implementation whose verdict's EXISTENCE
depends on the ordering at the UN-reduced pair does not satisfy the spec — at the
F2P's own inputs (`0.12.2` against `0.12dev`) the raw pair is one the comparison
raises on while the reduced pair `0.12.2` / `0.12` is one it answers, so such an
implementation returns no verdict where the specified behavior returns one. What
the spec does NOT do is forbid touching the raw pair at all: an implementation may
settle whether the raw pair is commensurable (a question that always completes)
and discard the answer, and that one still verifies. Both halves are shipped as
battery cases — `weak-definedness-leak` must be rejected, `pos-guarded-raw-probe`
must verify — so the clause is held between them rather than over-fitted to the
gold control flow.

That is load-bearing and was ADDED to close a measured hole, twice. An early
revision of this bundle carried the comparison as a total `Bool`, and an audit
found two same-spec implementations that verified while their faithful patches did
not resolve: each evaluated the comparison on the raw required string and then
discarded the answer (behind a tautological guard; folded in as `xor raw raw`).
Over a total `Bool` carrier those implementations are EXTENSIONALLY EQUAL to the
gold one — `funext` proves the functions equal, measured — so the hole could not be
closed by any additional value-level clause; the discarded call is invisible in the
value. Making the ordering total-but-`Option Bool`-valued did not close it either:
that reports where the comparison has no verdict, but it still lets an
implementation apply the comparison anywhere and drop the resulting `none`, and the
discarded application stays a pure subterm the value cannot see — measured, the
same evasion verifies. The repair is to carry the raising operator as an operation
on its DOMAIN, so that its application at a pair is not even expressible until the
pair's commensurability has been settled by a question that has an answer wherever
it is asked. The unchanged comparison callees are still framed identically in the
spec and the impl, so the behavioral degrees of freedom the spec leaves are exactly
the reduction the fix introduces AND the definedness that reduction exists to
protect.
