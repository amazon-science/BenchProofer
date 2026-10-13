# refinement.md — django__django-16116

The operation-by-operation correspondence between `Solution.lean`'s
implementation (the `runCheckedWrite` impl region) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A-reference** (a runtime
property validated == the real callee by `axiom_check.py` / G-AX; there is **no
consumed axiom**), or **I** (identical concrete operation). The claim: *any
implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (byte-identical; it applies at
`base_commit` and is the real correctness oracle, G-RESOLVE).

## A. The decision site — `Command.handle`, the non-empty-`changes` branch (`makemigrations.py:251-257`)

Gold hunk (the re-ordering):
```
         else:
+            if check_changes:
+                sys.exit(1)
             if self.update:
                 self.write_to_last_migration_files(changes)
             else:
                 self.write_migration_files(changes)
-            if check_changes:
-                sys.exit(1)
```

The change moves the `if check_changes: sys.exit(1)` guard from **after** the
write block to **before** it. Post-patch a check-only run aborts before any
write runs (no artifact emitted); pre-patch it writes the artifact first, then
aborts.

| # | Solution.lean impl op (`runCheckedWrite`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | param `checkOnly : Bool` | `check_changes` (the `--check` option, `makemigrations.py:69-76`/`handle`) | R | a Python `bool` ↔ Lean `Bool` (mapping.md §2). |
| A2 | param `update : Bool` | `self.update` (the `--update` option) | R | a Python `bool` ↔ Lean `Bool` (mapping.md §2). |
| A3 | `if checkOnly then return { written := noWrite, exited := true }` | the gold's relocated `if check_changes: sys.exit(1)` placed *before* the write block | A-reference | `sys.exit(1)` raises `SystemExit` and **unwinds the stack**, so the write statements sequenced after it do not run — hence *no artifact is emitted* (`written = noWrite`) and the process aborts (`exited = true`). The raise-and-unwind property is validated against the real `sys.exit` by `axiom_check.py` (G-AX); see mapping.md §3. The early `return` in the model IS the control-flow effect of that unwind. |
| A4 | `else` branch: `let wk := if update then latest else standard; return { written := wk, exited := false }` | `if self.update: self.write_to_last_migration_files(changes) else: self.write_migration_files(changes)` (reached only when not check-only, and no abort) | I (under R) | identical two-way branch on `update`: fold into the latest migration vs emit a fresh one; the artifact-kind observable `latest`/`standard` ↔ the two write methods (mapping.md §2). No abort on this path (`exited = false`). |

The discriminating content of the change lives in **A3**: post-patch the abort
is sequenced *before* the writes, so in check-only mode the unwind prevents any
write — `written = noWrite`. `Solution_prepatch.lean` reproduces the pre-patch
order (emit `wk` first, then set `exited := checkOnly`) and **fails** the
postcondition `checkOnly = true → out.written = WriteKind.noWrite` (and the
`out = stepOutcome checkOnly update` equality) — exactly the spec sensing the
re-ordering (G-DIFF, confirmed: unsolved goal at the `ensures` clauses, because
the prepatch returns `written = (if update then latest else standard)` even when
`checkOnly = true`, whereas `stepOutcome true _ = { written := noWrite, … }`).

## B. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-reference, or I. The operation that genuinely changed —
*the relative order of the abort and the write*, i.e. whether the write runs at
all in check-only mode — is modeled **deeply** (the `if checkOnly then … else …`
branch with the abort placed first, A3), not hidden behind an axiom about the
function under change. There is **no consumed axiom**: the only callee whose
runtime behaviour is relied on, `sys.exit`, is UNCHANGED, so modeling it as a
consumed axiom would be a dead axiom. Its raise-and-unwind property is instead an
**A-reference**, validated against the real callee by G-AX (mapping.md §3).

## C. Read-only inputs / directive 5

Both inputs are read-only mode flags (the step never mutates `checkOnly` or
`update`): neither is declared `mut`, so their post-states are trivially
unchanged (directive 5: an unmutated param needs no `mut` and no
`ensures xOld = x`). The result is a **freshly built** `StepOutcome`; a wrong
impl cannot satisfy the postcondition by aliasing an input. Because the spec
pins `checkOnly = true → out.written = noWrite` (and the full
`out = stepOutcome checkOnly update` truth table), the only way to verify is to
*not emit* an artifact in check-only mode — which is exactly why the prepatch,
which always emits `wk`, cannot verify.

## D. verify(Solution) ⇒ resolved

`runCheckedWrite` verifies only if, in check-only mode, it emits no artifact and
aborts, and otherwise emits the update/standard artifact without aborting (the
`out = stepOutcome checkOnly update` postcondition plus the two discriminating
clauses). By R (the `bool` flags and the write-method ↔ `WriteKind` bijection)
and the A3 correspondence — where the model's early `return` in check-only mode
IS the stack-unwind effect of the gold's relocated `sys.exit(1)` — the verified
control flow equals the gold patch: abort-before-write in check-only mode,
write-without-abort otherwise. By G-AX the real `sys.exit(1)` raises and unwinds
so the write statements after it do not run (the A-reference, mapping.md §3).
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement and the audited callee reference — and the gold
patch resolves (G-RESOLVE). The trust points are exactly the two of PLAN §1.1:
refinement fidelity (this document, G-EQ) and the callee-reference soundness
(G-AX); there is no consumed axiom.
