# mapping.md — django__django-16454

Binds every `Solution.lean` symbol to its repository counterpart at
`base_commit = 1250483ebf73f7a82ff820b94092c63ce4238264`, states the type
abstraction (the bijection G-CONF uses to bridge Lean↔Python), and gives the
provenance of the (non-)axioms.

Repo file under change: `django/core/management/base.py`.

## 1. Symbol ↔ repo binding

| Solution.lean symbol | repo symbol (file:line @ base_commit) | role |
|---|---|---|
| `nestedParserErrorConfig (nestedAcceptsConfig) (config)` | `CommandParser.add_subparsers(self, **kwargs)` — added method at `django/core/management/base.py:75` (post-patch) | the modeled changed behaviour: the error-presentation configuration a freshly-spawned nested parser is constructed with |
| `inheritedErrorConfig` *(deep model — R/I)* | the body of the added `add_subparsers`: the `issubclass(...)`-guarded `kwargs["parser_class"] = partial(parser_class, called_from_command_line=self.called_from_command_line)` rebind | pure spec: the configuration value threaded into the nested parser |
| `config : Option Bool` | `self.called_from_command_line` — set in `CommandParser.__init__` at `base.py:57`; tri-state `None`/`True`/`False` | the parent parser's error-presentation configuration |
| `nestedAcceptsConfig : Bool` | `issubclass(parser_class, CommandParser)` where `parser_class = kwargs.get("parser_class", type(self))` (`base.py:76-77` post-patch) | whether the nested parser kind understands the configuration |

The pre-patch repo state the change addresses (refinement audit only, not in the
consumer spec view): `CommandParser` had **no** `add_subparsers` override, so
`argparse.ArgumentParser.add_subparsers()` was used unchanged and the nested
parsers it created received `parser_class=type(self)` with **no**
`called_from_command_line` threaded — i.e. the configuration was never
propagated (the nested parser's `called_from_command_line` defaulted to `None`).

## 2. Type abstraction (R-refinements) — the Lean↔Python bijection

This is the table G-CONF (§4.1) uses to translate values between the Lean value
domain and the Python repo types. A wrong entry surfaces as spurious G-CONF
disagreements (the falsifiability the plan §4 trust statement refers to).

| repo reality | Lean carrier | bijection |
|---|---|---|
| `self.called_from_command_line` — the parent's config, a tri-state `None`/`True`/`False` | `Option Bool` | `None ↔ none`; `True ↔ some true`; `False ↔ some false`. This is the value that ends up as the nested parser's `called_from_command_line` (directly post-patch, or `None` pre-patch). |
| `issubclass(parser_class, CommandParser)` — whether the nested kind understands the config | `Bool` | `True ↔ true`; `False ↔ false`. `parser_class` is `kwargs.get("parser_class", type(self))`; since the modeled parent is always a `CommandParser`, the default `type(self)` is a `CommandParser` subclass, so the flag is `True` unless the caller passes a non-`CommandParser` `parser_class` (the `subparser_vanilla` F2P test path). |
| the configuration the nested parser is *constructed with* | `Option Bool` | the observable output. Post-patch: `partial(parser_class, called_from_command_line=self.called_from_command_line)` ⇒ the constructed nested parser carries `self.called_from_command_line` exactly when the kind is compatible; for a non-`CommandParser` kind `parser_class` is left untouched ⇒ that kind never had the attribute ⇒ unset (`none`). |

Note on `partial`: the gold patch threads the config by *wrapping the nested
parser class* in `functools.partial(..., called_from_command_line=...)`. The
observable consequence — the only thing the F2P test and the desired behaviour
care about — is that the nested parser, once constructed, carries the parent's
`called_from_command_line`. `inheritedErrorConfig` models that observable
consequence (the value the nested parser is built with), not the `partial`
mechanism itself.

## 3. Callee provenance (kind-A)

**None.** There are no axiomatized callees and no deep-model references to an
unchanged callee. The entire changed behaviour is a closed function of two
abstracted inputs (`nestedAcceptsConfig`, `config`) and is modeled deeply in the
`pure` region (`inheritedErrorConfig`). G-AX is therefore skipped (no
`axiom_check.py`); the abstraction of the two inputs from the real
`issubclass`/`called_from_command_line` observations is an R-refinement
validated by G-CONF, not an axiom.

`super().add_subparsers(**kwargs)` (the unchanged `argparse` call the patch
delegates to after rebinding `parser_class`) is NOT modeled: it does not affect
*which configuration the nested parser is constructed with* — it merely performs
the construction using the (possibly rebound) `parser_class`. The behaviour the
issue and the F2P test observe is entirely the `parser_class` rebind, which is
what `inheritedErrorConfig` captures.

## 4. G-CONF fuzz seed (pinned for deterministic eval — plan §4.1, §11.3)

`conformance_check.py` seeds its `random.Random` with **`16454`** so the
consumer-side verdict (§11.3) is reproducible. The R/I shadow it builds
transliterates `inheritedErrorConfig` (the R/I-tagged decision) to Python and
compares it, over the full boundary cross-product plus fuzz, against the real
patched `CommandParser.add_subparsers` behaviour: it constructs nested parsers
through the patched method and reads back the nested parser's
`called_from_command_line`. There are no A-tagged callees to leave as the real
repo callee.
