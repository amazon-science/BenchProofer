# mapping.md — django__django-11292

Binds every `model.py` symbol to its repository counterpart at
`base_commit = eb16c7260e573ec513d84cb586d96bdf508f3173`, states the type
abstraction, and gives the provenance of the argparse semantics the deep model
is validated against (G-AX / axiom_check.py). There are NO consumed axioms.

Repo file under change: `django/core/management/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `parser_offers_skip(requires_validation)` | the skip-option registration in `BaseCommand.create_parser` — the guarded `if self.requires_system_checks: parser.add_argument('--skip-checks', action='store_true', ...)` hunk (`django/core/management/base.py:289`, post-patch) | the modeled changed site (1): whether the invocation parser offers/accepts the skip request |
| `will_run_validation(requires_validation, requested_skip)` | the validation gate in `BaseCommand.execute` — `if self.requires_system_checks and not options['skip_checks']: self.check()` (`django/core/management/base.py:360`) | the modeled changed site (2): the run/skip decision the whole change exists to affect |
| `skip_request_offered(requires_validation)` *(pure spec)* | the abstract notion behind the `create_parser` guard `if self.requires_system_checks:` | pure spec helper: the skip request is offered iff validation required |
| `effective_skip(requires_validation, requested_skip)` *(pure spec)* | the value `options['skip_checks']` ends up holding for a validating command vs. its absence/default for a non-validating one (argparse `store_true` semantics) | pure spec helper: a request takes effect only when the parser offered it |
| `requires_validation` (bool param) | `BaseCommand.requires_system_checks` class attribute (`django/core/management/base.py:223`) | command-level flag: does this command perform validation |
| `requested_skip` (bool param) | the `--skip-checks` token present on the command line (→ `options['skip_checks'] is True`) | invocation-level input: did the user ask to skip |

Pre-patch repo symbols the change touches (for the refinement audit, not in the
consumer spec view):
- `DjangoHelpFormatter.show_last` set (`base.py:96-99`): `--skip-checks` is added
  so the new option sorts after command-specific args in `--help`. Cosmetic
  (ordering only); it does NOT affect the run/skip decision and is not modeled.
- `BaseCommand.base_stealth_options` (`base.py:226`): `'skip_checks'` is removed
  from the stealth-option tuple because `--skip-checks` is now a real parser
  option rather than a `call_command`-only stealth kwarg. Bookkeeping; it does
  not affect the decision and is not modeled.
- `execute`'s gate read changes `options.get('skip_checks')` →
  `options['skip_checks']` (`base.py:360`): observationally identical given that
  the `store_true` key is now always present for a validating command (R2 in
  axiom_check.py); modeled as the same boolean read.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `self.requires_system_checks` (a class-attribute bool) | `requires_validation: bool` | identity on booleans |
| `--skip-checks` token present on the command line | `requested_skip: bool` | token present ↔ `requested_skip == True`; for a validating command this equals `options['skip_checks']` (argparse `store_true`) |
| `options['skip_checks']` (the parsed namespace value) | `effective_skip(requires_validation, requested_skip)` | for a validating command the namespace carries the user's request; for a non-validating command the option is not registered, so no request is in force (modeled as `False`) |
| `self.check()` is invoked | `Result() == True` of `will_run_validation` | the gate's then-branch ↔ the decision being True |
| `parser.add_argument('--skip-checks', ...)` is reached | `parser_offers_skip(...) == True` | the option is registered ↔ the parser offers the request |

`argparse` rejects an unregistered token (`SystemExit`), so a `--skip-checks`
supplied to a non-validating command is NOT silently honoured — it has no
effect, matching `effective_skip(..) == False` when not offered.

## 3. Callee / library-semantics provenance (A-reference — checked by G-AX)

No `@ContractOnly` axiom is consumed. The deep model rests on two semantic facts
about the standard-library argument parser the gold patch builds on
(`argparse`, which Django's `CommandParser` subclasses unchanged). These are
the A-reference obligations validated by `axiom_check.py` against the REAL
`argparse` (stdlib-only import):

### 3.1 Skip-option exposure ↔ the `create_parser` guard (A-reference for `parser_offers_skip`)
**Callee:** `argparse.ArgumentParser.add_argument` / `parse_args`. The gold
`create_parser` registers `--skip-checks` (`action='store_true'`) **iff**
`self.requires_system_checks`. A parser built that way exposes `skip_checks` in
its parsed namespace exactly when the option was registered; an unregistered
`--skip-checks` token is rejected (`SystemExit`). Hence
`parser_offers_skip(requires_validation) == requires_validation`.
Source: gold hunk `django/core/management/base.py:289-294`; CPython
`Lib/argparse.py` (`store_true` action, `parse_args`); docs
https://docs.python.org/3/library/argparse.html#action (`'store_true'`).

### 3.2 `store_true` default + always-present ↔ the `execute` gate read (A-reference for `effective_skip`/the gate)
**Callee:** `argparse` `store_true` semantics. Once registered, the option's
attribute is ALWAYS present in the parsed namespace: `False` when the token is
absent, `True` when present. This is exactly why the gold `execute` switches
from `options.get('skip_checks')` to `options['skip_checks']` (the key is now
always present for a validating command) and why the gate boolean
`requires_system_checks and not options['skip_checks']` is reproduced by
`will_run_validation`'s `requires_validation and not effective_skip(..)`.

**Soundness check (G-AX):** `axiom_check.py` builds a real `argparse` parser by
mirroring the gold `create_parser` guard, then asserts: (a) `skip_checks` is in
the parsed namespace iff `requires_validation` (R1); (b) a `store_true` option
defaults to `False` when its token is absent and a non-validating command
rejects the token (R2); and (c) the real end-to-end gate decision
(`requires_system_checks and not options['skip_checks']`) equals the model's
`will_run_validation` over the full boolean cross-product of
(requires_validation, token-present). Exit 0 iff sound. It imports only the
standard-library `argparse` — the module the gold patch builds on.
