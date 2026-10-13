# mapping.md — django__django-11749

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 350123f38c2b6217c38d70bfbd924a9ba3df1289`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and records
callee provenance + flag dependencies.

Repo file under change: `django/core/management/__init__.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `selectForwarded (options : List OptionView)` | the `parse_args += [ … for opt in parser_actions if … ]` list-comprehension inside `call_command` — `django/core/management/__init__.py:135-138` (changed body lines 135-138) | the modeled changed function: the per-option pass that decides which supplied options are forwarded to `parser.parse_args()` |
| `forwarded (a : OptionView)` | the post-patch comprehension predicate `opt.dest in options and (opt.required or opt in mutually_exclusive_required_options)` (`__init__.py:137-138` post-patch) | pure spec: forward-this-option verdict for one declared option |
| `forwardedAll (options : List OptionView)` | the comprehension applied to every action in `parser_actions`, in order, selecting those re-passed to `parse_args` | pure spec: the per-option forward verdict list |
| `OptionView.supplied` | `opt.dest in options` — the option's destination name is a key of the caller's `**options` (`__init__.py:137` post-patch) | a value for this option was supplied by the caller |
| `OptionView.individuallyRequired` | `opt.required` — the `argparse` action's own `required` flag (`__init__.py:137` PRE-patch sole predicate) | the option is required on its own |
| `OptionView.inRequiredGroup` | `opt in mutually_exclusive_required_options`, where that set is `{opt for group in parser._mutually_exclusive_groups for opt in group._group_actions if group.required}` (`__init__.py:130-134` post-patch, ADDED) | the option belongs to a mutually exclusive group that is itself `required=True` |

`forwarded` reads all three observations. The directive-5 frame point: the
pre-patch predicate read only `individuallyRequired` (and `supplied`); the
patch's behavioral content is precisely that membership of a *required* mutually
exclusive group now also forces forwarding. A wrong impl that ignores
`inRequiredGroup` (the true pre-patch) cannot satisfy the frozen spec (G-DIFF,
`Solution_prepatch.lean`).

Repo facts NOT modeled (they precede / follow the modeled comprehension and are
unchanged by the patch — refinement audit only, not the consumer spec view):
the `opt_mapping` / `arg_options` key remapping (`__init__.py:115-120`); the
`get_actions` flattening of sub-parser actions (`__init__.py:123-132`, used to
build `parser_actions` — unchanged); the formatting `'{}={}'.format(min(opt.
option_strings), arg_options[opt.dest])` of each forwarded option
(`__init__.py:136`, unchanged); the subsequent `parser.parse_args(...)`,
unknown-option check, and `command.execute(...)`. None of these touch the
*which-options-are-forwarded* predicate the patch changes.

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo facts. A wrong entry surfaces as spurious G-CONF
disagreements.

| repo reality | Lean carrier | bijection |
|---|---|---|
| one declared `argparse` action + the call's `options`/groups | `OptionView` | a record of the three observations the predicate reads (below) |
| `opt.dest in options` | `supplied : Bool` | Python truthiness ↔ `Bool` |
| `opt.required` | `individuallyRequired : Bool` | Python truthiness ↔ `Bool` |
| `opt in mutually_exclusive_required_options` | `inRequiredGroup : Bool` | Python membership truth ↔ `Bool` |
| "this option is appended to `parse_args` (forwarded for re-parsing)" vs "omitted" | the `Bool` verdict (`true` = forwarded) | the comprehension keeps exactly the options whose predicate is true; `true ↔ appended`, `false ↔ skipped` |
| the whole comprehension result (`parser_actions` order) | `List Bool` | per-option verdict, in action order |

Only *which* options are forwarded is modeled; the formatted `name=value`
string each forwarded option becomes (`'{}={}'.format(...)`) is an unchanged
op (refinement.md A4) outside the predicate the patch edits, so it is not in the
carrier — G-CONF compares the boolean keep-mask, which is what the patch
changes.

## 3. Callee provenance

**No axioms and no deep-model A-references.** The patch's behavioral content is
pure control flow over three already-computed observations of one declared
option (whether its dest was supplied, whether it is individually required, and
whether it is a member of a required mutually exclusive group). It calls no
library function whose contract the proof must assume: the construction of the
`mutually_exclusive_required_options` set (`parser._mutually_exclusive_groups`,
`group._group_actions`, `group.required`) and the membership/`dest in options`
tests all execute to produce those observations, which the model takes as free
inputs. There is therefore nothing for G-AX to check; `axiom_check.py` is a
`status=skip` stub and `meta.json axioms = []`, `deep_model_references = []`.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`11749`** so the
consumer-side verdict is reproducible. The shadow transliterates `forwarded`
(the R/I op); the oracle is the patched comprehension predicate run against
**real `argparse` parsers** built with randomized declared options, mutually
exclusive groups (required and optional), and supplied-key sets — including the
F2P scenario (a required mutually exclusive group whose member's `dest` is
supplied). Both sides range over the full `(supplied, individuallyRequired,
inRequiredGroup)` Boolean matrix plus fuzzed parsers.
