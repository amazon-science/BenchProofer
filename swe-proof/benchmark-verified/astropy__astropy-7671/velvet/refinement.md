# refinement.md — astropy__astropy-7671

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`meetsRequirement` `do` block, the deep `cleanLabel` model, and the opaque
`labelGE` axiom) and `patch.diff` (the gold patch). Each step is tagged **R**
(type refinement), **A** (axiomatized callee — **A-consumed** where the proof
uses the axiom, **A-reference** where a deep model is validated == the real
callee by G-AX), or **I** (identical concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The version-comparison site — `minversion()` (`introspection.py:140`)

Gold hunk (the four added lines + the unchanged comparison they precede):
```
+    expr = '^([1-9]\d*!)?(0|[1-9]\d*)(\.(0|[1-9]\d*))*'
+    m = re.match(expr, version)
+    if m:
+        version = m.group(0)
     if inclusive:
         return LooseVersion(have_version) >= LooseVersion(version)
     else:
         return LooseVersion(have_version) > LooseVersion(version)
```

| # | Solution.lean impl op (`meetsRequirement`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `version : List Char` | `version: str` arg of `minversion` | R | `str` ↔ `List Char` (mapping.md §2). G-CONF bridges via `ch ↔ Char.ofNat (ord ch)`. |
| A2 | parameter `have_ : List Char` | `have_version` (resolved from `module` by the UNCHANGED prologue, lines 124–141) | R | `str` ↔ `List Char`. The prologue is unchanged and only supplies `have_version`; not modeled, reached identically on every branch. |
| A3 | parameter `inclusive : Bool` | `inclusive: bool` arg | R/I | `Bool` ↔ `bool`, identity; selects `>=` vs `>`. |
| A4 | `cleaned := cleanLabel version`: the orderable leading portion (epoch?, leading numeric segment, dotted numeric tail), computed by `epochLen`/`segLen`/`digitRun`/`dottedTail`; raw string when no leading segment | `expr=…; m=re.match(expr, version); if m: version=m.group(0)` | A-reference + I | the changed extraction op is modeled **deeply**: `cleanLabel` (pure region) IS the PEP440 leading-portion parse. The parsing ops (`take`/`drop`/digit tests, the `if r=0 then version` non-match fallback = the `if m:` guard) are **I** (concrete, transliterated by G-CONF); the equality of that deep model to the real `re.match` extractor is the **A-reference** G-AX validates. mapping.md §3.1. |
| A5 | `result := labelGE have_ cleaned inclusive`; `return result` | `return LooseVersion(have_version) >= / > LooseVersion(version)` (version now = the cleaned prefix) | A-consumed | `labelGE` is the unchanged ordering callee, modeled by an OPAQUE axiom (weakest contract = none, directive 7). The proof consumes it definitionally: the postcondition `out = labelGE have_ (cleanLabel version) inclusive` holds by `rfl` after the impl binds `cleaned = cleanLabel version`. G-AX confirms the real callee is bool-or-raise (mapping.md §3.2). |

**Modeled domain (precondition):** `meetsRequirement` requires the required
label to be ASCII (`∀ c ∈ version, c.toNat < 128`; mapping.md §2.1). Python's
`\d` in the real extractor is Unicode-aware while the deep model's `isDigit` is
the ASCII `'0'..'9'` test, so on a non-ASCII decimal digit (e.g. `'1١'`) the
two disagree; the ASCII plane — which contains the full public version grammar
and every graded input — is the domain the correspondence below is claimed
over. Both fuzz harnesses (G-AX, G-CONF) already draw from ASCII alphabets.

**Termination (total-correctness) claim:** the spec is verified under
`loom.semantics.termination "total"` (`TotalCorrectness`), so a verifying impl
must both terminate and return the pinned verdict. This matches the real
patched `minversion`: it is straight-line code (resolve `have_version`, one
`re.match`, one `LooseVersion` comparison) with no loop or recursion, so it
terminates on every input; it either returns a `bool` or raises (the `Except`
carrier). Partial-correctness semantics would unfaithfully admit divergent
impls (e.g. an infinite loop before a vacuous `return`), which do NOT resolve
the real instance — the SWE-bench harness times such a patch out and marks it
unresolved.

Discriminating content of the change — the required label is reduced to its
orderable leading portion BEFORE the comparison — lives in
`cleanLabel version` (model) ⇔ `re.match(expr, version).group(0)` (real).
The pre-patch code passed the **raw** `version` to the comparison;
`Solution_prepatch.lean` reproduces that (`labelGE have_ version inclusive`) and
**fails** `out = labelGE have_ (cleanLabel version) inclusive` whenever
`cleanLabel version ≠ version` (G-DIFF). On the F2P-added input `'0.12dev'`
(`have='0.12.2'`), the raw comparison raises `TypeError` (the reported bug)
while the cleaned `'0.12'` returns `True` — the exact behaviour the new test
asserts.

## B. No second site
The patch changes a single function (`minversion`). The added `import re` (line
7) is module-level plumbing with no observable behaviour of its own; it is the
mechanism by which A4's `re.match` becomes available, already covered by A4.

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R, A, or I. The one operation that genuinely *changed* — the
leading-portion extraction inserted before the comparison — is modeled **deeply**
(the spelled-out parser `cleanLabel`, step A4, an A-reference + I), not hidden
behind an axiom about the function under change. The only consumed axiom,
`labelGE` (step A5), is **opaque** and covers an **unchanged** callee
(`LooseVersion` ordering); it pins no behaviour, so it cannot make a wrong impl
verify.

## D. verify(Solution) ⇒ resolved

`meetsRequirement` verifies only if its output equals
`labelGE have_ (cleanLabel version) inclusive` (A4 + A5): the verdict the
unchanged ordering callee returns for the available label against the **cleaned**
required label. By R (`str ↔ List Char`, `bool` identity) and the unchanged
`module`→`have_version` prologue, the verified function equals the patched
`minversion` on the tested `str` inputs; by G-AX the deep model `cleanLabel`
equals the real `re.match` extractor (A-reference) and the real `LooseVersion`
ordering is the bool-or-raise callee `labelGE` models (A-consumed); by G-CONF
the R/I transliteration of `cleanLabel` composed with the real ordering agrees
with `patch.diff`'s behaviour (verdict AND raise-set) on ≥10⁵ inputs. Therefore
a model satisfying this spec, refined by the map above, is the gold patch up to
type refinement and the audited callee — and the gold patch resolves
(G-RESOLVE). Trust points are exactly the two of plan §1.1: axiom soundness
(G-AX) and refinement fidelity (this doc, G-EQ + G-CONF).
