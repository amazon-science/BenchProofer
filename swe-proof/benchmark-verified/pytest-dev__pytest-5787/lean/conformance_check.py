#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for pytest-dev__pytest-5787.

The bundle models TWO routines (mapping.md):
  * serialization   — `serialize_longrepr` inside the post-patch `_report_to_json`
  * deserialization — the post-patch `_report_kwargs_from_json`
of a failure representation (`report.longrepr`), which is either a single
exception (one traceback + one crash location) or a chain of linked exceptions
(an ordered list of `(traceback, crash, description)` links). Both carry an
ordered list of titled sections.

Standing up real `ExceptionChainRepr`/`ReprTraceback` graphs requires raising and
chaining real exceptions and is heavy + brittle; the modeled values are PURE
functions of the data the (de)serialization reads. So the ORACLE below is a
faithful in-process replica of the POST-PATCH serialize/deserialize logic at the
data abstraction of mapping.md (the entry-payload copy — unchanged by the fix —
is modeled as the identity, matching `packLink`/`unpackLink`), and the SHADOW is
the op-for-op transliteration of `implementation_serialize` /
`implementation_deserialize` (Solution.lean impl regions), per refinement.md.

This genuinely tests the soundness-critical clause: a CHAIN must survive a
serialize→deserialize round-trip with every link preserved, in order, with its
connective description — rather than collapsing to only its outermost exception
(the pre-patch regression the issue reports). It also pins the single-exception
and empty-chain cases.

stdlib-only. Pinned seed: 5787 (also in mapping.md).
"""
import random
import sys

SEED = 5787
N = 120_000

# ----- data model (mapping.md bijection) -------------------------------------
# FileLoc          -> {"path": str, "lineno": int, "message": str}
# Traceback        -> {"entries": [str], "extraline": str|None, "style": str}
# Link             -> (Traceback, FileLoc, description: str|None)
# Longrepr.single  -> ("single", traceback, crash, sections)
# Longrepr.chained -> ("chained", [Link], sections)
# Serialized       -> {"crash": FileLoc, "traceback": Traceback,
#                      "sections": [...], "chain": [Link]|None}
# sections         -> [(name, content, sep)]


def outer_of(chain):
    # last link's (traceback, crash); chain is non-empty in the chained case
    if chain:
        tb, cr, _desc = chain[-1]
        return (tb, cr)
    return (None, None)


# ----- ORACLE: faithful replica of POST-PATCH logic --------------------------
def oracle_serialize(lr):
    kind = lr[0]
    if kind == "single":
        _, tb, cr, secs = lr
        # serialize_longrepr: reprcrash, reprtraceback, sections; non-chain -> chain=None
        return {"crash": cr, "traceback": tb, "sections": secs, "chain": None}
    else:
        _, chain, secs = lr
        tb, cr = outer_of(chain)  # = ExceptionChainRepr.reprtraceback/reprcrash = chain[-1]
        ser_chain = []
        for repr_tb, repr_crash, description in chain:
            ser_chain.append((repr_tb, repr_crash, description))
        return {"crash": cr, "traceback": tb, "sections": secs, "chain": ser_chain}


def oracle_deserialize(s):
    # _report_kwargs_from_json: if chain truthy -> ExceptionChainRepr(chain);
    # else ReprExceptionInfo(reprtraceback, reprcrash). sections carried through.
    if s["chain"]:
        chain = []
        for repr_tb, repr_crash, description in s["chain"]:
            chain.append((repr_tb, repr_crash, description))
        return ("chained", chain, s["sections"])
    else:
        return ("single", s["traceback"], s["crash"], s["sections"])


# ----- SHADOW of the Lean impl (the R/I legs) --------------------------------
def shadow_serialize(lr):
    kind = lr[0]
    if kind == "single":
        _, tb, cr, secs = lr
        return {"crash": cr, "traceback": tb, "sections": secs, "chain": None}
    else:
        _, chain, secs = lr
        outer = outer_of(chain)
        ser_chain = []
        for link in chain:           # for link in chain do serChain := serChain ++ [packLink link]
            ser_chain = ser_chain + [link]
        return {"crash": outer[1], "traceback": outer[0], "sections": secs,
                "chain": ser_chain}


def shadow_deserialize(s):
    chain = s["chain"]
    if chain is not None and len(chain) >= 1:   # match s.chain with | some (l :: ls)
        de_chain = []
        for link in chain:           # for link in (l :: ls) do deChain := deChain ++ [unpackLink link]
            de_chain = de_chain + [link]
        return ("chained", de_chain, s["sections"])
    else:                             # | _ => .single ...
        return ("single", s["traceback"], s["crash"], s["sections"])


# ----- fuzzers ----------------------------------------------------------------
def rand_fileloc(rng):
    return {"path": rng.choice(["mod.py", "test_x.py", "a/b.py", ""]),
            "lineno": rng.randint(0, 500),
            "message": rng.choice(["ValueError", "RuntimeError: x", "", "E   boom"])}


def rand_traceback(rng):
    n = rng.randint(0, 4)
    return {"entries": [rng.choice(["    def f():", ">   g()", "E   ValueError", ""])
                        for _ in range(n)],
            "extraline": rng.choice([None, "", ":3: ValueError"]),
            "style": rng.choice(["long", "short", "native"])}


def rand_sections(rng):
    n = rng.randint(0, 3)
    return [(rng.choice(["title", "Captured log", "x"]),
             rng.choice(["contents", "", "line1\nline2"]),
             rng.choice(["-", "=", "_"])) for _ in range(n)]


def rand_link(rng):
    desc = rng.choice([None,
                       "The above exception was the direct cause of the following exception:",
                       "During handling of the above exception, another exception occurred:"])
    return (rand_traceback(rng), rand_fileloc(rng), desc)


def rand_longrepr(rng):
    if rng.random() < 0.5:
        return ("single", rand_traceback(rng), rand_fileloc(rng), rand_sections(rng))
    else:
        n = rng.randint(1, 4)   # a real ExceptionChainRepr always has >=1 link
        return ("chained", [rand_link(rng) for _ in range(n)], rand_sections(rng))


def rand_serialized(rng):
    # exercise the deserialize branch directly, incl. chain=None and chain=[]
    chain_choice = rng.random()
    if chain_choice < 0.4:
        chain = None
    elif chain_choice < 0.5:
        chain = []                       # empty list -> single branch (both legs)
    else:
        chain = [rand_link(rng) for _ in range(rng.randint(1, 4))]
    return {"crash": rand_fileloc(rng), "traceback": rand_traceback(rng),
            "sections": rand_sections(rng), "chain": chain}


def _edge_cases():
    tb = {"entries": ["    def f():", ">   g()"], "extraline": None, "style": "long"}
    cr = {"path": "mod.py", "lineno": 3, "message": "ValueError"}
    secs = [("title", "contents", "=")]
    # F2P: a 2-link chain (the #5786 scenario) must round-trip with both links
    link1 = (tb, cr, "The above exception was the direct cause of the following exception:")
    link2 = ({"entries": ["E   RuntimeError"], "extraline": None, "style": "long"},
             {"path": "mod.py", "lineno": 7, "message": "RuntimeError"}, None)
    yield ("chained", [link1, link2], secs)
    # single exception
    yield ("single", tb, cr, secs)
    # one-link chain
    yield ("chained", [link1], [])
    # chain with no sections
    yield ("chained", [link1, link2], [])


def disagree_serialize(lr):
    g, w = oracle_serialize(lr), shadow_serialize(lr)
    return None if g == w else (lr, g, w)


def disagree_deserialize(s):
    g, w = oracle_deserialize(s), shadow_deserialize(s)
    return None if g == w else (s, g, w)


def disagree_roundtrip(lr):
    """The property the issue demands: deserialize(serialize(x)) preserves the
    chain. Compare oracle round-trip vs shadow round-trip (and to each other)."""
    o = oracle_deserialize(oracle_serialize(lr))
    sh = shadow_deserialize(shadow_serialize(lr))
    return None if o == sh else (lr, o, sh)


def main() -> int:
    checked = 0
    for lr in _edge_cases():
        for d in (disagree_serialize(lr), disagree_roundtrip(lr)):
            if d:
                print(f"DISAGREE edge: in={d[0]} oracle={d[1]} shadow={d[2]}")
                print("status=fail")
                return 1
        checked += 2

    rng = random.Random(SEED)
    for _ in range(N):
        lr = rand_longrepr(rng)
        for d in (disagree_serialize(lr), disagree_roundtrip(lr)):
            if d:
                print(f"DISAGREE fuzz(longrepr): in={d[0]} oracle={d[1]} shadow={d[2]}")
                print("status=fail")
                return 1
        s = rand_serialized(rng)
        d = disagree_deserialize(s)
        if d:
            print(f"DISAGREE fuzz(serialized): in={d[0]} oracle={d[1]} shadow={d[2]}")
            print("status=fail")
            return 1
        checked += 3

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
