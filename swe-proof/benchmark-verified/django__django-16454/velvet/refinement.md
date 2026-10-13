# refinement.md — django__django-16454

Operation-by-operation correspondence between `Solution.lean`'s impl region (the
`nestedParserErrorConfig` `do` block and the deep `inheritedErrorConfig` model)
and `patch.diff` (the gold patch). Each step is tagged **R** (type refinement),
**A** (axiomatized callee — A-consumed / A-reference), or **I** (identical
concrete op).

The R/I legs are mechanically refuted by **G-CONF** (`conformance_check.py`,
§4.1); the A legs and this narrative are audited by **G-EQ**. Claim: any impl
verifying against this frozen spec, refined per the map below, is behaviourally
equal to the gold patch on the tested inputs, so it resolves.

`patch.diff` is the gold patch **verbatim** (G-RESOLVE).

## A. The change site — `CommandParser.add_subparsers()` (`django/core/management/base.py:75` post-patch)

Gold hunk (the added method + its `from functools import partial` import):
```
+    def add_subparsers(self, **kwargs):
+        parser_class = kwargs.get("parser_class", type(self))
+        if issubclass(parser_class, CommandParser):
+            kwargs["parser_class"] = partial(
+                parser_class,
+                called_from_command_line=self.called_from_command_line,
+            )
+        return super().add_subparsers(**kwargs)
```

| # | Solution.lean impl op (`nestedParserErrorConfig`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | input `config : Option Bool` | `self.called_from_command_line` (tri-state) | R | `None/True/False ↔ none/some true/some false` (mapping.md §2). G-CONF bridges. |
| A2 | input `nestedAcceptsConfig : Bool` | `issubclass(parser_class, CommandParser)` where `parser_class = kwargs.get("parser_class", type(self))` | R | the kind-compatibility predicate ↔ `Bool` (mapping.md §2). G-CONF computes the real `issubclass` over both branches (default `type(self)` ⇒ `True`; an explicit non-`CommandParser` `parser_class` ⇒ `False`). |
| A3 | `if nestedAcceptsConfig then return config else return none` — i.e. `out = inheritedErrorConfig nestedAcceptsConfig config` | the `if issubclass(...)` guard that rebinds `kwargs["parser_class"] = partial(parser_class, called_from_command_line=self.called_from_command_line)`, leaving `kwargs` untouched otherwise; the observable result is the `called_from_command_line` the constructed nested parser carries | I | identical control/data flow: when the kind is compatible the parent's config is threaded into the constructed nested parser (`config`); when not, the nested parser is left with the unset config (`none` — a non-`CommandParser` kind has no such attribute, defaulting to `None`). Modeled deeply by `inheritedErrorConfig`; the `partial`/`super().add_subparsers` mechanism is the construction vehicle, observationally captured by the threaded config value (mapping.md §2 "Note on `partial`"). |

Discriminating content of the change — a compatible nested parser receives the
parent's configuration rather than the unset configuration. The pre-patch had no
`add_subparsers` override, so the nested parser's `called_from_command_line` was
always `None` (`none`); `Solution_prepatch.lean` reproduces that (`return none`)
and **fails** `out = inheritedErrorConfig nestedAcceptsConfig config` exactly
when `nestedAcceptsConfig` holds and `config ≠ none` (G-DIFF). This is the bug
the F2P `test_subparser_error_formatting` observes: the Django-kind subparser
(`subparser`) must inherit the command-line error formatting, so a bad argument
produces a one-line usage error rather than a stack trace.

## B. The non-Django subparser path (F2P `test_subparser_non_django_error_formatting`)

This second F2P test passes `parser_class=argparse.ArgumentParser` (a
non-`CommandParser` kind) ⇒ `issubclass(parser_class, CommandParser)` is
`False` ⇒ `nestedAcceptsConfig = false` ⇒ `inheritedErrorConfig = none`: the
patch leaves `kwargs` untouched and the vanilla `argparse.ArgumentParser`
subparser is created with no Django config. This is the `else` leg of A3; it is
not a separately-fixed behaviour (the spec stays byte-identical, G-DIFF), and it
is the same `else` branch the prepatch's `return none` happens to get right — the
prepatch only diverges on the compatible branch (§A).

## C. No kind-3 (inexpressible-changed-op) steps

Every step is R or I. There are no axioms (A) at all. The operation that
genuinely changed — propagating the parent's error-presentation configuration
into compatible nested parsers — is modeled **deeply** as the closed function
`inheritedErrorConfig`, not hidden behind an axiom about the function under
change. The `issubclass` kind test and the `called_from_command_line` value are
abstracted to typed inputs (R), validated against the real classes by G-CONF.

## D. verify(Solution) ⇒ resolved

`nestedParserErrorConfig` verifies only if its output equals
`inheritedErrorConfig nestedAcceptsConfig config` — the parent's config on the
compatible branch (A3), unset otherwise. By R (`Option Bool ↔
None/True/False`, `Bool ↔ issubclass`) the verified decision equals the
constructed nested parser's `called_from_command_line` on every input; by G-CONF
the R/I transliteration of `inheritedErrorConfig` agrees with the patched
`add_subparsers` behaviour over the full boundary cross-product + fuzz.
Therefore a model satisfying this spec, refined by the map above, is the gold
patch up to type refinement — and the gold patch resolves (G-RESOLVE). There are
no axiom trust points (plan §1.1 trust point #1 is vacuous here); the residual
trust is only the type bijection (mapping.md §2), which G-CONF makes falsifiable.
