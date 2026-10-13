# mapping.md — django__django-16454

## Instance
- repo: django/django
- base_commit: 1250483ebf73f7a82ff820b94092c63ce4238264
- spec_provenance: cold (derived from problem_statement + gold patch + base-commit
  source only)

## The logical change
`CommandParser` (django/core/management/base.py:45) is a subclass of
`argparse.ArgumentParser` that takes an extra construction keyword,
`called_from_command_line`, which governs how `CommandParser.error` reports a bad
argument: when truthy it prints a concise usage message and exits; when falsy it
raises a `CommandError` (so the message is surfaced as an exception with a
traceback).

A parser can spawn nested sub-parsers via `add_subparsers().add_parser(name)`.
At `base_commit`, `CommandParser` did NOT override `add_subparsers`, so the
inherited `argparse.ArgumentParser.add_subparsers` constructed each sub-parser
WITHOUT the `called_from_command_line` keyword. Same-family sub-parsers
(`CommandParser` instances) thus defaulted `called_from_command_line` to `None`,
losing the parent's value — so an argument error inside a sub-command surfaced as
a traceback instead of a usage message.

The fix adds an override:
```python
    def add_subparsers(self, **kwargs):
        parser_class = kwargs.get("parser_class", type(self))
        if issubclass(parser_class, CommandParser):
            kwargs["parser_class"] = partial(
                parser_class,
                called_from_command_line=self.called_from_command_line,
            )
        return super().add_subparsers(**kwargs)
```
When the requested sub-parser class is itself a `CommandParser` (same family), it
is wrapped with `functools.partial` so each constructed sub-parser receives the
parent's `called_from_command_line`. When the class is foreign (does NOT subclass
`CommandParser`, e.g. a plain `argparse.ArgumentParser`), it is left untouched —
the flag concept does not apply to it.

## Symbol binding
| Lean symbol | Python source @ base_commit |
|---|---|
| `implementation_addSubparsers` | `CommandParser.add_subparsers` (added by gold patch at django/core/management/base.py:75-83) — specifically the per-sub-parser flag-propagation decision |
| `problem_spec_addSubparsers` | the post-condition this decision must satisfy |

## Type bijection (Lean ↔ Python) — used by G-CONF
| Lean | Python | notes |
|---|---|---|
| `sameFamily : Bool` | `issubclass(parser_class, CommandParser)` | `true ↔` requested sub-parser class is the same family that recognises the flag; `false ↔` a foreign class |
| `parentFlag : Option Bool` | `self.called_from_command_line` | `none ↔ None` (flag unset), `some b ↔ b` (concrete `True`/`False`) |
| result `: Option (Option Bool)` | observable sub-parser flag | `some v ↔` a constructed sub-parser whose `called_from_command_line == v` (a same-family sub-parser carrying the flag); `none ↔` the constructed sub-parser is foreign and has NO `called_from_command_line` attribute (flag does not apply) |

`Option Bool ↔ (bool | None)`: `called_from_command_line` is set to a bool by
`run_from_argv` / `create_parser` (django/core/management/base.py:294,393) or
defaults to `None` when never set. The outer `Option` on the result encodes the
same-family vs foreign branch.

## Callee provenance / flag deps
- No unchanged repo callee is consumed as an axiom. The propagation decision is a
  pure computation over `(issubclass(parser_class, CommandParser),
  self.called_from_command_line)`. The downstream `super().add_subparsers(**kwargs)`
  call (the inherited argparse machinery that materialises the sub-parser action
  and constructs sub-parser objects) is UNCHANGED by the fix and is abstracted to
  "the flag value the constructed sub-parser carries"; it is not modeled or
  axiomatized. `axiom_check.py` is a skip stub.
- The `issubclass(parser_class, CommandParser)` family test is modeled DEEPLY as
  the boolean input `sameFamily` (no axiom): G-CONF exercises it directly against
  the real `issubclass` over both same-family and foreign parser classes.

## G-CONF fuzz seed
- pinned seed: `16454` (see conformance_check.py `random.Random(16454)`).
