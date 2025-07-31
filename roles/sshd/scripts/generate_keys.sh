#!/usr/bin/sh

# https://www.ssh-audit.com/hardening_guides.html#ubuntu_24_04_lts

if [ "${#}" -ne "1" ]; then
  echo "Hostname as argument needed"
  exit 1
fi

SCRIPT_DIR="$(readlink -f "$(dirname "${0}")")"
KEY_DIR="$(readlink -f "${SCRIPT_DIR}/../keys")"
FILE_DIR="$(readlink -f "${SCRIPT_DIR}/../files")"
HOSTNAME="${1}"
KEY_ED25519="${KEY_DIR}/ssh_${HOSTNAME}_ed25519_key"
KEY_RSA="${KEY_DIR}/ssh_${HOSTNAME}_rsa_key"

# ed25519
if [ ! -e "${KEY_ED25519}" ]; then
  ssh-keygen -q -t ed25519 -N "" -C "sshd@${HOSTNAME}" -f "${KEY_ED25519}"
fi
ansible-vault encrypt "${KEY_ED25519}" --output "${FILE_DIR}/$(basename ${KEY_ED25519}).aes256" 1>/dev/null
HASH_ED25519=$(sha256sum "${KEY_ED25519}" | cut -d ' ' -f1)

# rsa
if [ ! -e "${KEY_RSA}" ]; then
  ssh-keygen -q -t rsa -b 4096 -N "" -C "sshd@${HOSTNAME}" -f "${KEY_RSA}"
fi
ansible-vault encrypt "${KEY_RSA}" --output "${FILE_DIR}/$(basename ${KEY_RSA}).aes256" 1>/dev/null
HASH_RSA=$(sha256sum "${KEY_RSA}" | cut -d ' ' -f1)

# moduli
ansible-vault encrypt "${MODULI_SCREEN}" --output "${FILE_DIR}/$(basename ).aes256" 1>/dev/null
HASH_MODULI=$(sha256sum "${MODULI_SCREEN}" | cut -d ' ' -f1)

# output
echo "sshd:"
echo "  host_key:"
echo "    - name: ed25519"
echo "      sha256: ${HASH_ED25519}"
echo "    - name: rsa"
echo "      sha256: ${HASH_RSA}"

exit 0
