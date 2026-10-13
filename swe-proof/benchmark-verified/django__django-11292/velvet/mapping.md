# mapping.md — django__django-11292

Cold spec (`spec_provenance: cold`): derived only from `problem_statement`, the
gold `patch`, and the real source at `base_commit`
`eb16c7260e573ec513d84cb586d96bdf508f3173`.

## 0. The change in one line

Expose the pre-existing `skip_checks` stealth option on the command line as a
real `--skip-checks` flag, so a management command that performs system checks
registers the flag and, when it is given, does not run the checks.

## 1. Symbol binding (file:line @ base_commit)

All sites are in `django/core/management/base.py` (the single changed file).

| gold-patch site | base_commit location | modeled? | model symbol |
|---|---|---|---|
| `BaseCommand.create_parser` registers the flag under a guard | `base.py:249` (def); insertion after the `--force-color` block at `base.py:286‑288`, before `self.add_arguments(parser)` at `base.py:289` | **yes** | `registeredCommandOptions` |
| `BaseCommand.execute` gates the checks on the flag | `base.py:342` (def); the gate at `base.py:360` | **yes** | `shouldRunSystemChecks` |
| `DjangoHelpFormatter.show_last` gains `--skip-checks` | `base.py:96` | **no** (test‑neutral; see §4) | — |
| `BaseCommand.base_stealth_options` drops `skip_checks` | `base.py:226` | **no** (test‑neutral; see §4) | — |

The command exercised by the F2P test, `set_option`
(`tests/user_commands/management/commands/set_option.py`), is an ordinary
`BaseCommand` subclass: it does **not** override `requires_system_checks`, so it
inherits the class default `True` (`base.py:223`). Hence in the tested
configuration the flag IS registered and the checks ARE gated on it.

## 2. The Lean ↔ Python type bijection (used by G-CONF)

| Python (repo reality) | Lean model | notes |
|---|---|---|
| `self.requires_system_checks` (class bool) | `requiresSystemChecks : Bool` | free input; the patch reads it, does not change it |
| the set of option strings the parser recognises *excluding* the new flag | `commonOptions : List String` | free input = the frame: framework options (`--version`, `-v/--verbosity`, `--settings`, `--pythonpath`, `--traceback`, `--no-color`, `--force-color`, `-h/--help`) **plus** whatever the command's own `add_arguments` registers. The patch does not touch any of these. |
| the string literal `'--skip-checks'` | `"--skip-checks" : String` | public token (problem statement title) |
| the set of option strings the parser recognises *after* the change | `registeredCommandOptions`'s result `out : List String` | membership `"--skip-checks" ∈ out` is the behavioural content; list order is incidental (argparse acceptance is set-based; `show_last` only reorders *help display*) |
| `options['skip_checks']` (bool in the parsed namespace) | `skipRequested : Bool` | `action='store_true'`, default `False` |
| "`self.check()` is invoked" | `shouldRunSystemChecks`'s result `result : Bool` | `True` ⟺ the gate `requires_system_checks and not options['skip_checks']` is taken |

## 3. Callee provenance + flag deps

No axioms / no A-reference deep models. The two modeled operations are pure
boolean / list-frame logic over **free inputs**:

* `registeredCommandOptions` delegates the construction of `commonOptions` to
  `argparse.ArgumentParser.add_argument` (CPython stdlib, unchanged) and to the
  command's own `add_arguments` (command-specific, unchanged). Neither is
  changed by the patch and neither's *internals* are load-bearing for the
  modeled behaviour — only the conditional **addition** of one more option is.
  So `commonOptions` is taken as a free frame input; there is nothing to
  axiomatize and nothing for G-AX to check.
* `shouldRunSystemChecks` is a pure conjunction of two free booleans.

Flag dependency worth recording for G-CONF: the registration is guarded by
`requiresSystemChecks`; a command with `requires_system_checks = False`
(e.g. `runserver`, `shell`, `test`) registers **no** `--skip-checks` flag. The
conformance fuzz therefore covers both polarities of `requiresSystemChecks`.

## 4. Why the two unmodeled hunks are test-neutral

* `show_last` (`base.py:96`): only `DjangoHelpFormatter._reordered_actions`
  consumes it, and only to sort actions for `--help` **display**. It changes no
  parse result and no check decision. Not observed by any F2P/P2P test.
* `base_stealth_options` (`base.py:226`): consumed by
  `management.call_command` to compute `valid_options` for its "Unknown
  option(s)" diagnostic. After the change `skip_checks` is no longer a *stealth*
  option but becomes a real parser `dest`, so it stays in `valid_options` either
  way (P2P `test_call_command_unrecognized_option` still lists `skip_checks`).
  Net effect on any observable behaviour: none. Both hunks are carried verbatim
  in `patch.diff` (gold) so the harness resolves, but they are outside the
  modeled spec by design (no behavioural delta to pin).

## 5. G-CONF fuzz seed

Pinned seed: **`11292`**. `conformance_check.py` exhausts the 2-bit cube
`(requiresSystemChecks, skipRequested)` and fuzzes `commonOptions` (random
option-string lists) for ≥10⁵ inputs against an oracle that builds a real
`argparse` parser exactly as the patched `create_parser` does (parser
acceptance) plus the transliterated `execute` gate. `conf_skip = false`.
