from http import HTTPStatus
from typing import Annotated, List, Optional, Tuple, cast

import click
from InquirerPy import inquirer
from tabulate import tabulate

import smart_tests.args4p.typer as typer
from smart_tests import args4p
from smart_tests.app import Application
from smart_tests.commands.compare.subsets import _display_from_subset_ids, _from_subset_ids, get_column_width, wrap_data
from smart_tests.utils.smart_tests_client import SmartTestsClient


def _get_previous_subset_id(client: SmartTestsClient, subset_id: int) -> Optional[int]:
    """Fetch the previous subset ID for the given subset from the API.

    Returns:
        Previous subset ID if found, None otherwise
    """
    try:
        response = client.request("get", f"subset-analyze/{subset_id}/previous")
        if response.status_code == HTTPStatus.NOT_FOUND:
            return None
        response.raise_for_status()
        payload = response.json()
        return payload.get("previousSubsettingId")
    except Exception as e:
        client.print_exception_and_recover(e, "Warning: failed to fetch previous subset ID")
        return None


def _get_pts_summary_for_expected_tests(
    expected_tests: List[str],
    expected_rows: List[Tuple[str, int, str, str, float]],
    total_tests: int
) -> str:
    """Get summary of PTS effectiveness based on expected tests

    Args:
        expected_tests: Tests the user selected
        expected_rows: List of (rank, after_order, test_name, reason, density) for expected tests
        total_tests: Total number of tests in the subset

    Example output:
        ✅ Tests Promoted:
        - test_model.py promoted by 42 positions to rank #1

        ✅ Tests Prioritized:
        - Expected test prioritized at rank #1 out of 67 (top 1.5%)

        ✅ Test Selection:
        - PTS successfully picked expected tests with high confidence
        - test_model.py: density 0.84 (very strong correlation)
    """

    if not expected_rows:
        return "⚠ No results to analyze"

    # Calculate metrics
    top_50_percent = total_tests / 2

    prioritized = [r for r in expected_rows if r[1] <= top_50_percent]
    promoted = [r for r in expected_rows if isinstance(r[0], str) and r[0].startswith('↑')]
    high_density = [r for r in expected_rows if r[4] > 0.6]

    # Build summary sections
    sections = []

    # Tests Promoted section (only if one or more promoted) - SHOW FIRST (flashiest metric!)
    if promoted:
        sections.append("✅ Tests Promoted:")

        for rank, after, test_name, reason, density in promoted:
            short_name = test_name.split('=')[-1].split('/')[-1] if '=' in test_name else test_name.split('/')[-1]
            promotion_amount = int(rank.replace('↑', ''))
            sections.append(f"- {short_name} promoted by {promotion_amount} positions to rank #{after}")

    # Tests Prioritized section (only if one or more in top 50%)
    if prioritized:
        if sections:  # Add spacing if previous section exists
            sections.append("")
        sections.append("✅ Tests Prioritized:")

        if len(expected_tests) == 1:
            test_rank = prioritized[0][1]
            percentage = (test_rank / total_tests) * 100
            sections.append(f"- Expected test prioritized at rank #{test_rank} out of {total_tests} (top {percentage:.1f}%)")
        else:
            # Multiple tests
            top_n = max(r[1] for r in prioritized)
            percentage = (top_n / total_tests) * 100
            count_text = f"{len(prioritized)}/{len(expected_tests)}"
            sections.append(
                f"- {count_text} of expected tests prioritized in top {top_n} "
                f"out of {total_tests} (top {percentage:.1f}%)")

            # Show individual rankings if helpful
            for rank, after, test_name, reason, density in prioritized:
                short_name = test_name.split('=')[-1].split('/')[-1] if '=' in test_name else test_name.split('/')[-1]
                sections.append(f"- {short_name} ranked #{after}")

    # Test Selection section (only if one or more have density > 0.6)
    if high_density:
        sections.append("")
        sections.append("✅ Test Selection:")
        sections.append("- PTS successfully picked expected tests with high confidence")

        for rank, after, test_name, reason, density in high_density:
            short_name = test_name.split('=')[-1].split('/')[-1] if '=' in test_name else test_name.split('/')[-1]

            # Descriptive density labels
            if density >= 0.8:
                confidence = "very strong"
            elif density >= 0.7:
                confidence = "strong"
            else:
                confidence = "moderate"

            sections.append(f"- {short_name}: density {density:.2f} ({confidence} confidence)")

    return "\n".join(sections) if sections else "⚠ Expected tests were not prioritized, promoted, or had high density"


def _echo_pts_summary_for_expected_tests(
    expected_tests: List[str],
    rows: List[Tuple[str, int, str, str, float]],
    total_tests: int
):
    click.echo()

    # Filter rows for expected tests only
    # rows format: (rank, after_order, test_name, reason, density)
    expected_rows = [
        row for row in rows
        if any(expected in row[2] for expected in expected_tests)
    ]

    summary = _get_pts_summary_for_expected_tests(expected_tests=expected_tests, expected_rows=expected_rows,
                                                  total_tests=total_tests)

    if summary:
        click.echo()
        click.echo(summary)
        click.echo()


def _get_related_tests(
    client: SmartTestsClient,
    changed_files: List[str],
    selected_tests: List[str],
    promoted_tests_data: List[Tuple[str, int, str, str, float]]
) -> List[str]:
    """Get related test suggestions from backend.

    Args:
        client: API client
        changed_files: List of changed file paths
        selected_tests: Tests user expected to be prioritized
        promoted_tests_data: Tuples of (rank, promotion, test_name, reason, density)

    Returns:
        List of suggested test names (max 3), or empty list on failure
    """
    try:
        # Limit to 500 tests
        promoted_tests_payload = [
            {
                "testName": name,
                "promotionAmount": promo,
                "density": density
            }
            for rank, promo, name, reason, density in promoted_tests_data[:500]
        ]

        payload = {
            "changedFiles": sorted(changed_files),
            "selectedTests": selected_tests,
            "promotedTests": promoted_tests_payload
        }

        response = client.request(
            "post",
            "subset-analyze/suggest-related-tests",
            payload=payload
        )
        response.raise_for_status()
        return response.json().get("relatedTests", [])

    except Exception:
        return []


def _analyze_subset(app: Application, subset_id: int, baseline_subset_id: Optional[int]):
    client = SmartTestsClient(app=app)

    # If baseline_subset_id not provided, try to fetch from API
    if baseline_subset_id is None:
        click.echo("→ Fetching previous subset ID...")
        baseline_subset_id = _get_previous_subset_id(client, subset_id)
        if baseline_subset_id is None:
            click.secho(
                "✗ No previous subset available for comparison. This appears to be the first subset.",
                fg="red",
                err=True
            )
            return
        click.echo(f"✓ Found previous subset ID: {baseline_subset_id}")

    click.echo("→ Fetching subset data...")
    try:
        rows, total, promoted, demoted, affected = _from_subset_ids(client, baseline_subset_id, subset_id)
    except Exception as e:
        click.secho(f"✗ Failed to fetch subset data: {e}", fg="red", err=True)
        return

    # Filter out DELETED tests - rows format: (rank, after_order, test_name, reason, density)
    # After filtering: rank is str, after_order is int, density is float
    rows_without_deleted = cast(
        List[Tuple[str, int, str, str, float]],
        [row for row in rows if row[0] != "DELETED"]
    )
    test_names = [row[2] for row in rows_without_deleted]

    if not test_names:
        click.secho("✗ No tests found in subset", fg="red", err=True)
        return

    click.echo(f"✓ Found {len(test_names)} tests in subset")
    click.echo()

    # Step 1: Select Expected Tests
    click.echo("─" * 70)
    click.echo("Select Expected Tests")
    click.echo("─" * 70)
    click.echo()

    if affected:
        click.echo("Code files modified:")
        for file in sorted(affected):
            click.echo("  - " + click.style(file, bold=True))
        click.echo()

    click.echo("Which tests do you expect PTS to prioritize?")
    click.echo()

    expected_tests = []
    if inquirer.confirm(message="Select expected tests?", default=True).execute():
        click.echo()
        tab_space = click.style("Tab/Space", fg="cyan")
        enter_key = click.style("Enter", fg="cyan")
        click.echo(
            f"Use {tab_space} to toggle selection, {enter_key} when done"
        )
        click.echo()

        try:
            expected_tests = inquirer.fuzzy(
                message="Search and select expected tests:",
                choices=test_names,
                multiselect=True,
                max_height="70%",
                mandatory=True,
                marker="✓ ",
                marker_pl="  ",
            ).execute()

            if expected_tests:
                click.echo(f"\n✓ Selected {len(expected_tests)} expected test(s):")
                for test in expected_tests:
                    click.echo(f"  • {test}")
            else:
                click.echo("\nNo tests selected.")
        except (KeyboardInterrupt, EOFError):
            click.echo("\nSkipped test selection.")
            expected_tests = []

    # If user didn't select any tests, fallback to:
    # smart_tests/commands/compare/subsets.py
    if not expected_tests:
        _display_from_subset_ids(rows, total, promoted, demoted, affected)
        return

    # Step 2: Show Comparison Results
    rows_matching_expected_tests = [
        (rank, after, test_name, reason, density)
        for rank, after, test_name, reason, density in rows_without_deleted
        if any(expected in test_name for expected in expected_tests)
    ]

    click.echo()
    click.echo("─" * 70)
    click.echo("Comparison Results")
    click.echo("─" * 70)
    click.echo()

    # Show filtered table
    headers = ["Δ Rank", "Subset Rank", "Test Name", "Reason", "Density"]
    column_width = get_column_width()
    tabular_data = [
        (rank, after, wrap_data(test_name, width=column_width), wrap_data(reason, width=column_width), density)
        for rank, after, test_name, reason, density in rows_matching_expected_tests
    ]
    click.echo(tabulate(tabular_data, headers=headers, tablefmt="simple"))

    # Check if any expected tests were prioritized (top 50%) or promoted
    top_50_percent = total / 2
    any_prioritized_or_promoted = any(
        rank.startswith('↑') or after <= top_50_percent
        for rank, after, test_name, reason, density in rows_matching_expected_tests
    )

    if not any_prioritized_or_promoted:
        # Try to suggest related tests using backend
        suggestions = []
        try:
            # Build list of tests to send to backend for suggestions
            # Include: (1) Top 50% tests, (2) All promoted tests
            # This ensures backend sees both high-ranking tests and tests that moved significantly
            top_50_percent = total / 2

            # Collect tests to send to backend (use dict to deduplicate by test_name)
            # Store: (rank_str, promotion_amount, test_name, reason, density, after_order)
            tests_for_ai = {}

            for rank, after, test_name, reason, density in rows_without_deleted:
                # Calculate promotion amount
                if isinstance(rank, str) and rank.startswith('↑'):
                    promotion_amount = int(rank.replace('↑', ''))
                else:
                    promotion_amount = 0

                # Include if in top 50% OR promoted
                if after <= top_50_percent or promotion_amount > 0:
                    tests_for_ai[test_name] = (rank, promotion_amount, test_name, reason, density, after)

            # Convert to list and sort by:
            # 1. Promotion amount (descending) - most promoted first
            # 2. Rank position (ascending) - lower rank is better
            tests_with_order = list(tests_for_ai.values())
            tests_with_order.sort(key=lambda x: (-x[1], x[5]))

            # Remove after_order from tuples (backend expects 5-tuple)
            promoted_tests_data: List[Tuple[str, int, str, str, float]] = [
                (rank, promo, name, reason, density)
                for rank, promo, name, reason, density, after in tests_with_order
            ]

            # Limit to 500 tests for backend context
            # Why limit the context?
            # - LLMs doesn't perform well in very long contexts
            # - 500 tests ≈ 12.5K tokens, well within limits
            # - 500 limit should cover top 50% of test + all promoted tests in most large test suites (1000+ tests)
            promoted_tests_data = promoted_tests_data[:500]

            if affected and promoted_tests_data:
                suggestions = _get_related_tests(
                    client=client,
                    changed_files=sorted(affected),
                    selected_tests=expected_tests,
                    promoted_tests_data=promoted_tests_data
                )
        except Exception:
            pass

        click.echo()

        if not suggestions:
            click.secho("⚠ Expected test(s) were not promoted in this instance.")
            click.echo("- Make sure subset is created with related tests")
            click.echo("- Or try modifying a different file, and try again")
            click.echo()

            if inquirer.confirm(
                    message="Would you like to search and inspect all tests?",
                    default=True
            ).execute():
                _display_from_subset_ids(rows, total, promoted, demoted, affected)

            return

        # Show suggestions as selectable options
        click.secho("Did you expect the following test(s) instead?", fg="cyan")

        suggestion_choices = []
        suggestion_map = {}  # Map display text to test name
        for suggestion in suggestions:
            # Find the test in rows to show its stats
            for rank, after, test_name, reason, density in rows_without_deleted:
                if suggestion in test_name:
                    display_text = f"{test_name} (Rank #{after}, {rank}, Density {density:.2f})"
                    suggestion_choices.append(display_text)
                    suggestion_map[display_text] = test_name
                    break

        suggestion_choices.append("No, search all tests instead")

        selected_option = inquirer.select(
            message="Select a test to see its summary:",
            choices=suggestion_choices,
            default=suggestion_choices[0] if suggestion_choices else None,
        ).execute()

        if selected_option != "No, search all tests instead":
            # User selected a suggested test - show AI summary for it
            selected_test_name = suggestion_map[selected_option]
            _echo_pts_summary_for_expected_tests([selected_test_name], rows_without_deleted, total)
            return
        else:
            _display_from_subset_ids(rows, total, promoted, demoted, affected)
            return

    _echo_pts_summary_for_expected_tests(expected_tests, rows_without_deleted, total)


@args4p.command()
def subset(
    app: Application,
    subset_id: Annotated[int, typer.Argument(help="Subset ID to analyze")],
    baseline_subset_id: Annotated[
        Optional[int],
        typer.Option(
            "--baseline-subset-id",
            help="Baseline subset ID to compare against (auto-detected if not provided)"
        )
    ] = None,
):
    _analyze_subset(app, subset_id, baseline_subset_id)
