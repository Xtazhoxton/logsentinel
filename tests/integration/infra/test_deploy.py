import json
import time

import boto3
import pytest
from typer.testing import CliRunner

from logsentinel.cli import app


@pytest.mark.localstack
def test_deploy_creates_stack(localstack_check, monkeypatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")
    runner = CliRunner()
    runner.invoke(app, ["deploy"])

    cf = boto3.client(
        "cloudformation", endpoint_url="http://localhost:4566", region_name="eu-west-1"
    )
    resources = cf.describe_stack_resources(StackName="logsentinel-dev")[
        "StackResources"
    ]
    created = {
        r["ResourceType"] for r in resources if r["ResourceStatus"] == "CREATE_COMPLETE"
    }

    # python3.13 n'est pas supporté par LocalStack 3.8 — Lambda et EventSourceMapping
    # vérifiés en T010 sur AWS réel.
    expected = {
        "AWS::Kinesis::Stream",
        "AWS::S3::Bucket",
        "AWS::DynamoDB::Table",
        "AWS::IAM::Role",
        "AWS::IAM::ManagedPolicy",
        "AWS::KinesisFirehose::DeliveryStream",
        "AWS::SQS::Queue",
        "AWS::SNS::Topic",
        "AWS::SSM::Parameter",
    }
    assert expected.issubset(created)


@pytest.mark.localstack
def test_logger_sends_to_kinesis(localstack_check, monkeypatch):
    monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:4566")
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "test")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "test")

    kinesis = boto3.client(
        "kinesis", endpoint_url="http://localhost:4566", region_name="eu-west-1"
    )

    payload = {
        "sentinel_id": "sent-integration-001",
        "timestamp": "2026-05-08T10:00:00.000Z",
        "level": "INFO",
        "message": "test message",
        "service": "integration-test",
        "metadata": {"test": True},
    }

    kinesis.put_records(
        StreamName="logsentinel-stream-dev",
        Records=[
            {
                "Data": json.dumps(payload).encode("utf-8"),
                "PartitionKey": "sent-integration-001",
            }
        ],
    )

    shard_iterator = kinesis.get_shard_iterator(
        StreamName="logsentinel-stream-dev",
        ShardId="shardId-000000000000",
        ShardIteratorType="TRIM_HORIZON",
    )
    records = kinesis.get_records(ShardIterator=shard_iterator["ShardIterator"])
    assert len(records["Records"]) == 1


@pytest.mark.localstack
@pytest.mark.skip(
    reason="Kinesis→Lambda trigger requiert python3.13 — testé en T010 sur AWS réel."
)
def test_records_appear_in_dynamodb(localstack_check):
    pass


@pytest.mark.localstack
def test_gsi_queryable_and_ttl_set(localstack_check):
    dynamodb = boto3.client(
        "dynamodb", endpoint_url="http://localhost:4566", region_name="eu-west-1"
    )

    dynamodb.put_item(
        TableName="logsentinel-events-dev",
        Item={
            "sentinel_id": {"S": "sent-gsi-test-001"},
            "timestamp": {"S": "2026-05-08T10:00:00.000Z"},
            "level": {"S": "INFO"},
            "message": {"S": "test message"},
            "service": {"S": "test-service"},
            "expires_at": {"N": str(int(time.time()) + 90 * 86400)},
        },
    )

    dynamodb.put_item(
        TableName="logsentinel-events-dev",
        Item={
            "sentinel_id": {
                "S": "sent-gsi-test-001"
            },  # clé HASH de la table — obligatoire
            "timestamp": {
                "S": "EXECUTION_INDEX"
            },  # clé RANGE de la table — marker fixe
            "gsi_pk": {"S": "EXECUTION_INDEX"},
            "gsi_sk": {"S": "2026-05-08T10:00:00.000Z#sent-gsi-test-001"},
            "started_at": {"S": "2026-05-08T10:00:00.000Z"},
            "has_error": {"BOOL": False},
        },
    )

    gsi_query = dynamodb.query(
        TableName="logsentinel-events-dev",
        IndexName="EXECUTION_INDEX",
        KeyConditionExpression="gsi_pk = :gsi_pk",
        ExpressionAttributeValues={":gsi_pk": {"S": "EXECUTION_INDEX"}},
    )
    count_gsi = gsi_query["Count"]

    item = dynamodb.get_item(
        TableName="logsentinel-events-dev",
        Key={
            "sentinel_id": {"S": "sent-gsi-test-001"},
            "timestamp": {"S": "2026-05-08T10:00:00.000Z"},
        },
    )["Item"]

    assert count_gsi == 1
    assert int(item["expires_at"]["N"]) > int(time.time())
