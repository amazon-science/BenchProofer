#!/usr/bin/env python3
"""G-CONF differential conformance check for sphinx-doc__sphinx-8120 (nagini).

SHADOW: the impl region of model.py `select_translation`, copied verbatim
below with the contract calls (Requires/Ensures/Invariant/Assert) stripped.
The @Pure helpers (NO_TEXT/seq_defines/seq_tr/resolved/some_provides/
first_provider) copy over as plain functions on top of a small
immutable-tuple PSeq shim and serve as an internal cross-check of the
executable shadow. There are no @ContractOnly callees in this bundle.

ORACLE: the REAL patched repo method per mapping.md — `Sphinx._init_i18n`
(sphinx/application.py), which assembles the ordered catalog-source list and
resolves the message catalog through the unchanged `sphinx.locale.init` +
gettext merge. It is driven on a real Sphinx instance shell (the i18n state
it reads: srcdir, config.language, config.locale_dirs, source_encoding) with
real compiled `.mo` catalogs written under temporary project localedirs and a
temporary bundled-locale parent substituted for the package dir, then
observed through `translator.gettext(message)`. The gate applies patch.diff
to /testbed before this script runs; the script inserts /testbed at the head
of sys.path so the patched modules are imported. Both the module-level
translator registry and gettext's per-path translation cache are cleared
between scenarios (gettext caches by file path, and fallback chaining
mutates the cached objects in place).

Type bridge (mapping.md section 2): each distinct text is a distinct int
code >= 1 with a distinct backing string; the untranslated sentinel NO_TEXT
(0) maps to gettext returning the message string itself. Per source:
defines <-> "the source's compiled catalog has an entry for the message"
(a source with no catalog at all is skipped by the loader — same False
flag, both variants generated); tr <-> the code of the entry's text. The
system default source (the leading None localedir) provides nothing for
this catalog/language in any reachable configuration, so scenarios drive
system_defines=False (mirroring `[None]` exactly); the shadow still runs
the full assembled order.

Input domain: the preconditions demand parallel project lists, message and
provided texts coded >= 1 — satisfied by construction. Scenarios vary the
project-source count (0-5), which sources exist/provide, text codes
(including shared texts across sources), and the bundled source's presence.

>= 1e5 Requires-satisfying inputs: boundary scenarios + 100000 fuzz
scenarios. Pinned fuzz seed: 8120.

Exit 0 iff zero disagreements; on disagreement prints the scenario and both
outcomes and exits 1. stdlib + sphinx (the repo under test) only.
"""
import gettext
import json
import os
import random
import struct
import sys
import tempfile
import types

SEED = 8120
N_FUZZ = 100000

sys.path.insert(0, '/testbed')

from sphinx.application import Sphinx      # noqa: E402
import sphinx.application as sphinx_app_mod  # noqa: E402
import sphinx.locale as sphinx_locale        # noqa: E402


# --- PSeq shim: immutable sequence, the operations the pure region uses -------

class PSeq:
    __slots__ = ("_t",)

    def __init__(self, *items):
        self._t = tuple(items)

    @classmethod
    def _wrap(cls, t):
        s = cls()
        s._t = tuple(t)
        return s

    def take(self, n):
        return PSeq._wrap(self._t[:n])

    def drop(self, n):
        return PSeq._wrap(self._t[n:])

    def __add__(self, other):
        return PSeq._wrap(self._t + other._t)

    def __len__(self):
        return len(self._t)

    def __getitem__(self, i):
        return self._t[i]

    def __eq__(self, other):
        return isinstance(other, PSeq) and self._t == other._t


def ToSeq(lst):
    return PSeq._wrap(lst)


# --- pure helpers from model.py, contracts stripped ----------------------------

def NO_TEXT():
    return 0


def seq_defines(system_defines, ud, builtin_defines):
    return (PSeq(system_defines) + ud) + PSeq(builtin_defines)


def seq_tr(system_tr, ut, builtin_tr):
    return (PSeq(system_tr) + ut) + PSeq(builtin_tr)


def resolved(defines, tr):
    if len(defines) == 0:
        return NO_TEXT()
    if defines[0]:
        return tr[0]
    return resolved(defines.drop(1), tr.drop(1))


def some_provides(defines):
    if len(defines) == 0:
        return False
    if defines[0]:
        return True
    return some_provides(defines.drop(1))


def first_provider(defines):
    if defines[0]:
        return 0
    return 1 + first_provider(defines.drop(1))


# --- the impl region of model.py, verbatim, contract calls stripped ------------

def select_translation(system_defines, system_tr,
                       user_defines, user_tr,
                       builtin_defines, builtin_tr,
                       message):
    # Assemble the ordered source list:  default, then project sources, then
    # the bundled fallback (project sources ahead of the bundled fallback).
    defines = [system_defines]
    defines = defines + user_defines
    defines = defines + [builtin_defines]
    tr = [system_tr]
    tr = tr + user_tr
    tr = tr + [builtin_tr]

    n = len(defines)
    # Backward fold: build the first-wins resolution of the suffix `drop(i)`.
    res = NO_TEXT()
    i = n
    while i > 0:
        if defines[i - 1]:
            res = tr[i - 1]
        i = i - 1

    out = res
    if res == NO_TEXT():
        out = message
    return out


# --- .mo writer (the standard little-endian catalog layout) --------------------

def write_mo(path, mapping):
    keys = sorted(mapping)
    n = len(keys)
    ids = b''
    strs = b''
    id_off = []
    str_off = []
    for k in keys:
        kb = k.encode('utf-8')
        vb = mapping[k].encode('utf-8')
        id_off.append((len(kb), len(ids)))
        ids += kb + b'\x00'
        str_off.append((len(vb), len(strs)))
        strs += vb + b'\x00'
    keystart = 28 + 16 * n
    valstart = keystart + len(ids)
    out = struct.pack('<7I', 0x950412de, 0, n, 28, 28 + 8 * n, 0, 0)
    for length, off in id_off:
        out += struct.pack('<2I', length, keystart + off)
    for length, off in str_off:
        out += struct.pack('<2I', length, valstart + off)
    out += ids + strs
    with open(path, 'wb') as f:
        f.write(out)


# --- oracle driver ---------------------------------------------------------------

LANG = 'xx'
NPROJ = 5


def main():
    root = tempfile.mkdtemp(prefix='confch_')
    proj = []
    for i in range(NPROJ):
        d = os.path.join(root, 'proj%d' % i)
        os.makedirs(os.path.join(d, LANG, 'LC_MESSAGES'))
        proj.append(d)
    bundled_parent = os.path.join(root, 'bundled')
    os.makedirs(os.path.join(bundled_parent, 'locale', LANG, 'LC_MESSAGES'))
    srcdir = os.path.join(root, 'src')
    os.makedirs(srcdir)

    app = object.__new__(Sphinx)
    app.srcdir = srcdir
    cfg = types.SimpleNamespace(language=LANG, locale_dirs=[],
                                source_encoding='utf-8')
    app.config = cfg
    orig_pkgdir = sphinx_app_mod.package_dir

    MESSAGE_CODE = 1
    MESSAGE = 'message_1'

    def text_of(code):
        return MESSAGE if code == MESSAGE_CODE else 'text_%d' % code

    def code_of(text):
        if text == MESSAGE:
            return MESSAGE_CODE
        assert text.startswith('text_'), text
        return int(text[5:])

    def real_resolve(user, builtin):
        """user: per-project-source spec — None (no catalog file), or an int
        code (catalog provides text_of(code) for MESSAGE), or 'gap' (catalog
        exists without an entry). builtin: same for the bundled source.
        Returns the code the REAL patched _init_i18n resolution yields."""
        for i in range(NPROJ):
            mo = os.path.join(proj[i], LANG, 'LC_MESSAGES', 'sphinx.mo')
            if os.path.exists(mo):
                os.unlink(mo)
        for i, spec in enumerate(user):
            mo = os.path.join(proj[i], LANG, 'LC_MESSAGES', 'sphinx.mo')
            if spec is None:
                continue
            if spec == 'gap':
                write_mo(mo, {'unrelated_key': 'unrelated_value'})
            else:
                write_mo(mo, {MESSAGE: text_of(spec)})
        bmo = os.path.join(bundled_parent, 'locale', LANG, 'LC_MESSAGES',
                           'sphinx.mo')
        if os.path.exists(bmo):
            os.unlink(bmo)
        if builtin == 'gap':
            write_mo(bmo, {'unrelated_key': 'unrelated_value'})
        elif builtin is not None:
            write_mo(bmo, {MESSAGE: text_of(builtin)})

        cfg.locale_dirs = proj[:len(user)]
        # fresh resolution: both the module registry and gettext's per-path
        # object cache must be cleared (chaining mutates cached objects)
        sphinx_locale.translators.clear()
        gettext._translations.clear()
        sphinx_app_mod.package_dir = bundled_parent
        try:
            app._init_i18n()
        finally:
            sphinx_app_mod.package_dir = orig_pkgdir
        return code_of(app.translator.gettext(MESSAGE))

    def check(user, builtin):
        real = real_resolve(user, builtin)
        user_defines = [isinstance(s, int) for s in user]
        user_tr = [s if isinstance(s, int) else 0 for s in user]
        builtin_defines = isinstance(builtin, int)
        builtin_tr = builtin if isinstance(builtin, int) else 0
        shadow = select_translation(False, 0, user_defines, user_tr,
                                    builtin_defines, builtin_tr,
                                    MESSAGE_CODE)
        if shadow != real:
            return ('DISAGREEMENT\n  user=%r builtin=%r\n'
                    '  shadow=%d (%r)\n  real=%d (%r)'
                    % (user, builtin, shadow, text_of(shadow),
                       real, text_of(real)))
        # cross-check against the pure first-wins fold
        want = resolved(seq_defines(False, ToSeq(user_defines),
                                    builtin_defines),
                        seq_tr(0, ToSeq(user_tr), builtin_tr))
        if want == NO_TEXT():
            want = MESSAGE_CODE
        if shadow != want:
            return 'SHADOW SELF-CHECK failed for user=%r builtin=%r' % (
                user, builtin)
        return None

    checked = 0

    # --- boundary scenarios --------------------------------------------------
    boundary = [
        # (project source specs, bundled spec)
        ([2], 3),            # decisive: project overrides bundled
        ([None], 3),         # no project catalog: bundled wins
        (['gap'], 3),        # project catalog without the entry: bundled wins
        ([], None),          # nothing anywhere: untranslated
        ([], 4),             # bundled only
        ([2], None),         # project only
        ([2, 5], None),      # first project source wins
        ([None, 5], 3),      # gap then provider: second project beats bundled
        (['gap', 5], 3),
        ([2, 2], 2),         # every source provides the SAME text
        ([None, None, None, None, None], 6),
        ([2, 'gap', None, 5, 7], 8),
        (['gap'], None),     # catalogs exist, nobody provides
        (['gap', 'gap'], 'gap'),
    ]
    for user, builtin in boundary:
        err = check(user, builtin)
        if err:
            print(err)
            return 1
        checked += 1

    # --- fuzz ------------------------------------------------------------------
    rng = random.Random(SEED)
    next_code = [10]
    for _ in range(N_FUZZ):
        n_user = rng.randint(0, NPROJ)
        used = []
        user = []
        for _i in range(n_user):
            r = rng.random()
            if r < 0.30:
                user.append(None)
            elif r < 0.45:
                user.append('gap')
            elif used and r < 0.55:
                user.append(rng.choice(used))    # shared text across sources
            else:
                next_code[0] += 1
                if next_code[0] > 900000:
                    next_code[0] = 10
                used.append(next_code[0])
                user.append(next_code[0])
        r = rng.random()
        if r < 0.30:
            builtin = None
        elif r < 0.45:
            builtin = 'gap'
        elif used and r < 0.55:
            builtin = rng.choice(used)
        else:
            next_code[0] += 1
            builtin = next_code[0]
        err = check(user, builtin)
        if err:
            print(err)
            return 1
        checked += 1

    print('G-CONF OK: shadow first-wins resolution == real catalog-order '
          'resolution on %d scenarios (%d boundary + %d fuzz, seed %d).'
          % (checked, len(boundary), N_FUZZ, SEED))
    print(json.dumps({'checked': checked, 'disagreements': 0, 'seed': SEED,
                      'shadow': 'direct (contract-stripped impl region)'}))
    return 0


if __name__ == '__main__':
    sys.exit(main())
