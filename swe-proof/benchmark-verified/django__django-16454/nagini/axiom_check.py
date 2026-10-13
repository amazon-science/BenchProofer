#!/usr/bin/env python3
"""G-AX executable soundness check for django__django-16454.

Executes the REAL callee the one axiom stands in for
(``issubclass(parser_class, CommandParser)`` — the unchanged subclass guard the
patched ``add_subparsers`` calls) on boundary + fuzz parser-class tokens, and
asserts it satisfies the model's `is_error_aware_kind` contract (a PURE,
DETERMINISTIC two-valued predicate of the requested parser-class kind — the
weakest contract, no exact-value claims).

It additionally exercises the END-TO-END behaviour the patch targets as an extra
soundness witness for the deep model (`open_subcommand_group` +
`build_subcommand_parser`): it builds a real ``CommandParser``, opens a
sub-command group, constructs sub-command parsers, and asserts that an
error-aware (``CommandParser``-family) sub-command parser inherits the parent's
``called_from_command_line`` flag verbatim, while a plain
``argparse.ArgumentParser`` sub-command parser carries no such flag. That
end-to-end check is gated on the override being present (post-patch), so the
file is sound to run before or after applying patch.diff.

Imports only stdlib ``argparse`` and the Django module the patch edits
(``django.core.management.base``) — the very module the gold patch calls.
Exit 0 iff every obligation holds.
"""
import argparse
import sys

from django.core.management.base import CommandParser


# --- the axiom under check: is_error_aware_kind <-> issubclass(.., CommandParser)

def model_is_error_aware_kind(parser_class):
    """The model's two-valued usage of the axiomatized guard."""
    return issubclass(parser_class, CommandParser)


def check_axiom_deterministic(parser_class):
    """`is_error_aware_kind` must be a PURE DETERMINISTIC predicate of the
    requested kind: repeated evaluation yields the identical boolean, and the
    result is a genuine bool."""
    first = issubclass(parser_class, CommandParser)             # real callee
    assert isinstance(first, bool), (
        "issubclass(%r, CommandParser) is not a bool: %r" % (parser_class, first))
    for _ in range(64):
        again = issubclass(parser_class, CommandParser)
        assert again is first, (
            "issubclass(%r, CommandParser) is non-deterministic: %r vs %r"
            % (parser_class, first, again))
    # the model only ever consumes the boolean of the guard; confirm agreement
    assert model_is_error_aware_kind(parser_class) is first


def main():
    # --- boundary + fuzz parser-class tokens -----------------------------
    class CmdSub(CommandParser):
        pass

    class CmdSubSub(CmdSub):
        pass

    class Unrelated:
        pass

    class VanillaSub(argparse.ArgumentParser):
        pass

    classes = [
        CommandParser,                 # the parent default kind: error-aware
        CmdSub, CmdSubSub,             # subclasses: error-aware
        argparse.ArgumentParser,       # plain: NOT error-aware
        VanillaSub,                    # plain subclass: NOT error-aware
        Unrelated, object, int, str,   # unrelated: NOT error-aware
    ]
    expected_error_aware = {
        CommandParser: True, CmdSub: True, CmdSubSub: True,
        argparse.ArgumentParser: False, VanillaSub: False,
        Unrelated: False, object: False, int: False, str: False,
    }
    for cls in classes:
        check_axiom_deterministic(cls)
        assert issubclass(cls, CommandParser) is expected_error_aware[cls], (
            "issubclass(%r, CommandParser) disagrees with expected error-aware "
            "classification" % cls)

    # --- END-TO-END witness for the deep model (post-patch only) ----------
    e2e_checked = False
    if "add_subparsers" in CommandParser.__dict__:
        # error-aware sub-command parser inherits the parent's flag verbatim,
        # for every observable flag setting.
        for parent_flag in (None, True, False):
            parent = CommandParser(
                prog="manage.py x", called_from_command_line=parent_flag
            )
            sub_action = parent.add_subparsers()                 # default kind
            child = sub_action.add_parser("foo")
            assert getattr(child, "called_from_command_line", "MISSING") == \
                parent_flag, (
                "error-aware sub-command parser did not inherit "
                "called_from_command_line=%r (got %r)"
                % (parent_flag, getattr(child, "called_from_command_line",
                                        "MISSING")))
            # a plain sub-command parser kind carries no such flag.
            parent2 = CommandParser(
                prog="manage.py y", called_from_command_line=parent_flag
            )
            sub_action2 = parent2.add_subparsers(
                parser_class=argparse.ArgumentParser
            )
            child2 = sub_action2.add_parser("bar")
            assert not hasattr(child2, "called_from_command_line"), (
                "plain (non-error-aware) sub-command parser unexpectedly "
                "carries called_from_command_line"
            )
        e2e_checked = True

    print(
        "G-AX OK: is_error_aware_kind <-> issubclass(.., CommandParser) sound "
        "and deterministic on %d boundary classes; end-to-end flag propagation "
        "witness %s"
        % (len(classes), "verified" if e2e_checked else "skipped (pre-patch)")
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
