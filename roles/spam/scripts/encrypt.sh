#!/usr/bin/env bash
ansible-vault encrypt "${1}" --output="${2}"
sha256sum "${1}" | cut -d ' ' -f1
