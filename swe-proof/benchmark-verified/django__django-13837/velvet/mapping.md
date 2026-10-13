# mapping.md — django__django-13837

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 415f50298f97fb17f841a9df38d995ccf347dfcc`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records the
provenance of each modeled input. There are **no axioms** in this bundle, so
there is no axiom-provenance section and `axiom_check.py` is absent (G-AX skip).

Repo file under change: `django/utils/autoreload.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `buildChildArgs` (method) | `get_child_arguments()` — `django/utils/autoreload.py:213` (changed body 219–246) | the modeled changed function (assembles the child-process re-launch argv for the auto-reloader) |
| `childArgsSpec` (pure) | the intended post-patch body of `get_child_arguments` | pure spec: the argv as a total function of the runtime inputs |
| `baseArgs` / `warnFlags` (pure) | `args = [sys.executable] + ['-W%s' % o for o in sys.warnoptions]` (line 223) | pure spec: the always-present interpreter + warning-flag prefix |
| `EntryDesc` (type) | the top-level program-entry descriptor `__main__.__spec__` (post-patch lines 224–225) | input carrier: how the program was started |
| `ScriptProbe` (type) | the on-disk existence checks on `py_script` (lines 228, 232, 238) | input carrier: the script-path probe outcome |
| `ArgErr.scriptMissing` | `raise RuntimeError('Script %s does not exist.' % py_script)` (line 243) | the invalid-invocation failure |

The pre-patch repo symbols the change removes (refinement audit only, not in the
consumer spec view): `import django.__main__` / `django_main_path =
Path(django.__main__.__file__)` and the `py_script == django_main_path` test
(lines 219–224 pre-patch).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

The table G-CONF (§4.1) uses to translate values between the Lean value domain
and the Python repo types. A wrong entry surfaces as a spurious G-CONF
disagreement.

| repo reality | Lean carrier | bijection |
|---|---|---|
| `sys.executable` (path `str`) | `interp : List Char` | `s` ↔ `s.toList`-shaped `List Char` |
| `sys.warnoptions` (list of raw option `str`) | `warnOpts : List (List Char)` | each raw option `o` ↔ a `List Char`; `warnFlags` prefixes `-W` to each, modeling `'-W%s' % o`; list `++` ↔ `List` `++` |
| `sys.argv` (list of `str`) | `argv : List (List Char)` | the full argument vector, element-wise `str ↔ List Char`; `sys.argv[1:]` ↔ `argv.drop 1` |
| `str(py_script.with_suffix('.exe'))` | `exePath : List Char` | the native-executable-suffix path (host-derived; a free input) |
| `str(py_script.with_name('%s-script.py' % py_script.name))` | `scriptPath : List Char` | the generated-launcher-script path (host-derived; a free input) |
| `__main__.__spec__` / `.parent` | `entry : EntryDesc` | `__spec__ is None` ↔ `.notModule`; `__spec__` present with empty `.parent` (`""`, falsy) ↔ `.pathEntry`; `__spec__` present with non-empty `.parent == pkg` ↔ `.moduleEntry pkg` (`pkg` the parent string as `List Char`) |
| the script-path existence probe | `probe : ScriptProbe` | `py_script.exists()` ↔ `.exists`; (¬exists ∧ `.exe` exists) ↔ `.exeEntry`; (¬exists ∧ ¬exe ∧ `-script.py` exists) ↔ `.scriptEntry`; none exist ↔ `.missing` |
| `args` return (list of `str`) | `Except.ok (out : List (List Char))` | the argument vector; element-wise `str ↔ List Char` |
| `raise RuntimeError('Script … does not exist.')` | `Except.error .scriptMissing` | both map to the G-CONF `ERROR` sentinel `("__SCRIPT_MISSING__",)` |

`EntryDesc` faithfully partitions the three observable cases of
`__main__.__spec__` the post-patch test `__main__.__spec__ is not None and
__main__.__spec__.parent` distinguishes: `None`, present-but-empty parent (the
directory/zipfile entry — the docs say `.parent` is `""` there), and
present-with-non-empty parent (the `-m pkg` start). `ScriptProbe` partitions the
mutually-exclusive, ordered filesystem outcomes the `elif … else` ladder consults
only on the non-module path. `List Char` / `List (List Char)` indexing is total
and sound; the carrier is `List Char` because tokens are compared/concatenated
per code point.

## 3. Input provenance (no kind-A — no callees assumed; nothing for G-AX)

Every value `buildChildArgs` consumes is a **read-only input** standing for a
runtime/host query the auto-reloader performs (it takes no Python argument). None
is `mut`; nothing is mutated (directive 5).

- `interp` ← `sys.executable`; `warnOpts` ← `sys.warnoptions`;
  `argv` ← `sys.argv` (and `argv.drop 1` ← `sys.argv[1:]`).
- `entry` ← `__main__.__spec__` (and its `.parent`), the documented entry-point
  descriptor (https://docs.python.org/3/reference/import.html#main-spec).
- `probe`, `exePath`, `scriptPath` ← the `Path(...).exists()` /
  `.with_suffix('.exe')` / `.with_name('%s-script.py' % name)` host queries.

None of these is a *callee whose behavior the proof assumes* — they are the
function's inputs, controlled by the caller/runtime (the F2P test mocks
`sys.argv`, `sys.warnoptions`, `sys.executable`, and `sys.modules['__main__']`,
and realizes the script path on disk). The `…Exists`/`…Path`/`entry` inputs are
**free** — the postconditions hold for every value, strictly weaker than the
real, correlated environment values, hence sound (directive 7). The unchanged
filesystem predicates/constructors (`Path.exists`, `with_suffix`, `with_name`)
are modeled as opaque observations, not axiomatized behaviour. Hence there are
**no axioms**, no A-reference deep models of callees, and **no `axiom_check.py`**;
`meta.json gates.G-AX.status = "skip"`. The mapping above is exercised
end-to-end by G-CONF, which realizes each input's denoted runtime state and
invokes the real patched function.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`13837`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow transliterates
`childArgsSpec`/`baseArgs`/`warnFlags` (all R/I-tagged ops, incl. the `-W`
prefixing) to Python; there is no A-tagged callee to leave as a real callee
(none exist). The oracle invokes the patched
`django.utils.autoreload.get_child_arguments` under the mocked sys-state and the
on-disk script-path realization each modeled input denotes. The fuzz space spans
every `EntryDesc × ScriptProbe` combination (28 boundary scenarios × 2
warn-option settings) plus the exact F2P scenario, then ≥10⁵ randomized
scenarios.
