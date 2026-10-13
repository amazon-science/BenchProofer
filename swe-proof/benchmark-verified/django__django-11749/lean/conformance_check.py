#!/usr/bin/env python3
"""G-CONF for django__django-11749.

Differential test: the Lean impl's R/I shadow (Python re-implementation of
`implementation_requiredOptionArgs`) vs the behaviour of the gold patch's
`parse_args` construction, over >=1e5 fuzzed parser configurations. Exit 0 iff
zero disagreements. stdlib-only.

Bridge (mapping.md): a ParserAction is (id, option_strings, required, dest); a
group is (required, [action ids]). The two dict-shaped inputs are carried
SEPARATELY, because the source reads them from two different dicts:
`option_keys` is the set of keys the caller passed (`options`), and
`arg_options` is the value table the source subscripts. The patched predicate
forwards `min(option_strings)=arg_options[dest]` for each action whose dest is
in `options` and (required or it is in a required group).

WHY TWO DICTS AND NOT ONE (the defect this revision fixes). The source builds

    opt_mapping = {min(s.option_strings).lstrip('-').replace('-','_'): s.dest
                   for s in parser._actions if s.option_strings}
    arg_options = {opt_mapping.get(key, key): value
                   for key, value in options.items()}

so `arg_options` is `options` REKEYED: a caller key that matches some action's
flag-derived name is replaced by that action's `dest`. The patched comprehension
then tests membership against `options` but reads the value from `arg_options`,
and those are different dicts whenever the renaming fires. An earlier revision
of this script modeled BOTH sides with a single dict and used
`options.get(dest, "")` on the shadow AND the oracle, which made the comparison
shadow-vs-shadow at exactly the input where the model and the repo disagreed --
the same blind spot documented below for `min`, reproduced for the subscript.
Measured against the real repo at the patched commit, with a command declaring
a required mutually-exclusive group holding `--x` (dest `shop`) and `--shop`
(dest `shop_id`):

    call_command(cmd, shop='foo')
    opt_mapping['shop'] = 'shop_id'
    options     = {'shop': 'foo'}
    arg_options = {'shop_id': 'foo'}      <-- key 'shop' ABSENT (rekeyed)
    selected: dest='shop' flags=['--x'] required=False in_required_group=True
    -> KeyError: 'shop' at django/core/management/__init__.py:141

PARTIALITY (the point this check exists to pin down). The construction has TWO
partial operations, and BOTH are modeled rather than totalized:
  * the flag selection is a bare `min(opt.option_strings)`, which RAISES
    `ValueError: min() arg is an empty sequence` when a selected action declares
    no option flag at all -- an action with no flag is a positional, and a
    required positional (or a positional inside a required group) whose
    destination is supplied by keyword IS selected;
  * the value read is a bare `arg_options[opt.dest]` subscript, which RAISES
    `KeyError` when a SELECTED action's dest is not a key of the value table --
    reachable exactly as measured above, and newly reachable because the patch's
    mutually-exclusive-group disjunct selects actions the pre-patch predicate
    did not.
The construction produces no value at either point, and the Lean model reflects
that by being `Option`-valued: `leastFlag?` is `none` on the empty flag list,
`argOptions.lookup dest` is `none` at an uncarried destination, and `renderAll`
propagates either. So the two sides here are compared as `list | None`, with
`None` meaning "the construction produced no value":
  * the shadow reaches it STRUCTURALLY, by mirroring `renderArg?`/`renderAll`;
  * the oracle reaches it OPERATIONALLY, by evaluating the real unguarded
    `min(...)` and the real unguarded subscript inside the real comprehension
    and catching ValueError and KeyError.
Neither side guards either operation behind a totalization. Both branches are
generated (`gen_case` draws k=0 flags, and draws the key sets independently so a
named dest need not be a carried key) and both are pinned as boundary cases.
"""
import json
import random
import sys

SEED = 11749
N = 120_000


def lean_shadow(actions, groups, option_keys, arg_options, prefix):
    """Mirror of implementation_requiredOptionArgs (R/I ops only).

    Returns None where the Lean model is `none`: some selected action has no
    least flag, or the value table carries nothing at its dest. Mirrors
    `leastFlag?` / `renderArg?` / `renderAll` directly.
    """
    in_required_group = set()
    for g in groups:
        if g["required"]:
            for aid in g["action_ids"]:
                in_required_group.add(aid)

    def least_flag(xs):                       # leastFlag? : List String -> Option
        if not xs:
            return None
        m = xs[0]
        for s in xs[1:]:
            if s < m:
                m = s
        return m

    out = list(prefix)
    for opt in actions:
        dest_in = opt["dest"] in option_keys           # destInOptions optionKeys
        if dest_in and (opt["required"] or opt["id"] in in_required_group):
            flag = least_flag(opt["option_strings"])   # leastFlag?
            if flag is None:
                return None                            # renderAll propagates
            if opt["dest"] not in arg_options:         # argOptions.lookup
                return None                            # renderAll propagates
            out.append("{}={}".format(flag, arg_options[opt["dest"]]))
    return out


def gold_patch(actions, groups, option_keys, arg_options, prefix):
    """Behaviour of the patched call_command parse_args construction.

    Models object identity via id: the required-group set collects the actual
    action objects (by id) of every required group. The flag selection is the
    REAL unguarded `min(opt.option_strings)` and the value read is the REAL
    unguarded `arg_options[opt.dest]` subscript; when the comprehension raises
    (empty flag list, or a dest the value table does not carry, on a selected
    action) the construction yields no value and that is reported as None,
    which is what the caller observes.
    """
    mutually_exclusive_required = {
        opt["id"]
        for g in groups if g["required"]
        for opt in actions if opt["id"] in set(g["action_ids"])
    }
    parse_args = list(prefix)
    try:
        parse_args += [
            "{}={}".format(min(opt["option_strings"]),
                           arg_options[opt["dest"]])
            for opt in actions if (
                opt["dest"] in option_keys and
                (opt["required"] or opt["id"] in mutually_exclusive_required)
            )
        ]
    except (ValueError, KeyError):
        return None
    return parse_args


def rand_str(rng, pool):
    return rng.choice(pool)


def gen_case(rng):
    n = rng.randint(0, 6)
    dest_pool = ["foo_id", "foo_name", "shop", "shop_id", "bar", "baz", "qux"]
    flag_pool = ["--foo-id", "--foo-name", "--shop", "--bar", "-b", "--baz", "--qux", "-a"]
    val_pool = ["1", "x", "foo", "", "12", "y"]
    actions = []
    for i in range(n):
        k = rng.randint(0, 3)
        ostr = rng.sample(flag_pool, k) if k <= len(flag_pool) else flag_pool[:]
        actions.append({
            "id": i,
            "option_strings": ostr,
            "required": rng.random() < 0.4,
            "dest": rand_str(rng, dest_pool),
        })
    # groups reference a random subset of action ids
    groups = []
    for _ in range(rng.randint(0, 3)):
        if n == 0:
            ids = []
        else:
            mm = rng.randint(0, n)
            ids = rng.sample(range(n), mm)
        groups.append({"required": rng.random() < 0.5, "action_ids": ids})
    # The caller's keys and the value table are drawn INDEPENDENTLY, because the
    # source's rekeying makes them independent: a named dest need not be a
    # carried key (that is the KeyError branch) and a carried key need not be
    # named. Correlated slightly so the ALIGNED configuration -- the common one
    # in practice -- is still well covered.
    option_keys, arg_options = [], {}
    for d in dest_pool:
        named = rng.random() < 0.5
        if named:
            option_keys.append(d)
        # carried with high probability when named, low when not: covers
        # aligned, named-but-uncarried, and carried-but-unnamed.
        if rng.random() < (0.8 if named else 0.25):
            arg_options[d] = rand_str(rng, val_pool)
    prefix = [rand_str(rng, ["pos1", "pos2", "3"]) for _ in range(rng.randint(0, 3))]
    return actions, groups, option_keys, arg_options, prefix


def main():
    rng = random.Random(SEED)
    mism = 0
    examples = []
    # boundary cases
    boundary = [
        ([], [], [], {}, []),
        ([{"id": 0, "option_strings": ["--foo-id"], "required": False, "dest": "foo_id"},
          {"id": 1, "option_strings": ["--foo-name"], "required": False, "dest": "foo_name"}],
         [{"required": True, "action_ids": [0, 1]}],
         ["foo_id"], {"foo_id": "1"}, []),
        # a required action declaring NO flag whose dest is supplied: the real
        # comprehension's min() raises, so the construction yields no value.
        ([{"id": 0, "option_strings": [], "required": True, "dest": "bar"}],
         [], ["bar"], {"bar": "hello"}, []),
        # same action inside a required group, not individually required.
        ([{"id": 0, "option_strings": [], "required": False, "dest": "bar"}],
         [{"required": True, "action_ids": [0]}], ["bar"], {"bar": "hello"}, []),
        # a flagless action that is NOT selected must not poison the result.
        ([{"id": 0, "option_strings": [], "required": False, "dest": "bar"},
          {"id": 1, "option_strings": ["--baz"], "required": True, "dest": "baz"}],
         [], ["baz"], {"baz": "2"}, ["app"]),
        # THE MEASURED WITNESS, transcribed. A required mutually-exclusive group
        # holding --x (dest shop) and --shop (dest shop_id); the caller passes
        # shop='foo', which opt_mapping rekeys to shop_id, so the value table
        # does NOT carry 'shop'. The group disjunct selects dest 'shop' and the
        # subscript raises KeyError: the construction yields no value.
        ([{"id": 0, "option_strings": ["--x"], "required": False, "dest": "shop"},
          {"id": 1, "option_strings": ["--shop"], "required": False, "dest": "shop_id"}],
         [{"required": True, "action_ids": [0, 1]}],
         ["shop"], {"shop_id": "foo"}, []),
        # the same shape with the caller naming the dest the table DOES carry:
        # the construction succeeds, so the KeyError branch is not spurious.
        ([{"id": 0, "option_strings": ["--x"], "required": False, "dest": "shop"},
          {"id": 1, "option_strings": ["--shop"], "required": False, "dest": "shop_id"}],
         [{"required": True, "action_ids": [0, 1]}],
         ["shop_id"], {"shop_id": "7"}, []),
        # a value carried at a dest that was NOT named: not selected, so the
        # construction is defined and the value is simply unused.
        ([{"id": 0, "option_strings": ["--bar"], "required": True, "dest": "bar"}],
         [], [], {"bar": "9"}, []),
    ]
    cases = boundary + [gen_case(rng) for _ in range(N)]
    undef_flag = 0
    undef_value = 0
    for c in cases:
        a = lean_shadow(*c)
        b = gold_patch(*c)
        if b is None:
            # Which partial op fired? Re-run the oracle catching one at a time,
            # so the two undefined branches are counted SEPARATELY: a run that
            # reached only one of them would not have tested the other.
            actions, groups, option_keys, arg_options, _p = c
            mer = {
                opt["id"]
                for g in groups if g["required"]
                for opt in actions if opt["id"] in set(g["action_ids"])
            }
            sel = [o for o in actions
                   if o["dest"] in option_keys
                   and (o["required"] or o["id"] in mer)]
            if any(not o["option_strings"] for o in sel):
                undef_flag += 1
            if any(o["dest"] not in arg_options for o in sel):
                undef_value += 1
        if a != b:
            mism += 1
            if len(examples) < 5:
                examples.append({"case": c, "shadow": a, "gold": b})
    # Both undefined branches are load-bearing components of the postcondition,
    # so a run that never reached one of them would not have tested it: report
    # each count and fail if the generator stopped producing such inputs.
    missing = [nm for nm, ct in (("empty-flag", undef_flag),
                                 ("uncarried-dest", undef_value)) if ct == 0]
    if missing:
        print(json.dumps({"status": "fail", "cases": len(cases),
                          "mismatches": mism,
                          "error": "no case exercised the undefined branch(es): "
                                   + ", ".join(missing)}))
        sys.exit(1)
    status = "pass" if mism == 0 else "fail"
    print(json.dumps({"status": status, "cases": len(cases),
                      "mismatches": mism,
                      "undefined_empty_flag": undef_flag,
                      "undefined_uncarried_dest": undef_value,
                      "examples": examples}))
    sys.exit(0 if mism == 0 else 1)


if __name__ == "__main__":
    main()
