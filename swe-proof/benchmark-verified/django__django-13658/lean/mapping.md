# mapping.md — django__django-13658

## Symbol binding (file:line @ base_commit 0773837e15bb632afffb6848a58c59a791008fa1)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_progName` (result = presented program name) | program name threaded into the option parser via `%(prog)s` in `ManagementUtility.execute()`, i.e. `self.prog_name` | `django/core/management/__init__.py:334-352` (`execute`); `:347` is the changed line (`prog=self.prog_name` added post-fix) |
| `basename` / `computeProgName` (deep model) | `self.prog_name = os.path.basename(self.argv[0])`, with the `__main__.py` → `python -m django` special case | `django/core/management/__init__.py:188-192` (`ManagementUtility.__init__`) |
| `argv` (utility's own arg vector) | `self.argv` = `argv or sys.argv[:]` | `:189` |
| `_ambient` (process-global arg vector) | `sys.argv` | stdlib `sys` |
| `result : String` | `self.prog_name : str` (the `%(prog)s` substitution) | `:190` |

## Lean ↔ Python type bijection (used by G-CONF; no G-AX axioms)

| Python | Lean | notes |
|---|---|---|
| `list[str]` (argv) | `List String` | one element per argument; first element is the launch path |
| `str` (an argument) | `String` | |
| `str` (program name) | `String` | the presented `%(prog)s` value |
| `os.path.basename(s)` on POSIX | `basename s = (s.splitToList (· = '/')).reverse.headI` | final `/`-separated component; whole string if no `/`; empty string if trailing `/`. POSIX only (repo path semantics; tests run on POSIX). |
| `'python -m django'` special case | `if basename = "__main__.py" then "python -m django"` | `ManagementUtility.__init__` lines 191-192 |

## Callee provenance + flag deps

No consumed callee axioms. The only operations are:
- `os.path.basename` — modeled DEEPLY as `basename` (A-reference; validated == the
  real computation by G-CONF, which observes `ManagementUtility(argv).prog_name`).
- the `__main__.py` special case — modeled DEEPLY as the `if` in `computeProgName`.

There is no flag dependency. The `_ambient` argument corresponds to the process
`sys.argv`; the fix makes the result independent of it, which the spec encodes by
never mentioning `_ambient` in `problem_spec_progName` and which G-CONF exercises
by mocking `sys.argv` to an unrelated vector.

## Precondition

`argv ≠ []` — the utility's argument vector always has at least the launch path
(`self.argv[0]` is indexed unconditionally in `__init__`). Modeled as the binder
hypothesis on `correct_progName`. `List.headI` is total in Lean (returns the
default `""` on `[]`), so the impl still elaborates without the hypothesis; the
hypothesis records the real-world guarantee.

## G-CONF fuzz seed

Pinned seed: **13658**. N = 100_000 fuzzed inputs + 9 deterministic boundary
cases (empty arg0, bare `/`, trailing `/`, `__main__.py`, ambient `[None]`, the
F2P `['django-admin','help','shell']` with ambient `[None,'help','shell']`).
