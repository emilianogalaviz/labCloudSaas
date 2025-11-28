#!/usr/bin/env bash
set -euo pipefail

# This helper inspects and clears stale Terraform state locks stored in DynamoDB.
# Run it from the repository root or the terraform/ directory.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TERRAFORM_DIR="${SCRIPT_DIR%/scripts}"
cd "$TERRAFORM_DIR"

TABLE_NAME="${TF_LOCK_TABLE:-labcloud-terraform-locks}"

print_usage() {
  cat <<USAGE
Usage:
  ./scripts/state_lock_helper.sh             # only list existing locks
  ./scripts/state_lock_helper.sh <LOCK_ID>   # force-unlock the given lock ID

Environment variables:
  TF_LOCK_TABLE   Override the DynamoDB table name (default: labcloud-terraform-locks)

Notes:
- You need AWS credentials with permissions to read and update the lock table.
- When unlocking, Terraform must be installed and backend configuration should match the remote state.
USAGE
}

if [[ "${1-}" == "-h" || "${1-}" == "--help" ]]; then
  print_usage
  exit 0
fi

echo "Checking DynamoDB table: ${TABLE_NAME}" >&2
aws dynamodb scan --table-name "$TABLE_NAME" --projection-expression "LockID, Info" --output table || true

LOCK_ID="${1-}"
if [[ -z "$LOCK_ID" ]]; then
  exit 0
fi

echo "Forcing unlock for state lock: ${LOCK_ID}" >&2
terraform -chdir="$TERRAFORM_DIR" force-unlock -force "$LOCK_ID"
