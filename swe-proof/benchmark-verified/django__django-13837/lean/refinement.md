# refinement.md — operation correspondence (django__django-13837)

Maps every op in `implementation_getChildArguments` to its `patch.diff`
counterpart. Tags: **R** type refinement · **A-consumed** proof uses axiom
property · **A-reference** deep model validated == real callee (G-AX) · **I**
identical op.

The post-patch Python computes:
```
import __main__
py_script = Path(sys.argv[0])
args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]
if __main__.__spec__ is not None and __main__.__spec__.parent:
    args += ['-m', __main__.__spec__.parent]; args += sys.argv[1:]
elif not py_script.exists():
    exe_entrypoint = py_script.with_suffix('.exe')
    if exe_entrypoint.exists(): return [str(exe_entrypoint), *sys.argv[1:]]
    script_entrypoint = py_script.with_name('%s-script.py' % py_script.name)
    if script_entrypoint.exists(): return [*args, str(script_entrypoint), *sys.argv[1:]]
    raise RuntimeError('Script %s does not exist.' % py_script)
else:
    args += sys.argv
return args
```

| # | Lean impl op | patch.diff / function counterpart | tag | justification |
|---|---|---|---|---|
| 1 | `let mut args := [executable]` | `args = [sys.executable] + …` | R | `sys.executable : str` ↔ `executable : String`; list-prefix init |
| 2 | `for o in warnoptions do args := args ++ ["-W" ++ o]` | `['-W%s' % o for o in sys.warnoptions]` appended | R | comprehension ↔ accumulator `for`; `'-W%s'%o` ↔ `"-W" ++ o` (str ↔ String) |
| 3 | `if launchPackage ≠ ""` | `if __main__.__spec__ is not None and __main__.__spec__.parent` | R | the changed guard. `__spec__.parent` is non-empty-str ⟺ `-m pkg`; encoded as `launchPackage ≠ ""` (mapping.md). This is the discriminating clause. |
| 4 | `return .ok (args ++ ["-m", launchPackage] ++ argv.tail)` | `args += ['-m', __main__.__spec__.parent]; args += sys.argv[1:]` | R | the changed body: emit the *launched* module name `launchPackage` (not a literal), then trailing args; `sys.argv[1:]` ↔ `argv.tail` |
| 5 | `else if ¬ scriptPresent then …` | `elif not py_script.exists():` | R | `py_script.exists()` ↔ `scriptPresent : Bool` |
| 6 | `match exeAlt with \| some exe => return .ok (exe :: argv.tail)` | `exe_entrypoint = py_script.with_suffix('.exe'); if exe_entrypoint.exists(): return [str(exe_entrypoint), *sys.argv[1:]]` | R | existence-probe-with-path ↔ `Option String`; unchanged branch |
| 7 | `\| none => match scriptAlt with \| some sp => return .ok (args ++ [sp] ++ argv.tail)` | `script_entrypoint = py_script.with_name(...); if script_entrypoint.exists(): return [*args, str(script_entrypoint), *sys.argv[1:]]` | R | same; unchanged branch |
| 8 | `\| none => return .error ("Script " ++ posixStr (argv.headD "") ++ " does not exist.")` | `raise RuntimeError('Script %s does not exist.' % py_script)` | R | exception ↔ `Except.error`; `'%s' % py_script == str(Path(sys.argv[0]))` — `str(Path(·))` normalizes the raw string (drops trailing/duplicate `/` and `.` segments, `"" → "."`), modeled by `posixStr (argv.headD "")` |
| 9 | `else return .ok (args ++ argv)` | `else: args += sys.argv; return args` | R | unchanged verbatim-replay branch; note full `argv`, not `argv.tail` |

Every row is **R** (type refinement) — every op is the concrete Python op under
the String/List/Bool/Option/Except bijection of mapping.md. There are **no
A-consumed and no A-reference rows**: no UNCHANGED pure callee's property is
assumed, and nothing is modeled "deeply" in place of a callee — the environment
probes are reified as typed inputs (`launchPackage`, `scriptPresent`, `exeAlt`,
`scriptAlt`). No changed-inexpressible op.

## Discriminating clause (G-DIFF)
Rows 3–4. The pre-patch routine recognises a module launch *only* when the
launch package label is exactly `"django"` and always re-invokes the literal
module `"django"`; `Solution_prepatch.lean` encodes this as
`if launchPackage = "django" then … "-m", "django" …`. For any module launch
with `launchPackage ∉ {"", "django"}` (e.g. `launchPackage = "pkg_other"`), the
prepatch falls through to the verbatim / fallback branches while the frozen
`problem_spec_getChildArguments` (pinned to `childArgsSpec`, which emits
`["-m", launchPackage]`) demands the module re-invocation. The two disagree on
that input, so the prepatch `correct_getChildArguments` is unclosable. That is
the G-DIFF signal, and it is exactly the F2P test
`test_run_as_non_django_module`.
