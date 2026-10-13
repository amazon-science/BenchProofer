# refinement.md — django__django-16454

The operation-by-operation correspondence between `model.py`'s implementation
(`open_subcommand_group` — the changed function — and `build_subcommand_parser`
— the unchanged sub-command constructor it feeds) and `patch.diff` (the gold
patch). Each step is tagged **R** (type refinement), **A** (axiomatized
callee — split into **A-consumed**, where the proof uses the axiom, and
**A-reference**, where a deep model is validated == the real callee by
axiom_check.py / G-AX), or **I** (identical concrete operation). The claim:
*any implementation that verifies against this frozen spec, refined per the map
below, is behaviourally equal to the gold patch on the tested inputs, so it
resolves.*

`patch.diff` is the gold patch **verbatim** (it applies at `base_commit` and is
the real correctness oracle, G-RESOLVE).

## A. The changed function — `CommandParser.add_subparsers` (`django/core/management/base.py:75-83` post-patch)

Gold hunk:
```python
+    def add_subparsers(self, **kwargs):
+        parser_class = kwargs.get("parser_class", type(self))
+        if issubclass(parser_class, CommandParser):
+            kwargs["parser_class"] = partial(
+                parser_class,
+                called_from_command_line=self.called_from_command_line,
+            )
+        return super().add_subparsers(**kwargs)
```

| # | model.py impl op (`open_subcommand_group`) | patch.diff op | tag | justification |
|---|---|---|---|---|
| A1 | `parent: OpeningParser`, field `error_style` | `self` (a `CommandParser`), `self.called_from_command_line` | R | `CommandParser` ↔ minimal `OpeningParser`; `called_from_command_line: Optional[bool]` ↔ `error_style: Optional[bool]` (mapping.md §2). Read-only here ⇒ required+ensured at `Acc(..., 1/2)`. |
| A2 | `parser_class_token: int` | `parser_class = kwargs.get("parser_class", type(self))` | R | the requested sub-command parser kind, an opaque token; the parent default `type(self)` is the error-aware kind (mapping.md §2). |
| A3 | `is_error_aware_kind(parser_class_token)` | `issubclass(parser_class, CommandParser)` | A-consumed | the unchanged subclass guard; weakest contract = pure & deterministic in the token (mapping.md §3.1). The proof consumes it in both postconditions (`injects_flag == is_error_aware_kind(...)`). G-AX checks the real `issubclass`. |
| A4 | `builder.injects_flag = True; builder.inherited_style = parent.error_style` (the `if` branch) | `kwargs["parser_class"] = partial(parser_class, called_from_command_line=self.called_from_command_line)` | R | the `partial` that binds `called_from_command_line=self.called_from_command_line` is the construction policy "build sub-command parsers with the flag bound to the parent's value." Its observable effect ↔ `(injects_flag=True, inherited_style=parent.error_style)` recorded on the returned action/builder (mapping.md §2). |
| A5 | `builder.injects_flag = False` (the `else` branch) | falling through with `kwargs["parser_class"]` left as the bare requested class | R | no `partial` wrap ⇒ no flag injection; the plain requested class is used as-is. ↔ `injects_flag=False`. The spec additionally pins the FRAME of this path: `Implies(not injects_flag, inherited_style is Old(inherited_style))` — the gold else-path records **no** binding of any kind (it merely falls through), so a rival that scribbles a garbage style value on the plain path is rejected (this frame clause closed the G-PANEL-1 weakness that admitted such a write). |
| A6 | `return None` (the builder is configured in place) | `return super().add_subparsers(**kwargs)` | R | `super().add_subparsers(**kwargs)` constructs and returns the `_SubParsersAction` carrying the (possibly `partial`-wrapped) `parser_class`; modelled as the side-effect of recording the policy on the `SubCommandBuilder` and the unchanged construction it triggers (step B). The generic `add_subparsers` machinery (prog/title handling) is unchanged and behaviour-irrelevant to the tested error formatting. |

## B. The unchanged sub-command constructor — `_SubParsersAction.add_parser` (CPython `Lib/argparse.py`)

This step is NOT changed by the gold patch; it is the consumer of the policy
A4/A5 set up. It is modelled to pin the END-TO-END observable (the flag a
constructed sub-command parser carries), which is what the F2P test measures.

Relevant unchanged stdlib line: `parser = self._parser_class(**kwargs)`.

| # | model.py impl op (`build_subcommand_parser`) | patch.diff / stdlib op | tag | justification |
|---|---|---|---|---|
| B1 | `if builder.injects_flag:` | `self._parser_class` is a `partial(CommandParser_family, called_from_command_line=<v>)` vs. a bare class | R | the recorded policy (mapping.md §2). |
| B2 | `child.carries_flag = True; child.error_style = builder.inherited_style` | `parser = self._parser_class(**kwargs)` with the `partial` ⇒ the new `CommandParser` is built with `called_from_command_line=<inherited v>` | R + I | the `partial` call binds the keyword; the constructed error-aware subparser stores `called_from_command_line = <inherited v>` (`CommandParser.__init__`, `base.py:57`). `is`-identity to `builder.inherited_style` is the verbatim propagation. |
| B3 | `child.carries_flag = False` (else) | `parser = self._parser_class(**kwargs)` with a bare vanilla class ⇒ no `called_from_command_line` attribute | R | a plain `argparse.ArgumentParser` neither accepts nor stores the flag; modelled as `carries_flag=False`. The untouched plain path (regression-guarded by `test_subparser_non_django_error_formatting`). The spec additionally pins the FRAME of this path: `Implies(not carries_flag, error_style is Old(error_style))` — a plain sub-command parser is built with **no** flag value written at all, so a rival that sets a bogus `error_style` on the plain path is rejected (closing the symmetric G-PANEL-1 weakness). |

The discriminating content of the change lives in A3+A4: when the requested
kind is error-aware (the default `type(self)`), the new code injects the
parent's flag (`injects_flag == is_error_aware_kind(...)` true, `inherited_style
is parent.error_style`). The pre-patch code has **no** `add_subparsers`
override, so the inherited generic version never injects;
`model_prepatch.py` reproduces that (`builder.injects_flag = False`
unconditionally) and **fails** the postcondition
`Ensures(builder.injects_flag == is_error_aware_kind(parser_class_token))` on
the error-aware branch — exactly the spec sensing the change (G-DIFF). The
downstream consequence (the constructed sub-command parser's
`called_from_command_line` selecting the human-facing error style in
`CommandParser.error`, `base.py:68-72`) is what the F2P
`test_subparser_error_formatting` observes; B2 ties the model's flag to it.

## C. No kind-3 (unexpressible-changed-op) steps

Every step above is R, A-consumed, or I. The one operation that genuinely
*changed* — opening a sub-command group so the inherited error-style flag is
propagated to constructed sub-command parsers — is modelled **deeply** (the
`open_subcommand_group` policy + the `build_subcommand_parser` consumption,
both spelled out and verified), not hidden behind an axiom about the function
under change. The only consumed axiom, `is_error_aware_kind`
(**A-consumed**, A3), covers an **unchanged** built-in guard
(`issubclass(parser_class, CommandParser)`) the new code calls; it asserts no
`Ensures`, only purity/determinism (the weakest contract). There is **no
A-reference** deep-model-vs-callee equality here: the changed behaviour is
expressed directly over the modelled fields, and `axiom_check.py` additionally
exercises the real end-to-end propagation as an extra soundness witness.

## D. verify(model) ⇒ resolved

`open_subcommand_group` verifies only if it records the injection policy
exactly tracking `is_error_aware_kind` (A3) and, when injecting, binds the
parent's flag verbatim (`inherited_style is parent.error_style`, A4);
`build_subcommand_parser` verifies only if a constructed sub-command parser
carries that exact flag (B2). By R (`CommandParser` ↔ `OpeningParser`,
`called_from_command_line` ↔ `error_style`, `partial`-binding ↔ the recorded
policy, mapping.md §2) the verified pair equals the gold
`add_subparsers` override followed by the unchanged `add_parser` on the tested
inputs; by A-consumed the real `issubclass` is the deterministic guard the
axiom stands in for (G-AX). Therefore a model satisfying this spec, refined by
the map above, is the gold patch up to type refinement and the one audited
guard — and the gold patch resolves (G-RESOLVE). The trust points are exactly
the two of PLAN §1.1: axiom soundness (G-AX) and refinement fidelity (this
document, G-EQ).
