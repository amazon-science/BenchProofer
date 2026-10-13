# mapping.md — django__django-11292

## Symbol binding (file:line @ base_commit eb16c7260e)
Modeled function: the launch-time decision a management command makes about
whether to run its system checks, as realised by the pair
`BaseCommand.create_parser` (option registration) and `BaseCommand.execute`
(the check decision), `django/core/management/base.py`.

The gold patch:
* `create_parser` (`base.py:248-310` @ base) — after registering `--force-color`,
  registers a new `--skip-checks` store-true argument *iff*
  `self.requires_system_checks` (`base.py:289-293` post-patch).
* `execute` (`base.py:342-374` @ base) — the check gate changes from
  `self.requires_system_checks and not options.get('skip_checks')` to
  `self.requires_system_checks and not options['skip_checks']` (`base.py:365`).
* `base_stealth_options` drops `'skip_checks'` (now a real parsed option, not a
  stealth one) and `DjangoHelpFormatter.show_last` gains `'--skip-checks'` — both
  cosmetic/bookkeeping consequences of `--skip-checks` becoming a real CLI option;
  they do not change the launch decision and are not separately modeled.

Lean modeled function name: `runCommand` (deliberately neutral — it names the
*behavior* "decide what happens when a command is launched", not a patched
symbol; see G-LEAK note).

| Lean symbol | Python binding (file:line @ base) |
|---|---|
| `runCommand` (modeled launch decision) | `BaseCommand.create_parser` + `BaseCommand.execute`, `base.py` |
| `commandPerformsChecks` | `self.requires_system_checks` (`base.py:240` default `True`; the gate condition `base.py:365` and the registration guard `base.py:289`) |
| `skipRequested` | whether `--skip-checks` was passed on the command line, surfaced as `options['skip_checks']` (`base.py:365`) |
| `RunResult.ranChecks` | the `self.check()` branch is taken (`base.py:366`) |
| `RunResult.skippedChecks` | `execute` proceeds to `self.handle(...)` without `self.check()` |
| `RunResult.unrecognizedOption` | argparse rejects `--skip-checks` because no such argument was registered (pre-patch behavior, or any command for which the option is not registered) |

## Lean ↔ Python type bijection (used by G-CONF and G-AX)
| Python | Lean |
|---|---|
| `self.requires_system_checks : bool` | `commandPerformsChecks : Bool` |
| `--skip-checks` present on argv (post-parse `options['skip_checks']`) | `skipRequested : Bool` |
| `self.check()` is called | `RunResult.ranChecks` |
| `self.handle()` reached without `self.check()` | `RunResult.skippedChecks` |
| argparse `error: unrecognized arguments: --skip-checks` | `RunResult.unrecognizedOption` |

### Option-registration / decision modeling note
The patch ties two things together: the option `--skip-checks` is *registered*
exactly when `requires_system_checks` is true (`base.py:289`), and the `execute`
gate reads that option to decide whether to call `check()` (`base.py:365`). The
end-to-end observable, for a command launched from the command line, is the
function of two booleans:

* `requires_system_checks = False`: no `--skip-checks` option is registered.
  * no skip on argv → `execute` skips `check()` anyway (the gate's first
    conjunct is false) → `skippedChecks`.
  * `--skip-checks` on argv → argparse rejects it as unrecognised →
    `unrecognizedOption`. (The command would never have run `check()` either way,
    but the launch fails before `execute`.)
* `requires_system_checks = True`: `--skip-checks` IS registered.
  * `--skip-checks` on argv → `options['skip_checks'] = True` → gate false →
    `skippedChecks`.
  * not on argv → `options['skip_checks'] = False` → gate true → `ranChecks`.

This is exactly `problem_spec_runCommand`. The actual execution of `self.check()`
is an UNCHANGED dependency observed only as WHETHER it is reached, so it enters as
the `ranChecks` / `skippedChecks` outcome, not as an axiomatized callee.

Note on `options.get('skip_checks')` → `options['skip_checks']`: post-patch the
key is always present (argparse stores `False` by default for the store-true
option whenever it is registered, i.e. whenever `requires_system_checks`). For a
command launched from the command line — the F2P shape — the two index forms
agree; the change to `[...]` is a tidy-up enabled by the option now always being
defined on the parsed namespace.

## Callee provenance + flag deps
- No unchanged callee is *consumed* as an axiom. `self.check()` enters as DATA:
  its only observable is whether it runs (`ranChecks` vs `skippedChecks`).
- Flag dependency: the registration of `--skip-checks` is conditioned on
  `requires_system_checks` (`base.py:289`); this is captured directly by the
  `commandPerformsChecks` guard in the impl, not by an axiom.

## G-LEAK
The problem_statement says: "Add --skip-checks option to management commands",
"Management commands already have skip_checks stealth option", "skip checks when
running a command from the command line". So the public statement itself uses
"skip checks" / "command" / "command line". The spec view names the behavior
("skip a command's pre-run checks", "offers a skip option") and never names the
patched symbols (`create_parser`, `execute`, `requires_system_checks`,
`base_stealth_options`, `DjangoHelpFormatter`) nor narrates the edit. No leaked
identifier.

## Pinned G-CONF fuzz seed
`11292`.
