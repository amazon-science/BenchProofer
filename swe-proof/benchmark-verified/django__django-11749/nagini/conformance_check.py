#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11749 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls stripped (Requires/Ensures/Invariant/Assert removed) and the @Pure
helpers `supplied` / `mandatory` / `in_mandated_set` copied over as plain
functions. The carrier is a plain List[int]; no PSeq appears in the impl
region, so no sequence shim is needed. There are no @ContractOnly callees.

ORACLE: the REAL patched repo code the model models per mapping.md — the
selection inside `django.core.management.call_command` that decides which
caller-supplied keyword options are threaded through the option parser before
defaults are computed. The gate applies patch.diff to /testbed before this
script runs; PYTHONPATH=/testbed makes the patched code importable.

Type bridge (mapping.md section 2): each declared option is an int packing
three independent boolean facts in its low bits. For every fuzzed encoding
list the oracle builds a REAL command whose parser declares one option per
encoding, realizing each fact through the real argparse structures the
selection reads:

  * bit 0 ("the caller supplied this option") — the option's destination name
    is included in the keyword options passed to call_command;
  * bit 1 ("individually mandatory") — the option is declared required;
  * bit 2 ("member of a mandated set of alternatives") — the option is placed
    in a mutually-exclusive group declared with required=True. argparse's
    public API rejects an individually-required member inside such a group,
    so the (bit1 and bit2) combination — which the model's domain includes —
    is realized by setting the action's `required` attribute after insertion;
    the selection under test only ever reads that attribute and the group
    structure, so this is a faithful realization of the encoded facts.

The observable is which option values are threaded through the parser, in
declaration order. The oracle captures it at the exact modeled site: the
command's parser has its parse_args wrapped by a spy that records the
argument list it receives and then aborts call_command (nothing after the
recorded call is part of the modeled behavior, and aborting keeps inputs in
the model's full domain, e.g. a mandatory option the caller did not supply
would otherwise error out later during actual parsing). Each recorded entry
is 'flag=value'; mapping the flag back to its declaration index recovers the
real forwarded sub-list, which is compared (order and multiplicity) against
the shadow's output. Each option's caller value is unique per index, and the
value observed in the recorded entry is checked to be that caller value.

Built-in options the command base class always declares (help, verbosity,
settings module, etc.) are present in the real parser during every run; none
is individually required, none sits in a required alternatives group, and the
caller never supplies them, so they are inert under the selection on both
sides — the fuzzed options are the entire forwarded candidate set.

Input domain (the model's Requires): any list of ints. Boundary cases cover
the empty list, all 8 single-encoding lists, all 64 pairs, all 512 triples,
the full-alphabet list, and encodings outside 0..7 (high bits and negatives,
decoded by the same bit predicates on both sides). Fuzz draws lists of length
0..6 with elements mostly in 0..7 plus occasional out-of-range ints.

>= 1e5 Requires-satisfying inputs: 585+ boundary + 100000 fuzz lists.
Pinned fuzz seed: 11749.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 11749
N_FUZZ = 100_000


# --- pure helpers from model.py, decorators + docstring contracts stripped ---

def supplied(a):
    return a % 2 == 1


def mandatory(a):
    return (a // 2) % 2 == 1


def in_mandated_set(a):
    return (a // 4) % 2 == 1


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def select_forwarded(actions):
    result = []
    i = len(actions)
    while i > 0:
        a = actions[i - 1]
        if supplied(a) and (mandatory(a) or in_mandated_set(a)):
            result = [a] + result
        i = i - 1
    return result


# --- oracle: observe the real selection inside the patched call_command ------

class _Abort(Exception):
    """Raised by the parse_args spy to stop call_command right after the
    modeled selection has produced its observable."""


def make_probe_command(BaseCommand, encodings, recorder):
    class ProbeCommand(BaseCommand):
        help = "conformance probe"

        def add_arguments(self, parser):
            for k, a in enumerate(encodings):
                flag = "--o%03d" % k
                if in_mandated_set(a):
                    grp = parser.add_mutually_exclusive_group(required=True)
                    action = grp.add_argument(flag)
                    if mandatory(a):
                        # realize the individually-mandatory fact for a group
                        # member (the public API forbids declaring it so)
                        action.required = True
                elif mandatory(a):
                    parser.add_argument(flag, required=True)
                else:
                    parser.add_argument(flag)

        def create_parser(self, *args, **kwargs):
            parser = super().create_parser(*args, **kwargs)

            def spy(args=None, namespace=None):
                recorder.append(list(args) if args is not None else None)
                raise _Abort()

            parser.parse_args = spy
            return parser

        def handle(self, *args, **options):
            pass

    return ProbeCommand()


def real_forwarded(call_command, BaseCommand, encodings):
    """Run the REAL patched call_command on a command realizing `encodings`
    and return the forwarded sub-list as encodings (declaration order), or a
    string describing an in-oracle anomaly."""
    recorder = []
    cmd = make_probe_command(BaseCommand, encodings, recorder)
    kwargs = {"o%03d" % k: "v%d" % k
              for k, a in enumerate(encodings) if supplied(a)}
    try:
        call_command(cmd, **kwargs)
    except _Abort:
        pass
    if len(recorder) != 1 or recorder[0] is None:
        return "parse_args not observed exactly once: %r" % (recorder,)
    out = []
    for entry in recorder[0]:
        name, sep, value = entry.partition("=")
        if sep != "=" or not name.startswith("--o"):
            return "unexpected threaded entry: %r" % (entry,)
        k = int(name[3:])
        if value != "v%d" % k:
            return "threaded value mismatch at index %d: %r" % (k, entry)
        out.append(encodings[k])
    return out


def check_case(call_command, BaseCommand, encodings):
    shadow_out = select_forwarded(list(encodings))
    real_out = real_forwarded(call_command, BaseCommand, encodings)
    if shadow_out != real_out:
        return ("DISAGREEMENT\n  actions=%r\n  shadow=%r\n  real=%r"
                % (list(encodings), shadow_out, real_out))
    return None


def boundary_cases():
    cases = [[]]
    cases += [[a] for a in range(8)]
    cases += [[a, b] for a in range(8) for b in range(8)]
    cases += [[a, b, c] for a in range(8) for b in range(8) for c in range(8)]
    cases.append(list(range(8)))
    cases.append(list(reversed(range(8))))
    # out-of-range encodings: high bits and negatives decode via the same
    # bit predicates on both sides
    cases += [[8], [9], [15], [13], [12, 5, 9], [-1], [-3, 5], [1000001, 6]]
    return cases


def rand_case(rng):
    n = rng.randint(0, 6)
    out = []
    for _ in range(n):
        r = rng.randint(0, 19)
        if r < 16:
            out.append(r % 8)
        elif r < 18:
            out.append(rng.randint(8, 10 ** 6))
        else:
            out.append(rng.randint(-100, -1))
    return out


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        django.setup()
    from django.core.management import call_command
    from django.core.management.base import BaseCommand

    n_boundary = 0
    checked = 0
    for encodings in boundary_cases():
        err = check_case(call_command, BaseCommand, encodings)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        encodings = rand_case(rng)
        err = check_case(call_command, BaseCommand, encodings)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real forwarded selection on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
