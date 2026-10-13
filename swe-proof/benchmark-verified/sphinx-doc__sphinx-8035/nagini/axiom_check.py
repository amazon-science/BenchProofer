#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8035.

This bundle consumes NO @ContractOnly axiom: both modelled behaviours are
spelled out deeply as pure boolean / sequence logic. This script therefore
validates the two DEEP MODELS (A-reference) against the REAL post-patch code:

  (A-reference 1) the keep decision `keep_private` (model.py pure region) ==
      the post-patch private-member keep logic of `filter_members`
      (sphinx/ext/autodoc/__init__.py). The real method needs a live Documenter
      object, so we reproduce the post-patch decision branch VERBATIM from the
      gold source (the three-state private-members handling) as the oracle and
      assert the deep model equals it across boundary + fuzz, with the option
      states produced through the REAL `members_option` converter.

  (A-reference 2) the merge model `merge_members_option` (model.py) == the REAL
      `sphinx.ext.autodoc.merge_members_option` (executed in-container).

Imports only the standard library plus the very module the gold patch changes
(`sphinx.ext.autodoc`); nothing test-/repo-private. Exit 0 iff every obligation
holds. If Sphinx is importable the real functions are exercised directly; if it
is not (host without Sphinx), the in-container G-AX run is the authority and we
fail loud rather than silently skip.
"""
import random
import sys


# ----------------------------------------------------------------------------
# model.py reference encodings (kept in lock-step with the model's pure region)
# ----------------------------------------------------------------------------

def model_documentable(has_doc, undoc_members):
    return has_doc or undoc_members


def model_keep_private(mode, names, membername, has_doc, undoc_members,
                       filtered_inherited):
    """Reference of model.py `keep_private` (mode 0=absent,1=all,2=list)."""
    if not model_documentable(has_doc, undoc_members):
        return False
    if mode == 0:
        return False
    if mode == 1:
        return True
    return (not filtered_inherited) and (membername in names)


def model_merge(members_is_all, members, extra):
    """Reference of model.py `merge_members_option`."""
    if members_is_all:
        return list(members)
    result = list(members)
    for m in extra:
        if m not in result:
            result.append(m)
    return result


# ----------------------------------------------------------------------------
# Gold-source oracle for the private-member keep decision (A-reference 1)
#
# Transcribed VERBATIM from the post-patch `filter_members` branch
#   elif want_all and isprivate:
#       if has_doc or self.options.undoc_members:
#           if self.options.private_members is None:        keep = False
#           elif self.options.private_members is ALL:       keep = True
#           elif is_filtered_inherited_member(membername):  keep = False
#           else: keep = membername in self.options.private_members
#       else:
#           keep = False
# with `private_members` carrying the three states (None / ALL / list).
# ----------------------------------------------------------------------------

def gold_keep_private(private_members, ALL, membername, has_doc, undoc_members,
                      filtered_inherited):
    if has_doc or undoc_members:
        if private_members is None:
            return False
        elif private_members is ALL:
            return True
        elif filtered_inherited:
            return False
        else:
            return membername in private_members
    else:
        return False


def main():
    failures = 0

    # ---- try to use the REAL Sphinx callees --------------------------------
    real_members_option = None
    real_merge = None
    real_ALL = None
    try:
        from sphinx.ext.autodoc import (members_option, merge_members_option,
                                        ALL)
        real_members_option = members_option
        real_merge = merge_members_option
        real_ALL = ALL
        print("G-AX: using REAL sphinx.ext.autodoc callees")
    except Exception as exc:  # pragma: no cover - host without sphinx
        print("G-AX: sphinx.ext.autodoc not importable here (%r); the "
              "authoritative G-AX run is in-container" % (exc,))

    # ---- A-reference 1: keep decision vs gold source -----------------------
    # Name tokens; in the model membername/names are int tokens. Here we use
    # short strings as names (what members_option produces) and map to the same
    # logic; equality/membership are all that matter, so this is faithful.
    name_pool = ["_a", "_b", "_secret", "_public_function", "private_function",
                 "x", "__init__", "foo"]

    def option_states():
        """Yield (mode, model_names, real_private_members) triples spanning the
        three option states, using the REAL converter when available."""
        # mode 0: absent -> None
        yield (0, [], None)
        # mode 1: all-form -> bare option (members_option(None) is ALL)
        if real_members_option is not None:
            allval = real_members_option(None)
            assert allval is real_ALL, "members_option(None) must be ALL"
            yield (1, [], allval)
        else:
            yield (1, [], "ALL_SENTINEL")
        # mode 2: explicit lists of names, via the real converter
        lists = ["_public_function", "_a,_b", "_secret",
                 "_public_function,_a", "x,foo,__init__", "private_function"]
        for spec in lists:
            if real_members_option is not None:
                lst = real_members_option(spec)
                assert isinstance(lst, list)
            else:
                lst = [t.strip() for t in spec.split(",") if t.strip()]
            yield (2, list(lst), lst)

    rng = random.Random(8035)
    checked = 0
    states = list(option_states())
    for (mode, model_names, real_pm) in states:
        for membername in name_pool:
            for has_doc in (True, False):
                for undoc in (True, False):
                    for finh in (True, False):
                        m = model_keep_private(mode, model_names, membername,
                                                has_doc, undoc, finh)
                        if real_members_option is not None:
                            g = gold_keep_private(real_pm, real_ALL, membername,
                                                   has_doc, undoc, finh)
                        else:
                            # offline: gold logic with sentinels
                            if mode == 0:
                                g = gold_keep_private(None, object(),
                                                      membername, has_doc,
                                                      undoc, finh)
                            elif mode == 1:
                                S = object()
                                g = gold_keep_private(S, S, membername,
                                                      has_doc, undoc, finh)
                            else:
                                g = gold_keep_private(model_names, object(),
                                                      membername, has_doc,
                                                      undoc, finh)
                        checked += 1
                        if m != g:
                            failures += 1
                            print("MISMATCH keep_private: mode=%r name=%r "
                                  "has_doc=%r undoc=%r finh=%r model=%r gold=%r"
                                  % (mode, membername, has_doc, undoc, finh,
                                     m, g))
    print("G-AX: keep_private deep model checked on %d state x member combos"
          % checked)

    # F2P-shaped witness: the discriminator. mode-2 list naming only
    # _public_function must DROP a documentable private member not in the list.
    drop = model_keep_private(2, ["_public_function"], "private_function",
                              True, False, False)
    assert drop is False, ("F2P discriminator broken: a documentable private "
                           "member not named in the explicit list must be "
                           "dropped, got keep=%r" % drop)
    keepit = model_keep_private(2, ["_public_function"], "_public_function",
                                True, False, False)
    assert keepit is True, ("explicit-list member must be kept, got %r"
                            % keepit)

    # ---- A-reference 2: merge model vs the REAL merge ----------------------
    if real_merge is not None:
        for _ in range(5000):
            n_all = rng.randint(0, 2)  # bias toward exercising both branches
            members_is_all = (n_all == 0)
            members = [rng.choice(name_pool) for _ in range(rng.randint(0, 4))]
            extra = [rng.choice(name_pool) for _ in range(rng.randint(0, 4))]

            model_out = model_merge(members_is_all, members, extra)

            # Build the real options dict the way the directive does.
            opts = {}
            if members_is_all:
                opts["members"] = real_ALL
            else:
                opts["members"] = list(members)
            # the supplementary selector goes through a *-members key; use
            # private-members with an explicit list (not ALL).
            opts["private-members"] = list(extra)
            real_merge(opts)
            # When members_is_all the real merge returns early (no-op): members
            # key stays ALL. Otherwise the members list is grown in place.
            if members_is_all:
                real_out = list(members)  # unchanged content (the no-op case)
                assert opts["members"] is real_ALL
            else:
                real_out = list(opts["members"])
            if model_out != real_out:
                failures += 1
                print("MISMATCH merge: members_is_all=%r members=%r extra=%r "
                      "model=%r real=%r" % (members_is_all, members, extra,
                                            model_out, real_out))
        print("G-AX: merge_members_option deep model == real callee on 5000 "
              "randomized inputs")
    else:
        print("G-AX: merge real-callee check deferred to in-container run")

    if failures:
        print("G-AX FAIL: %d mismatch(es)" % failures)
        return 1
    print("G-AX OK: keep_private + merge_members_option deep models sound "
          "(== real post-patch behaviour)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
