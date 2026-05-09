# logsentinel-cli

Developer CLI for the LogSentinel observability platform.

Provisions the full AWS data pipeline and provides tools to inspect structured log data from distributed Lambda executions.

---

## Installation

```bash
pip install logsentinel
```

Requires Python 3.13+ and AWS credentials configured (`aws configure`).

---

## Commands

### `logsentinel deploy`

Provisions the LogSentinel AWS data pipeline via CloudFormation:

- Kinesis Data Stream (log ingestion from SDK)
- Consumer Lambda (Kinesis → DynamoDB writer)
- DynamoDB table (execution event store, with TTL and GSI)
- Kinesis Firehose → S3 (raw archive)
- SQS DLQ + SNS alert (SDK fallback destinations)

```bash
logsentinel deploy
logsentinel deploy --env prod --region us-east-1 --retention-days 365
```

| Option | Default | Description |
|--------|---------|-------------|
| `--env` | `dev` | Deployment environment, used as a stack and resource name suffix |
| `--region` | `eu-west-1` | AWS region |
| `--retention-days` | `90` | DynamoDB TTL in days |

### `logsentinel parse`

Parse a local CloudWatch JSON export and display log entries as a formatted table.

```bash
logsentinel parse logs.json
logsentinel parse logs.json --level ERROR
logsentinel parse logs.json --search "timeout"
```

| Option | Description |
|--------|-------------|
| `--level` | Minimum log level to display (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |
| `--search` | Keyword filter applied to the message field |

### `logsentinel e2e`

Run an end-to-end acceptance test against a live AWS environment. Deploys a test Lambda that uses the SDK, invokes it, then verifies that records appear in DynamoDB.

```bash
logsentinel e2e --deploy               # create test Lambda + IAM role
logsentinel e2e --run                  # invoke Lambda, poll DynamoDB, assert 5 records
logsentinel e2e --teardown             # remove test Lambda
logsentinel e2e --deploy --region ap-northeast-1  # target a specific region
```

---

## Requirements

- Python 3.13+
- AWS credentials: `aws configure` or environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`)
- IAM permissions: CloudFormation, Kinesis, DynamoDB, S3, SQS, SNS, SSM, Lambda, IAM
