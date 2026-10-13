#!/usr/bin/env python3
r"""G-CONF differential conformance check for django__django-16454 (plan §4.1).

Runs IN-CONTAINER with the gold patch applied (the orchestrator passes
apply_gold=True), so the ORACLE is the patched repo's real behaviour.

Refutes (does not prove) the R/I refinement legs of refinement.md by executing
both sides on the same fuzzed inputs and comparing observable outputs:

  * SHADOW  — Solution.lean's modeled decision (`inheritedErrorConfig`)
              transliterated to Python over the real repo types, via the
              mapping.md §2 bijection:
                  config             <->  self.called_from_command_line
                                          (None/True/False  <->  none/some T/some F)
                  nestedAcceptsConfig <-> issubclass(parser_class, CommandParser)
                                          where parser_class =
                                          kwargs.get("parser_class", type(self))
              There are NO A-tagged ops (no consumed axioms), so the shadow is
              pure R/I.
  * ORACLE  — `patch.diff`'s behaviour: a real patched `CommandParser` is built
              with the given `called_from_command_line`, its patched
              `add_subparsers(**kwargs)` is called, a nested parser is created
              via `.add_parser("foo")`, and the nested parser's
              `called_from_command_line` is read back (absent attribute => None,
              the unset configuration).

They must agree on every input. Exit 0 iff zero disagreements; any disagreement
is a mechanical R/I-fidelity counterexample.

No database is touched: we only build parsers in-process. stdlib + django only.
Fuzz seed pinned (mapping.md §4).
"""
import argparse
import random
import sys

SEED = 16454
N_FUZZ = 100_000


def _bootstrap_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            INSTALLED_APPS=[],
            DATABASES={},
        )
    django.setup()


# --- the R/I shadow: Solution.lean inheritedErrorConfig
#   config modeled as one of: None, True, False  (Option Bool)
#   nested_accepts_config modeled as a bool
def shadow_inherited_error_config(nested_accepts_config, config):
    if nested_accepts_config:
        return config
    return None


def main():
    _bootstrap_django()
    from django.core.management.base import CommandParser

    # A second CommandParser subclass, to exercise the "compatible nested kind"
    # branch with a kind that is NOT exactly CommandParser (issubclass still
    # True => config must still be threaded).
    class SubCommandParser(CommandParser):
        pass

    # The three parser_class candidates the desired behaviour distinguishes:
    #   - default (None passed => add_subparsers uses type(self) = CommandParser)
    #   - an explicit CommandParser subclass (still compatible)
    #   - a non-CommandParser kind (argparse.ArgumentParser; NOT compatible)
    # The F2P tests exercise the default-CommandParser path (subparser) and the
    # argparse.ArgumentParser path (subparser_vanilla).
    parser_class_candidates = [
        ("default", None, True),                          # type(self) is CommandParser
        ("commandparser", CommandParser, True),
        ("subclass", SubCommandParser, True),
        ("vanilla", argparse.ArgumentParser, False),
    ]
    config_candidates = [None, True, False]

    def oracle(config_value, parser_class):
        """patch.diff behaviour: build a real patched CommandParser, call the
        patched add_subparsers, create a nested parser, read back its config."""
        parser = CommandParser(
            prog="manage.py test",
            called_from_command_line=config_value,
        )
        kwargs = {}
        if parser_class is not None:
            kwargs["parser_class"] = parser_class
        subparsers = parser.add_subparsers(**kwargs)
        nested = subparsers.add_parser("foo")
        return getattr(nested, "called_from_command_line", None)

    def boundary_inputs():
        for cfg in config_candidates:
            for name, pc, _accepts in parser_class_candidates:
                yield (cfg, name, pc)

    rng = random.Random(SEED)

    def fuzz_inputs(n):
        yield from boundary_inputs()
        for _ in range(n):
            cfg = rng.choice(config_candidates)
            name, pc, _accepts = rng.choice(parser_class_candidates)
            yield (cfg, name, pc)

    disagreements = []
    count = 0
    for cfg, name, pc in fuzz_inputs(N_FUZZ):
        count += 1
        # nestedAcceptsConfig (R): the real issubclass over the effective class.
        effective_class = pc if pc is not None else CommandParser
        nested_accepts = issubclass(effective_class, CommandParser)
        shadow = shadow_inherited_error_config(nested_accepts, cfg)
        observed = oracle(cfg, pc)
        if shadow != observed:
            disagreements.append((cfg, name, shadow, observed))
            if len(disagreements) >= 5:
                break

    if disagreements:
        print("G-CONF FAIL: %d R/I disagreement(s) over %d inputs (seed=%d):"
              % (len(disagreements), count, SEED))
        for cfg, name, sh, obs in disagreements:
            print("  config=%r parser_class=%s shadow=%r oracle=%r"
                  % (cfg, name, sh, obs))
        return 1
    print("G-CONF OK: R/I shadow of nestedParserErrorConfig agrees with "
          "patch.diff behaviour on %d inputs (seed=%d), 0 disagreements "
          "(compatible nested kind -> parent config threaded through; "
          "non-CommandParser kind -> unset config)." % (count, SEED))
    return 0


if __name__ == "__main__":
    sys.exit(main())
