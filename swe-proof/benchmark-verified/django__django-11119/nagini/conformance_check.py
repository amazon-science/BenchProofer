#!/usr/bin/env python3
"""G-CONF differential conformance check for django__django-11119 (nagini).

SHADOW: the impl region of model.py, copied verbatim below with the contract
calls (Requires/Ensures/Invariant/Assert) stripped. The @Pure helpers of the
pure region (seq_* / entity / escaped_seq) copy over as plain functions on a
small immutable-tuple PSeq shim; they are contract-side but serve here as an
internal cross-check of the shadow. There are no @ContractOnly callees in
this bundle (the axioms region is empty).

ORACLE: the REAL patched repo function the model models per mapping.md /
meta.json — ``django.template.engine.Engine.render_to_string``. The gate
applies patch.diff to /testbed before this script runs. We construct one
Engine per policy value of its ``autoescape`` flag, each with a cached
in-memory loader holding a template that interpolates exactly one context
value (``{{ obj }}`` with no surrounding literal text), and call
``render_to_string`` on it. The rendered string IS the rendered
interpolation of the value, so it compares directly against the shadow's
output (mapping.md section 2: the constant literal prefix/suffix of the F2P
template is omitted from the model; here we simply use an empty prefix and
suffix).

Type bridge (mapping.md section 2): the context value and the rendered
fragment are ``str``; the model carrier is ``List[int]`` of Unicode code
points via ``ord``/``chr``. The bridge is a bijection on non-surrogate code
points, so generation happens over ``str`` and is lowered per call. The
engine policy flag is a plain bool (identity).

Input domain: the precondition demands only a readable list of code points
plus a bool, so every (str, bool) pair lowers to a Requires-satisfying
input. Every value is checked under BOTH policy values. Generation stresses
the decision boundary: the five HTML-significant characters alone, doubled,
combined, embedded in text, already-escaped entity text (must double-escape
under the ON policy), template-syntax-looking values (a context value is
data, never re-parsed), accented/astral code points, and whitespace.

>= 1e5 Requires-satisfying inputs: boundary cases + a per-code-point sweep
around the significant characters + 55000 fuzz values, each under both
policy values. Pinned fuzz seed: 11119.

Exit 0 iff zero disagreements; on disagreement prints the input and both
outputs and exits 1. stdlib only.
"""
import json
import random
import sys

SEED = 11119
N_FUZZ = 55000


# --- PSeq shim: immutable sequence, the operations the pure region uses ------

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

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure region of model.py, contracts stripped ------------------------------

def seq_amp():
    # '&amp;'
    return PSeq(38, 97, 109, 112, 59)


def seq_lt():
    # '&lt;'
    return PSeq(38, 108, 116, 59)


def seq_gt():
    # '&gt;'
    return PSeq(38, 103, 116, 59)


def seq_quot():
    # '&quot;'
    return PSeq(38, 113, 117, 111, 116, 59)


def seq_apos_dec():
    # '&#39;'  (the apostrophe entity emitted at this code base)
    return PSeq(38, 35, 51, 57, 59)


def entity(c):
    """Entity sequence emitted for a single code point under escaping: the five
    significant ones expand, every other code point maps to itself."""
    if c == 38:        # '&'
        return seq_amp()
    if c == 60:        # '<'
        return seq_lt()
    if c == 62:        # '>'
        return seq_gt()
    if c == 34:        # '"'
        return seq_quot()
    if c == 39:        # "'"
        return seq_apos_dec()
    return PSeq(c)


def escaped_seq(s):
    """The escape of a whole sequence: concatenate the per-code-point entity
    sequences (iterative here to avoid recursion limits; extensionally the
    same front-recursive fold as the model's pure region)."""
    out = PSeq()
    for k in range(len(s)):
        out = out + entity(s[k])
    return out


# --- the impl region of model.py, verbatim, contract calls stripped -----------

def render_value(value, engine_autoescape):
    # The context built for rendering inherits the renderer's policy flag.
    ctx_autoescape = engine_autoescape
    result = []  # type: list
    if ctx_autoescape:
        i = len(value)
        while i > 0:
            c = value[i - 1]
            if c == 38:
                result = [38, 97, 109, 112, 59] + result
            elif c == 60:
                result = [38, 108, 116, 59] + result
            elif c == 62:
                result = [38, 103, 116, 59] + result
            elif c == 34:
                result = [38, 113, 117, 111, 116, 59] + result
            elif c == 39:
                result = [38, 35, 51, 57, 59] + result
            else:
                result = [c] + result
            i = i - 1
    else:
        i = 0
        while i < len(value):
            result = result + [value[i]]
            i = i + 1
    return result
    # (the stripped Assert lines carried only proof-side sequence facts)


# --- oracle: the real patched Engine.render_to_string -------------------------

TEMPLATE_NAME = "conf_single_value.html"


def make_engines():
    """One REAL Engine per policy value, each holding an in-memory template
    that interpolates exactly one context value. The cached loader wrapper
    compiles the template once so 1e5+ renders stay cheap."""
    from django.conf import settings
    if not settings.configured:
        settings.configure()
    from django.template import Engine
    loaders = [(
        "django.template.loaders.cached.Loader",
        [("django.template.loaders.locmem.Loader",
          {TEMPLATE_NAME: "{{ obj }}"})],
    )]
    return {
        True: Engine(loaders=loaders, autoescape=True),
        False: Engine(loaders=loaders, autoescape=False),
    }


# --- differential driver -------------------------------------------------------

def check(engines, s, flag):
    """Run shadow and oracle on one (value, policy) pair; return an error
    string on disagreement, else None."""
    value = [ord(ch) for ch in s]                       # bridge: str -> List[int]
    shadow = render_value(value, flag)
    rendered = engines[flag].render_to_string(TEMPLATE_NAME, {"obj": s})
    real = [ord(ch) for ch in str(rendered)]            # bridge back
    if shadow != real:
        return ("DISAGREEMENT on value %r (code points %r), policy=%r:\n"
                "  shadow (impl region)          = %r\n"
                "  real (patched render_to_string) = %r (%r)"
                % (s, value, flag, shadow, real, str(rendered)))
    # internal cross-check: the executable impl agrees with the pure spec fold
    if flag:
        if ToSeq(shadow) != escaped_seq(ToSeq(value)):
            return ("INTERNAL: impl region and pure escaped_seq disagree on %r"
                    % s)
    else:
        if ToSeq(shadow) != ToSeq(value):
            return "INTERNAL: impl region not verbatim on %r" % s
    return None


def boundary_cases():
    significant = ["&", "<", ">", '"', "'"]
    cases = [""]
    cases += significant                             # each significant char alone
    cases += [c + c for c in significant]            # doubled
    cases += ["".join(significant)]                  # all five together
    cases += ["".join(reversed(significant))]
    cases += ["a" + c for c in significant]          # trailing significant
    cases += [c + "a" for c in significant]          # leading significant
    cases += ["x" + c + "y" for c in significant]    # embedded
    cases += [
        "<script>",                                  # the F2P witness value
        "<script>alert('xss')</script>",
        "a&b<c>d\"e'f",
        "x=1&amp;y=&lt;2&gt;",                       # entity text: double-escapes
        "&amp;", "&#39;", "&quot;", "&lt;", "&gt;",
        "&#x27;", "&apos;",
        "Joe's Crab Shack",
        "Can't find my keys",
        "obj:<script>",
        "{{ obj }}", "{% if %}", "{#c#}",            # data, never re-parsed
        "plain text", "  spaced  ", "line\nbreak", "tab\there",
        "\r", "\r\n", "\x00", "\x7f",
        "e\u0301", "\u00e9", "\u2022", "\U0001F600",
        "\U0001F600<\U0001F600", "&\U0001F600;",
        "0", "9", ";", "#", "%", "=", "/",
    ]
    return cases


def main():
    engines = make_engines()
    checked = 0

    boundary = boundary_cases()
    for s in boundary:
        for flag in (True, False):
            err = check(engines, s, flag)
            if err:
                print(err)
                return 1
            checked += 1

    # per-code-point sweep around each significant character's class boundary
    sweep_cps = []
    for cp in (34, 38, 39, 60, 62):
        sweep_cps += [cp - 1, cp, cp + 1]
    sweep_cps += [0, 1, 9, 10, 13, 32, 47, 58, 59, 61, 63, 64, 65,
                  0x7f, 0x80, 0xa0, 0xe9, 0x2022, 0x10000, 0x1F600, 0x10FFFF]
    for cp in sweep_cps:
        if cp < 0 or 0xD800 <= cp <= 0xDFFF:
            continue
        ch = chr(cp)
        for s in (ch, "a" + ch, ch + "b", "a" + ch + "b", ch + "&" + ch):
            for flag in (True, False):
                err = check(engines, s, flag)
                if err:
                    print(err)
                    return 1
                checked += 1

    # randomized fuzz: significant chars weighted heavily, entity fragments,
    # ordinary text, unicode (pinned seed)
    rng = random.Random(SEED)
    alphabet = (["&", "<", ">", '"', "'"] * 3
                + ["a", "Z", "0", "9", " ", ";", "#", "m", "p", "l", "t",
                   "q", "u", "o", "g", "x", "3", "7", "2", "-", ".", "=",
                   "\n", "\t"]
                + ["\u00e9", "\u2022", "\U0001F600"])
    for _ in range(N_FUZZ):
        n = rng.randint(0, 24)
        s = "".join(rng.choice(alphabet) for _ in range(n))
        for flag in (True, False):
            err = check(engines, s, flag)
            if err:
                print(err)
                return 1
            checked += 1

    print("G-CONF OK: shadow impl == real patched Engine.render_to_string on "
          "%d (value, policy) inputs (%d boundary + sweep + %d fuzz values, "
          "both policy values each, seed %d); 0 disagreements."
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({"checked": checked, "disagreements": 0, "seed": SEED,
                      "shadow": "direct (contract-stripped impl region)"}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
