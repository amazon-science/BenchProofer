# mapping.md — django__django-11749

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 350123f38c2b6217c38d70bfbd924a9ba3df1289`, states the type
abstraction, and records callee provenance.

Repo file under change: `django/core/management/__init__.py`.
Function under change: `call_command(command_name, *args, **options)`
(`django/core/management/__init__.py:76`), specifically the construction of the
`parse_args` additions at lines 135–138.

## 1. Symbol ↔ repo binding

| model.py symbol | repo construct (file:line @ base_commit) | role |
|---|---|---|
| `select_forwarded(actions)` | the `parse_args += [ ... for opt in parser_actions if <pred> ]` list comprehension in `call_command` (`django/core/management/__init__.py:135-138`) | the modeled changed selection: which declared options have their caller-supplied values threaded through the parser |
| `actions` (`List[int]`) | `parser_actions` (`= list(get_actions(parser))`, line 132) — the flat list of `argparse` actions of the command's parser, in declaration order | the declared options |
| `supplied(a)` | `opt.dest in options` (the original `**options` keys, after `opt_mapping`/`arg_options` normalization; line 137 / post-patch line 142) | the caller supplied a value for this option |
| `mandatory(a)` | `opt.required` (the `argparse.Action.required` attribute) | the option is individually mandatory |
| `in_mandated_set(a)` | `opt in mutually_exclusive_required_options`, where that set is `{opt for group in parser._mutually_exclusive_groups for opt in group._group_actions if group.required}` (post-patch lines 133-137) | the option is a member of a mutually-exclusive group whose `required` flag is set |
| `forward(a)` | the post-patch predicate `opt.dest in options and (opt.required or opt in mutually_exclusive_required_options)` (post-patch lines 142-145) | the forwarding predicate |
| `forwarded_seq(s)` | the whole post-patch list comprehension's membership+order semantics | pure spec: the order-preserving filter of the declared options under `forward` |

The pre-patch predicate the change replaces (for the refinement audit, not
referenced from the consumer spec view): `opt.required and opt.dest in options`
(`django/core/management/__init__.py:137`). It forwards an option only when the
option is individually mandatory, ignoring membership of a mandated set of
alternatives.

## 2. Type abstraction (R-refinements)

The changed list comprehension reads, for each `argparse` action `opt`, only
three independent boolean facts and emits, for each forwarded action, exactly
one formatted argument string `'{}={}'.format(min(opt.option_strings),
arg_options[opt.dest])`. The string-formatting and the per-action value lookup
are **identical pre- and post-patch** — only the *membership predicate* of the
forwarded set changed. The model therefore abstracts each action to the three
facts that the (changed) predicate reads, and abstracts the forwarded result to
the order-preserving sub-list of the declared options.

| repo reality | model carrier | bijection |
|---|---|---|
| an `argparse` action `opt` in `parser_actions` | one `int` `a`, `0 <= a < 8`, packing three independent booleans in distinct low bits | `supplied(a) = (a % 2 == 1)` ↔ `opt.dest in options`; `mandatory(a) = ((a // 2) % 2 == 1)` ↔ `opt.required`; `in_mandated_set(a) = ((a // 4) % 2 == 1)` ↔ `opt in mutually_exclusive_required_options`. The three facts are independent, so all eight combinations occur; the bit-packing is a faithful 1:1 encoding of the only action properties the predicate observes. |
| `parser_actions` (ordered list of actions) | `actions: List[int]` (same order) | `actions[k]` ↔ the encoding of `parser_actions[k]`; `len(actions)` ↔ `len(parser_actions)`. Declaration order preserved. |
| the appended `parse_args` entries (a list of formatted strings) | `select_forwarded(actions): List[int]` (the forwarded action encodings, in order) | each forwarded action maps to exactly one appended string `'{}={}'.format(min(opt.option_strings), arg_options[opt.dest])`; the string content is a pure function of the action and is unchanged by this patch, so the appended list of strings ↔ the list of forwarded actions order-preservingly. The behaviour the F2P test observes is *whether a given option's value is threaded through the parser*, i.e. membership of this forwarded set. |
| `parser._mutually_exclusive_groups` / `group._group_actions` / `group.required` | folded into `in_mandated_set(a)` | the post-patch set-comprehension computes, per action, the single boolean "this action is in some group whose `required` is `True`"; the model carries that boolean directly. The group structure is observed only through this per-action boolean. |

`PSeq[int]` (via `ToSeq`) carries the sequence specification; `select_forwarded`
proves its output equals the front-recursive filter `forwarded_seq` by a
backward per-element fold (one auto-unfold per declared option).

## 3. Callee provenance (kind-A)

None. The change is pure selection logic over the declared options. The
post-patch code calls no new library/utility callee whose behaviour the proof
must over-approximate: `min`, `.format`, dict membership, and the
set-comprehension over `parser._mutually_exclusive_groups` are all either
identical to the pre-patch code (`min`/`.format`/value lookup) or are folded
into the per-action boolean `in_mandated_set` (the group scan). There is
therefore no `@ContractOnly` axiom and no `axiom_check.py` (no G-AX obligation).
The three per-action facts are the real `argparse` attributes
`Action.required`, the `dest in options` test, and group membership of a
`required` mutually-exclusive group — directly observable, not axiomatized.

`argparse` reference (CPython stdlib `Lib/argparse.py`): a mutually-exclusive
group created via `parser.add_mutually_exclusive_group(required=True)` sets the
group's `required` attribute to `True` while leaving each member action's own
`required` attribute `False` (the group, not the member, is mandated). This is
exactly the configuration the F2P test
`test_mutually_exclusive_group_required_options` exercises, and the situation
the pre-patch predicate `opt.required and ...` failed to forward.
