import pathlib
import zipfile
from enum import Enum
from pathlib import Path
from typing import Any, Optional

import boto3
import typer
from botocore import exceptions as botocore_exceptions
from rich.console import Console

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
    sts = boto3.client("sts", region_name=region)
    try:
        identity = sts.get_caller_identity()
        account_id = identity["Account"]  # "123456789012"
    except botocore_exceptions.NoCredentialsError:
        typer.echo("No AWS credentials found. Run: aws configure", err=True)
        raise typer.Exit(code=1)

    s3 = boto3.client("s3", region_name=region)
    bucket_name = f"logsentinel-artifacts-{account_id}"
    try:
        s3.head_bucket(Bucket=bucket_name)
        typer.echo("LogSentinel bucket {} found. Creation omitted".format(account_id))
    except botocore_exceptions.ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("404", "NoSuchBucket"):
            typer.echo("LogSentinel bucket {} not found. Creation is needed".format(account_id))
            kwargs: dict[str, Any] = {"Bucket": bucket_name}
            if region != "us-east-1":
                kwargs["CreateBucketConfiguration"] = {"LocationConstraint": region}
            s3.create_bucket(**kwargs)
            typer.echo("LogSentinel bucket {} created.".format(bucket_name))
            pass
        else:
            raise

    typer.echo("Packaging LogSentinel artifacts into zip file")
    handler_path = pathlib.Path(__file__).parent.parent / "infra" / "consumer" / "handler.py"
    zip_path = pathlib.Path("/tmp/consumer.zip")
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        zf.write(handler_path, arcname="handler.py")
    typer.echo("Zip file created, now uploading to S3 {}".format(bucket_name))

    s3.upload_file(str(zip_path), bucket_name, "consumer.zip")
    typer.echo("LogSentinel bucket {} uploaded".format(f"s3://{bucket_name}/consumer.zip"))

    stack_name = f"logsentinel-{env}"
    cf = boto3.client("cloudformation", region_name=region)

    try:
        typer.echo("Stack creation starting")
        cf.describe_stacks(StackName=stack_name)
        try:
            typer.echo("Stack already exists, updating the stack")
            cf.update_stack(
                StackName=stack_name,
                TemplateBody=open(
                    pathlib.Path(__file__).parent.parent / "infra" / "stack.yaml"
                ).read(),
                Parameters=[
                    {"ParameterKey": "Env", "ParameterValue": env},
                    {"ParameterKey": "RetentionDays", "ParameterValue": str(retention_days)},
                    {
                        "ParameterKey": "ArtifactsBucketName",
                        "ParameterValue": bucket_name,
                    },
                ],
                Capabilities=["CAPABILITY_NAMED_IAM"],
            )
            typer.echo("Stack updated, deployment in progress")
            cf.get_waiter("stack_update_complete").wait(StackName=stack_name)
            typer.echo("Stack deployed")
        except botocore_exceptions.ClientError as e:
            if "No updates are to be performed" in str(e):
                typer.echo("No updates are to be performed, stack already up tp date")
            else:
                raise

    except botocore_exceptions.ClientError as e:
        if "does not exist" in str(e):
            cf.create_stack(
                StackName=stack_name,
                TemplateBody=open(pathlib.Path(__file__).parent.parent / "infra" / "stack.yaml").read(),
                Parameters=[
                    {"ParameterKey": "Env", "ParameterValue": env},
                    {"ParameterKey": "RetentionDays", "ParameterValue": str(retention_days)},
                    {"ParameterKey": "ArtifactsBucketName", "ParameterValue": bucket_name},
                ],
                Capabilities=["CAPABILITY_NAMED_IAM"],
            )
            typer.echo("Stack deployed, deployment in progress")
            cf.get_waiter("stack_create_complete").wait(StackName=stack_name)
            typer.echo("Stack deployed")
            pass
        else:
            raise

    response = cf.describe_stacks_resources(StackName=stack_name)
    for resource in response["StacksResources"]:
        typer.echo(resource["ResourceType"])
        typer.echo(resource["PhysicalResourceId"])
        typer.echo(resource["ResourceStatus"])

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

