import importlib.util
import io
import json
import pathlib
import time
import zipfile
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import boto3
import typer
from botocore import exceptions as botocore_exceptions
from rich.console import Console
from rich.table import Table

from logsentinel import __version__
from logsentinel.filters import LevelFilter, SearchFilter
from logsentinel.formatters import TableFormatter
from logsentinel.models import LogLevel
from logsentinel.parsers import CloudWatchParser

app = typer.Typer(name="logsentinel", help="logsentinel CLI tool", add_completion=False)


class Format(str, Enum):
    cloudwatch = "cloudwatch"


@app.command()
def version() -> None:
    typer.echo("LogSentinel v{}".format(__version__))


valid_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}


@app.command()
def deploy(
        env: str = typer.Option("dev", "-e", "--env", help="Deployment environment"),
        retention_days: int = typer.Option(90, "--retention-days", help="Retention days"),
        region: str = typer.Option("eu-west-1", "--region", help="AWS region"),
) -> None:
    """Provision the LogSentinel AWS data pipeline via CloudFormation."""
    console = Console()

    # --- Credentials check ---
    sts = boto3.client("sts", region_name=region)
    try:
        identity = sts.get_caller_identity()
        account_id = identity["Account"]
        console.print(f"[bold]Account:[/bold] {account_id}  [bold]Region:[/bold] {region}")
    except botocore_exceptions.NoCredentialsError:
        typer.echo("No AWS credentials found. Run: aws configure", err=True)
        raise typer.Exit(code=1)

    # --- Artifacts bucket ---
    s3 = boto3.client("s3", region_name=region)
    bucket_name = f"logsentinel-artifacts-{account_id}"
    try:
        s3.head_bucket(Bucket=bucket_name)
        console.print(f"[dim]Artifacts bucket already exists:[/dim] {bucket_name}")
    except botocore_exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            console.print(f"Creating artifacts bucket [bold]{bucket_name}[/bold]...")
            kwargs: dict[str, Any] = {"Bucket": bucket_name}
            if region != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
            s3.create_bucket(**kwargs)
            console.print("[green]✓[/green] Bucket created")
        else:
            raise

    # --- Package Lambda ---
    console.print("Packaging consumer Lambda...")
    handler_path = pathlib.Path(__file__).parent.parent / "infra" / "consumer" / "handler.py"
    zip_path = pathlib.Path("/tmp/consumer.zip")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(handler_path, arcname="handler.py")

    # --- Upload to S3 ---
    console.print(f"Uploading to [bold]s3://{bucket_name}/consumer.zip[/bold]...")
    s3.upload_file(str(zip_path), bucket_name, "consumer.zip")
    console.print("[green]✓[/green] Upload complete")

    # --- CloudFormation ---
    stack_name = f"logsentinel-{env}"
    cf = boto3.client("cloudformation", region_name=region)
    template_body = (pathlib.Path(__file__).parent.parent / "infra" / "stack.yaml").read_text()
    parameters = [
        {"ParameterKey": "Env", "ParameterValue": env},
        {"ParameterKey": "RetentionDays", "ParameterValue": str(retention_days)},
        {"ParameterKey": "ArtifactsBucketName", "ParameterValue": bucket_name},
    ]

    try:
        cf.describe_stacks(StackName=stack_name)
        console.print(f"Stack [bold]{stack_name}[/bold] exists — applying updates...")
        try:
            cf.update_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,  # type: ignore[arg-type]
                Capabilities=["CAPABILITY_NAMED_IAM"],
            )
            console.print("Waiting for update to complete...")
            cf.get_waiter("stack_update_complete").wait(StackName=stack_name)
            console.print("[green]✓[/green] Stack updated")
        except botocore_exceptions.ClientError as e:
            if "No updates are to be performed" in str(e):
                console.print("[dim]Stack is already up to date — nothing to do.[/dim]")
            else:
                raise

    except botocore_exceptions.ClientError as e:
        if "does not exist" in str(e):
            console.print(f"Creating stack [bold]{stack_name}[/bold]...")
            cf.create_stack(
                StackName=stack_name,
                TemplateBody=template_body,
                Parameters=parameters,  # type: ignore[arg-type]
                Capabilities=["CAPABILITY_NAMED_IAM"],
            )
            console.print("Waiting for stack creation to complete...")
            cf.get_waiter("stack_create_complete").wait(StackName=stack_name)
            console.print("[green]✓[/green] Stack created")
        else:
            raise

    # --- Resources summary ---
    response = cf.describe_stack_resources(StackName=stack_name)
    table = Table(title=f"Stack: {stack_name}", show_lines=False)
    table.add_column("Resource Type", style="cyan", no_wrap=True)
    table.add_column("Logical ID", style="white")
    table.add_column("Physical ID", style="dim", overflow="fold")
    table.add_column("Status", no_wrap=True)

    for resource in response["StackResources"]:
        status = resource["ResourceStatus"]
        if "COMPLETE" in status and "DELETE" not in status:
            status_style = "green"
        elif "FAILED" in status:
            status_style = "red"
        else:
            status_style = "yellow"
        table.add_row(
            resource["ResourceType"],
            resource["LogicalResourceId"],
            resource.get("PhysicalResourceId", "—"),
            f"[{status_style}]{status}[/{status_style}]",
        )

    console.print(table)


@app.command()
def e2e(
        deploy: bool = typer.Option(False, "--deploy", is_flag=True, help="Deploy the test lambda function"),
        run: bool = typer.Option(False, "--run", is_flag=True, help="Run the query to accept the e2e or not"),
        teardown: bool = typer.Option(False, "--teardown", is_flag=True, help="Teardown the lambda function"),
        env: str = typer.Option("dev", "--env", help="AWS Environment"),
        region: str = typer.Option("eu-west-1", "--region", help="AWS Region"),
) -> None:
    """Run the E2E acceptance test on real AWS."""
    if deploy:
        iam = boto3.client("iam", region_name=region)
        assume_role_policy = {
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "lambda.amazonaws.com"
                    },
                    "Action": "sts:AssumeRole"
                }
            ]
        }

        sts_client = boto3.client("sts", region_name=region)
        account_id = sts_client.get_caller_identity()["Account"]
        sdk_policy_arn = f"arn:aws:iam::{account_id}:policy/LogSentinelSDKPolicy"

        try:
            role = iam.create_role(
                RoleName="logsentinel-e2e-role",
                AssumeRolePolicyDocument=json.dumps(assume_role_policy),
            )
            role_arn = role["Role"]["Arn"]
            iam.attach_role_policy(
                RoleName="logsentinel-e2e-role",
                PolicyArn="arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
            )
            iam.attach_role_policy(
                RoleName="logsentinel-e2e-role",
                PolicyArn=sdk_policy_arn
            )
        except iam.exceptions.EntityAlreadyExistsException:
            role_arn = iam.get_role(RoleName="logsentinel-e2e-role")["Role"]["Arn"]

        buffer = io.BytesIO()
        handler_path = pathlib.Path(__file__).parent.parent.parent.parent / "tests" / "e2e" / "test_lambda" / "handler.py"
        spec = importlib.util.find_spec("logsentinel_sdk")
        if spec is None or spec.submodule_search_locations is None:
            typer.echo("logsentinel_sdk not installed — run: poetry add --group dev ../logsentinel-sdk", err=True)
            raise typer.Exit(code=1)
        sdk_dir = pathlib.Path(spec.submodule_search_locations[0])
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.write(handler_path, arcname="handler.py")
            for file in sdk_dir.rglob("*.py"):
                zf.write(file, arcname=f"logsentinel_sdk/{file.relative_to(sdk_dir)}")
        buffer.seek(0)
        zip_bytes = buffer.read()

        time.sleep(10)
        lambda_client = boto3.client("lambda", region_name=region)
        try:
            lambda_client.create_function(
                FunctionName="logsentinel-e2e-test",
                Runtime="python3.13",
                Role=role_arn,
                Handler="handler.handler",
                Code={"ZipFile": zip_bytes},
            )
        except lambda_client.exceptions.ResourceConflictException:
            lambda_client.update_function_code(FunctionName="logsentinel-e2e-test", ZipFile=zip_bytes)

    elif run:
        lambda_client = boto3.client("lambda", region_name=region)
        response = lambda_client.invoke(
            FunctionName="logsentinel-e2e-test",
            InvocationType="RequestResponse",
        )
        payload = json.loads(response["Payload"].read())
        sentinel_id = payload["sentinel_id"]


        dynamodb = boto3.client("dynamodb", region_name=region)
        for _ in range(10):
            result = dynamodb.query(
                TableName=f"logsentinel-events-{env}",
                KeyConditionExpression="sentinel_id = :sid",
                ExpressionAttributeValues={":sid": {"S": sentinel_id}},
            )
            if len(result["Items"]) >= 5:
                typer.echo("✓ All 5 records found in DynamoDB")
                raise typer.Exit(code=0)
            time.sleep(1)
        typer.echo("✗ Timeout: records not found after 10s", err=True)
        raise typer.Exit(code=1)

    elif teardown:
        lambda_client = boto3.client("lambda", region_name=region)
        lambda_client.delete_function(FunctionName="logsentinel-e2e-test")
        typer.echo("✓ Test Lambda deleted")

    else:
        typer.echo("Specify --deploy, --run, or --teardown", err=True)
        raise typer.Exit(code=1)

@app.command()
def parse(
    file: Path = typer.Argument(exists=True),
    format: Format = typer.Option(Format.cloudwatch, "--format"),
    level: Optional[str] = typer.Option(None, "--level"),
    search: Optional[str] = typer.Option(None, "--search")
) -> None:
    if level is not None:
        if level.upper() not in valid_levels:
            typer.echo("Error: invalid level {}".format(level), err=True)
            raise typer.Exit(code=1)
    parser = CloudWatchParser()
    try:
        result = parser.parse_file(file)
    except FileNotFoundError:
        typer.echo("Error: file {} not found".format(file), err=True)
        raise typer.Exit(code=1)
    except ValueError:
        typer.echo("Error: file {} not valid".format(file), err=True)
        raise typer.Exit(code=1)
    if len(result) == 0:
        typer.echo("No log entries found.")
        raise typer.Exit(code=0)

    if level is not None:
        min_level = LogLevel[level.upper()]
        level_filter = LevelFilter(min_level)
        result = level_filter.apply(result)

    if search is not None:
        result = SearchFilter(search).apply(result)

    table = TableFormatter().format(entries=result)
    Console().print(table)

