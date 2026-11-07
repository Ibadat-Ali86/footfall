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
@click.option(
    "--parquet",
    default="phase0/data/snapshots.parquet",
    help="Path to Parquet snapshots",
)
@click.option(
    "--registry",
    default="registry/seed.yaml",
    help="Path to registry seed YAML",
)
@click.option(
    "--ledger-output",
    default="data/ledger/calls.jsonl",
    help="Path to calls ledger JSONL",
)
@click.option(
    "--output",
    default="data/backtest/latest.json",
    help="Path to backtest report output JSON",
)
def backtest(parquet: str, registry: str, ledger_output: str, output: str) -> None:
    """Run the weekly backtest and append to the call ledger."""
    from footfall.ledger.reproduce import run_reproduce_pipeline

    manifest = run_reproduce_pipeline(
        snapshots_parquet=parquet,
        registry_yaml=registry,
        ledger_output=ledger_output,
        backtest_output=output,
        verify=False,
    )
    click.echo(
        f"Backtest complete: {manifest['total_calls']} calls evaluated, "
        f"{manifest['resolved_calls']} resolved ({manifest['coverage']:.1%} coverage). "
        f"Precision: {manifest['breakout_precision']:.1%}. Report -> {output}"
    )


@main.command()
@click.option(
    "--verify",
    is_flag=True,
    default=False,
    help="Verify that rebuilt outputs match the cryptographic manifest",
)
@click.option(
    "--manifest",
    default="data/backtest/manifest.json",
    help="Path to reference manifest JSON",
)
def reproduce(verify: bool, manifest: str) -> None:
    """Rebuild derived tables and backtest from raw snapshots and verify hashes (Section 11.5)."""
    from footfall.ledger.reproduce import run_reproduce_pipeline

    try:
        res = run_reproduce_pipeline(verify=verify, manifest_path=manifest)
        click.echo(
            f"Reproduce verification successful: "
            f"Ledger SHA-256={res['calls_ledger_sha256'][:16]}..., "
            f"Backtest SHA-256={res['backtest_report_sha256'][:16]}..."
        )
    except Exception as exc:
        click.echo(f"Reproduce verification failed: {exc}", err=True)
        sys.exit(1)


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


@main.command()
@click.option(
    "--output-dir",
    default="exports/v1",
    help="Target directory for static export files",
)
@click.option(
    "--snapshots",
    default="phase0/data/snapshots.parquet",
    help="Path to Parquet snapshots",
)
@click.option(
    "--registry",
    default="registry/seed.yaml",
    help="Path to registry seed YAML",
)
@click.option(
    "--as-of",
    default="2026-11-02",
    help="Effective date for static exports (YYYY-MM-DD)",
)
def export(output_dir: str, snapshots: str, registry: str, as_of: str) -> None:
    """Generate static export bundle and shields.io badges (Section 12.1)."""
    from footfall.export import generate_static_export_bundle

    summary = generate_static_export_bundle(
        snapshots_parquet=snapshots,
        registry_yaml=registry,
        output_dir=output_dir,
        as_of=as_of,
    )
    click.echo(
        f"Export bundle generated in {output_dir}: "
        f"{summary['entities_count']} entities, {summary['badges_count']} badges, "
        f"{summary['leaderboards_count']} leaderboards."
    )


@main.command()
@click.option("--host", default="127.0.0.1", help="Bind host address")
@click.option("--port", default=8000, help="Port to listen on")
@click.option("--exports-dir", default="exports/v1", help="Path to static exports directory")
@click.option(
    "--stdio", is_flag=True, default=False, help="Run over stdio transport instead of HTTP"
)
def serve(host: str, port: int, exports_dir: str, stdio: bool) -> None:
    """Run the Footfall MCP server (Section 12.2)."""
    import asyncio

    import uvicorn

    from footfall.server import create_mcp_server, create_streamable_app

    if stdio:
        server = create_mcp_server(exports_dir=exports_dir)
        asyncio.run(server.run_stdio_async())
    else:
        app = create_streamable_app(exports_dir=exports_dir)
        uvicorn.run(app, host=host, port=port)


@main.command()
@click.argument("manifest", type=click.Path(exists=True, path_type=Path))
@click.option("--exports-dir", default="exports/v1", help="Path to static exports directory")
@click.option("--json-out", is_flag=True, default=False, help="Emit output as JSON")
def stack(manifest: Path, exports_dir: str, json_out: bool) -> None:
    """Analyze dependencies in a manifest file (pyproject.toml, requirements.txt, package.json)."""
    import json

    from footfall.stack import StackAnalyzer

    analyzer = StackAnalyzer.create_from_exports(exports_dir=exports_dir)
    report = analyzer.analyze_manifest(manifest)

    if json_out:
        click.echo(json.dumps(report.to_dict(), indent=2))
        return

    click.echo(f"=== Footfall Stack Health: {report.manifest_file} ===")
    click.echo(f"Total Declared Dependencies: {report.total_dependencies}")
    click.echo(f"Tracked AI Ecosystem Tools: {report.tracked_tools_count}")
    click.echo(f"Mean Adoption z-score:       {report.mean_adoption_z:+.2f}")
    click.echo("\nLifecycle Phase Distribution:")
    for phase, count in sorted(report.phase_distribution.items()):
        click.echo(f"  - {phase:<18}: {count}")

    if report.tracked_items:
        click.echo("\nTracked Tools Detail:")
        for item in report.tracked_items:
            click.echo(
                f"  - {item.display_name:<20} [{item.category:<15}] "
                f"Phase: {item.phase:<12} "
                f"(adoption_z: {item.adoption_z:+.2f}, D: {item.divergence:+.2f})"
            )


@main.command()
@click.option(
    "--ledger",
    default="data/ledger/calls.jsonl",
    type=click.Path(exists=True, path_type=Path),
    help="Path to call ledger JSONL",
)
@click.option(
    "--feed-dir",
    type=click.Path(path_type=Path),
    help="Output directory for RSS, Atom, and JSON feeds",
)
@click.option("--webhook-url", help="HTTPS webhook destination URL")
@click.option("--webhook-secret", help="Shared secret for HMAC-SHA256 signature")
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="Process alerts without writing feeds or dispatching webhooks",
)
def alerts(
    ledger: Path,
    feed_dir: Path | None,
    webhook_url: str | None,
    webhook_secret: str | None,
    dry_run: bool,
) -> None:
    """Process ecosystem alerts: generate syndication feeds and dispatch webhooks."""
    import json
    from collections import defaultdict
    from typing import Any

    from footfall.alerts import AlertDetector, FeedGenerator, WebhookDispatcher

    records_by_entity: dict[str, list[dict[str, Any]]] = defaultdict(list)
    with ledger.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if stripped:
                rec = json.loads(stripped)
                records_by_entity[rec["entity_id"]].append(rec)

    prev_state: dict[str, dict[str, Any]] = {}
    curr_state: dict[str, dict[str, Any]] = {}
    latest_ts = "2026-11-01T00:00:00Z"

    for eid, history in records_by_entity.items():
        if len(history) >= 2:
            prev_state[eid] = history[-2]
            curr_state[eid] = history[-1]
            latest_ts = history[-1].get("timestamp", latest_ts)
        elif len(history) == 1:
            curr_state[eid] = history[0]
            latest_ts = history[0].get("timestamp", latest_ts)

    detector = AlertDetector()
    events = detector.detect_changes(prev_state, curr_state, timestamp=latest_ts)

    click.echo(f"Alerts processed: {len(events)}")
    for ev in events:
        click.echo(f"  - [{ev.alert_type.value}] {ev.display_name}: {ev.summary}")

    if dry_run:
        click.echo("Dry run enabled. Feeds and webhooks not dispatched.")
        return

    if feed_dir:
        feed_dir.mkdir(parents=True, exist_ok=True)
        gen = FeedGenerator()
        (feed_dir / "rss.xml").write_text(gen.generate_rss(events), encoding="utf-8")
        (feed_dir / "atom.xml").write_text(gen.generate_atom(events), encoding="utf-8")
        (feed_dir / "feed.json").write_text(
            json.dumps(gen.generate_json_feed(events), indent=2), encoding="utf-8"
        )
        click.echo(f"Syndication feeds written to: {feed_dir}")

    if webhook_url:
        dispatcher = WebhookDispatcher(webhook_url=webhook_url, secret=webhook_secret)
        success = dispatcher.dispatch(events)
        click.echo(f"Webhook dispatch result: {'success' if success else 'failed'}")
