import base64
import json
from datetime import datetime, timedelta, timezone

import pytest

from logsentinel.infra.consumer.handler import handler


def test_valid_single_record(aws_dynamodb):
    date = datetime.now(timezone.utc).isoformat()
    now = datetime.now(timezone.utc).timestamp()
    expected_expires_at = now + (90 * 86400)
    single_record = {
        "sentinel_id": "276492346772639",
        "timestamp": date,
        "level": "INFO",
        "message": "Premier enregistrement de test : initialisation",
        "service": "test-service",
        "metadata": {"user_id": 123, "action": "login"},
    }
    dump_bytes = json.dumps(single_record).encode("utf-8")
    encoded_str = base64.b64encode(dump_bytes).decode("utf-8")
    event = {"Records": [{"kinesis": {"data": encoded_str}}]}
    handler(event, {})
    response = aws_dynamodb.query(
        TableName="logsentinel-events",
        KeyConditionExpression="sentinel_id = :sid",
        ExpressionAttributeValues={":sid": {"S": "276492346772639"}},
    )
    items = response["Items"]  # liste de dicts avec typed values
    count = response["Count"]

    assert items[0]["sentinel_id"] == {"S": "276492346772639"}
    assert items[0]["timestamp"] == {"S": date}
    assert int(items[0]["expires_at"]["N"]) == pytest.approx(expected_expires_at, abs=10)
    assert items[1]["gsi_pk"] == {"S": "EXECUTION_INDEX"}
    assert items[1]["gsi_sk"] == {"S": f"{date}#276492346772639"}
    assert count == 2


def test_valid_multiple_records(aws_dynamodb):
    base = datetime.now(timezone.utc)
    date1 = base.isoformat()
    date2 = (base + timedelta(seconds=1)).isoformat()
    date3 = (base + timedelta(seconds=2)).isoformat()
    multiple_record = [
        {
            "sentinel_id": "276492346772639",
            "timestamp": date1,
            "level": "INFO",
            "message": "Premier enregistrement de test : initialisation",
            "service": "test-service",
            "metadata": {"user_id": 123, "action": "login"},
        },
        {
            "sentinel_id": "276492346772639",
            "timestamp": date2,
            "level": "INFO",
            "message": "Premier enregistrement de test : initialisation",
            "service": "test-service",
            "metadata": {"user_id": 123, "action": "login"},
        },
        {
            "sentinel_id": "276492346772639",
            "timestamp": date3,
            "level": "ERROR",
            "message": "Premier enregistrement de test : initialisation",
            "service": "test-service",
            "metadata": {"user_id": 123, "action": "login"},
        },
    ]
    event_list = []
    for event in multiple_record:
        dump_bytes = json.dumps(event).encode("utf-8")
        encoded_str = base64.b64encode(dump_bytes).decode("utf-8")
        event_list.append({"kinesis": {"data": encoded_str}})

    event = {"Records": event_list}
    handler(event, {})
    response = aws_dynamodb.query(
        TableName="logsentinel-events",
        KeyConditionExpression="sentinel_id = :sid",
        ExpressionAttributeValues={":sid": {"S": "276492346772639"}},
    )
    items = response["Items"]
    count = response["Count"]
    query_gsi = aws_dynamodb.query(
        TableName="logsentinel-events",
        IndexName="EXECUTION_INDEX",
        KeyConditionExpression="gsi_pk = :pk",
        ExpressionAttributeValues={":pk": {"S": "EXECUTION_INDEX"}},
    )
    count_gsi = query_gsi["Count"]
    items_gsi = query_gsi["Items"]

    assert items_gsi[0]["has_error"]["BOOL"] == True
    assert count_gsi == 1
    assert count == 4


def test_malformed_record(aws_dynamodb):
    base = datetime.now(timezone.utc)
    date1 = base.isoformat()
    date2 = (base + timedelta(seconds=1)).isoformat()
    multiple_record = [
        {
            "sentinel_id": "276492346772639",
            "timestamp": date1,
            "level": "INFO",
            "message": "Premier enregistrement de test : initialisation",
            "service": "test-service",
            "metadata": {"user_id": 123, "action": "login"},
        },
        {
            "sentinel_id": "276492346772639",
            "timestamp": date2,
            "level": "INFO",
            "message": "Premier enregistrement de test : initialisation",
            "service": "test-service",
            "metadata": {"user_id": 123, "action": "login"},
        },
    ]
    event_list = []
    dump_bytes = json.dumps(multiple_record[0]).encode("utf-8")
    encoded_str = base64.b64encode(dump_bytes).decode("utf-8")
    event_list.append({"kinesis": {"data": encoded_str}})
    event_list.append(json.dumps(multiple_record[1]))

    event = {"Records": event_list}
    handler(event, {})
    response = aws_dynamodb.query(
        TableName="logsentinel-events",
        KeyConditionExpression="sentinel_id = :sid",
        ExpressionAttributeValues={":sid": {"S": "276492346772639"}},
    )
    items = response["Items"]
    count = response["Count"]

    assert count == 2