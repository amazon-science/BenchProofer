# refinement.md — django__django-13658

Operation-by-operation correspondence between `Solution.lean`'s impl region
(the `usageProgName` `do` block, plus the deep models `progNameOf`/`basename`)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A-consumed** (proof uses an axiom's `ensures`), **A-reference** (a deep model
validated == the real callee by G-AX), or **I** (identical concrete op). EVERY
step is R, A, or I; there is no kind-3 (inexpressible changed op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A-reference legs + this narrative are audited by **G-EQ** / **G-AX**.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The parser program-name site — `ManagementUtility.execute` (`__init__.py:347`)

Gold hunk:
```
- parser = CommandParser(usage='%(prog)s subcommand [options] [args]', add_help=False, allow_abbrev=False)
+ parser = CommandParser(
+     prog=self.prog_name,
+     usage='%(prog)s subcommand [options] [args]',
+     add_help=False,
+     allow_abbrev=False,
+ )
```

The observable behavior: the program name `argparse` renders for `'%(prog)s'`.
Pre-patch, `prog` is unset, so `argparse` defaults it to
`os.path.basename(sys.argv[0])` — the **process-global** vector. Post-patch,
`prog=self.prog_name`, where `self.prog_name = progNameOf(self.argv)` — the
**invocation's own** vector (`__init__.py:189-192`, unchanged).

| # | Solution.lean impl op (`usageProgName`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | parameter `argv : List String` | `self.argv` (the passed argument vector) | R | `list[str] ↔ List String` (mapping.md §2); `argv[0] ↔ (argv.headD "")`. |
| A2 | parameter `processArgv : List String` | `sys.argv` (argparse's default source for `prog`) | R | `list[str] ↔ List String`. Read-only; never read by the impl — mirrors that the fix makes the result independent of the process global. |
| A3 | `out = progNameOf argv`: basename of the first entry, with `__main__.py → python -m django` | `prog=self.prog_name` (= `os.path.basename(self.argv[0])` + the rename) fed into `CommandParser`; `'%(prog)s'` then renders it | A-reference + I | the changed value-flow is modeled **deeply**: `progNameOf`/`basename` (pure region) ARE the derivation. The list/string ops (`headD`, `basename`, the `if`-rename) are **I** (concrete, transliterated by G-CONF); the equality of `progNameOf` to the real `ManagementUtility.prog_name` and of `basename` to the real `os.path.basename` are the **A-references** G-AX validates. mapping.md §3. |
| A4 | `out` returned (`List Char`) | `parser.prog`, rendered by `'%(prog)s'` into the usage text the F2P test reads | R | the program name is observed as the rendered token (`usage: django-admin shell`); `List Char ↔ str` on content (mapping.md §2). |

Discriminating content of the change — the program name comes from `argv`, not
`processArgv`. `Solution_prepatch.lean` derives `out = progNameOf processArgv`
(argparse's pre-patch default source) and **fails** `out = progNameOf argv`
exactly on `progNameOf processArgv = progNameOf argv` (G-DIFF): the two vectors
are independent, so equality is unprovable. The F2P test
`test_program_name_from_argv` is precisely this discriminator (sets
`sys.argv = [None, …]` while passing a real `argv`).

## B. No consumed axioms

There are no `axiom`s and no `:|` stubs; `prove_correct usageProgName by
loom_solve` consumes none. The two operations the derivation uses
(`os.path.basename`, the `prog_name` computation) are UNCHANGED callees modeled
**deeply** as `basename`/`progNameOf` — A-references validated == their real
callees by G-AX (`axiom_check.py`), not contracts the proof assumes. (Directive
6: no dead axioms.)

## C. `mut`-frame discipline (directive 5)

Neither parameter is `mut`; both `argv` and `processArgv` are read-only and the
method returns a fresh `out`. `processArgv` is supplied to make the spec able to
state independence from the process global, and the impl provably never reads it
(`out = progNameOf argv`). No post-state frame obligation arises.

## D. No kind-3 (inexpressible-changed-op) steps

Every step is R, A-reference, or I. The one operation that genuinely *changed* —
which argument vector the program name is derived from — is modeled directly as
the choice of input to the deeply-modeled `progNameOf` (`argv`, not
`processArgv`), an A-reference + I, not hidden behind an axiom about the function
under change.

## E. verify(Solution) ⇒ resolved

`usageProgName` verifies only if `out = progNameOf argv` (A3) — the program name
derived from the invocation's own vector, with the standard basename + rename. By
R (`list[str] ↔ List String`, `argv[0] ↔ headD`, `List Char ↔ str` on content)
this equals the `self.prog_name` the patched `CommandParser(prog=self.prog_name)`
feeds `'%(prog)s'`; by G-AX the deep models equal their real callees
(`basename == os.path.basename`, `progNameOf == ManagementUtility.prog_name`); by
G-CONF the R/I transliteration agrees with `patch.diff`'s rendered program name
over ≥10⁵ inputs (including independence from `processArgv`). Therefore a model
satisfying this spec, refined by the map above, is the gold patch up to type
refinement and validated references — and the gold patch resolves (G-RESOLVE).
