#!/usr/bin/env bash
ansible-vault encrypt "${1}" --output="${2}"
