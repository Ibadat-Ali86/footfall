"""CLI entry point for the footfall pipeline."""

from __future__ import annotations

import asyncio
import sys
from datetime import UTC, date, datetime, timedelta
from pathlib import Path

import click

from footfall.collectors import (
    GitHubCollector,
    HackerNewsCollector,
    HuggingFaceCollector,
    NpmCollector,
    PyPICollector,
    Snapshot,
)
from footfall.registry import load_registry
from footfall.store.raw import (
    DailyQualityGateError,
    RawSnapshotStore,
    validate_daily_snapshots,
)


def resolve_target_date(date_str: str) -> str:
    """Resolve 'yesterday' or YYYY-MM-DD to ISO date string."""
    if date_str.lower() == "yesterday":
        yesterday = datetime.now(UTC).date() - timedelta(days=1)
        return yesterday.isoformat()
    return date.fromisoformat(date_str).isoformat()


@click.group()
@click.version_option(package_name="footfall-core")
def main() -> None:
    """Footfall — Real usage, not hype."""


@main.command()
@click.option("--date", default="yesterday", help="Collection date (YYYY-MM-DD or 'yesterday')")
@click.option("--raw-dir", default="data/raw", help="Path to raw storage directory")
@click.option("--registry", default="registry/seed.yaml", help="Path to registry seed YAML")
def collect(date: str, raw_dir: str, registry: str) -> None:
    """Collect daily snapshots from all configured sources."""
    obs_date = resolve_target_date(date)
    reg_path = Path(registry)
    if not reg_path.is_file():
        default_path = Path(__file__).parents[2] / registry
        if default_path.is_file():
            reg_path = default_path

    entities = load_registry(reg_path)
    store = RawSnapshotStore(raw_dir)

    async def _run_collection() -> list[Snapshot]:
        npm = NpmCollector()
        pypi = PyPICollector()
        gh = GitHubCollector()
        hf = HuggingFaceCollector()
        hn = HackerNewsCollector()

        all_snaps: list[Snapshot] = []

        for entity in entities:
            for s in entity.sources:
                if s.source.value == "npm":
                    snaps = await npm.collect_entity(entity.entity_id, s.key, obs_date)
                    all_snaps.extend(snaps)
                elif s.source.value == "pypi":
                    snaps = await pypi.collect_entity(entity.entity_id, s.key, obs_date)
                    all_snaps.extend(snaps)
                elif s.source.value == "github":
                    snaps = await gh.collect_entity(entity.entity_id, s.key, obs_date)
                    all_snaps.extend(snaps)
                elif s.source.value == "hf":
                    snaps = await hf.collect_entity(entity.entity_id, s.key, obs_date)
                    all_snaps.extend(snaps)

            # Query HN attention for GitHub repo
            gh_key = next((src.key for src in entity.sources if src.source.value == "github"), None)
            if gh_key:
                hn_snaps = await hn.collect_entity(entity.entity_id, gh_key, obs_date)
                all_snaps.extend(hn_snaps)

        return all_snaps

    click.echo(f"Collecting snapshots for {obs_date} across {len(entities)} entities...")
    snapshots = asyncio.run(_run_collection())
    written_file = store.write_daily_file(obs_date, snapshots, validate=False)
    click.echo(f"Collected {len(snapshots)} snapshots -> {written_file}")


@main.command()
@click.option("--date", default="yesterday", help="Collection date (YYYY-MM-DD or 'yesterday')")
@click.option("--raw-dir", default="data/raw", help="Path to raw storage directory")
@click.option("--registry", default="registry/seed.yaml", help="Path to registry seed YAML")
@click.option("--min-coverage", default=0.80, help="Minimum active entity coverage share")
def validate(date: str, raw_dir: str, registry: str, min_coverage: float) -> None:
    """Validate collected data quality; block publish on failures."""
    obs_date = resolve_target_date(date)
    reg_path = Path(registry)
    if not reg_path.is_file():
        default_path = Path(__file__).parents[2] / registry
        if default_path.is_file():
            reg_path = default_path

    entities = load_registry(reg_path) if reg_path.is_file() else []
    total_active = len(entities) if entities else 1

    store = RawSnapshotStore(raw_dir)
    try:
        snapshots = store.read_daily_file(obs_date)
        metrics = validate_daily_snapshots(
            snapshots=snapshots,
            obs_date=obs_date,
            total_active_entities=total_active,
            min_coverage_share=min_coverage,
        )
        click.echo(
            f"Validation passed for {obs_date}: "
            f"{metrics['total_snapshots']} snapshots across {metrics['unique_entities']} entities "
            f"({metrics['coverage_share']:.1%} coverage, error share {metrics['error_share']:.1%})"
        )
    except (DailyQualityGateError, FileNotFoundError, Exception) as exc:
        click.echo(f"Validation failed for {obs_date}: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.option("--date", default="yesterday", help="Collection date (YYYY-MM-DD or 'yesterday')")
@click.option("--raw-dir", default="data/raw", help="Path to raw storage directory")
def publish(date: str, raw_dir: str) -> None:
    """Write raw data to footfall-data repo and export static files."""
    obs_date = resolve_target_date(date)
    store = RawSnapshotStore(raw_dir)
    daily_file = store.get_daily_path(obs_date)

    if not daily_file.is_file():
        click.echo(f"Cannot publish: {daily_file} does not exist!", err=True)
        sys.exit(1)

    click.echo(f"Publish verified for {obs_date}: {daily_file} is ready for footfall-data push.")


@main.command()
def features() -> None:
    """Compute weekly features and phase classifications."""
    # TODO T1.4, T1.5 — implement feature and phase engines
    raise NotImplementedError("features: not yet implemented (tasks T1.4, T1.5)")


@main.command()
def backtest() -> None:
    """Run the weekly backtest and append to the call ledger."""
    # TODO T1.7 — implement ledger and backtest
    raise NotImplementedError("backtest: not yet implemented (task T1.7)")


@main.command()
@click.option(
    "--parquet",
    default="phase0/data/snapshots.parquet",
    help="Path to Parquet snapshots",
)
@click.option(
    "--output",
    default="phase0/data_quality_report.md",
    help="Path to output report",
)
def report(parquet: str, output: str) -> None:
    """Generate automated data quality report from Parquet dataset."""
    from footfall.backfill import generate_quality_report

    generate_quality_report(parquet, output)
    click.echo(f"Quality report generated: {output}")
