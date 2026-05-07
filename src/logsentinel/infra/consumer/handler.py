import base64
import datetime
import json
import os
from datetime import timezone
from typing import Any

import boto3
from boto3.dynamodb.types import TypeSerializer
from botocore.exceptions import ClientError

dynamodb = boto3.client("dynamodb", region_name=os.environ.get("AWS_REGION", "eu-west-1"))
TABLE_NAME = os.environ.get("LOGSENTINEL_TABLE_NAME", "logsentinel-events")
RETENTION_DAYS = int(os.environ.get("LOGSENTINEL_RETENTION_DAYS", "90"))
serializer = TypeSerializer()

def handler(event: dict[str, Any], context: object) -> None:
    for record in event["Records"]:
        try:
            raw_record = record["kinesis"]["data"]
            decoded_record = base64.b64decode(raw_record)
            payload = json.loads(decoded_record)
            Item = {
                "sentinel_id": {"S": payload["sentinel_id"]},
                "timestamp": {"S": payload["timestamp"]},
                "level": {"S": payload["level"]},
                "message": {"S": payload["message"]},
                "service": {"S": payload["service"]},
                "expires_at": {
                    "N": str(
                        int(
                            datetime.datetime.now(timezone.utc).timestamp()
                            + RETENTION_DAYS * 86400
                        )
                    )
                },
                "metadata": serializer.serialize(payload["metadata"]),
            }
            if payload.get("parent_service"):
                Item["parent_service"] = {"S": payload["parent_service"]}

            if payload.get("lambda_request_id"):
                Item["lambda_request_id"] = {"S": payload["lambda_request_id"]}
                

            dynamodb.put_item(
                TableName=TABLE_NAME,
                Item= Item
            )
            try:
                dynamodb.put_item(
                    TableName=TABLE_NAME,
                    Item={
                        "gsi_pk": {"S": "EXECUTION_INDEX"},
                        "gsi_sk": {"S": f"{payload['timestamp']}#{payload['sentinel_id']}"},
                        "sentinel_id": {"S": payload["sentinel_id"]},
                        "timestamp": {"S": "EXECUTION_INDEX"},
                        "started_at": {"S": payload["timestamp"]},
                        "has_error": {"BOOL": False},
                        "services": {"SS": [payload["service"]]},
                    },
                    ConditionExpression="attribute_not_exists(gsi_pk)",
                )
            except ClientError as e:
                if e.response["Error"]["Code"] == "ConditionalCheckFailedException":
                    pass
                else:
                    raise e
            update_expression = "ADD services :svc"
            expression_attribute_values: dict[str, Any] = {":svc": {"SS": [payload["service"]]}}
            if payload["level"] == "ERROR" or payload["level"] == "CRITICAL":
                update_expression = "SET has_error = :true ADD services :svc"
                expression_attribute_values.update({":true": {"BOOL": True}})


            dynamodb.update_item(
                TableName=TABLE_NAME,
                Key={
                    "sentinel_id": {"S": payload["sentinel_id"]},
                    "timestamp": {"S": "EXECUTION_INDEX"},
                },
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_attribute_values,
            )


        except Exception as e:
            print(f"Skipping malformed record: {e}")
            continue

