#!/usr/bin/env bash
# Docker access comes from the host's docker socket, bind-mounted in
# by devcontainer.json, so the container's user needs to be in a
# group with the same GID as that socket. That GID varies by host
# machine, so it can't be baked into the image at build time - this
# runs on every container start (see devcontainer.json's
# postStartCommand) instead.
set -euo pipefail

socket_gid=$(stat -c '%g' /var/run/docker.sock)

if ! getent group "${socket_gid}" > /dev/null; then
    sudo groupadd --gid "${socket_gid}" docker-host
fi

sudo usermod --append --groups "${socket_gid}" "$(whoami)"
