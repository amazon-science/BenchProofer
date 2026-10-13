# mapping.md — django__django-15987

Cold construction. Spec derived solely from `problem_statement`, the gold
`patch`, and the repo source at `base_commit`
(`7e6b537f5b92be152779fc492bb908d27fe7c52a`). No prior twin/spec consulted.

## Symbol binding (file:line @ base_commit)

| Lean symbol | Python symbol | location @ base_commit |
|---|---|---|
| `implementation_fixtureDirs` / `problem_spec_fixtureDirs` / `correct_fixtureDirs` | the per-app default-fixture-directory collision check inside `Command.fixture_dirs` | `django/core/management/commands/loaddata.py:354-383` (changed block: the `for app_config …` loop, line 367 `if app_dir in fixture_dirs:`) |

The function is a `@cached_property` that assembles the list of fixture
directories. The CHANGED behavior is the guard that forbids an application's own
default fixtures directory (`<app.path>/fixtures`) from also appearing in the
user-configured `settings.FIXTURE_DIRS`. The gold patch edits exactly one line:

```python
for app_config in apps.get_app_configs():
    app_label = app_config.label
    app_dir = os.path.join(app_config.path, "fixtures")
-   if app_dir in fixture_dirs:
+   if app_dir in [str(d) for d in fixture_dirs]:
        raise ImproperlyConfigured(
            "'%s' is a default fixture directory for the '%s' app "
            "and cannot be listed in settings.FIXTURE_DIRS." % (app_dir, app_label)
        )
```

`app_dir` is always a `str` (produced by `os.path.join`). Each element `d` of
`settings.FIXTURE_DIRS` may be a `str` OR a `pathlib.Path` (the documented,
supported configuration). The pre-patch membership test `app_dir in
fixture_dirs` compares `app_dir == d` element-wise; in Python a `str` is never
`==` to a `Path`, so a `Path`-typed configured directory that names the same
location goes UNDETECTED. The patched test coerces every entry to its string
form (`str(d)`) first, so the comparison is location-vs-location regardless of
the entry's runtime type.

## Modeled behavior

The modeled relation is: **given the configured fixture directories and the
installed application components (each with its intrinsic default fixtures
directory), return the first component whose default directory equals (by textual
location) some configured directory, or `none` if none does.** That first
component is exactly the one whose presence triggers the
`ImproperlyConfigured` raise (with its `app_label`); `none` means no per-app
collision and the property continues building its list.

The raise itself (an exception with a formatted message) is modeled as
"identify the offending component": returning `some c` ↔ the real code raising
on component `c`; returning `none` ↔ the loop completing without raising.
Frame: the message text and the rest of `fixture_dirs`' list assembly
(`os.path.isdir` filtering, `dirs.extend`, `realpath`) are UNCHANGED by the
patch and out of the modeled frame — the patch touches only the membership
predicate, so the spec pins only the predicate's outcome.

## Lean ↔ Python type bijection

| Python | Lean | bijection |
|---|---|---|
| an element `d` of `settings.FIXTURE_DIRS` | `ConfiguredDir` (`value : String`, `isObject : Bool`) | `value` = the location's textual form (`str(d)` / `os.fspath(d)`); `isObject = true` iff `d` was supplied as a `pathlib.Path` (a structured location object), `false` iff `d` is a plain `str` |
| `settings.FIXTURE_DIRS` | `dirs : List ConfiguredDir` | order-preserving list |
| an installed app component | `Component` (`label : String`, `defaultDir : String`) | `label` = `app_config.label`; `defaultDir` = `os.path.join(app_config.path, "fixtures")` |
| `apps.get_app_configs()` (the iteration) | `comps : List Component` | iteration order preserved (the patch does not reorder; first-match matters) |
| `app_dir in [str(d) for d in fixture_dirs]` | `collides dirs c.defaultDir` (= `dirs.any (fun d => d.value == c.defaultDir)`) | string-form membership; type tag IGNORED (the fix) |
| the component that triggers `raise ImproperlyConfigured(...)`, or "no raise" | `result : Option Component` | first colliding component ↦ `some c`; loop completes ↦ `none` |

Notes / unchanged frame:
* The earlier whole-list duplicate guard (`len(fixture_dirs) != len(set(...))`)
  is a SEPARATE, unchanged check above the modeled loop; it is out of frame.
* `os.path.join(app_config.path, "fixtures")` always yields a `str`, so the
  target side of the comparison is always plain text — only the configured-entry
  side can be a `Path`. This is why `isObject` lives on `ConfiguredDir`, not on
  `Component`.

## Callee provenance / flag deps

* No UNCHANGED callee needs an axiom. The changed behavior is modeled deeply
  with concrete Lean operations (a textual-equality membership test `collides`
  and a first-match scan `List.find?`). → `axioms` region is EMPTY;
  `axiom_check.py` is a skip stub.
* The discriminator is the runtime type of each `FIXTURE_DIRS` entry
  (`str` vs `pathlib.Path`), captured by `ConfiguredDir.isObject`. There is no
  runtime config flag; G-CONF fuzzes both entry types.

## G-CONF fuzz seed

Pinned seed: **20240823** (instance `created_at` date). `conformance_check.py`
builds the Python R/I shadow of `implementation_fixtureDirs` (string-form
membership + first match) and diffs it against the REAL patched
`Command.fixture_dirs` collision behavior: for fuzzed `(FIXTURE_DIRS,
app-default-dirs)` configurations mixing `str` and `Path` entries, it observes
whether the real code raises `ImproperlyConfigured` and for which `app_label`,
and compares against the shadow's first-colliding-component prediction over the
full small matrix plus ≥1e5 randomized draws.
