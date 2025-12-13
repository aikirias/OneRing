#!/bin/bash
set -euo pipefail

PG_HBA="$PGDATA/pg_hba.conf"
BASE_DN="${LDAP_BASE_DN:-dc=oner,dc=local}"

cat <<EOF >> "$PG_HBA"
# LDAP authentication added by bootstrap
host all all 0.0.0.0/0 ldap ldapserver=openldap ldapport=389 ldapprefix="uid=" ldapsuffix=",ou=people,${BASE_DN}"
EOF
