# syntax=docker/dockerfile:1
# https://docs.docker.com/reference/dockerfile/
FROM  ubuntu:24.04

LABEL name="Ansible controller" \
    description="Control node running Ubuntu 24.04" \
    version="1.10"

ARG   DEBIAN_FRONTEND=noninteractive
ARG   ARG_USER

ENV   LANG=en_US.utf8

RUN   \
    # apt cache folders as tmpfs, discarded after build.
    # No need to delete these folders later
    --mount=type=tmpfs,target=/var/lib/apt/lists \
    --mount=type=tmpfs,target=/var/cache/apt \
    \
    apt-get update \
    && apt-get upgrade \
    --yes \
    -qq \
    && apt-get install \
    --no-install-recommends \
    --yes \
    -qq \
    # Ansible
    ansible \
    ansible-lint \
    # Let's be on the safe side,
    # our default shell should be
    # available
    bash \
    bash-completion \
    # git within devcontainer
    git \
    # locales support
    locales \
    # Python support
    python3.12 \
    python-is-python3 \
    # Invoke to organize cmd commands
    python3-invoke \
    # User may become root
    sudo \
    # Editor
    neovim \
    luarocks \
    # Network
    ca-certificates \
    curl \
    iputils-ping \
    ssh \
    sshpass \
    wget \
    # Generate en_US.UTF-8 locales
    && localedef \
    --inputfile=en_US \
    --force \
    --charmap=UTF-8 \
    --alias-file=/usr/share/locale/locale.alias \
    en_US.UTF-8 \
    # Add non-root user,
    # password needed for `sudo`
    && useradd \
    --create-home \
    --user-group \
    --shell /usr/bin/bash \
    ${ARG_USER} \
    && inv \
    --print-completion-script=bash \
    > /etc/bash_completion.d/invoke

COPY \
    --chmod=644 \
    ansible-galaxy.yml \
    /ansible-galaxy.yml

RUN \
    ansible-galaxy \
    install \
    --role-file \
    /ansible-galaxy.yml


USER ${ARG_USER}

# Can't set default user here, USER takes
# only a string, but our user name is stored
# in a secret file. Don't want to add an additional
# environment variable, we set the user
# in devcontainer.json via 'remoteUser'.
# This also takes care of mapping uid:gid correctly.

# Keep container running, vscode needs
# to attach to it
CMD [ "sleep", "infinity" ]
