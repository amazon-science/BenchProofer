#!/usr/bin/env python3
"""G-CONF differential conformance check for pallets__flask-5014 (nagini).

SHADOW: the impl region of model.py's `validate_name`, copied verbatim below
with the contract calls (Requires/Ensures/Exsures) stripped. `PSeq` is a
plain immutable-tuple shim (len / [i] / drop are all the fold uses); the
@Pure helper `contains_dot` copies over as a plain function; `ToSeq`
materialises a code-point list into the shim. The one @ContractOnly callee,
`init_base`, calls the REAL repo function it models per mapping.md section 1:
the unchanged base initialiser `flask.scaffold.Scaffold.__init__`, invoked
here by constructing a `Scaffold` directly with the same defaulted arguments
the modeled constructor passes. Any exception it raises maps to the model's
user-defined `BaseInitError` channel (mapping.md section 2: the model
observes only that the base init may fail as a unit, not the concrete
builtin exception type).

ORACLE: the REAL patched repo function the model models — the
name-validation prologue of `flask.Blueprint.__init__`
(src/flask/blueprints.py, per mapping.md section 1). The gate applies
patch.diff to /testbed before this script runs; PYTHONPATH=/testbed makes
the patched package importable. Constructing a Blueprint exercises the
prologue; its outcome is classified into the same three channels the model
has: normal completion, name rejection (ValueError <-> NameValidationError),
or base-init failure (any other exception <-> BaseInitError).

Type bridge (mapping.md section 2): the `str` arguments map to `List[int]`
of Unicode code points ([ord(c) for c in s], bijective); the shadow is run
on the code-point lists while the oracle receives the original strings.
Only the exit channel is compared — the model pins which channel fires,
never an exception message.

Input domain: Requires demands only (fractional) permission on the two
lists, so every (name, import_name) pair of strings is Requires-satisfying.
Fuzz names are drawn from an alphabet including the dot, spaces and
non-ASCII code points, lengths 0..12; import_name is mostly held at an
in-sys.modules resolvable module (isolating the name decision) with a
dedicated sweep crossing boundary names against unresolvable / relative
dotted import names (exercising the base-init failure channel on both
sides).

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 name fuzz +
import_name cross sweep. Pinned fuzz seed: 501404.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 501404
N_FUZZ = 100_000


# --- model.py exception classes (user-defined channels) ----------------------

class NameValidationError(Exception):
    pass


class BaseInitError(Exception):
    pass


# --- PSeq shim: immutable sequence with the operations the fold uses ----------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, items):
        s = cls()
        s._t = tuple(items)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- @ContractOnly callee: calls the REAL repo function it models -------------

def init_base(import_name_str):
    """The real unchanged base initialiser (flask.scaffold.Scaffold.__init__),
    invoked with the same defaulted arguments the modeled constructor passes.
    A failure-as-a-unit maps to the model's BaseInitError channel."""
    from flask.scaffold import Scaffold
    try:
        Scaffold(import_name_str)
    except BaseException as exc:  # noqa: BLE001 — fails as a unit
        raise BaseInitError() from exc


# --- pure helper from model.py, contracts stripped -----------------------------

def contains_dot(s):
    if len(s) == 0:
        return False
    return s[0] == 46 or contains_dot(s.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped ------------
# (init_base receives the original string so the real callee sees the same
# argument the oracle passes; the code-point bridge is bijective either way.)

def validate_name(name, import_name, import_name_str):
    init_base(import_name_str)
    if len(name) == 0:
        raise NameValidationError()
    if contains_dot(ToSeq(name)):
        raise NameValidationError()
    return


# --- shadow / oracle channel classification ------------------------------------

def shadow_outcome(name_str, import_name_str):
    name = [ord(c) for c in name_str]
    import_name = [ord(c) for c in import_name_str]
    try:
        validate_name(name, import_name, import_name_str)
        return "return"
    except NameValidationError:
        return "name-reject"
    except BaseInitError:
        return "base-init-fail"


def real_outcome(flask_mod, name_str, import_name_str):
    """Run the real patched constructor prologue and classify its exit
    channel. ValueError is the name-rejection channel; any other exception
    is the base-init failure channel (mapping.md section 2)."""
    try:
        flask_mod.Blueprint(name_str, import_name_str)
        return "return"
    except ValueError:
        return "name-reject"
    except BaseException:  # noqa: BLE001
        return "base-init-fail"


def check_pair(flask_mod, name_str, import_name_str):
    s = shadow_outcome(name_str, import_name_str)
    r = real_outcome(flask_mod, name_str, import_name_str)
    if s != r:
        return ("DISAGREEMENT\n  name=%r\n  import_name=%r\n  shadow=%s\n  real=%s"
                % (name_str, import_name_str, s, r))
    return None


# --- input generation ------------------------------------------------------------

# resolvable import names (already importable in the container)
RESOLVABLE_IMPORTS = ["flask", "os", "sys", "__main__"]
# relative / unresolvable dotted import names (base init fails as a unit)
FAILING_IMPORTS = [".", "..", "no.such.package",
                   "definitely.not.a.real.module.xyzzy",
                   ".leading", "trailing.",
                   "no_such_top_level_module_qwertyz"]

BOUNDARY_NAMES = [
    "",            # zero code points: the reject the normal post forbids
    ".",           # dot only
    "a",           # minimal accepted
    "a.b",
    "app.ui",
    ".leading",
    "trailing.",
    "my_blueprint",
    "admin-panel",
    " ",           # non-empty, dot-free
    "a b c",
    "0",
    "ünïcодe",  # non-ASCII, dot-free
    "•.•",                # non-ASCII with a dot
    "." * 12,
    "x" * 64,
]

ALPHABET = list("abcXYZ012._- .") + ["é", "•"]


def main():
    import flask  # the REAL patched repo (PYTHONPATH=/testbed, gold applied)

    checked = 0

    # boundary names x (resolvable + failing) import names
    for name in BOUNDARY_NAMES:
        for imp in RESOLVABLE_IMPORTS + FAILING_IMPORTS:
            err = check_pair(flask, name, imp)
            if err:
                print(err)
                return 1
            checked += 1

    # pinned-seed fuzz over names, resolvable import name (isolates the
    # accept/reject decision the model pins)
    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        n = rng.randint(0, 12)
        name = "".join(rng.choice(ALPHABET) for _ in range(n))
        imp = rng.choice(RESOLVABLE_IMPORTS)
        err = check_pair(flask, name, imp)
        if err:
            print(err)
            return 1
        checked += 1

    # fuzzed dotted / relative / nonsense import names crossed with a few
    # names from every decision class (exercises the base-init channel)
    for _ in range(500):
        nseg = rng.randint(0, 4)
        seg = ["".join(rng.choice(list("abcdefghxyz_"))
                       for _ in range(rng.randint(0, 5)))
               for _ in range(nseg)]
        imp = ".".join(seg)
        for name in ("", "ok", "a.b"):
            err = check_pair(flask, name, imp)
            if err:
                print(err)
                return 1
            checked += 1

    n_boundary = len(BOUNDARY_NAMES) * (len(RESOLVABLE_IMPORTS) + len(FAILING_IMPORTS))
    print("G-CONF OK: shadow impl == real constructor prologue on %d inputs "
          "(%d boundary + %d name fuzz + %d import-name cross, seed %d)."
          % (checked, n_boundary, N_FUZZ, checked - n_boundary - N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region; "
                                "init_base -> real base initialiser)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
