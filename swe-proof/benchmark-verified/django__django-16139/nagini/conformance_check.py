#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-16139 (nagini).

SHADOW: the impl region of model.py's `build_action_reference`, copied
verbatim below with the contract calls (Assert lines) stripped. The @Pure
helpers `DOTDOT` and `resolve` are copied over as plain functions; PSeq /
ToSeq become a thin immutable-tuple shim (`_PSeqT`) providing the len /
index / take / drop / + / == operations the copied code uses. No
@ContractOnly callees exist in this bundle (meta.json axioms == []).

ORACLE: the REAL patched repo function the model models per mapping.md --
`django.contrib.auth.forms.UserChangeForm.__init__`, whose observable output
here is the relative hyperlink it substitutes into the read-only password
field's help text (extracted from the field's `<a href="...">`, exactly the
observation the repo's own test makes). The gate applies patch.diff to
/testbed before this script runs; PYTHONPATH=/testbed makes the patched
code importable.

TYPE BRIDGE (mapping.md section 2): a URL path is a list of opaque
path-segment ids; the up-one-level step is the sentinel DOTDOT == -1;
ordinary segments are non-negative ints; distinct segments <-> distinct ids.
Each trial therefore starts from a CONCRETE scenario (prefix segment names,
an access-token segment, action-page names, an integer primary key), builds
the segment->id bijection for it (the pk's segment gets the pk integer
itself as its id, so the model's `pk` argument and the real instance's
primary key coincide), runs the shadow on the id view, renders the shadow's
returned step list back through the inverse bijection to a relative URL
string, and diffs that string against the href the real patched form
produced for a user with that primary key. As a semantic cross-check, both
references are also resolved against the concrete current-page URL with the
stdlib resolver (urllib.parse.urljoin) and the resolved targets compared.

INPUT DOMAIN: the model's Requires demand non-negative prefix entries and
non-negative token / current_action / pk / secondary_action; the
concrete-scenario construction satisfies this by giving every distinct
segment a distinct non-negative id. Boundary cases cover pk in {0, 1, huge},
token == pk vs token != pk (numeric and name-like access tokens), and
prefix depths 0..5 including the deployed admin shape; fuzz draws random
depths, segment names, and pk magnitudes.

>= 1e5 Requires-satisfying inputs: boundary cases + 100000 fuzz trials.
Pinned fuzz seed: 16139.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import re
import sys
import urllib.parse

SEED = 16139
N_FUZZ = 100_000


# --- PSeq/ToSeq shim (immutable sequence with take/drop) -----------------------

class _PSeqT(object):
    __slots__ = ("_t",)

    def __init__(self, items=()):
        self._t = tuple(items)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __add__(self, other):
        return _PSeqT(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, _PSeqT) and self._t == other._t

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self._t)

    def take(self, n):
        return _PSeqT(self._t[:n])

    def drop(self, n):
        return _PSeqT(self._t[n:])


def PSeq(*items):
    return _PSeqT(items)


def ToSeq(xs):
    return _PSeqT(tuple(xs))


# --- pure helpers from model.py, decorators stripped ----------------------------

def DOTDOT():
    """Sentinel path step meaning 'up one level' (the ".." segment)."""
    return -1


def resolve(base_dir, rel):
    """Resolve a relative reference `rel` against the directory-segment list
    `base_dir` of the current (trailing-slash) location, per the standard
    hierarchical rule: a ".." step (DOTDOT) drops the last accumulated segment;
    any other step is appended. Front-recursive over `rel` so a single unfold
    is available per loop step."""
    if len(rel) == 0:
        return base_dir
    if rel[0] == DOTDOT():
        if len(base_dir) == 0:
            return resolve(base_dir, rel.drop(1))
        return resolve(base_dir.take(len(base_dir) - 1), rel.drop(1))
    return resolve(base_dir + PSeq(rel[0]), rel.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped -------------
# (the Assert(...) proof lines are contract calls and are removed; the plain
#  assignments of the impl region are kept as-is)

def build_action_reference(prefix, token, current_action, pk, secondary_action):
    # rel = ['..', '..', <pk>, <secondary_action>]
    result = [DOTDOT(), DOTDOT(), pk, secondary_action]  # type: List[int]
    base0 = ToSeq(prefix) + PSeq(token) + PSeq(current_action)
    rel = ToSeq(result)
    base1 = ToSeq(prefix) + PSeq(token)
    return result


# --- concrete-scenario construction and the id bijection ------------------------

_NAME_ALPHABET = ("admin", "auth", "user", "accounts", "staff", "member",
                  "org", "site", "aa", "b1", "c-2", "d_3", "e.mail",
                  "uuid-0f", "testclient", "x", "y", "zz")
_ACTION_NAMES = ("change", "password")  # current / secondary action pages


def make_bijection(segments, pk_value):
    """Assign a distinct non-negative id to each distinct segment name; the
    segment spelling the primary key gets the pk integer itself as its id.
    Returns (seg->id dict, id->seg dict)."""
    pk_seg = str(pk_value)
    seg_to_id = {}
    used = {pk_value}
    nxt = 0
    for seg in segments:
        if seg in seg_to_id:
            continue
        if seg == pk_seg:
            seg_to_id[seg] = pk_value
            continue
        while nxt in used:
            nxt += 1
        seg_to_id[seg] = nxt
        used.add(nxt)
        nxt += 1
    if pk_seg not in seg_to_id:
        seg_to_id[pk_seg] = pk_value
    id_to_seg = {i: s for s, i in seg_to_id.items()}
    return seg_to_id, id_to_seg


def render_reference(steps, id_to_seg):
    """Inverse bridge: a relative URL string from the shadow's step-id list
    (DOTDOT -> '..', ordinary ids through the bijection). Returns (url, None)
    or (None, error string) if the shadow emitted an id outside the
    bijection."""
    parts = []
    for step in steps:
        if step == DOTDOT():
            parts.append("..")
        elif step in id_to_seg:
            parts.append(id_to_seg[step])
        else:
            return None, "shadow emitted unmapped segment id %r" % (step,)
    return "/".join(parts) + "/", None


HREF_RE = re.compile(r'<a href="(.*?)">')


def check_case(make_form, prefix_segs, token_seg, pk_value):
    """One concrete scenario: current page at
    /<prefix..>/<token>/change/ for an object whose primary key is pk_value.
    Diffs the shadow's rendered reference against the real patched form's
    help-text href, plus the urljoin-resolved targets. Returns an error
    string on disagreement, else None."""
    segments = list(prefix_segs) + [token_seg] + list(_ACTION_NAMES)
    seg_to_id, id_to_seg = make_bijection(segments, pk_value)

    prefix_ids = [seg_to_id[s] for s in prefix_segs]
    token_id = seg_to_id[token_seg]
    ca_id = seg_to_id["change"]
    sa_id = seg_to_id["password"]
    pk_id = seg_to_id[str(pk_value)]

    # SHADOW (id view) -> rendered relative URL string
    steps = build_action_reference(prefix_ids, token_id, ca_id, pk_id, sa_id)
    shadow_href, err = render_reference(steps, id_to_seg)

    # REAL patched repo function -> href substituted into the help text
    form = make_form(pk_value)
    help_text = str(form.fields["password"].help_text)
    m = HREF_RE.search(help_text)
    real_href = m.group(1) if m else None

    ok = (err is None and real_href is not None and shadow_href == real_href)
    if ok:
        # semantic cross-check: both references resolve (stdlib resolver)
        # to the same absolute target from the current page's URL
        base_url = "/" + "".join(s + "/" for s in
                                 list(prefix_segs) + [token_seg, "change"])
        ok = (urllib.parse.urljoin(base_url, shadow_href)
              == urllib.parse.urljoin(base_url, real_href))
    if ok:
        return None
    return ("DISAGREEMENT\n"
            "  prefix=%r token=%r pk=%r\n"
            "  model ids: prefix=%r token=%r current_action=%r pk=%r "
            "secondary_action=%r\n"
            "  shadow steps=%r -> href=%r%s\n"
            "  real help-text href=%r"
            % (prefix_segs, token_seg, pk_value,
               prefix_ids, token_id, ca_id, pk_id, sa_id,
               steps, shadow_href, (" (%s)" % err) if err else "",
               real_href))


def boundary_cases():
    admin = ["admin", "auth", "user"]
    cases = []
    for pk in (0, 1, 2, 7, 999, 10 ** 6, 2 ** 31 - 1, 10 ** 18):
        cases.append((admin, str(pk), pk))            # token == pk
        cases.append((admin, str(pk + 1), pk))        # numeric token != pk
        cases.append((admin, "testclient", pk))       # name-like token
        cases.append((admin, "uuid-0f", pk))
    for prefix in ([], ["x"], ["a", "b"], ["admin", "org", "staff", "member",
                                           "accounts"]):
        cases.append((prefix, "testclient", 42))
        cases.append((prefix, "42", 42))
    return cases


def rand_case(rng):
    depth = rng.randint(0, 5)
    prefix = [rng.choice(_NAME_ALPHABET) for _ in range(depth)]
    r = rng.random()
    if r < 0.35:
        pk = rng.randint(0, 10 ** 4)
    elif r < 0.85:
        pk = rng.randint(0, 10 ** 9)
    else:
        pk = rng.randint(0, 10 ** 18)
    t = rng.random()
    if t < 0.25:
        token = str(pk)                       # reached via the primary key
    elif t < 0.55:
        token = str(rng.randint(0, 10 ** 9))  # a different numeric identifier
    else:
        token = rng.choice(_NAME_ALPHABET)    # a name-like identifier
    return prefix, token, pk


def main():
    import django
    from django.conf import settings
    if not settings.configured:
        settings.configure(
            DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3",
                                   "NAME": ":memory:"}},
            INSTALLED_APPS=["django.contrib.contenttypes",
                            "django.contrib.auth"],
            USE_TZ=False,
        )
    django.setup()

    # REAL patched callee: the form __init__ that builds the password
    # field's help-text link for the given user instance. The form class is
    # narrowed to the password field only (a Meta.fields restriction) so the
    # unrelated many-to-many form fields don't touch the database; the
    # inherited __init__ under test runs unchanged and its observable output
    # here -- the formatted help-text link -- is produced by exactly the
    # patched code path.
    from django.contrib.auth.forms import UserChangeForm
    from django.contrib.auth.models import User

    class ConfUserChangeForm(UserChangeForm):
        class Meta(UserChangeForm.Meta):
            model = User
            fields = ["password"]

    def make_form(pk_value):
        # Fresh form per input: the help text is formatted per instance
        # inside __init__, keyed by the instance's primary key.
        return ConfUserChangeForm(instance=User(pk=pk_value))

    rng = random.Random(SEED)
    checked = 0
    n_boundary = 0
    for prefix, token, pk in boundary_cases():
        err = check_case(make_form, prefix, token, pk)
        if err:
            print(err)
            return 1
        checked += 1
        n_boundary += 1
    for _ in range(N_FUZZ):
        prefix, token, pk = rand_case(rng)
        err = check_case(make_form, prefix, token, pk)
        if err:
            print(err)
            return 1
        checked += 1

    print("G-CONF OK: shadow impl == real UserChangeForm password help-text "
          "reference (href string AND urljoin-resolved target) on %d inputs "
          "(%d boundary + %d fuzz, seed %d)."
          % (checked, n_boundary, N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
