# mapping.md — django__django-16454

Binds every `model.py` symbol to its repository counterpart at
`base_commit = 1250483ebf73f7a82ff820b94092c63ce4238264`, states the type
abstraction, and gives the provenance of the one axiom (callee source + the
exact behaviour the axiom encodes).

Repo file under change: `django/core/management/base.py`.

## 1. Symbol ↔ repo binding

| model.py symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `open_subcommand_group(parent, builder, parser_class_token)` | `CommandParser.add_subparsers(self, **kwargs)` — added at `django/core/management/base.py:75` post-patch (overrides `argparse.ArgumentParser.add_subparsers`) | the modeled CHANGED function (opens a sub-command group and configures the sub-command-parser construction policy) |
| `build_subcommand_parser(builder, child)` | `argparse._SubParsersAction.add_parser(self, name, **kwargs)` — CPython stdlib `Lib/argparse.py`; specifically its `parser = self._parser_class(**kwargs)` step | the UNCHANGED callee that constructs one sub-command parser from the recorded factory; observes the propagated flag |
| `is_error_aware_kind(parser_class_token)` *(axiom — A-consumed)* | `issubclass(parser_class, CommandParser)` — `django/core/management/base.py:81` post-patch | unchanged runtime subclass test deciding whether the requested sub-command parser kind is the error-aware `CommandParser` family |
| `OpeningParser.error_style` | `CommandParser.called_from_command_line` — set in `CommandParser.__init__` (`base.py:54,57`); read in `CommandParser.error` (`base.py:68-72`) | the per-parser error-style flag (the touched field of the parent) |
| `SubCommandBuilder.injects_flag` / `.inherited_style` | the post-patch `kwargs["parser_class"] = partial(parser_class, called_from_command_line=self.called_from_command_line)` decision + bound value (`base.py:78-80`), carried into the returned `_SubParsersAction` and consumed by `add_parser` | the construction policy recorded on the sub-command builder |
| `SubCommandParser.carries_flag` / `.error_style` | the constructed sub-command parser's `called_from_command_line` (present and set when `parser_class` is `CommandParser`-family; absent for a vanilla `argparse.ArgumentParser`) | the touched field of a constructed sub-command parser |

The pre-patch state (for the refinement audit, not referenced from the consumer
spec view): `CommandParser` has **no** `add_subparsers` override, so the
inherited `argparse.ArgumentParser.add_subparsers` runs, which does
`kwargs.setdefault('parser_class', type(self))` and stores the bare class on
`_SubParsersAction._parser_class`; `add_parser` then calls
`self._parser_class(**kwargs)` with no `called_from_command_line`, so the
sub-command `CommandParser` is built with the constructor default
`called_from_command_line=None`.

## 2. Type abstraction (R-refinements)

| repo reality | model carrier | bijection |
|---|---|---|
| `CommandParser` (the parent) | `OpeningParser` class with only the touched field `error_style` | `parent.error_style` ↔ `self.called_from_command_line` |
| `called_from_command_line` value (`None` default / `True` set by `run_from_argv` / `False`) | `Optional[bool]` (`None` / `True` / `False`) | identity on the three observable settings; `is` identity used in the spec to forbid coercion |
| the returned `_SubParsersAction` | `SubCommandBuilder` class with the touched policy fields | the post-patch `parser_class` kwarg (a bare class vs. a `partial(..., called_from_command_line=...)`) ↔ `(injects_flag, inherited_style)`: a `partial` that binds the flag ↔ `injects_flag=True, inherited_style=<bound value>`; a bare class ↔ `injects_flag=False` |
| a constructed sub-command parser | `SubCommandParser` class with `carries_flag` + `error_style` | a `CommandParser`-family subparser ↔ `carries_flag=True`, `error_style=<its called_from_command_line>`; a vanilla `argparse.ArgumentParser` subparser (no such attribute) ↔ `carries_flag=False` |
| the requested `parser_class` (a type object) | `parser_class_token: int` | opaque token identifying the requested kind; only `is_error_aware_kind(token)` (the subclass test) is observed |
| `**kwargs` / keyword defaults | explicit positional params | `kwargs.get("parser_class", type(self))` ↔ `parser_class_token`; the parent default `type(self)` is the error-aware kind |

`partial(parser_class, called_from_command_line=...)` is modelled as the policy
that the later `parser_class(**kwargs)` call (in `add_parser`) is invoked with
the bound `called_from_command_line` value — i.e. `build_subcommand_parser`
constructs `child` carrying `builder.inherited_style`. This is exactly the
observable effect of `partial`: a deferred call with the extra keyword bound.

## 3. Callee provenance (kind-A — checked by G-AX / axiom_check.py)

### 3.1 `is_error_aware_kind` ↔ `issubclass(parser_class, CommandParser)` (A-consumed)
**Callee:** the built-in `issubclass(parser_class, CommandParser)` test
(`base.py:81` post-patch). The axiom encodes only what the proof needs: the
test is a **pure deterministic predicate** of the requested parser-class kind
(same kind ⇒ same boolean). No `Ensures` clause is asserted (the weakest
possible contract); the model relies solely on determinism, which Nagini gives
for a `@Pure` function. There is no claim about which classes are/aren't
subclasses — only that the answer is a function of the input token.

**Why this is the changed function's CALLEE, not the changed op:** the changed
operation is the *decision to wrap* `parser_class` with a flag-binding
`partial` and propagate the parent flag (modelled deeply in
`open_subcommand_group` + `build_subcommand_parser`). `issubclass(...,
CommandParser)` is an unchanged guard the new code calls; it is the only
axiomatized callee.

**Soundness check (G-AX):** `axiom_check.py` constructs real parser-class
tokens — `CommandParser`, subclasses of `CommandParser`, plain
`argparse.ArgumentParser`, and unrelated classes — and asserts
`issubclass(cls, CommandParser)` is deterministic (idempotent across repeated
evaluation) and agrees with the model's two-valued usage (error-aware vs not).
It also exercises the **end-to-end** behaviour the patch targets: it builds a
real `CommandParser`, calls `add_subparsers()` then `add_parser(...)`, and
asserts the constructed sub-command parser's `called_from_command_line` equals
the parent's (the `injects_flag`/`inherited_style` propagation), and that a
`parser_class=argparse.ArgumentParser` sub-command parser has no such attribute
(the untouched plain path). It imports only stdlib `argparse` + the Django
module the patch edits. Exit 0 iff sound.
