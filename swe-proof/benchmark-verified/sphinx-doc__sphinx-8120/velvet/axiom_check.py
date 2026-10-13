#!/usr/bin/env python3
"""G-AX executable soundness check for sphinx-doc__sphinx-8120.

Validates the ONE kind-A-reference of this bundle: the deep model `resolve`
(Solution.lean `pure` region) faithfully captures the message-lookup precedence
of the REAL, unchanged callee `sphinx.locale.init`
(`sphinx/locale/__init__.py`). `_init_i18n` (the function under change) calls
`init` with the assembled list; the modeled property is that `init` searches the
directory list IN ORDER, the first directory defining a message supplies it, and
later directories only fill in messages no earlier directory defined — exactly

    resolve cat (d :: ds) k = (cat d k).orElse (fun _ => resolve cat ds k)

Method: build real gettext `.mo` catalogs in temporary directories, assemble the
`locale_dirs` list (including a `None` system-default entry, per the model's
`sysNone`), call the REAL `sphinx.locale.init`, and assert the resulting
translator's `gettext` observations equal `resolve` over boundary + fuzz
configurations: user-overrides-package, package-only, system-only, conflicting
multi-dir definitions, and the empty list. Exit 0 iff the deep model matches the
real loader's precedence on every observation.

Imports `sphinx.locale` (the same module the gold patch keeps) + stdlib only.
"""
import os
import random
import struct
import sys
import tempfile


# --- minimal .mo writer (GNU gettext binary format) --------------------------
def write_mo(path, entries):
    """Write a .mo file mapping msgid->msgstr for the dict `entries`."""
    keys = sorted(entries.keys())
    offsets = []
    ids = b""
    strs = b""
    for k in keys:
        kb = k.encode("utf-8")
        vb = entries[k].encode("utf-8")
        offsets.append((len(ids), len(kb), len(strs), len(vb)))
        ids += kb + b"\x00"
        strs += vb + b"\x00"
    n = len(keys)
    keystart = 7 * 4 + 16 * n
    valuestart = keystart + len(ids)
    koffsets = []
    voffsets = []
    for o1, l1, o2, l2 in offsets:
        koffsets += [l1, o1 + keystart]
        voffsets += [l2, o2 + valuestart]
    output = struct.pack("Iiiiiii", 0x950412de, 0, n, 7 * 4,
                         7 * 4 + n * 8, 0, 0)
    output += struct.pack("i" * len(koffsets), *koffsets)
    output += struct.pack("i" * len(voffsets), *voffsets)
    output += ids
    output += strs
    with open(path, "wb") as f:
        f.write(output)


# --- the deep model under test: Solution.lean `resolve` ----------------------
def resolve(cat, dirs, k):
    """resolve cat dirs k — first dir defining k wins; else fall through."""
    for d in dirs:
        v = cat(d, k)
        if v is not None:
            return v
    return None


# --- harness: make a locale tree and call the REAL sphinx.locale.init --------
LANG = "de"
CATALOG = "sphinx"


def make_dir(base, name, entries):
    """Create <base>/<name>/<LANG>/LC_MESSAGES/sphinx.mo with `entries`.
    Returns the locale-dir path to pass to init (the <name> level)."""
    d = os.path.join(base, name)
    lc = os.path.join(d, LANG, "LC_MESSAGES")
    os.makedirs(lc, exist_ok=True)
    write_mo(os.path.join(lc, CATALOG + ".mo"), entries)
    return d


def check_config(locale, dir_specs, msg_keys, ns_counter):
    """dir_specs: ordered list of (kind, entries_dict_or_None). kind 'sys' is the
    None system-default entry (no catalog; defines nothing here); kind 'dir'
    creates a real .mo dir. Build the list, call REAL init, and compare the real
    translator's gettext to `resolve` over msg_keys."""
    from sphinx import locale as sphinx_locale

    with tempfile.TemporaryDirectory() as base:
        dirs = []
        contents = {}            # dir-path -> its entries dict (for `cat`)
        for i, (kind, entries) in enumerate(dir_specs):
            if kind == "sys":
                dirs.append(None)
                contents[None] = {}
            else:
                p = make_dir(base, "d%d" % i, entries)
                dirs.append(p)
                contents[p] = entries

        def cat(d, key):
            return contents.get(d, {}).get(key)

        # fresh namespace each call so translators cache does not bleed across
        ns = "gax%d" % ns_counter[0]
        ns_counter[0] += 1
        sphinx_locale.translators.clear()
        translator, _ = sphinx_locale.init(dirs, locale, catalog=CATALOG,
                                           namespace=ns)

        for k in msg_keys:
            real = translator.gettext(k)
            model = resolve(cat, dirs, k)
            # gettext returns the msgid itself when undefined; the model's `none`
            # corresponds to "no override -> the built-in source string (msgid)".
            model_obs = model if model is not None else k
            assert real == model_obs, (
                "resolve deep model unsound: dirs=%r key=%r real gettext=%r "
                "model=%r" % (dirs, k, real, model_obs))


def main():
    ns_counter = [0]
    keys = ["Quick search", "Fig. %s", "Listing %s", "Search", "untouched"]

    # --- boundary configurations --------------------------------------------
    # user dir overrides package dir (the issue's scenario): user FIRST wins
    check_config(LANG, [
        ("sys", None),
        ("dir", {"Quick search": "QUICK SEARCH", "Fig. %s": "USERFIG %s"}),   # user
        ("dir", {"Quick search": "PKG SEARCH", "Fig. %s": "PKGFIG %s",
                 "Listing %s": "PKGLIST %s"}),                                # package
    ], keys, ns_counter)

    # package only (no user dir): package values used
    check_config(LANG, [
        ("sys", None),
        ("dir", {"Fig. %s": "PKGFIG %s", "Listing %s": "PKGLIST %s"}),
    ], keys, ns_counter)

    # empty list: nothing defined, everything falls through to msgid
    check_config(LANG, [], keys, ns_counter)

    # only the system-default sentinel (defines nothing in this harness)
    check_config(LANG, [("sys", None)], keys, ns_counter)

    # three dirs, layered/conflicting definitions: first definer wins per key
    check_config(LANG, [
        ("sys", None),
        ("dir", {"Quick search": "A"}),
        ("dir", {"Quick search": "B", "Search": "Bsearch"}),
        ("dir", {"Quick search": "C", "Search": "Csearch", "Fig. %s": "Cfig"}),
    ], keys, ns_counter)

    # --- randomized fuzz -----------------------------------------------------
    rng = random.Random(8120)
    vocab = keys
    for _ in range(400):
        ndirs = rng.randint(0, 4)
        specs = [("sys", None)] if rng.random() < 0.8 else []
        for _d in range(ndirs):
            entries = {}
            for key in vocab:
                if rng.random() < 0.5:
                    entries[key] = "v%d_%s" % (rng.randint(0, 999), key[:3])
            specs.append(("dir", entries))
        check_config(LANG, specs, vocab, ns_counter)

    print("G-AX OK: resolve deep model (== sphinx.locale.init search-order "
          "precedence) sound on 5 boundary + 400 fuzz directory configurations; "
          "first-defining-dir-wins confirmed against the real gettext loader.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
