# mapping.md — django__django-13658

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 0773837e15bb632afffb6848a58c59a791008fa1`, states the type
abstraction, and gives the provenance of the one A-reference (an unchanged
library primitive the deep model is validated against by G-AX).

Repo file under change: `django/core/management/__init__.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `build_settings_parser(self)` | the settings/pythonpath pre-scan parser construction inside `ManagementUtility.execute` — `django/core/management/__init__.py:347` (the `CommandParser(...)` statement) | the modeled changed function: builds the option-pre-scan parser and fixes which source its program name comes from |
| `Utility` (class) | `ManagementUtility` — `django/core/management/__init__.py:184` | the utility carrying the computed program name |
| `Utility.argv0_basename` | `os.path.basename(self.argv[0])` where `self.argv = argv or sys.argv[:]` — computed in `ManagementUtility.__init__`, `django/core/management/__init__.py:189-190` | basename of the utility's OWN first argument (the source the fix routes to the parser) |
| `Utility.sys_argv0_basename` | `os.path.basename(sys.argv[0])` — argparse's implicit program-name default when no `prog` is supplied (the pre-patch source) | basename of the ambient/process-wide first argument |
| `Parser` (class) | `CommandParser` (subclass of `argparse.ArgumentParser`) — `django/core/management/base.py:45` | the option-pre-scan parser; only its `prog` attribute is touched |
| `Parser.prog` | `argparse.ArgumentParser.prog` (the program name used by `%(prog)s` in the usage string) | the displayed program name |
| `program_name(basename)` *(deep model — A-reference)* | the `prog_name` computation in `ManagementUtility.__init__` — `django/core/management/__init__.py:190-192` (`os.path.basename(self.argv[0])`, with the `__main__.py` → `'python -m django'` special case) | pure spec: the program-name rule; validated `== real prog_name` by axiom_check.py (G-AX), NOT consumed as an axiom |
| `bootstrap_name()` | the literal `'__main__.py'` (`__init__.py:191`) | pure spec: bootstrap basename as code points |
| `module_invocation()` | the literal `'python -m django'` (`__init__.py:192`) | pure spec: module-invocation name as code points |

The pre-patch repo behaviour the change corrects (for the refinement audit, not
referenced from the consumer spec view): at `__init__.py:347` the parser is
built as `CommandParser(usage='%(prog)s subcommand [options] [args]',
add_help=False, allow_abbrev=False)` — with no `prog`, so `argparse` defaults
the program name to `os.path.basename(sys.argv[0])` (the ambient source). The
gold patch adds `prog=self.prog_name`, routing the utility's OWN argv-derived
program name into the parser.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `str` (program names, basenames) | `List[int]` of Unicode code points | `s[k]` ↔ `text[k] == ord(s[k])`; `len(s)` ↔ `len(text)`; an empty `str` ↔ `[]`; equality of `str` ↔ `PSeq` equality via `ToSeq` |
| `str` value inside a specification | `PSeq[int]` (pure Viper sequence) | `ToSeq(list)` materializes the list as a `PSeq`; `PSeq` `+`/`take`/`len`/`[i]` mirror `str` `+`/slice/`len`/index |
| `CommandParser(...)` object (only `prog` observed) | `Parser` minimal class with one field `prog: List[int]` | the F2P test observes the parser's program name through the usage string `%(prog)s`; only `prog` is touched, so the model carries only `prog` |
| `ManagementUtility` (only the two program-name sources observed) | `Utility` minimal class with `argv0_basename`, `sys_argv0_basename` | the change concerns only which of the two first-argument basenames the parser's `prog` is derived from |
| `self.prog_name` (the `__init__`-computed name) | `program_name(ToSeq(self.argv0_basename))` | a deep pure function of the utility's OWN first-argument basename (§3) |

`str` indexing/iteration is banned in Nagini, so the carrier is `List[int]`
throughout; the specification is phrased over `PSeq[int]` via `ToSeq`. The
`os.path.basename` split is applied at the boundary (the model's inputs are
already the basenames), exactly as `__init__` stores `os.path.basename(...)`.

## 3. A-reference provenance (checked by G-AX / axiom_check.py)

There are **no consumed `@ContractOnly` axioms**. The behaviour the change is
about — *which* argument vector the parser's program name is derived from — is
modeled **deeply**: `build_settings_parser` sets `Result().prog ==
program_name(ToSeq(self.argv0_basename))`, spelled out as a verified copy of the
utility's own first-argument code points (with the bootstrap-name branch). The
two unchanged library primitives the refinement leans on are validated against
their real semantics out-of-band by `axiom_check.py`:

### 3.1 `program_name` deep model ↔ `ManagementUtility.__init__`'s `prog_name`
**Source** (`django/core/management/__init__.py:188-193`):

```python
def __init__(self, argv=None):
    self.argv = argv or sys.argv[:]
    self.prog_name = os.path.basename(self.argv[0])
    if self.prog_name == '__main__.py':
        self.prog_name = 'python -m django'
    self.settings_exception = None
```

`program_name(basename)` returns `basename` except that the bootstrap basename
`'__main__.py'` maps to `'python -m django'` — exactly this rule. G-AX asserts
`program_name(os.path.basename(argv0)) == ` the real `prog_name` on boundary +
20 000 fuzz `argv0` values (including ones whose basename is the bootstrap name).

### 3.2 Argument-parser program-name handling ↔ `argparse.ArgumentParser`
**Source:** CPython `argparse.ArgumentParser.__init__`
(`Lib/argparse.py`): when `prog` is `None` it is set to
`_os.path.basename(_sys.argv[0])`; when a `prog` string is supplied it is used
verbatim. `CommandParser` (`django/core/management/base.py:45`) forwards all
keyword arguments to `ArgumentParser` unchanged, so its program-name handling is
argparse's.

G-AX asserts both directions on boundary + fuzz inputs:
- **POST-patch (the model's contract):** `ArgumentParser(prog=p, usage=...,
  add_help=False, allow_abbrev=False).prog == p` — supplying `self.prog_name`
  makes the parser use the utility's own argv-derived name.
- **PRE-patch (the prepatch skeleton's source):** with no `prog`, the parser's
  program name defaults to `os.path.basename(sys.argv[0])` — the ambient source
  modeled by `sys_argv0_basename`.

This is the only flag dependency: the program-name handling is exercised with
exactly the keyword arguments the call site uses (`usage`, `add_help=False`,
`allow_abbrev=False`), none of which affect `prog`. `axiom_check.py` imports only
the standard-library `argparse`, `os`, `sys` modules — the very modules the
changed code uses; nothing repo-specific.
