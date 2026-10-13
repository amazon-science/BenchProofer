# mapping.md — django__django-13658

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 0773837e15bb632afffb6848a58c59a791008fa1`, states the type
abstraction (the bijection G-CONF and G-AX use to bridge Lean↔Python), and
gives the provenance of each deep-model reference.

Repo file under change: `django/core/management/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `usageProgName (argv processArgv : List String)` | the program-name selection feeding the early-options parser in `ManagementUtility.execute` — `django/core/management/__init__.py:347` (the `CommandParser(...)` whose `usage='%(prog)s …'` names the program) | the modeled changed behavior: which program name the usage parser is given |
| `argv` parameter | `self.argv` of the `ManagementUtility` instance (`django/core/management/__init__.py:189`, set from the `argv` passed to `__init__`/`execute_from_command_line`) | the invocation's own argument vector |
| `processArgv` parameter | `sys.argv` (the process-global vector `argparse` falls back to for `prog` when none is passed) | the process-global argument vector — read-only, must not influence the result |
| `basename (path : List Char)` *(deep model — A-reference)* | `os.path.basename` (CPython `posixpath.basename`), called at `django/core/management/__init__.py:190` | pure spec: final path component (POSIX separators) |
| `progNameOf (argv : List String)` *(deep model — A-reference)* | `ManagementUtility.prog_name` as computed in `__init__` — `os.path.basename(self.argv[0])` then the `'__main__.py' → 'python -m django'` rename (`django/core/management/__init__.py:190-192`) | pure spec: the program name derived from a given argument vector |

The behavioral change (`patch.diff`, `__init__.py:347`): the `CommandParser` is
constructed **with** `prog=self.prog_name` instead of letting `argparse` default
`prog` to `os.path.basename(sys.argv[0])`. `self.prog_name` is
`progNameOf(self.argv)`; the argparse default is `basename(sys.argv[0])`, i.e.
`basename((processArgv).headD "")` (without the `__main__.py` rename). So the fix
replaces a result derived from `processArgv` with one derived from `argv` — the
single observable change the F2P test (`test_program_name_from_argv`) pins.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) and G-AX use to translate values between the
Lean value domain and the Python repo types.

| repo reality | Lean carrier | bijection |
|---|---|---|
| an argument vector (`list[str]`: `self.argv` / `sys.argv`) | `List String` | Python list `v` ↔ `List String`; `v[0]` ↔ `(l.headD "")` (both pick the first entry; the precondition `argv ≠ []` mirrors that a vector reaching the parser is non-empty, since `__init__` resolves `argv or sys.argv[:]`); `len(v)` ↔ `l.length` |
| a single program-name/path `str` | `List Char` | `s` (Python str) ↔ `s.toList`-shaped `List Char`; `ch ↔ Char.ofNat (ord ch)`; per-code-point on the BMP this is total and exact |
| `os.path.basename(p)` (POSIX) | `basename : List Char → List Char` | last path component: longest suffix with no `'/'`. POSIX `posixpath.basename` = `p.rpartition('/')[2]`, exactly `(p.reverse.takeWhile (· ≠ '/')).reverse` |
| the `'__main__.py' → 'python -m django'` rename | the `if b = "__main__.py" then …` branch of `progNameOf` | string equality on the basename; identity otherwise |

`prog` passed to `argparse.ArgumentParser` becomes `parser.prog`, which is what
`'%(prog)s'` in the usage string renders to. Modeling the *value* of the program
name (a `List Char`) is faithful because the F2P test observes exactly that
rendered token (`usage: django-admin shell`).

## 3. Callee provenance (kind-A-reference — checked by G-AX / axiom_check.py)

### 3.1 `basename` deep model ↔ `os.path.basename` (A-reference)
**Callee:** CPython `os.path.basename` (POSIX → `posixpath.basename`), unchanged
by the patch. It is modeled **deeply** by `basename` in the `pure` region; there
is **no consumed axiom**. `posixpath.basename(p)` returns the substring after the
last `'/'` (and `p` itself if there is no `'/'`), which is exactly
`(p.reverse.takeWhile (· ≠ '/')).reverse`. G-AX runs the real `os.path.basename`
on boundary + fuzz paths and asserts equality with the deep model.

### 3.2 `progNameOf` deep model ↔ `ManagementUtility.prog_name` (A-reference)
**Callee/site:** the `prog_name` computation in `ManagementUtility.__init__`
(`os.path.basename(self.argv[0])`, then `'__main__.py' → 'python -m django'`),
unchanged by the patch — the patch only *uses* `self.prog_name` at the parser
site. `progNameOf` is the deep model of that derivation. G-AX constructs real
`ManagementUtility` instances over fuzzed vectors and asserts
`progNameOf(v) == ManagementUtility(v).prog_name`.

**Soundness check (G-AX):** `axiom_check.py` imports only `os.path` and Django's
`ManagementUtility`, runs both real callees on boundary inputs (empty-ish first
entries, `__main__.py`, dotted names, multi-slash paths, the F2P `django-admin`)
plus randomized fuzz, and asserts (a) `basename == os.path.basename` and
(b) `progNameOf == ManagementUtility(v).prog_name`. Exit 0 iff sound.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13658`** so the
consumer-side verdict is reproducible. The R/I shadow it builds transliterates
`basename`/`progNameOf` (R/I-tagged ops) to Python and compares against
`patch.diff`'s behaviour: the program name `argparse` reports for the early
options parser, observed end-to-end through `execute_from_command_line` /
`ManagementUtility`. There are no A-tagged callees inside the impl region (the
two deep models are R/I content, validated as references by G-AX), so the shadow
is pure R/I and `conf_skip=false`.
