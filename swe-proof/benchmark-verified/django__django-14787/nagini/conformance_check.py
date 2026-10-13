#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-14787 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Old/Acc) stripped. `FuncIdentity` copies over as a
plain attribute-carrying class (its __init__ Ensures dropped). There are no
@Pure helpers and no @ContractOnly callees in this bundle (the stdlib
wrapper-update primitive is modelled deeply inside the impl region itself).

ORACLE: the REAL patched repo code path the model models per mapping.md /
refinement.md — the assembly of the per-instance bound callable inside
`django.utils.decorators._multi_decorate(...)._wrapper`. The assembly is a
closure-local statement, so it is observed exactly the way its downstream
consumer does: `_multi_decorate` is invoked with a capturing decorator, the
returned wrapper is installed on a class and called on an instance, and the
decorator records the identity attributes (presence + value of the callable's
name and defining module) of the object it receives. That object IS the
assembled bound callable the model returns. The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
module importable.

Type bridge (mapping.md section 2): the two str-valued identity attributes are
modelled as (presence flag: bool, opaque int token) pairs; only presence and
value-equality are behaviour-bearing. Each trial fixes a bijection
{name string <-> name token, module string <-> module token} (distinct strings
get distinct tokens), maps the real observation back into the carrier, and
compares the 4-tuple (has_name, name, has_module, module) against the shadow's
output. Any observed string outside the bijection maps to a fresh sentinel
token, so a value mismatch can never be masked.

Input domain: Requires demands a method whose name and module attributes are
both present — true of every plain function, and the trial fixtures are plain
functions with (possibly unusual) name/module strings assigned. The method
read-only clauses are checked too: the fixture's attributes must be unchanged
after the call.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials.
Pinned fuzz seed: 14787.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys


# --- FuncIdentity from model.py, contracts stripped ---------------------------

class FuncIdentity:
    def __init__(self, has_name, name, has_module, module):
        self.has_name = has_name
        self.name = name
        self.has_module = has_module
        self.module = module


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def assemble_bound_callable(method):
    # The assembled callable is a plain partial application that on its own
    # exposes no function-identity metadata; the wrapper-update copies, from the
    # method onto it, each identity attribute the method possesses. The method
    # has both attributes (precondition), so the assembled callable ends up
    # carrying both — its name and module marked present and equal to the
    # method's own (the spelled-out per-attribute copy, collapsed to its result
    # for the contracted domain).
    has_name = method.has_name
    name = method.name
    has_module = method.has_module
    module = method.module
    bound = FuncIdentity(has_name, name, has_module, module)
    return bound


# --- oracle: observe the real assembled callable ------------------------------

def observe_real(multi_decorate, name_str, module_str):
    """Build a fresh method with the given identity strings, run it through the
    real (patched) decorator machinery, and return what a decorator observes on
    the callable it is handed: (has_name, name, has_module, module, err).
    Also checks the method itself is left unmodified (read-only clauses)."""
    def method(self):
        return "ok"
    method.__name__ = name_str
    method.__module__ = module_str

    seen = {}

    def capture(func):
        seen["has_name"] = hasattr(func, "__name__")
        seen["name"] = getattr(func, "__name__", None)
        seen["has_module"] = hasattr(func, "__module__")
        seen["module"] = getattr(func, "__module__", None)
        return func

    wrapper = multi_decorate(capture, method)

    class Host:
        pass

    Host.m = wrapper
    ret = Host().m()
    if ret != "ok":
        return None, "wrapper did not delegate to the method (got %r)" % (ret,)
    if not seen:
        return None, "decorator was never handed the assembled callable"
    # read-only clauses: the method's own identity must be unchanged
    if method.__name__ != name_str or method.__module__ != module_str:
        return None, ("method identity mutated: name=%r module=%r"
                      % (method.__name__, method.__module__))
    return seen, None


def check_trial(multi_decorate, name_str, module_str, name_tok, module_tok):
    """Run shadow and oracle on one identity pair; return an error string on
    disagreement, else None. Tokens must be distinct iff strings are."""
    # shadow over the carrier (Requires: both attributes present)
    m = FuncIdentity(True, name_tok, True, module_tok)
    shadow = assemble_bound_callable(m)
    shadow_tuple = (shadow.has_name, shadow.name,
                    shadow.has_module, shadow.module)
    # method read-only in the shadow too
    if (m.has_name, m.name, m.has_module, m.module) != (True, name_tok,
                                                        True, module_tok):
        return "shadow mutated its input method: %r" % ((m.has_name, m.name,
                                                         m.has_module,
                                                         m.module),)

    seen, err = observe_real(multi_decorate, name_str, module_str)
    if err:
        return ("ORACLE ERROR on name=%r module=%r: %s"
                % (name_str, module_str, err))

    # bridge: map observed strings back into the token carrier
    bij = {name_str: name_tok, module_str: module_tok}
    sentinel = -1  # any string outside the trial's bijection
    real_tuple = (seen["has_name"],
                  bij.get(seen["name"], sentinel) if seen["has_name"] else 0,
                  seen["has_module"],
                  bij.get(seen["module"], sentinel) if seen["has_module"] else 0)

    if shadow_tuple != real_tuple:
        return ("DISAGREEMENT\n  input: name=%r module=%r "
                "(tokens %d/%d)\n  shadow=%r\n  real=%r (observed name=%r "
                "module=%r)"
                % (name_str, module_str, name_tok, module_tok,
                   shadow_tuple, real_tuple, seen["name"], seen["module"]))
    return None


def boundary_cases():
    return [
        ("method", "tests"),
        ("m", ""),                              # empty module string
        ("", "pkg.mod"),                        # empty name string
        ("", ""),                               # both empty
        ("same", "same"),                       # name string == module string
        ("weird name with spaces", "some.dotted.module"),
        ("<lambda>", "__main__"),
        ("x" * 500, "y" * 500),                 # long strings
        ("éüñ", "mödule"),  # non-ascii
        ("__call__", "functools"),              # collides with builtin names
        ("name\nwith\nnewlines", "mod\ttab"),
    ]


ALPHABET = ("abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._ <>-é")


def rand_str(rng):
    return "".join(rng.choice(ALPHABET) for _ in range(rng.randint(0, 24)))


SEED = 14787
N_FUZZ = 100_000


def main():
    from django.utils.decorators import _multi_decorate  # REAL patched repo fn

    checked = 0
    for i, (name_str, module_str) in enumerate(boundary_cases()):
        # tokens: distinct iff strings distinct
        name_tok = 1
        module_tok = 1 if module_str == name_str else 2
        err = check_trial(_multi_decorate, name_str, module_str,
                          name_tok, module_tok)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        name_str = rand_str(rng)
        module_str = rand_str(rng)
        name_tok = rng.randint(-10**6, 10**6)
        if module_str == name_str:
            module_tok = name_tok
        else:
            module_tok = name_tok + 1 + rng.randint(0, 10**3)
        err = check_trial(_multi_decorate, name_str, module_str,
                          name_tok, module_tok)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real assembled-callable identity on %d "
          "inputs (%d boundary + %d fuzz, seed %d)."
          % (checked, len(boundary_cases()), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
