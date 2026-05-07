import pytest
import boto3
import os
from moto import mock_aws


@pytest.fixture
def aws_dynamodb():
    with mock_aws():
        dynamodb = boto3.client("dynamodb", region_name=os.environ.get("AWS_REGION", "eu-west-1"))
        dynamodb.create_table(
            TableName="logsentinel-events",
            KeySchema=[
                {"AttributeName": "sentinel_id", "KeyType": "HASH"},
                {"AttributeName": "timestamp", "KeyType": "RANGE"},
            ],
            AttributeDefinitions=[
                {"AttributeName": "sentinel_id", "AttributeType": "S"},
                {"AttributeName": "timestamp", "AttributeType": "S"},
                {"AttributeName": "gsi_pk", "AttributeType": "S"},
                {"AttributeName": "gsi_sk", "AttributeType": "S"},
            ],
            BillingMode="PAY_PER_REQUEST",
            GlobalSecondaryIndexes=[
                {
                    "IndexName": "EXECUTION_INDEX",
                    "KeySchema": [
                        {"AttributeName": "gsi_pk", "KeyType": "HASH"},
                        {"AttributeName": "gsi_sk", "KeyType": "RANGE"},
                    ],
                    "Projection": {"ProjectionType": "ALL"},
                }
            ]
        )
        yield dynamodb
