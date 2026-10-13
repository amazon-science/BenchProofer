#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-15128 (nagini).

SHADOW: the impl region of model.py's ``build_relabel_map``, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helpers ``BASE``/``floor_of``/``fresh_alias`` copy over as plain
functions. The ``disjoint_by_floor`` ghost lemma is proof-only (its body is a
no-op loop carrying quantified facts), so its invocation is stripped like the
other contract calls. This bundle consumes no @ContractOnly axiom, so every
shadow callee is the model's own code.

ORACLE: the REAL patched repo function the model models per mapping.md --
``django.db.models.sql.query.Query.bump_prefix``. The gate applies the patch
to /testbed before this script runs; the script only imports and drives the
patched code. The modeled value is the relabel map ``bump_prefix`` constructs
and hands to ``Query.change_aliases``; we observe it with a recording subclass
whose ``change_aliases`` override captures the map and then delegates to the
real method unchanged (so the real disjointness assertion still runs on every
input). The freshly chosen ``alias_prefix`` is read back off the query after
the call.

Type bridge (mapping.md section 2): aliases are strings on the real side and
non-negative ints on the model side, related by an injective encoding in which
a namespace ``ns`` owns the integer region [ns*BASE, (ns+1)*BASE). Per input
we build the encoding explicitly: each distinct current alias string (plus the
designated left-unmapped alias, if any) gets a distinct int below
``floor_of(new_ns)`` -- satisfying the model precondition that current aliases
live strictly below the fresh namespace's floor, which mirrors the real
guarantee that the freshly chosen prefix differs from every current alias's
namespace -- and the fresh name for ordinal position ``pos`` in the fresh
prefix's namespace corresponds to ``new_ns*BASE + pos``. The real ``exclude``
parameter is a set; the model carries a single designated alias, so the bridge
drives the real side with a one-element set (or ``None``, bridged as a
designated int distinct from every current alias's encoding -- both mean
"nothing is left unmapped among the current aliases"). Inputs with duplicate
aliases are outside the bridge's image (real alias-map keys are distinct dict
keys), so generation keeps aliases distinct.

The comparison, per input: for every ordinal position, the shadow's
source-flag must equal real key-membership of that alias in the captured map,
and where flagged, the shadow's target encoding must equal the encoding of the
real captured value (parsed back through the fresh-namespace leg of the
bijection). The induced dict {alias: target | flagged} is compared against the
captured map as a whole as well.

Input domain: distinct alias strings that cannot collide with any fresh name
(old-prefix-letter + digits, or lowercase table-style names), 0..10 of them;
the designated alias present at any position, absent, or not supplied; varied
old prefixes and varied pre-seeded prefix reservations so the real side picks
different fresh prefixes; varied model-side fresh namespaces. Boundary cases
plus 110000 fuzz inputs (>= 1e5, all Requires-satisfying). Pinned fuzz seed:
151280.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

sys.path.insert(0, "/testbed")

SEED = 151280
N_FUZZ = 110000


# --- pure helpers from model.py, contracts stripped ---------------------------

def BASE():
    return 1000


def floor_of(ns):
    return ns * BASE()


def fresh_alias(new_ns, pos):
    return new_ns * BASE() + pos


# (disjoint_by_floor is a ghost proof lemma -- a no-op loop that carries
#  quantified arithmetic facts; stripped along with the other contract calls.)


# --- the impl region of build_relabel_map, verbatim, contracts stripped -------

def build_relabel_map(aliases, new_ns, excluded):
    targets = []  # type: list
    is_source = []  # type: list
    pos = 0
    while pos < len(aliases):
        t = fresh_alias(new_ns, pos)
        targets.append(t)
        if aliases[pos] != excluded:
            is_source.append(1)
        else:
            is_source.append(0)
        pos = pos + 1
    # (ghost lemma invocation stripped: proof-only, no runtime effect)
    return targets, is_source


# --- oracle plumbing -----------------------------------------------------------

def setup_django():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(INSTALLED_APPS=[], DATABASES={})
    django.setup()


_CAP = {}


def make_real_query(alias_order, old_prefix, reserved_prefixes):
    """A real Query whose ordered alias map holds the given aliases, with the
    given current prefix and the given set of already-reserved prefixes (which
    steers WHICH fresh prefix the real routine picks next)."""
    from django.db.models.sql.datastructures import BaseTable
    q = _CAP["cls"](None)
    q.alias_prefix = old_prefix
    q.subq_aliases = frozenset(reserved_prefixes)
    for a in alias_order:
        q.alias_map[a] = BaseTable(a, a)
        q.table_map[a] = [a]
        q.alias_refcount[a] = 1
    return q


def init_capture_class():
    from django.db.models.sql.query import Query as RealQuery

    class CapturingQuery(RealQuery):
        """Records the map handed to change_aliases, then delegates to the
        REAL method unchanged (its internal assertion still runs)."""

        def __init__(self, *args, **kwargs):
            super(CapturingQuery, self).__init__(*args, **kwargs)
            self.captured_maps = []

        def change_aliases(self, change_map):
            self.captured_maps.append(dict(change_map))
            return super(CapturingQuery, self).change_aliases(change_map)

    _CAP["cls"] = CapturingQuery
    _CAP["real"] = RealQuery


# --- the differential ------------------------------------------------------------

def check_one(alias_order, old_prefix, reserved_prefixes, designated, new_ns):
    """Drive the real patched routine on one input and diff it against the
    shadow through the encoding bridge. `designated` is the alias string left
    unmapped, or None (nothing supplied). Returns an error string or None."""
    inp = (alias_order, old_prefix, sorted(reserved_prefixes), designated,
           new_ns)

    q = make_real_query(alias_order, old_prefix, reserved_prefixes)
    other = _CAP["real"](None)
    other.alias_prefix = old_prefix
    exclude = {designated} if designated is not None else None
    try:
        q.bump_prefix(other, exclude=exclude)
    except AssertionError as exc:
        return ("REAL SIDE ASSERTION on input=%r: %r" % (inp, exc))
    if len(q.captured_maps) != 1:
        return ("ORACLE PLUMBING: expected exactly one captured map on "
                "input=%r, got %d" % (inp, len(q.captured_maps)))
    cm = q.captured_maps[0]
    new_prefix = q.alias_prefix
    if new_prefix == old_prefix:
        return ("ORACLE PLUMBING: fresh prefix not chosen on input=%r" % (inp,))

    # Build the per-input injective encoding: each distinct current alias
    # (plus the designated alias, if supplied) -> a distinct int below the
    # fresh namespace's floor. floor_of(new_ns) >= BASE() > the handful of
    # distinct strings per input, so the codes always fit.
    enc = {}
    for a in alias_order:
        enc[a] = len(enc)
    if designated is not None and designated not in enc:
        enc[designated] = len(enc)
    if designated is not None:
        designated_int = enc[designated]
    else:
        # nothing supplied: bridge as a designated int distinct from every
        # current alias's encoding (equivalent -- no current alias matches it)
        designated_int = len(enc)
    aliases_int = [enc[a] for a in alias_order]

    targets, is_source = build_relabel_map(aliases_int, new_ns, designated_int)

    if len(targets) != len(alias_order) or len(is_source) != len(alias_order):
        return ("DISAGREEMENT (shadow output lengths) on input=%r: "
                "targets=%r is_source=%r" % (inp, targets, is_source))

    def lower_value(v):
        """Real fresh-name string -> its int encoding, or None if it is not in
        the fresh namespace's image (which would itself be a disagreement)."""
        if v.startswith(new_prefix) and v[len(new_prefix):].isdigit():
            return new_ns * BASE() + int(v[len(new_prefix):])
        return None

    induced = {}
    for pos, alias in enumerate(alias_order):
        real_flag = 1 if alias in cm else 0
        if is_source[pos] != real_flag:
            return ("DISAGREEMENT (source flag) on input=%r at pos=%d "
                    "alias=%r:\n  shadow is_source = %r\n  real key-membership"
                    " = %r\n  captured map = %r"
                    % (inp, pos, alias, is_source[pos], real_flag, cm))
        if real_flag:
            got = lower_value(cm[alias])
            if got is None:
                return ("DISAGREEMENT (real value outside fresh namespace) on "
                        "input=%r at pos=%d alias=%r: real value %r has no "
                        "encoding under the bridge; shadow target = %r"
                        % (inp, pos, alias, cm[alias], targets[pos]))
            if targets[pos] != got:
                return ("DISAGREEMENT (target value) on input=%r at pos=%d "
                        "alias=%r:\n  shadow target = %r\n  real value %r "
                        "encodes to %r" % (inp, pos, alias, targets[pos],
                                           cm[alias], got))
            induced[aliases_int[pos]] = targets[pos]

    # Whole-map comparison: the induced {alias: target | flagged} dict must
    # be the captured map, transported through the encoding.
    real_lowered = {}
    for alias, v in cm.items():
        if alias not in enc:
            return ("DISAGREEMENT (unexpected real key) on input=%r: captured "
                    "map has key %r not among the current aliases; map=%r"
                    % (inp, alias, cm))
        got = lower_value(v)
        if got is None:
            return ("DISAGREEMENT (real value outside fresh namespace) on "
                    "input=%r: real value %r has no encoding; map=%r"
                    % (inp, v, cm))
        real_lowered[enc[alias]] = got
    if induced != real_lowered:
        return ("DISAGREEMENT (induced map) on input=%r:\n"
                "  shadow induced map = %r\n  real captured map (lowered) = %r"
                % (inp, induced, real_lowered))
    return None


# --- input generation -------------------------------------------------------------

LOWER_NAMES = ["alpha", "beta", "gamma", "delta", "epsilon", "zeta", "eta",
               "theta", "iota", "kappa", "table_a", "table_b"]


def boundary_cases():
    """Hand-picked edges. Each tuple: (alias_order, old_prefix,
    reserved_prefixes, designated, new_ns)."""
    return [
        # empty alias map, nothing designated / something designated
        ([], "T", {"T"}, None, 1),
        ([], "T", {"T"}, "alpha", 1),
        # single alias which IS the designated one
        (["alpha"], "T", {"T"}, "alpha", 1),
        # single alias, nothing designated
        (["alpha"], "T", {"T"}, None, 1),
        # the designated alias first (the typical shape: base first, then
        # prefixed join aliases with sequential suffixes)
        (["alpha", "T4", "T5"], "T", {"T"}, "alpha", 1),
        # designated in the middle / last
        (["T1", "alpha", "T3"], "T", {"T"}, "alpha", 2),
        (["T1", "T2", "alpha"], "T", {"T"}, "alpha", 3),
        # designated alias absent from the alias map
        (["T1", "T2"], "T", {"T"}, "omega_absent", 1),
        # nothing designated: every alias is a key
        (["T1", "T2", "T3"], "T", {"T"}, None, 1),
        # several reserved prefixes: the fresh prefix is further along
        (["alpha", "T4", "T5"], "T", {"T", "U", "V"}, "alpha", 4),
        # non-sequential suffixes, larger namespaces (aliases live in the
        # OLD prefix's namespace -- the precondition's real-side counterpart)
        (["S9", "S0", "alpha", "S42"], "S", {"S"}, "alpha", 6),
        # all-lowercase alias names (table-name-style aliases only)
        (["alpha", "beta", "gamma"], "A", {"A"}, "beta", 1),
    ]


def gen_fuzz(rng):
    old_prefix = chr(ord("A") + rng.randrange(0, 22))  # 'A'..'V'
    # reserve 0..3 letters after the old prefix so the real side picks a
    # varied fresh prefix
    k = rng.randrange(0, 4)
    reserved = {chr(ord(old_prefix) + i) for i in range(k + 1)}
    n = rng.randrange(0, 11)
    aliases = []
    used_nums = set()
    used_names = set()
    for _ in range(n):
        if rng.random() < 0.6:
            num = rng.randrange(0, 100)
            if num in used_nums:
                continue
            used_nums.add(num)
            aliases.append("%s%d" % (old_prefix, num))
        else:
            name = LOWER_NAMES[rng.randrange(0, len(LOWER_NAMES))]
            if name in used_names:
                continue
            used_names.add(name)
            aliases.append(name)
    roll = rng.random()
    if roll < 0.55 and aliases:
        designated = aliases[rng.randrange(0, len(aliases))]
    elif roll < 0.75:
        designated = "omega_absent"   # supplied but matches no current alias
    else:
        designated = None             # not supplied at all
    new_ns = rng.randrange(1, 7)
    return aliases, old_prefix, reserved, designated, new_ns


def main():
    try:
        setup_django()
        init_capture_class()
    except Exception as exc:  # pragma: no cover - environment guard
        print("G-CONF ERROR: Django not importable/configurable: %r" % (exc,))
        return 1

    checked = 0
    boundary = boundary_cases()
    for case in boundary:
        err = check_one(*case)
        if err:
            print(err)
            return 1
        checked += 1

    rng = random.Random(SEED)
    for _ in range(N_FUZZ):
        case = gen_fuzz(rng)
        err = check_one(*case)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl (contract-stripped build_relabel_map) == "
          "real patched alias-relabel construction on %d inputs (%d boundary "
          "+ %d fuzz, seed %d): per-position source flags, per-position "
          "target encodings, and the induced map all agree; 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
