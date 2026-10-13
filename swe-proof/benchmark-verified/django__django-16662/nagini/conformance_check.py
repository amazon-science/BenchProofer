#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16662 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Assert lines carrying proof-side multiset facts) stripped. The @Pure
helper ``compkey`` copies over as a plain function. There are no @ContractOnly
callees in this bundle.

ORACLE: the REAL patched repo operation the model models per mapping.md — the
import-line ordering step inside ``MigrationWriter.as_string``
(django/db/migrations/writer.py). The gate applies patch.diff to /testbed
before this script runs. Two oracle layers, both executing real repo code:

  (A) bulk differential: the per-line ordering key is EXTRACTED FROM THE REAL
      FUNCTION AT RUNTIME — the single ``<lambda>`` code constant of the
      patched ``as_string`` code object, materialised with the writer module's
      own globals — and the real ``sorted`` runs with it over assembled
      import-statement strings. No key text is hard-coded here; the shadow is
      diffed against whatever ordering the patched code object encodes.

  (B) end-to-end grounding: the REAL ``MigrationWriter.as_string`` is run on
      real Migration objects whose serialized imports form three-line
      configurations (including the shape the issue's regression test
      observes), and the imports block of the emitted source is checked to be
      exactly the arrangement the shadow produces.

Type bridge (mapping.md section 2): each import line is the pair
(group flag in {0,1}, order-preserving int code of the module-name token).
For the bulk oracle the code is realised as a 10-digit zero-padded decimal
module name, so lexicographic string order coincides with numeric code order;
this makes every Requires-satisfying (flags, modules) input — the full domain
0 <= module < 1e9, duplicates included — directly realisable as concrete
lines. Realistic dotted module names with rank codes are exercised as well.

Input domain: exactly the model's Requires — three lines, flags[k] in {0,1},
0 <= modules[k] < 1000000000.

>= 1e5 Requires-satisfying inputs: exhaustive flag combos x boundary module
triples + realistic-name configurations + 100000 fuzz triples. Pinned fuzz
seed: 16662.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys
import types

SEED = 16662
N_FUZZ = 100000
SCALE = 1000000000  # the model's group-flag scale (model.py compkey bound)


# --- pure helper from model.py, contracts stripped ---------------------------

def compkey(is_from, module):
    return is_from * 1000000000 + module


# --- the impl region of model.py, verbatim, contract calls stripped ----------

def arrange_lines(flags, modules):
    k0 = compkey(flags[0], modules[0])
    k1 = compkey(flags[1], modules[1])
    k2 = compkey(flags[2], modules[2])
    x = k0
    y = k1
    z = k2
    if x > y:
        t = x
        x = y
        y = t
    if y > z:
        t2 = y
        y = z
        z = t2
    if x > y:
        t3 = x
        x = y
        y = t3
    res = [x, y, z]
    return res
    # (the stripped Assert lines carried only proof-side multiset facts)


# --- oracle A: the real ordering key extracted from the patched function -----

def real_key():
    """Extract the per-line ordering key from the REAL patched
    ``MigrationWriter.as_string`` code object: its single ``<lambda>`` code
    constant, materialised with the writer module's own globals. Executing
    this function IS executing the patched repo's ordering decision."""
    from django.db.migrations import writer as writer_mod
    fn = writer_mod.MigrationWriter.as_string
    code = getattr(fn, "__func__", fn).__code__
    lambdas = [c for c in code.co_consts
               if isinstance(c, types.CodeType) and c.co_name == "<lambda>"]
    if len(lambdas) != 1:
        raise AssertionError(
            "expected exactly one ordering lambda in as_string, found %d"
            % len(lambdas))
    return types.FunctionType(lambdas[0], writer_mod.__dict__)


# --- bridge: (flag, module code) <-> concrete import-statement line ----------

def make_line(flag, name):
    """Assemble the import-statement string carrying the pair (flag, name):
    a plain module import for flag 0, an object import for flag 1. The second
    whitespace token — the one the ordering reads — is the module name in
    both forms."""
    if flag:
        return "from %s import x" % name
    return "import %s" % name


def code_name(code):
    """Order-preserving realisation of an integer module code as a module
    name: 10-digit zero-padded decimal, so name_a < name_b (str) iff
    code_a < code_b (int). Total on the whole Requires range [0, 1e9)."""
    return "%010d" % code


def check_triple(key, flags, modules, names):
    """One differential observation: run the real sorted with the real
    extracted key on the three assembled lines, map each output line back to
    its compkey, and compare with the shadow's arrangement. `names[k]` must be
    an order-preserving realisation of `modules[k]`. Returns an error string
    on disagreement, else None."""
    lines = [make_line(flags[k], names[k]) for k in range(3)]
    real_sorted = sorted(lines, key=key)
    name2code = {}
    for k in range(3):
        name2code[names[k]] = modules[k]
    real_keys = []
    for ln in real_sorted:
        parts = ln.split()
        f = 1 if parts[0] == "from" else 0
        real_keys.append(compkey(f, name2code[parts[1]]))
    shadow = arrange_lines(list(flags), list(modules))
    if shadow != real_keys:
        return ("DISAGREEMENT on flags=%r modules=%r (lines %r):\n"
                "  shadow (impl region)            = %r\n"
                "  real (patched ordering, sorted) = %r\n"
                "  real sorted lines               = %r"
                % (flags, modules, lines, shadow, real_keys, real_sorted))
    return None


# --- oracle B: the real as_string end-to-end ----------------------------------

def endtoend_configs():
    """Build real Migration objects whose serialized import sets are
    three-line configurations, run the REAL MigrationWriter.as_string, and
    return (imports_block_lines, migration_description) pairs."""
    import datetime
    import time
    from django.conf import settings
    if not settings.configured:
        settings.configure(USE_TZ=False, INSTALLED_APPS=[])
    import django
    django.setup()
    from django.db import migrations, models
    from django.db.migrations.writer import MigrationWriter

    configs = []

    # Config 1: two plain module imports + one object import — the shape the
    # issue's regression test observes. A datetime-valued default serializes
    # with a plain `import datetime`; a function default from the time module
    # serializes with a plain `import time`; the writer always emits the
    # object import of its own machinery.
    mig1 = type("Migration", (migrations.Migration,), {
        "operations": [
            migrations.AddField("mymodel", "f1", models.DateTimeField(
                default=datetime.datetime(2012, 1, 1, 1, 1))),
            migrations.AddField("mymodel", "f2", models.FloatField(
                default=time.time)),
        ],
        "dependencies": [],
    })("0001_x", "testapp")
    configs.append((mig1, "two plain imports + one from-import"))

    # Config 2: one plain module import + two object imports (a swappable
    # dependency makes the writer emit a settings object import).
    mig2 = type("Migration", (migrations.Migration,), {
        "operations": [
            migrations.AddField("mymodel", "f1", models.DateTimeField(
                default=datetime.datetime(2012, 1, 1, 1, 1))),
        ],
        "dependencies": [("__setting__", "AUTH_USER_MODEL")],
    })("0001_y", "testapp")
    configs.append((mig2, "one plain import + two from-imports"))

    out = []
    for mig, desc in configs:
        src = MigrationWriter(mig, include_header=False).as_string()
        block = [ln for ln in src.splitlines()
                 if ln.startswith("import ") or ln.startswith("from ")]
        out.append((block, desc, src))
    return out


def check_endtoend():
    """Diff the shadow against the imports block the REAL as_string emits."""
    for block, desc, src in endtoend_configs():
        if len(block) != 3:
            return ("END-TO-END: expected a three-line imports block for %s, "
                    "got %r\nsource:\n%s" % (desc, block, src))
        flags = [1 if ln.split()[0] == "from" else 0 for ln in block]
        names = [ln.split()[1] for ln in block]
        # order-preserving rank code of the module names present
        rank = {}
        for r, nm in enumerate(sorted(set(names))):
            rank[nm] = r
        modules = [rank[nm] for nm in names]
        shadow = arrange_lines(flags, modules)
        emitted = [compkey(flags[k], modules[k]) for k in range(3)]
        # the real emitted order must BE the shadow's arrangement: since the
        # block is the real output order, its keys in emission order must
        # equal the shadow's arranged keys
        if emitted != shadow:
            return ("END-TO-END DISAGREEMENT (%s):\n"
                    "  real as_string imports block = %r\n"
                    "  emitted keys (in real order) = %r\n"
                    "  shadow arrangement           = %r"
                    % (desc, block, emitted, shadow))
    return None


# --- driver --------------------------------------------------------------------

def main():
    key = real_key()
    checked = 0

    # boundary: all 8 flag combos x module triples over boundary values
    # (extremes of the Requires range, adjacent values, forced duplicates)
    boundary_vals = [0, 1, 2, 499999999, 999999998, 999999999]
    n_boundary = 0
    for f0 in (0, 1):
        for f1 in (0, 1):
            for f2 in (0, 1):
                for m0 in boundary_vals:
                    for m1 in boundary_vals:
                        for m2 in boundary_vals:
                            flags = (f0, f1, f2)
                            modules = (m0, m1, m2)
                            names = [code_name(m) for m in modules]
                            err = check_triple(key, flags, modules, names)
                            if err:
                                print(err)
                                return 1
                            checked += 1
                            n_boundary += 1

    # realistic dotted module names, rank-coded (order-preserving), all flag
    # combos and all position permutations of a name triple
    import itertools
    name_pool = ["a", "abc.def", "b", "datetime", "django.conf", "django.db",
                 "time", "uuid", "zoneinfo"]
    rng = random.Random(SEED)
    for _ in range(200):
        triple = rng.sample(name_pool, 3)
        present = sorted(set(triple))
        rank = {nm: i * 7 + 3 for i, nm in enumerate(present)}
        for perm in itertools.permutations(triple):
            for f0 in (0, 1):
                for f1 in (0, 1):
                    for f2 in (0, 1):
                        flags = (f0, f1, f2)
                        modules = tuple(rank[nm] for nm in perm)
                        err = check_triple(key, flags, modules, list(perm))
                        if err:
                            print(err)
                            return 1
                        checked += 1

    # fuzz: pinned seed; module codes over the full Requires range with
    # forced duplicate mass
    for _ in range(N_FUZZ):
        flags = (rng.randint(0, 1), rng.randint(0, 1), rng.randint(0, 1))
        style = rng.randint(0, 3)
        if style == 0:
            modules = tuple(rng.randint(0, SCALE - 1) for _ in range(3))
        elif style == 1:
            modules = tuple(rng.randint(0, 5) for _ in range(3))
        elif style == 2:
            m = rng.randint(0, SCALE - 1)
            modules = (m, m, rng.randint(0, SCALE - 1))
        else:
            m = rng.randint(0, SCALE - 1)
            modules = (m, m, m)
        names = [code_name(m) for m in modules]
        err = check_triple(key, flags, modules, names)
        if err:
            print(err)
            return 1
        checked += 1

    # end-to-end grounding through the real as_string
    err = check_endtoend()
    if err:
        print(err)
        return 1
    n_e2e = 2
    checked += n_e2e

    print("G-CONF OK: shadow impl == real patched import ordering on %d "
          "inputs (%d boundary + realistic-name sweeps + %d fuzz, seed %d; "
          "+%d end-to-end as_string configs); 0 disagreements."
          % (checked, n_boundary, N_FUZZ, SEED, n_e2e))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
