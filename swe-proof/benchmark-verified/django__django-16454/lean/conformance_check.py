#!/usr/bin/env python3
"""G-CONF for django__django-16454.

The gold patch is already applied to /testbed when this runs. We compare the R/I
Python shadow of `implementation_addSubparsers` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched
`CommandParser.add_subparsers`, over >=1e5 fuzzed inputs. Zero disagreements =>
exit 0.

Model (refinement.md): `add_subparsers` decides whether a constructed sub-parser
carries the parent's `called_from_command_line` flag, and which value. Outcome
modeled as Option (Option Bool):
  * some v <-> the constructed sub-parser is a same-family CommandParser carrying
               called_from_command_line == v  (v: None<->none, bool<->some b);
  * none   <-> the constructed sub-parser is foreign (no called_from_command_line
               attribute) -- the flag does not apply.

  * Oracle = the REAL patched CommandParser.add_subparsers, driven live: build a
             parent CommandParser(called_from_command_line=parentFlag), call
             add_subparsers(parser_class=cls), construct a sub-parser via
             .add_parser("x"), then read whether the sub-parser has a
             called_from_command_line attribute and its value.
  * Shadow = (some parentFlag) if sameFamily else none.

Type bijection (mapping.md):
  sameFamily<->issubclass(parser_class, CommandParser),
  parentFlag<->self.called_from_command_line (bool|None, None<->none),
  result<->Option (Option Bool) outcome.
stdlib-only; no hypothesis required.
"""
import argparse
import random
import sys

import django
from django.conf import settings
if not settings.configured:
    settings.configure(
        DEBUG=False,
        USE_TZ=False,
        DATABASES={},
        INSTALLED_APPS=[],
        TEMPLATES=[],
    )
    django.setup()

from django.core.management.base import CommandParser


class CommandParserSubclass(CommandParser):
    """A same-family parser class (subclass of CommandParser)."""
    pass


class ForeignParser(argparse.ArgumentParser):
    """A foreign parser class that does NOT subclass CommandParser."""
    pass


_SENTINEL = object()

# (label, parser_class, is_same_family)
PARSER_CLASSES = [
    ("CommandParser", CommandParser, True),
    ("CommandParserSubclass", CommandParserSubclass, True),
    ("ArgumentParser", argparse.ArgumentParser, False),
    ("ForeignParser", ForeignParser, False),
]


def oracle(parent_flag, parser_class):
    """Outcome of the patched repo function as Option (Option Bool):
    None             -> none (foreign sub-parser: no called_from_command_line)
    ("some", value)  -> some value (same-family sub-parser carrying the flag)
    """
    parent = CommandParser(called_from_command_line=parent_flag)
    subparsers = parent.add_subparsers(parser_class=parser_class)
    sub = subparsers.add_parser("x")
    val = getattr(sub, "called_from_command_line", _SENTINEL)
    if val is _SENTINEL:
        return None
    return ("some", val)


def shadow(parent_flag, same_family):
    """R/I transliteration of implementation_addSubparsers (Lean)."""
    carried = None
    if same_family:
        carried = ("some", parent_flag)
    return carried


def main():
    rng = random.Random(16454)  # pinned seed (mapping.md)
    N = 100_000
    disagreements = 0
    first = None
    for _ in range(N):
        parent_flag = rng.choice([None, True, False])
        label, cls, same_family = rng.choice(PARSER_CLASSES)
        o = oracle(parent_flag, cls)
        s = shadow(parent_flag, same_family)
        if o != s:
            disagreements += 1
            if first is None:
                first = (parent_flag, label, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r" % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
