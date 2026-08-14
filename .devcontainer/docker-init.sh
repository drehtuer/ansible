#!/usr/bin/env bash
# Starts dockerd in the background, so molecule's docker driver has
# a daemon to talk to, then hands off to the container's real command.
# Requires the container to run with --privileged (see devcontainer.json).
set -euo pipefail

if ! pgrep -x dockerd > /dev/null; then
    # vfs, not the default overlay2: the container's own root
    # filesystem is already an overlay mount (from the host's
    # Docker), and the kernel refuses to layer overlayfs on
    # overlayfs. vfs works everywhere, at the cost of slower
    # image layer handling.
    dockerd --storage-driver=vfs > /var/log/dockerd.log 2>&1 &

    for _ in $(seq 1 30); do
        [ -S /var/run/docker.sock ] && break
        sleep 1
    done

    if [ ! -S /var/run/docker.sock ]; then
        echo "dockerd did not come up in time, see /var/log/dockerd.log" >&2
        exit 1
    fi
fi

exec "$@"
