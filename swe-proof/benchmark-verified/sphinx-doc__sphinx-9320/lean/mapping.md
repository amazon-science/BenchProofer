# mapping.md — sphinx-doc__sphinx-9320

## Symbol binding (file:line @ base_commit e05cef574b8f23ab1b57f57e7da6dee509a4e230)

| Lean symbol | Python symbol | location |
|---|---|---|
| `implementation_validateRootEntry` / `problem_spec_validateRootEntry` | `is_path_or_empty` — the validator passed as the `validator` argument of the `do_prompt(...)` call for the "enter a new root path" question | `sphinx/cmd/quickstart.py:98-101` (post-patch); call site `:232` |
| `checkExistingDir` (opaque callee) | `is_path` — the unchanged existing-directory validator (`path.expanduser` then `path.isdir`, raising `ValidationError` otherwise) | `sphinx/cmd/quickstart.py:90-94` |
| `x : String` | the candidate entry string handed to the validator | `sphinx/cmd/quickstart.py:98` (param `x`) |
| `Except String String` result | the validator's outcome: a returned string (validated entry) vs. a raised `ValidationError(msg)` | `sphinx/cmd/quickstart.py:90-101` |

## What the modeled step does

The "enter a new root path" prompt is reached only when an existing Sphinx
project (a `conf.py`) is detected. `do_prompt(text, default, validator)` reads a
line and passes it through `validator`; if the validator raises
`ValidationError`, `do_prompt` re-prompts (the entry is rejected). The caller
then does:

```python
d['path'] = do_prompt(__('Please enter a new root path (or just Enter to exit)'),
                      '', is_path_or_empty)
if not d['path']:
    sys.exit(1)
```

At base_commit the validator was `is_path`:
```python
def is_path(x: str) -> str:
    x = path.expanduser(x)
    if not path.isdir(x):
        raise ValidationError(__("Please enter a valid path name."))
    return x
```
An empty entry (`x = ''`) makes `path.isdir('')` false, so `is_path` RAISES and
`do_prompt` re-prompts forever — the user can never reach the `if not d['path']`
guard to exit. (This is the issue: pressing Enter gives "Please enter a valid
path name." instead of exiting.)

Post-patch routes the prompt through `is_path_or_empty`:
```python
def is_path_or_empty(x: str) -> str:
    if x == '':
        return x
    return is_path(x)
```
Now an empty entry is RETURNED verbatim (no exception), so `do_prompt` returns
`''`, `d['path']` is falsy, and `sys.exit(1)` fires — the user exits by pressing
Enter. A non-empty entry is delegated unchanged to `is_path`, preserving the
existing-directory requirement.

The modeled function is exactly `is_path_or_empty`. Its observable contract: an
empty entry is accepted as-is; a non-empty entry produces precisely whatever the
unchanged existing-directory validator (`is_path`) produces for it.

## Lean ↔ Python type bijection (used by G-CONF and G-AX)

| Python | Lean | bijection |
|---|---|---|
| the candidate entry `x : str` | `x : String` | identity (UTF-8 string). |
| `is_path_or_empty` RETURNS `s` | `Except.ok s` | a returned string ↔ `.ok s` (accepted entry). |
| `is_path_or_empty` RAISES `ValidationError(msg)` | `Except.error msg` | a raised validation error ↔ `.error msg`. |
| `is_path(x)` (returns or raises) | `checkExistingDir x : Except String String` | the unchanged existing-directory validator: returned string ↔ `.ok`, raised `ValidationError(msg)` ↔ `.error msg`. |
| `x == ''` | `x == ""` | empty-string test. |

Equality of the two `.ok`/`.error` carriers is exactly equality of the Python
return value / raised-message, so the empty-vs-delegate routing is faithfully
captured.

## Callee provenance + flag dependencies

- **`is_path` — `checkExistingDir` (A-reference, unchanged).** The patch does NOT
  modify `is_path`; `is_path_or_empty` simply delegates to it for non-empty
  entries. It appears IDENTICALLY in the spec (`problem_spec`'s non-empty clause)
  and the impl (the `return checkExistingDir x` branch), so it is an A-reference
  that cancels in the differential, not a consumed axiom. No property of it is
  consumed by `correct_validateRootEntry` (the empty branch is discharged purely;
  the non-empty branch is a syntactic identity). G-AX is therefore a skip stub.
- **`do_prompt`, `sys.exit`, the `if not d['path']` guard — outside the model.**
  The patch's only edit to behavior is the validator swap; the prompt loop and the
  exit guard are unchanged plumbing. The model captures the validator's
  input→outcome relation, which is the whole of the observable change (an empty
  entry now flows back to the caller as `''` instead of looping).
- **Flag dependencies.** None. `is_path_or_empty` behaves identically regardless of
  configuration; the empty-acceptance is unconditional.

## G-CONF fuzz seed

Pinned LCG seed: **9320** (see `conformance_check.py` `SEED`). Corpus: fuzzed
entry strings — the empty string, dotted/relative path-like names, absolute-ish
names, whitespace, and unicode — diffed against an in-process replica of the
post-patch `is_path_or_empty` routing (the empty entry returned verbatim;
non-empty entries delegated to a stand-in existing-directory validator that is
SHARED between the oracle and the shadow, so it cancels). ≥1e5 samples. G-AX is a
skip stub (the existing-directory validator is an A-reference, identical in spec
and impl, exercised by G-CONF).
