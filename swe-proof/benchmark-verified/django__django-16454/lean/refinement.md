# refinement.md — django__django-16454

Maps every operation in `implementation_addSubparsers` to its `patch.diff`
counterpart in the added `CommandParser.add_subparsers` override
(django/core/management/base.py:75-83). Tags: **R** type-refinement,
**A-consumed** proof uses a callee axiom, **A-reference** op left as the real
repo callee in G-CONF, **I** identical concrete op.

## Patch (the added override)
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

The new behavior: if the requested sub-parser class is a `CommandParser`
(same family), pre-bind `called_from_command_line=self.called_from_command_line`
so every constructed sub-parser carries the parent's flag value; otherwise leave
the foreign class untouched. The `super().add_subparsers(**kwargs)` call is the
unchanged argparse machinery.

## Modeling decision
The observable behavior is: when a sub-parser is later constructed, does it carry
the parent's `called_from_command_line`, and if so which value? We model the
outcome as `Option (Option Bool)`:
- `some v` ↔ the constructed sub-parser is a same-family `CommandParser` carrying
  `called_from_command_line == v` (`v : Option Bool`, `none`/`some b`);
- `none`  ↔ the constructed sub-parser is foreign (no `called_from_command_line`
  attribute) — the flag does not apply.

`sameFamily : Bool` is the deep model of `issubclass(parser_class,
CommandParser)`. `parentFlag : Option Bool` is `self.called_from_command_line`.
The `partial`-wrapping / `super().add_subparsers` side effect is abstracted to
"the flag value the constructed sub-parser carries" (the unchanged callee); the
spec/proof do not model `functools.partial` or argparse internals.

## Operation correspondence
| # | Lean op (`implementation_addSubparsers`) | patch.diff op | tag | note |
|---|---|---|---|---|
| 1 | `let mut carried : Option (Option Bool) := none` | foreign-class default: the sub-parser is not wrapped, so it carries no flag | I | default outcome: flag does not apply |
| 2 | `if sameFamily then …` | `if issubclass(parser_class, CommandParser):` | R | `issubclass(parser_class, CommandParser) : bool ↔ sameFamily : Bool` (deep model of the subclass test) |
| 3 | `carried := some parentFlag` | `kwargs["parser_class"] = partial(parser_class, called_from_command_line=self.called_from_command_line)` | R | the parent's flag value is pre-bound; the constructed sub-parser carries EXACTLY `parentFlag`. `self.called_from_command_line : (bool\|None) ↔ parentFlag : Option Bool`. This is the FIXED behavior. |
| 4 | `return carried` | `return super().add_subparsers(**kwargs)` constructs the sub-parser action; the resulting sub-parser's flag is `carried` | I | total outcome — never fails to produce an answer |

## R/I legs ⇒ G-CONF
Ops 2 and 3 (the family test + flag propagation, R) are the modeled change; ops
1,4 (I) are the unchanged framing. `conf_skip = false`: the impl region is
genuine R/I content. `conformance_check.py` builds the Python shadow (the
propagation decision) and differential-tests it against the REAL patched
`CommandParser.add_subparsers` — constructing a parent `CommandParser` with a
chosen `called_from_command_line`, calling `add_subparsers(parser_class=…)` with
both same-family (`CommandParser` / subclass) and foreign
(`argparse.ArgumentParser`) classes, then constructing a sub-parser via
`.add_parser("x")` and reading whether it carries `called_from_command_line` and
which value — over ≥10^5 fuzzed inputs.

## No A-consumed / A-reference row
The propagation decision calls no unchanged callee that needs a property: it is a
boolean branch plus the flag value. The `issubclass` family test is modeled
deeply (the boolean input `sameFamily`, exercised directly against real
`issubclass` in G-CONF), not axiomatized. The `partial` / `super().add_subparsers`
construction is abstracted to the carried flag value (not modeled, not
axiomatized). So `meta.json axioms = []`, `deep_model_references = []`, and
`axiom_check.py` is a skip stub.

## F2P alignment
`test_subparser_error_formatting` runs a management command with a `CommandParser`
sub-parser and an invalid sub-command argument; the FIX must report a concise
usage message (2-line stderr) rather than a traceback. This requires the
same-family sub-parser to inherit the parent's `called_from_command_line` — i.e.
the result must be `some parentFlag`, not the unset default. Pre-patch, the
inherited `add_subparsers` constructs the sub-parser WITHOUT the flag, so it
carries `none` regardless of `parentFlag` — modeled as the prepatch impl
returning `some none`, which violates the spec's `some parentFlag` clause on any
input where `parentFlag = some b` (the discriminating clause). The fixed impl
returns `some parentFlag`. `test_subparser_non_django_error_formatting` covers the
foreign-class branch (`argparse.ArgumentParser`): the sub-parser is left untouched
(`none`), which both impls and the spec agree on. `patch.diff` (gold verbatim)
makes the harness resolve.
