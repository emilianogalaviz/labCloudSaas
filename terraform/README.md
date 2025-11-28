# Terraform

## Remote state backend

The project uses an S3 bucket with a DynamoDB table (`labcloud-terraform-locks`) to manage remote state locking. If a previous apply or plan is interrupted, a lock record can remain and block new runs, resulting in an error similar to:

```
Error: Error acquiring the state lock

Error message: ConditionalCheckFailedException: The conditional request failed
```

## Clearing a stale lock

Use the helper script to inspect the lock table and, if necessary, force-unlock the stuck state entry:

```bash
cd terraform
./scripts/state_lock_helper.sh          # lists lock entries
./scripts/state_lock_helper.sh <LOCK_ID> # forces unlock for the given lock id
```

If you prefer to unlock manually, run `terraform force-unlock -force <LOCK_ID>` after confirming that no other Terraform runs are in progress.

**Note:** AWS credentials with permission to read and update the lock table are required for either approach.
