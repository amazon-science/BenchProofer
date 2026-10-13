# Pinned toolchain & dependency commits

ONE workspace serves BOTH Lean-family backends. A verdict is only meaningful
relative to the prover that produced it, so these pins are part of the artifact
rather than a convenience: every bundle in both backends elaborates against the
toolchain and dependency revisions recorded here.

The workspace is pinned to the SMT-backed backend's toolchain, and the
Mathlib-only backend imports Mathlib from the same workspace rather than
resolving its own. That is a deliberate constraint, not a coincidence of
versions: the SMT-backed library does not build on later toolchains, and two
toolchains in one checkout would mean two answers to "which prover ran", which
is the one thing a released verdict may not be ambiguous about. Every dependency
below is therefore fixed at the revision that library's own manifest fixes.

| component | pin |
|---|---|
| Lean toolchain | `leanprover/lean4:v4.24.0` |
| Velvet | `2cf0acb04c510848e597aa6214b7665fea86319d` |
| Loom | `d10340821daf0ea04e05e7eec53814e0a9b248ce` |
| Mathlib | `f897ebcf72cd16f89ab4577d0c826cd14afaafc7` |
| batteries | `8da40b72fece29b7d3fe3d768bac4c8910ce9bee` |
| aesop | `725ac8cd67acd70a7beaf47c3725e23484c1ef50` |
| Qq | `dea6a3361fa36d5a13f87333dc506ada582e025c` |
| proofwidgets | `556caed0eadb7901e068131d1be208dd907d07a2` |
| importGraph | `d768126816be17600904726ca7976b185786e6b9` |
| plausible | `dfd06ebfe8d0e8fa7faba9cb5e5a2e74e7bd2805` |
| LeanSearchClient | `99657ad92e23804e279f77ea6dbdeebaa1317b98` |
| auto | `36d85bf6372f1a35fb5487325d1ef965b33c6296` |
| Cli | `91c18fa62838ad0ab7384c03c9684d99d306e1da` |
| z3 | `4.15.4` |
| cvc5 | `1.3.1` |

`lake-manifest.json` and `lean-toolchain` in this directory are the machine-
readable form of the table; this file records why the pins are what they are.
`install.sh` compares the two after every build and fails closed on any
difference, so the table has to carry a row for each of the 12 packages the
manifest resolves, transitive ones included: 9 of them are requested by *branch*
(`inputRev` is `main` or `master`), which means the manifest revision is the only
thing that fixes them. The two solver rows are not manifest packages -- a lake
target downloads those binaries -- so the comparison leaves them to the build.

The SMT solvers are downloaded into `.lake/packages/Loom/.lake/build/` by a lake
target during `lake build`. Do not install them by hand: a solver found on
`PATH` instead of in the build tree would be a different binary from the one the
recorded verdicts were produced with.
