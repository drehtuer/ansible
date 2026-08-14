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
    # GitHub CLI apt repo, added below,
    # needs its keyring dir to exist first
    && install -d -m 755 /etc/apt/keyrings \
    && curl -fsSL https://cli.github.com/packages/githubcli-archive-keyring.gpg \
    -o /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && chmod go+r /etc/apt/keyrings/githubcli-archive-keyring.gpg \
    && echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/githubcli-archive-keyring.gpg] https://cli.github.com/packages stable main" \
    > /etc/apt/sources.list.d/github-cli.list \
    && apt-get update \
    && apt-get install \
    --no-install-recommends \
    --yes \
    -qq \
    # GitHub CLI, not in Ubuntu's own repos
    gh \
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
    > /etc/bash_completion.d/invoke \
    && gh completion \
    --shell bash \
    > /etc/bash_completion.d/gh

# Keep in sync with the version installed by
# .github/workflows/lint.yml, so CI and the
# Dev Container lint with the same ruff.
ARG   RUFF_VERSION=0.16.3

RUN   \
    # Python linter/formatter, not packaged for
    # Ubuntu 24.04, so install the pinned release
    # binary. uname -m maps to the x86_64/aarch64
    # build names used by upstream.
    curl \
    --location \
    --fail \
    --silent \
    --show-error \
    "https://github.com/astral-sh/ruff/releases/download/${RUFF_VERSION}/ruff-$(uname -m)-unknown-linux-gnu.tar.gz" \
    | tar \
    --extract \
    --gzip \
    --directory=/usr/local/bin \
    --strip-components=1 \
    "ruff-$(uname -m)-unknown-linux-gnu/ruff"

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
