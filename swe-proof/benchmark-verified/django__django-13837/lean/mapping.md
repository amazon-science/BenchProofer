# mapping.md — symbol binding & type bijection (django__django-13837)

## Modeled function
- **Lean** `implementation_getChildArguments :
  String → List String → List String → String → Bool →
  Option String → Option String → Except String (List String)`
- **Python** `django.utils.autoreload.get_child_arguments()` —
  `django/utils/autoreload.py:213-246 @ 415f50298f` (base_commit).

The function computes the argument vector used to relaunch the server process.
The patch changes only the *module-launch detection* branch: instead of
recognising the single hard-coded case "started as `python -m django`" (by
comparing the script path to django's own `__main__` file), it now recognises
*any* module launch and relaunches that same module by its package label, using
the documented `__main__.__spec__.parent` mechanism. All other branches
(alternate-entrypoint Windows fallback, verbatim argv replay, missing-script
error) are unchanged.

## Type bijection (used by G-CONF + G-AX)
| Python | Lean | notes |
|---|---|---|
| `sys.executable : str` | `executable : String` | interpreter path |
| `sys.warnoptions : list[str]` | `warnoptions : List String` | each → `-W<opt>` |
| `sys.argv : list[str]` | `argv : List String` | head = script (`argv[0]`), tail = `argv[1:]` |
| `__main__.__spec__.parent` (or `""`/None→not-a-module) | `launchPackage : String` | `""` ⟺ not started as a module; non-empty ⟺ started as `-m <launchPackage>` |
| `py_script.exists()` | `scriptPresent : Bool` | filesystem probe on `Path(sys.argv[0])` |
| `str(Path(sys.argv[0]))` (in the error message) | `posixStr (argv.headD "")` | `Path()` POSIX string normalization: drop empty/`.` segments, keep `//` or `/` root, `""` ↦ `"."` |
| `py_script.with_suffix('.exe').exists()` → that path | `exeAlt : Option String` | `some p` iff the `.exe` entrypoint exists |
| `py_script.with_name('%s-script.py').exists()` → that path | `scriptAlt : Option String` | `some p` iff the `-script.py` entrypoint exists |
| return `list[str]` / `raise RuntimeError(msg)` | `Except String (List String)` | `.ok argv` / `.error msg` |

### `__main__.__spec__` → `launchPackage` encoding (the changed predicate)
The post-patch guard is `__main__.__spec__ is not None and __main__.__spec__.parent`.
In Python, `__spec__.parent` is a `str` that is non-empty exactly when the
program was started with `-m <package>` (it is `""` when started by directory/
zipfile name, and `__spec__` is `None` when started as a plain script). The
single scalar `launchPackage : String` captures this faithfully:
- not a module launch (`__spec__ is None`, or `parent == ""`) ⟺ `launchPackage = ""`;
- started as `-m pkg` (`parent == "pkg"`, truthy) ⟺ `launchPackage = "pkg"`.
The guard `__main__.__spec__ is not None and __main__.__spec__.parent` is thus
exactly `launchPackage ≠ ""`, and the emitted token `__main__.__spec__.parent`
is exactly `launchPackage`.

### `Path(sys.argv[0])` rendering in the missing-script diagnostic
`raise RuntimeError('Script %s does not exist.' % py_script)` interpolates
`py_script = Path(sys.argv[0])`, and `str(Path(s))` NORMALIZES the raw string:
trailing `/` dropped (`"a/" → "a"`), duplicate `/` collapsed
(`"sub//x.py" → "sub/x.py"`), `.` segments dropped (`"a/./b" → "a/b"`,
`"./foo" → "foo"`), the empty path renders as `"."`, and an exactly-double
leading slash is preserved as the `//` root while `/` and `///…` render as `/`
(POSIX `PurePath` semantics). This is captured by the pure `posixStr` function,
applied to `argv.headD ""` in the error branch of `childArgsSpec`. Fixed on
2026-08-03 after a G-PANEL-2 faithfulness finding (spec previously emitted the
RAW `argv[0]`, diverging on e.g. `argv[0]="a/"`: real `'Script a does not
exist.'` vs old spec `'Script a/ does not exist.'`).

## Callee provenance
- No UNCHANGED callee is consumed as an axiom and there is no deep-model
  reference callee. `Path(...)`, `.exists()`, `.with_suffix`, `.with_name`, and
  the `__main__.__spec__` lookup are all *environment observations*, not pure
  callees the proof must reason about; each is lifted to a typed input
  (`scriptPresent`, `exeAlt`, `scriptAlt`, `launchPackage`). The list/string
  plumbing (`[sys.executable] + ['-W%s'%o ...]`, `sys.argv[1:]`) is concrete and
  modeled directly. The `axioms` region is therefore empty.

## Flag dependency
None. The only configuration that matters is whether the program was launched as
a module, which is reified by `launchPackage`.

## G-CONF fuzz seed
Pinned seed: **13837**. ≥10^5 fuzzed inputs over the seven-tuple
`(executable, warnoptions, argv, launchPackage, scriptPresent, exeAlt, scriptAlt)`,
oversampling the empty / non-empty `launchPackage` boundary and the
script-absent fallback chain.
