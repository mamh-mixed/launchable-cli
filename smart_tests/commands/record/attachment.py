import fnmatch
import tarfile
import zipfile
from io import BytesIO
from typing import Annotated, List, Tuple

import click

import smart_tests.args4p.typer as typer
from smart_tests.utils.session import SessionId, get_session

from ... import args4p
from ...app import Application
from ...utils.fail_fast_mode import warn_and_exit_if_fail_fast_mode
from ...utils.smart_tests_client import SmartTestsClient
from tabulate import tabulate


class AttachmentStatus:
    SUCCESS = "✓ Recorded successfully"
    FAILED = "⚠ Failed to record"
    SKIPPED_NON_TEXT = "⚠ Skipped: not a valid text file"


@args4p.command(help="Record attachment information")
def attachment(
    app: Application,
    session: Annotated[SessionId, SessionId.as_option()],
    attachments: Annotated[List[str], typer.Argument(
        multiple=True,
        help="Attachment files to upload"
    )],
    include_patterns: Annotated[List[str], typer.Option(
        '--include',
        help='Include only files matching pattern (e.g., "*.log"). Can be specified multiple times.',
        type=str,
        multiple=True,
    )] = []
):
    client = SmartTestsClient(app=app)
    summary_rows = []
    try:
        # Note: Call get_session method to check test session exists
        _ = get_session(session, client)
        for a in attachments:
            # If zip file
            if zipfile.is_zipfile(a):
                with zipfile.ZipFile(a, 'r') as zip_file:
                    for zip_info in zip_file.infolist():
                        if zip_info.is_dir():
                            continue

                        if not matches_include_patterns(zip_info.filename, include_patterns):
                            continue

                        file_content = zip_file.read(zip_info.filename)

                        if not valid_utf8_file(file_content):
                            summary_rows.append(
                                [zip_info.filename, AttachmentStatus.SKIPPED_NON_TEXT])
                            continue

                        status = post_attachment(
                            client, session, file_content, zip_info.filename)
                        summary_rows.append([zip_info.filename, status])

            # If tar file (tar, tar.gz, tar.bz2, tgz, etc.)
            elif tarfile.is_tarfile(a):
                with tarfile.open(a, 'r:*') as tar_file:
                    for tar_info in tar_file:
                        if tar_info.isdir():
                            continue

                        if not matches_include_patterns(tar_info.name, include_patterns):
                            continue

                        file_obj = tar_file.extractfile(tar_info)
                        if file_obj is None:
                            continue

                        file_content = file_obj.read()

                        if not valid_utf8_file(file_content):
                            summary_rows.append(
                                [tar_info.name, AttachmentStatus.SKIPPED_NON_TEXT])
                            continue

                        status = post_attachment(
                            client, session, file_content, tar_info.name)
                        summary_rows.append([tar_info.name, status])

            else:
                with open(a, mode='rb') as f:
                    file_content = f.read()

                    if not valid_utf8_file(file_content):
                        summary_rows.append(
                            [a, AttachmentStatus.SKIPPED_NON_TEXT])
                        continue

                    status = post_attachment(client, session, file_content, a)
                    summary_rows.append([a, status])
    except Exception as e:
        client.print_exception_and_recover(e)

    display_summary_as_table(summary_rows)


def matches_include_patterns(filename: str, include_patterns: List[str]) -> bool:
    """
    Check if a file should be included based on the include patterns.
    If no patterns are specified, all files are included.
    """
    if not include_patterns:
        return True

    for pattern in include_patterns:
        if fnmatch.fnmatch(filename, pattern):
            return True

    return False


def valid_utf8_file(file_content: bytes) -> bool:
    # Check for null bytes (binary files)
    if b'\x00' in file_content:
        return False

    try:
        file_content.decode('utf-8')
        return True
    except UnicodeDecodeError:
        return False


def post_attachment(client: SmartTestsClient, session: SessionId, file_content: bytes, filename: str) -> str:
    try:
        res = client.request(
            "post", session.subpath("attachment"), compress=True, payload=BytesIO(file_content),
            additional_headers={"Content-Disposition": "attachment;filename=\"{}\"".format(filename)})
        res.raise_for_status()
        return AttachmentStatus.SUCCESS
    except Exception as e:
        click.echo("Failed to upload {}: {}".format(
            filename, str(e)), err=True)
        return AttachmentStatus.FAILED


def display_summary_as_table(rows):
    headers = ["File", "Status"]
    click.echo(tabulate(rows, headers, tablefmt="github"))
