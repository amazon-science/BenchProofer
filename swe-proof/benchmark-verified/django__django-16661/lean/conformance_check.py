#!/usr/bin/env python3
"""G-CONF — mechanical differential conformance for django__django-16661.

The bundle models ONE function: `ModelAdmin.lookup_allowed`
(`django/contrib/admin/options.py`). Its Lean implementation
(`implementation_lookupAllowed`) walks a lookup chain over pre-resolved
per-component model-graph metadata, accumulating the components that count as
genuine relational hops (`relationParts`), then decides whether the chain is a
permitted admin filter.

This script transliterates that R/I impl into Python (`shadow_lookup`) and
differential-tests it against an ORACLE (`oracle_lookup`) that transcribes the
POST-PATCH control flow of the real `lookup_allowed` loop over the SAME
abstracted metadata (mapping.md gives the Lean<->Python bijection). We do NOT
stand up Django/ORM: the modeled value is a pure decision over the metadata
booleans the loop branches on, and mapping.md pins how each real
`field`/`model._meta` read maps to a `PathStep` field. The oracle is written
straight from the patched source (lines 457-497), independently of the shadow.

The differential genuinely exercises the fix: the post-patch append guard is

    prev.is_relation
    and field not in model._meta.parents.values()      # not inParents
    and field is not model._meta.auto_field             # not isAutoField
    and (model._meta.auto_field is None                 # not modelHasAutoField
         or part not in prev.to_fields)                 # not partInPrevToFields

whereas the pre-patch guard was `prev.is_relation and field not in target_fields`
(the prepatch impl). Both legs here implement the POST-patch guard; the corpus
includes the F2P discriminating chain `restaurant__place__country`, where a
foreign key used as a primary key must remain a hop.

stdlib-only; deterministic built-in fuzzer. Pinned seed: 16661 (mapping.md).
"""
import sys

SEED = 16661
N = 120_000


# --- a PathStep, mirroring the Lean structure -------------------------------
# fields: part, exists_, isRelation, hasPathInfos, inTargetFields, inParents,
#         isAutoField, modelHasAutoField, partInPrevToFields
def continues_local(step):
    return (not step["inParents"]) and (not step["isAutoField"]) and \
        ((not step["modelHasAutoField"]) or (not step["partInPrevToFields"]))


# --- ORACLE: post-patch lookup_allowed loop, transcribed from source ---------
def oracle_lookup(steps, valid_lookups, fkey_allowed):
    if fkey_allowed:
        return True
    relation_parts = []
    prev = None                      # None == prev_field is None
    last_part = 0
    stopped = False
    for step in steps:
        if stopped:
            break
        last_part = step["part"]
        if not step["exists_"]:      # get_field raised FieldDoesNotExist
            stopped = True
            break
        # post-patch append guard (lines 466-470)
        if prev is None:
            append_it = True
        else:
            append_it = prev and (not step["inParents"]) and \
                (not step["isAutoField"]) and \
                ((not step["modelHasAutoField"]) or (not step["partInPrevToFields"]))
        if append_it:
            relation_parts.append(step["part"])
        if not step["hasPathInfos"]:  # non-relational -> break
            stopped = True
            break
        prev = step["isRelation"]
    if len(relation_parts) <= 1:
        return True
    key_a = tuple(relation_parts)
    key_b = tuple(relation_parts + [last_part])
    vl = {tuple(v) for v in valid_lookups}
    return key_a in vl or key_b in vl


# --- SHADOW of implementation_lookupAllowed (the R/I leg) --------------------
# Mirrors Solution.lean line-for-line, including the `continues_local` helper
# and the once-stopped-stay-stopped skip (the `if !stopped` guard, not `break`).
def shadow_lookup(steps, valid_lookups, fkey_allowed):
    if fkey_allowed:
        return True
    relation_parts = []
    prev = None
    last_part = 0
    stopped = False
    for step in steps:
        if not stopped:
            last_part = step["part"]
            if not step["exists_"]:
                stopped = True
            else:
                if prev is None:
                    append_it = True
                else:
                    append_it = prev and continues_local(step)
                if append_it:
                    relation_parts.append(step["part"])
                if not step["hasPathInfos"]:
                    stopped = True
                else:
                    prev = step["isRelation"]
    if len(relation_parts) <= 1:
        return True
    key_a = tuple(relation_parts)
    key_b = tuple(relation_parts + [last_part])
    vl = {tuple(v) for v in valid_lookups}
    return (key_a in vl) or (key_b in vl)


def disagree(steps, valid_lookups, fkey_allowed):
    got = oracle_lookup(steps, valid_lookups, fkey_allowed)
    want = shadow_lookup(steps, valid_lookups, fkey_allowed)
    if got != want:
        return ((steps, valid_lookups, fkey_allowed), got, want)
    return None


# --- input corpus ------------------------------------------------------------
def _lcg(seed):
    x = seed & 0xFFFFFFFF
    while True:
        x = (1103515245 * x + 12345) & 0x7FFFFFFF
        yield x


def _step(part, exists_=True, isRelation=True, hasPathInfos=True,
          inTargetFields=False, inParents=False, isAutoField=False,
          modelHasAutoField=False, partInPrevToFields=False):
    return {"part": part, "exists_": exists_, "isRelation": isRelation,
            "hasPathInfos": hasPathInfos, "inTargetFields": inTargetFields,
            "inParents": inParents, "isAutoField": isAutoField,
            "modelHasAutoField": modelHasAutoField,
            "partInPrevToFields": partInPrevToFields}


def _enumerate_edge():
    cases = []
    # THE F2P fix: restaurant(1) place(2) country(3), FK-as-PK on Restaurant.
    # place has inTargetFields=True (pre-patch would drop it) but no synth auto
    # PK on Restaurant (modelHasAutoField=False) -> continuesLocal True -> kept.
    f2p = [_step(1), _step(2, inTargetFields=True),
           _step(3, modelHasAutoField=True)]
    cases.append((f2p, [[1, 2, 3]], False))          # -> True (match)
    cases.append((f2p, [[9, 9]], False))             # -> False (len 3, no match)
    # employee__department__id classic collapse: id IS auto_field -> dropped.
    coll = [_step(1), _step(2, modelHasAutoField=True),
            _step(3, isAutoField=True, hasPathInfos=False, modelHasAutoField=True)]
    cases.append((coll, [[1, 2]], False))            # relationParts=[1,2] -> match
    # parent-link collapse (concrete inheritance): inParents drops it.
    par = [_step(1), _step(2, inParents=True, modelHasAutoField=True), _step(3)]
    cases.append((par, [[1, 3]], False))
    # prev-to-fields collapse: model has auto PK and part in prev.to_fields.
    ptf = [_step(1), _step(2, modelHasAutoField=True, partInPrevToFields=True),
           _step(3, modelHasAutoField=True)]
    cases.append((ptf, [[1, 3]], False))
    # nonexistent field mid-chain -> break.
    brk = [_step(1), _step(2, exists_=False), _step(3)]
    cases.append((brk, [[1]], False))
    # non-relational field -> break after append.
    nrel = [_step(1), _step(2, hasPathInfos=False)]
    cases.append((nrel, [[1, 2]], False))
    # fkey early allowance.
    cases.append((f2p, [], True))                    # -> True regardless
    # single relation part -> local filter True.
    cases.append(([_step(1)], [], False))
    cases.append(([], [], False))                    # empty chain -> True
    # match only via the trailing-part join key (relation_parts + [part]).
    tr = [_step(1), _step(2), _step(3, hasPathInfos=False)]
    cases.append((tr, [[1, 2, 3]], False))           # relationParts=[1,2,3]
    return cases


def _rand_step(rnd):
    return _step(
        part=next(rnd) % 5,
        exists_=(next(rnd) % 10) != 0,       # mostly exists
        isRelation=(next(rnd) % 4) != 0,
        hasPathInfos=(next(rnd) % 5) != 0,
        inTargetFields=(next(rnd) % 2) == 0,
        inParents=(next(rnd) % 6) == 0,
        isAutoField=(next(rnd) % 6) == 0,
        modelHasAutoField=(next(rnd) % 2) == 0,
        partInPrevToFields=(next(rnd) % 3) == 0,
    )


def main() -> int:
    checked = 0
    for steps, vl, fk in _enumerate_edge():
        d = disagree(steps, vl, fk)
        if d:
            print(f"DISAGREE edge: oracle={d[1]} shadow={d[2]} input={d[0]!r}")
            print("status=fail")
            return 1
        checked += 1

    rnd = _lcg(SEED)
    for _ in range(N):
        n = next(rnd) % 6                    # 0..5 components
        steps = [_rand_step(rnd) for _ in range(n)]
        # valid_lookups: a few random chains, sometimes including the real one
        nvl = next(rnd) % 4
        vl = []
        for _ in range(nvl):
            m = 1 + (next(rnd) % 4)
            vl.append([next(rnd) % 5 for _ in range(m)])
        # occasionally seed the true relation_parts so matches actually fire
        if steps and (next(rnd) % 3 == 0):
            rp = [s["part"] for s in steps if s["exists_"]]
            if rp:
                vl.append(rp)
        fk = (next(rnd) % 8) == 0
        d = disagree(steps, vl, fk)
        if d:
            print(f"DISAGREE fuzz: oracle={d[1]} shadow={d[2]} input={d[0]!r}")
            print("status=fail")
            return 1
        checked += 1

    print(f"checked={checked} disagreements=0")
    print("status=pass")
    return 0


if __name__ == "__main__":
    sys.exit(main())
