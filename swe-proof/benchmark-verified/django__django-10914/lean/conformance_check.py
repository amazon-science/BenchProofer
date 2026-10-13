#!/usr/bin/env python3
"""G-CONF for django__django-10914.

The gold patch is already applied to /testbed when this runs (so the global
default FILE_UPLOAD_PERMISSIONS == 0o644). We compare the R/I Python shadow of
`implementation_effectiveFilePermissionsMode` (the Lean impl, transliterated
op-for-op per refinement.md) against the REAL patched permission-mode resolution
exercised through `django.core.files.storage.FileSystemStorage.file_permissions_mode`,
over >=1e5 fuzzed inputs. Zero disagreements => exit 0.

Type bijection (mapping.md):
  storageOverride : Option Nat  <->  the `file_permissions_mode=` ctor argument
                                     (None => the storage instance was given no
                                     explicit mode; `some m` => integer mode m)
  projectSetting  : Option (Option Nat)
                                <->  whether settings.FILE_UPLOAD_PERMISSIONS is
                                     left at its built-in default (None on the
                                     OUTER Option => not overridden in settings)
                                     vs. pinned by the project to a value (which
                                     itself may be None or an int)
  result          : Option Nat  <->  storage.file_permissions_mode (None or int)

stdlib-only; no hypothesis required.
"""
import random
import sys

import django
from django.conf import settings

if not settings.configured:
    settings.configure(
        DEBUG=False,
        DATABASES={},
        INSTALLED_APPS=[],
        MEDIA_ROOT="/tmp",
    )
    django.setup()

from django.core.files.storage import FileSystemStorage
from django.test import override_settings

# The post-patch built-in default of the setting. We assert the container is
# actually patched (defensive: G-CONF must run against the fixed tree).
BUILTIN_DEFAULT = getattr(settings, "FILE_UPLOAD_PERMISSIONS", "MISSING")


def oracle(storage_override, project_setting):
    """Real patched behavior: build a FileSystemStorage with the given instance
    override, under a settings context that either leaves
    FILE_UPLOAD_PERMISSIONS at its built-in default or pins it.

    storage_override: None | int
    project_setting:  ("default",) | ("set", None | int)
    Returns: None | int  (storage.file_permissions_mode)
    """
    if project_setting[0] == "default":
        # leave the global default in place
        st = FileSystemStorage(file_permissions_mode=storage_override)
        return st.file_permissions_mode
    else:
        with override_settings(FILE_UPLOAD_PERMISSIONS=project_setting[1]):
            st = FileSystemStorage(file_permissions_mode=storage_override)
            return st.file_permissions_mode


def shadow(storage_override, project_setting):
    """R/I transliteration of implementation_effectiveFilePermissionsMode (Lean).

    storageOverride : Option Nat        -> storage_override (None | int)
    projectSetting  : Option (Option Nat) -> project_setting tuple above
    """
    setting = BUILTIN_DEFAULT  # defaultUploadMode (the post-fix 0o644)
    if project_setting[0] != "default":
        setting = project_setting[1]  # `some v => setting := v`
    if storage_override is not None:
        return storage_override        # `some m => return some m`
    return setting                     # `none   => return setting`


MODE_POOL = [None, 0o644, 0o600, 0o777, 0o755, 0, 0o640, 0o444, 0o666]


def rand_mode(rng):
    if rng.random() < 0.4:
        return rng.choice(MODE_POOL)
    return rng.randint(0, 0o777)


def main():
    rng = random.Random(10914)  # pinned seed (mapping.md)
    if BUILTIN_DEFAULT != 0o644:
        print("G-CONF FAIL: container not patched; FILE_UPLOAD_PERMISSIONS=%r "
              "(expected 0o644)" % (BUILTIN_DEFAULT,))
        return 1
    N = 100_000
    disagreements = 0
    first = None
    for i in range(N):
        # storage instance override: None (no override) or an int mode
        if rng.random() < 0.5:
            storage_override = None
        else:
            storage_override = rand_mode(rng)
            if storage_override is None:
                storage_override = 0o644
        # project setting: leave at built-in default, or pin to None / a mode
        r = rng.random()
        if r < 0.5:
            project_setting = ("default",)
        else:
            project_setting = ("set", rand_mode(rng))
        o = oracle(storage_override, project_setting)
        s = shadow(storage_override, project_setting)
        if o != s:
            disagreements += 1
            if first is None:
                first = (storage_override, project_setting, o, s)
    if disagreements:
        print("G-CONF FAIL: %d/%d disagreements; first=%r"
              % (disagreements, N, first))
        return 1
    print("G-CONF OK: %d inputs, 0 disagreements" % N)
    return 0


if __name__ == "__main__":
    sys.exit(main())
