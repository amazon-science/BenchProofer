#!/usr/bin/env python3
"""G-AX soundness check for django__django-12858 — NO AXIOMS (status=skip).

This bundle axiomatizes nothing. The four schema accessors the modeled walk is
parameterized over (`lookup` = `Options.get_field`, `aliasField` = `Options.pk`,
`hasTransform` = `Field.get_transform`, `hasLookup` = `Field.get_lookup`) are
taken as FREE INPUTS: the spec makes no behavioural claim about any of them and
holds for EVERY schema (mapping.md §2/§3). There is therefore no axiom `ensures`
to falsify against a real callee, so G-AX is a no-op.

`meta.json` records `gates."G-AX".status = "skip"`. This script exists so the
orchestrator's batch runner finds a uniform entry point; it prints a skip
sentinel and exits with a distinguished code the runner maps to `skip`.
"""
import sys

# Be robust to an ASCII-only container stdout: emit UTF-8 (and never crash on a
# stray non-ASCII byte in a status line). The skip message below is ASCII-only
# regardless, so this is belt-and-suspenders.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="backslashreplace")
except Exception:
    pass


def main():
    print("G-AX SKIP: no axioms in django__django-12858 "
          "(schema accessors are free inputs; nothing to check against a real "
          "callee). See mapping.md sec.3 / refinement.md.")
    # Exit 0: there is nothing unsound to find. The runner treats the SKIP
    # sentinel (and meta.json gates.G-AX.status=skip) as "not applicable".
    return 0


if __name__ == "__main__":
    sys.exit(main())
