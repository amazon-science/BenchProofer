#!/usr/bin/env bash
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: CC-BY-NC-4.0

# Open the review site from a machine that is not the one serving it.
#
# The server binds loopback only (see serve.sh), so SSH is the access perimeter:
# this forwards a local port to the serving host's loopback, and you browse
# http://localhost:$LOCAL.
#
#   HOST=my-ssh-host bash viz/connect.sh
#   HOST=my-ssh-host LOCAL=8090 REMOTE=9001 bash viz/connect.sh
#
# HOST is any destination ssh(1) accepts: a hostname, user@host, or an alias
# from your ~/.ssh/config (which is where a ProxyJump through a bastion belongs).
set -euo pipefail

HOST="${HOST:-}"
LOCAL="${LOCAL:-8080}"
REMOTE="${REMOTE:-9000}"

if [[ -z "$HOST" ]]; then
  echo "Set HOST to the ssh destination serving the site, e.g. HOST=user@host bash viz/connect.sh" >&2
  exit 1
fi

echo "Tunneling localhost:${LOCAL}  ->  ${HOST}:127.0.0.1:${REMOTE}"
echo "Then open:  http://localhost:${LOCAL}"
echo "(Ctrl-C closes the tunnel.)"
exec ssh -N -L "${LOCAL}:127.0.0.1:${REMOTE}" "${HOST}"
