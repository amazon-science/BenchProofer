#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-12143 (nagini).

SHADOW: the impl regions of model.py (``match_literal``, ``run_is_digits``,
``is_edited_pk_key``) copied verbatim below with the contract calls
(Requires / Ensures / Invariant / Assert) stripped.  The @Pure helpers
(``is_digit`` / ``prefix_eq`` / ``all_digits`` / ``recognises``) copy over as
plain functions on top of a small immutable-tuple PSeq shim; they are
contract-side but serve here as an internal cross-check of the executable
shadow.  There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method the model models per mapping.md —
``django.contrib.admin.options.ModelAdmin._get_edited_object_pks``.  The gate
applies patch.diff to /testbed before this script runs.  The method needs only
``self.model._meta.pk.name`` and ``request.POST.items()``, so it is driven with
duck-typed stand-ins carrying the chosen primary-key field name and a POST
mapping of candidate keys to unique values; a key is accepted exactly when its
value comes back in the returned list.  That recovers the per-key acceptance
decision (the modeled behaviour) from the real method, including the unchanged
filtering comprehension around it (refinement.md R3).

TYPE BRIDGE (mapping.md section 2): repo values are ``str``; the model carrier
is ``List[int]`` of Unicode code points via ``ord`` (a bijection for
surrogate-free text).  Generation happens over ``str`` and each value is
lowered per shadow call.  The model's Requires demand only readable lists, so
every generated triple is Requires-satisfying.

DOMAIN SCOPING (mapping.md section 3, shared with axiom_check.py): the
equivalence is asserted over realistic submitted formset keys — the digit run
is ASCII 0-9 (the row index is rendered from a Python int; the pattern's wider
Unicode-digit acceptance is orthogonal to the modeled change), keys carry no
trailing newline (an HTTP form-field name cannot contain one; the end-anchor's
pre-newline tolerance is likewise orthogonal), and the primary-key field name
is a Python identifier (a Django model field name).  The generators below stay
inside that domain by construction: no decimal-digit code points outside
U+0030..U+0039 and no newline appear in any alphabet, and pk names are drawn
from identifier-only pools.

INPUT PLAN (>= 1e5 Requires-satisfying triples): boundary prefixes covering
every regex metacharacter, hyphen-bearing labels and the empty label, each
crossed with several pk names and per-combination key sets (built-to-match
keys of varying digit-run length plus structural near-misses: missing digit
region, empty digit run, non-digit in the run, leading/trailing junk, wrong
trailing name, degenerate keys); then 110000 randomized fuzz triples mixing
built-to-match keys, single-edit mutants of matching keys, and arbitrary
short keys over a metacharacter-rich alphabet.  Pinned fuzz seed: 12143.

Exit 0 iff zero disagreements; on a disagreement prints the input triple and
both outputs and exits 1.  stdlib only.
"""
import json
import random
import sys

SEED = 12143
N_FUZZ = 110000     # per-batch dedupe trims ~2%, so this stays >= 1e5 checked
BATCH = 200        # candidate keys per real-oracle invocation


# --- PSeq shim: immutable sequence with the operations the pure region uses --

class PSeq(object):
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- @Pure helpers from model.py, copied as plain functions -------------------

def is_digit(c):
    return 48 <= c and c <= 57


def prefix_eq(s, lit):
    if len(lit) == 0:
        return True
    if len(s) == 0:
        return False
    return s[0] == lit[0] and prefix_eq(s.drop(1), lit.drop(1))


def all_digits(s):
    if len(s) == 0:
        return True
    return is_digit(s[0]) and all_digits(s.drop(1))


def recognises(prefix, pkname, key):
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2
    return (
        d >= 1
        and prefix_eq(key, prefix)
        and key[np] == 45
        and all_digits(key.take(np + 1 + d).drop(np + 1))
        and key[np + 1 + d] == 45
        and prefix_eq(key.drop(np + 2 + d), pkname)
    )


# --- the impl regions of model.py, verbatim, contract calls stripped ----------

def match_literal(key, off, lit):
    m = len(lit)
    ok = True
    i = m
    while i > 0:
        # (stripped Assert lines carried only proof-side sequence facts)
        if key[off + i - 1] != lit[i - 1]:
            ok = False
        i = i - 1
    return ok


def run_is_digits(key, lo, hi):
    ok = True
    i = hi
    while i > lo:
        c = key[i - 1]
        # (stripped Assert lines carried only proof-side sequence facts)
        if not (48 <= c and c <= 57):
            ok = False
        i = i - 1
    return ok


def is_edited_pk_key(prefix, pkname, key):
    np = len(prefix)
    nk = len(pkname)
    n = len(key)
    d = n - np - nk - 2
    if d < 1:
        return False
    ok_label = match_literal(key, 0, prefix)
    hyphen1 = (key[np] == 45)
    ok_digits = run_is_digits(key, np + 1, np + 1 + d)
    hyphen2 = (key[np + 1 + d] == 45)
    ok_name = match_literal(key, np + 2 + d, pkname)
    return ok_label and hyphen1 and ok_digits and hyphen2 and ok_name


# --- oracle plumbing: duck-typed carriers for the real patched method ---------

class _PkField(object):
    def __init__(self, name):
        self.name = name


class _Meta(object):
    def __init__(self, pkname):
        self.pk = _PkField(pkname)


class _Model(object):
    def __init__(self, pkname):
        self._meta = _Meta(pkname)


class _Admin(object):
    def __init__(self, pkname):
        self.model = _Model(pkname)


class _Request(object):
    def __init__(self, post):
        self.POST = post


_REAL = None       # bound in main(): the unbound real repo method


def real_accepted_keys(prefix, pkname, keys):
    """Run the REAL patched method once over a batch of candidate keys and
    return the subset it accepts.  Each key maps to a unique sentinel value;
    acceptance == the sentinel appears in the returned value list."""
    post = {}
    val_to_key = {}
    for idx, k in enumerate(keys):
        v = "sentinel-%d" % idx
        post[k] = v
        val_to_key[v] = k
    values = _REAL(_Admin(pkname), _Request(post), prefix)
    return set(val_to_key[v] for v in values)


# --- differential driver -------------------------------------------------------

def check_batch(prefix, pkname, keys, do_cross_check):
    """Compare shadow vs real per-key decisions for one (prefix, pkname) batch;
    return an error string on the first disagreement, else None."""
    keys = list(dict.fromkeys(keys))          # dedupe, order-preserving
    accepted = real_accepted_keys(prefix, pkname, keys)
    p_list = [ord(ch) for ch in prefix]       # bridge: str -> List[int]
    n_list = [ord(ch) for ch in pkname]
    for k in keys:
        k_list = [ord(ch) for ch in k]
        shadow = is_edited_pk_key(p_list, n_list, k_list)
        real = (k in accepted)
        if shadow != real:
            return ("DISAGREEMENT on prefix=%r pkname=%r key=%r "
                    "(code points %r):\n"
                    "  shadow (impl region) = %r\n"
                    "  real (patched per-key acceptance) = %r"
                    % (prefix, pkname, k, k_list, shadow, real))
        if do_cross_check:
            spec = recognises(ToSeq(p_list), ToSeq(n_list), ToSeq(k_list))
            if shadow != spec:
                return ("INTERNAL: impl region and pure decomposition "
                        "disagree on prefix=%r pkname=%r key=%r"
                        % (prefix, pkname, k))
    return len(keys)


DIGITS = "0123456789"
PK_NAMES = ["uuid", "id", "pk", "code", "objectid", "row_id", "_k9"]
META = list("$.^*+?()[]{}|\\")
PLAIN = list("formAZxy_") + list("09")


def build_matching_key(rng, prefix, pkname, d):
    digits = "".join(rng.choice(DIGITS) for _ in range(d))
    return "%s-%s-%s" % (prefix, digits, pkname)


def boundary_batches(rng):
    prefixes = [
        "", "form", "form$", "a.b", "a+b", "a*b", "x|y", "a(b)c",
        "[set]", "{n}", "q?", "^anchor", "back\\slash", "form$$",
        "$", ".", "+", "*", "form-", "fo-rm", "-", "--",
    ]
    pknames = ["uuid", "id", "pk", "_k9"]
    for prefix in prefixes:
        for pkname in pknames:
            keys = [
                build_matching_key(rng, prefix, pkname, 1),
                build_matching_key(rng, prefix, pkname, 2),
                build_matching_key(rng, prefix, pkname, 5),
                "%s-%s" % (prefix, pkname),            # no digit region
                "%s--%s" % (prefix, pkname),           # empty digit run
                "%s-0-%sX" % (prefix, pkname),         # trailing junk
                "x%s-0-%s" % (prefix, pkname),         # leading junk
                "%s-0a-%s" % (prefix, pkname),         # non-digit in run
                "%s-0-%s" % (prefix, pkname[:-1]),     # truncated name
                "%s-0-%sz" % (prefix, pkname),         # extended name
                prefix,                                # bare label
                pkname,                                # bare name
                "",                                    # empty key
                "-0-",                                 # hyphens and digit only
                "%s-0-" % prefix,                      # missing name region
                "-0-%s" % pkname,                      # missing label region
            ]
            yield prefix, pkname, keys


def mutate_key(rng, key, alphabet):
    """One random single-character edit (replace / insert / delete)."""
    if not key:
        return rng.choice(alphabet)
    i = rng.randrange(len(key))
    op = rng.random()
    if op < 0.4:
        return key[:i] + rng.choice(alphabet) + key[i + 1:]
    if op < 0.7:
        return key[:i] + rng.choice(alphabet) + key[i:]
    return key[:i] + key[i + 1:]


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure()
        try:
            django.setup()
        except Exception:
            pass
    from django.contrib.admin.options import ModelAdmin

    global _REAL
    _REAL = ModelAdmin._get_edited_object_pks

    rng = random.Random(SEED)
    checked = 0

    # --- boundary batches (cross-checked against the pure decomposition) -----
    for prefix, pkname, keys in boundary_batches(rng):
        r = check_batch(prefix, pkname, keys, do_cross_check=True)
        if isinstance(r, str):
            print(r)
            return 1
        checked += r

    # --- randomized fuzz (pinned seed); cross-check on a 1-in-16 sample ------
    alphabet = PLAIN + META + ["-", "é", "名"]
    key_alphabet = alphabet + list(DIGITS)
    produced = 0
    while produced < N_FUZZ:
        plen = rng.randint(0, 6)
        prefix = "".join(rng.choice(alphabet) for _ in range(plen))
        pkname = rng.choice(PK_NAMES)
        keys = []
        for _ in range(BATCH):
            roll = rng.random()
            if roll < 0.4:
                d = rng.randint(1, 4)
                k = build_matching_key(rng, prefix, pkname, d)
            elif roll < 0.7:
                d = rng.randint(1, 3)
                k = mutate_key(rng, build_matching_key(rng, prefix, pkname, d),
                               key_alphabet)
            else:
                klen = rng.randint(0, 18)
                k = "".join(rng.choice(key_alphabet) for _ in range(klen))
            keys.append(k)
        r = check_batch(prefix, pkname, keys,
                        do_cross_check=(produced % (BATCH * 16) == 0))
        if isinstance(r, str):
            print(r)
            return 1
        checked += r
        produced += BATCH

    print("G-CONF OK: shadow impl == real patched per-key acceptance on "
          "%d (prefix, pkname, key) triples (boundary + %d fuzz, seed %d); "
          "0 disagreements." % (checked, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
