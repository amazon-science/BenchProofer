"""Twin-artifact model for django__django-11239.

Behaviour under specification (stated as desired behaviour, not as an edit):

  A database client launches an external interactive shell and must pass the
  connection's credential and transport-security settings to that shell through
  its process environment. The settings recognised are the connection password
  and the four mutual-TLS settings used to authenticate the connection with
  client certificates: the security mode, the trusted root certificate, the
  client certificate, and the client private key.

  For each recognised setting, when the connection supplies a non-empty value,
  that value is published into the launched shell's environment under the
  dedicated environment-variable name that shell reads for that setting; when
  the connection does not supply the setting (or supplies an empty value), the
  corresponding environment variable is left unset. The published value is the
  supplied value verbatim, and no environment variable is published for any
  setting the connection did not supply.

  The consequence that matters: a connection configured for mutual TLS -- which
  supplies the transport-security settings in addition to (or instead of) a
  password -- has every one of those settings reach the launched shell, not
  only the password. Each setting maps to its own distinct environment
  variable, so settings never collide.

Modelling choices (Nagini fragment):
  * The connection settings are a ``Dict[int, int]`` from a setting-name token
    to its value token; the published environment is likewise a
    ``Dict[int, int]`` from an environment-variable-name token to its value
    token. Only membership, per-key value, and which names are present are
    observed, so integer identity is the faithful carrier (mapping.md §2).
  * Presence of a setting key in the input mapping models a supplied non-empty
    value; absence models an unsupplied or empty value (both leave the variable
    unset). The five setting tokens and their five distinct environment-variable
    tokens are module-level constants (mapping.md §1).

No string indexing is used (Nagini bans it). The whole behaviour is modelled
deeply (the conditional per-setting publication is spelled out in the impl
region); there is no axiomatised callee. Markers (machine-parsed) delimit the
spec / proof / impl regions.
"""
from typing import Dict
from nagini_contracts.contracts import *


# axioms-start
# No axioms: the connection-setting publication is the behaviour under
# specification and is spelled out deeply in the impl region. There is no
# unchanged opaque callee to axiomatise.
# axioms-end


# pure-start
@Pure
def setting_password() -> int:
    return 0


@Pure
def setting_sslmode() -> int:
    return 1


@Pure
def setting_sslrootcert() -> int:
    return 2


@Pure
def setting_sslcert() -> int:
    return 3


@Pure
def setting_sslkey() -> int:
    return 4


@Pure
def envvar_password() -> int:
    return 100


@Pure
def envvar_sslmode() -> int:
    return 101


@Pure
def envvar_sslrootcert() -> int:
    return 102


@Pure
def envvar_sslcert() -> int:
    return 103


@Pure
def envvar_sslkey() -> int:
    return 104


# pure-end


def build_pg_env(conn_params: Dict[int, int]) -> Dict[int, int]:
    # pre-conditions-start
    Requires(Acc(dict_pred(conn_params), 1 / 2))
    # pre-conditions-end
    # post-conditions-start
    Ensures(Acc(dict_pred(conn_params), 1 / 2))
    Ensures(Acc(dict_pred(Result())))
    Ensures(Result() is not None)
    # For each recognised setting, its dedicated environment variable is present
    # in the published environment exactly when the connection supplies that
    # setting, and then it carries the supplied value verbatim. These five
    # biconditionals are the clause the mutual-TLS configuration depends on:
    # each of the four TLS settings (and the password) reaches the launched
    # shell when -- and only when -- supplied, under its own distinct name.
    Ensures((envvar_password() in Result())
            == (setting_password() in conn_params))
    Ensures(Implies(setting_password() in conn_params,
                    Result()[envvar_password()] == conn_params[setting_password()]))
    Ensures((envvar_sslmode() in Result())
            == (setting_sslmode() in conn_params))
    Ensures(Implies(setting_sslmode() in conn_params,
                    Result()[envvar_sslmode()] == conn_params[setting_sslmode()]))
    Ensures((envvar_sslrootcert() in Result())
            == (setting_sslrootcert() in conn_params))
    Ensures(Implies(setting_sslrootcert() in conn_params,
                    Result()[envvar_sslrootcert()] == conn_params[setting_sslrootcert()]))
    Ensures((envvar_sslcert() in Result())
            == (setting_sslcert() in conn_params))
    Ensures(Implies(setting_sslcert() in conn_params,
                    Result()[envvar_sslcert()] == conn_params[setting_sslcert()]))
    Ensures((envvar_sslkey() in Result())
            == (setting_sslkey() in conn_params))
    Ensures(Implies(setting_sslkey() in conn_params,
                    Result()[envvar_sslkey()] == conn_params[setting_sslkey()]))
    # No spurious variables: every published environment variable is one of the
    # five dedicated names above (the result holds no key outside this set).
    Ensures(Forall(int, lambda e: (
        Implies(e in Result(),
                e == envvar_password() or e == envvar_sslmode()
                or e == envvar_sslrootcert() or e == envvar_sslcert()
                or e == envvar_sslkey()))))
    # post-conditions-end
    # impl-start
    # Pre-patch skeleton: only the password setting is published; the four
    # mutual-TLS settings are never written to the launched shell's environment.
    env = {}  # type: Dict[int, int]
    if setting_password() in conn_params:
        env[envvar_password()] = conn_params[setting_password()]
    return env
    # impl-end
