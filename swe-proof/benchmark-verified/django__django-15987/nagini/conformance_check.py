#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15987 (nagini).

SHADOW: the impl region of model.py, copied VERBATIM below with the contract
calls stripped (Requires/Ensures/Invariant/Assert lines removed; nothing else
touched), plus the @Pure helper `any_match` copied over as a plain function
with a tuple-backed PSeq shim (providing `.drop(n)`).

ORACLE: the REAL patched repo decision the model models per mapping.md --
the duplicate-detection presence test inside the `fixture_dirs` cached
property of `django.core.management.commands.loaddata.Command`, imported
from /testbed (the gate applies the patch before this script runs;
PYTHONPATH=/testbed). One synthetic application is installed per case by
monkeypatching `apps.get_app_configs` in the command module's namespace, the
configured directory collection is placed in `settings.FIXTURE_DIRS`, and a
fresh Command's `fixture_dirs` property is evaluated. The observable is
whether the property raises ImproperlyConfigured for the
default-directory-already-configured reason (detected -> shadow True) or
completes / raises nothing of that kind (not detected -> shadow False).

Type bridge (mapping.md section 2): each configured entry d_k (a plain str
or a pathlib path object) is reduced with the REAL machinery to
  value_matches[k]  = (str(d_k) == app_dir)
  is_path_object[k] = isinstance(d_k, pathlib.PurePath)
where app_dir is the application's default fixtures directory
(os.path.join(app path, "fixtures")). Result True <-> the detection error is
raised.

Input domain: the model's Requires demands only read access and equal
lengths of the two parallel lists; both are guaranteed by construction (the
bridge derives both booleans from the same entry list). Generated entry
collections are deduplicated by (kind, spelling) so the property's separate
whole-collection duplicate guard (unchanged by the patch, outside the
modeled decision) never fires first.

>= 1e5 Requires-satisfying inputs: discrete boundary matrix + 100000 fuzz.
Pinned fuzz seed: 15987.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outcomes and exits 1. stdlib + django (the repo under test) only.
"""
import json
import os
import pathlib
import random
import sys

# --- configure Django settings before touching the command machinery --------
import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False, USE_TZ=True, DATABASES={}, INSTALLED_APPS=[],
        FIXTURE_DIRS=[],
    )
    django.setup()

from django.core.exceptions import ImproperlyConfigured
from django.core.management.commands import loaddata as loaddata_mod
from django.core.management.commands.loaddata import Command

SEED = 15987
N_FUZZ = 100_000

# The stable identifying fragment of the detection error's message (present
# both before and after the patch; only the decision that triggers it moved).
DETECT_MSG = "is a default fixture directory for the"

LABEL = "synthapp"
APP_PATH = os.path.join(os.sep, "srv", "synthapp")


# --- PSeq shim: a plain tuple with .drop(n) -----------------------------------

class PSeqShim(tuple):
    def drop(self, n):
        return PSeqShim(self[n:])


# --- pure helper from model.py, decorator stripped, body verbatim ------------

def any_match(eqs):
    """Whether some configured entry's path string equals the default
    directory's path string: the disjunction of the per-entry value matches.
    Front-recursive so a single unfold is available per loop step."""
    if len(eqs) == 0:
        return False
    return eqs[0] or any_match(eqs.drop(1))


# --- the impl region of model.py, verbatim (contract calls stripped) ---------

def default_dir_is_listed(value_matches, is_path_object):
    # impl-start
    result = False
    i = len(value_matches)
    while i > 0:
        # Compare by path string (the entry coerced to its path string equals
        # the default directory's path string).
        if value_matches[i - 1]:
            result = True
        i = i - 1
    return result
    # impl-end


# --- bridge: real configured entries -> the model's parallel bool lists ------

def abstract_entries(entries, app_dir):
    value_matches = [str(d) == app_dir for d in entries]
    is_path_object = [isinstance(d, pathlib.PurePath) for d in entries]
    return value_matches, is_path_object


# --- drive the REAL patched property ------------------------------------------

class FakeAppConfig:
    """Stand-in application component: the modeled decision reads only
    `.label` and `.path` (the default directory is derived from `.path`)."""
    def __init__(self, label, path):
        self.label = label
        self.path = path


_APP_CONFIGS = [FakeAppConfig(LABEL, APP_PATH)]
loaddata_mod.apps.get_app_configs = lambda: list(_APP_CONFIGS)


def oracle(entries):
    """Evaluate the REAL `fixture_dirs` property on a fresh Command with the
    given configured collection; True iff the default-directory detection
    error is raised for the synthetic application."""
    settings.FIXTURE_DIRS = entries
    cmd = Command()
    cmd.app_label = None  # no per-application filtering
    try:
        cmd.fixture_dirs
        return False
    except ImproperlyConfigured as e:
        msg = str(e)
        if DETECT_MSG in msg:
            label = msg.split("for the '", 1)[1].split("'", 1)[0]
            if label != LABEL:
                raise AssertionError(
                    "detection reported for unexpected component %r on "
                    "entries=%r" % (label, entries))
            return True
        # a different configuration error (e.g. the whole-collection
        # duplicate guard) -- the generator avoids these by construction
        raise AssertionError(
            "unexpected ImproperlyConfigured %r on entries=%r"
            % (msg, entries))


def check_case(entries, app_dir):
    real = oracle(entries)
    value_matches, is_path_object = abstract_entries(entries, app_dir)
    shadow = default_dir_is_listed(value_matches, is_path_object)
    # internal consistency: the impl region agrees with the pure fold
    assert shadow == any_match(PSeqShim(value_matches))
    if bool(shadow) != bool(real):
        return ("DISAGREEMENT\n"
                "  entries=%r\n  app_dir=%r\n"
                "  value_matches=%r is_path_object=%r\n"
                "  shadow=%r real=%r"
                % ([(str(e), type(e).__name__) for e in entries], app_dir,
                   value_matches, is_path_object, shadow, real))
    return None


# --- input generation ----------------------------------------------------------

def make_entries(spec):
    """spec: list of (location string, as_path_object). Deduplicated with the
    same set semantics the property's whole-collection duplicate guard uses
    (path objects normalize separators, so different spellings can compare
    equal; a path object and the equal string stay distinct raw values), so
    that guard never fires ahead of the modeled decision."""
    seen, entries = set(), []
    for loc, is_path in spec:
        entry = pathlib.Path(loc) if is_path else loc
        if entry in seen:
            continue
        seen.add(entry)
        entries.append(entry)
    return entries


def main():
    app_dir = os.path.join(APP_PATH, "fixtures")

    # Location pool: the default directory itself, near-miss spellings whose
    # path-object string form may or may not normalize back to it, and
    # unrelated directories.
    match_loc = app_dir
    near_locs = [
        app_dir + os.sep,                       # trailing separator
        APP_PATH + os.sep + os.sep + "fixtures",  # doubled separator
        os.path.join(APP_PATH, "Fixtures"),     # case difference
        os.path.join(APP_PATH, "fixtures", "sub"),
        APP_PATH,
    ]
    other_locs = [os.path.join(os.sep, "etc", "elsewhere%d" % i)
                  for i in range(4)]
    all_locs = [match_loc] + near_locs + other_locs

    disagreements = 0
    checked = 0

    def run_case(spec):
        nonlocal disagreements, checked
        err = check_case(make_entries(spec), app_dir)
        checked += 1
        if err:
            disagreements += 1
            if disagreements <= 5:
                print(err)

    # --- discrete boundary matrix -----------------------------------------
    run_case([])                                     # empty collection
    for loc in all_locs:
        run_case([(loc, False)])                     # single plain string
        run_case([(loc, True)])                      # single path object
    # a matching entry hidden among non-matching ones, in either kind
    for kind in (False, True):
        run_case([(other_locs[0], False), (match_loc, kind)])
        run_case([(other_locs[0], True), (match_loc, kind)])
        run_case([(match_loc, kind), (other_locs[1], False)])
    run_case([(match_loc, True), (match_loc, False)])  # both kinds match
    n_boundary = checked

    # --- randomized fuzz ----------------------------------------------------
    rng = random.Random(SEED)  # pinned seed
    for _ in range(N_FUZZ):
        k = rng.randint(0, 5)
        spec = [(rng.choice(all_locs), rng.random() < 0.5) for _ in range(k)]
        run_case(spec)

    if disagreements == 0:
        print("G-CONF OK: shadow impl == real presence test on %d inputs "
              "(%d boundary + %d fuzz, seed %d), 0 disagreements."
              % (checked, n_boundary, N_FUZZ, SEED))
        print(json.dumps({"checked": checked, "disagreements": 0,
                          "seed": SEED,
                          "shadow": "direct (contract-stripped impl region)"}))
        return 0
    print("status=fail %d disagreement(s) out of %d checks"
          % (disagreements, checked))
    return 1


if __name__ == "__main__":
    sys.exit(main())
