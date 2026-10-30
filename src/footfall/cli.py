"""CLI entry point for the footfall pipeline."""
from __future__ import annotations

import click


@click.group()
@click.version_option()
def main() -> None:
    """Footfall — Real usage, not hype."""


@main.command()
@click.option("--date", default="yesterday", help="Collection date (YYYY-MM-DD or 'yesterday')")
def collect(date: str) -> None:
    """Collect daily snapshots from all configured sources."""
    # TODO T1.1 — implement production collectors
    raise NotImplementedError("collect: not yet implemented (task T1.1)")


@main.command()
def validate() -> None:
    """Validate collected data quality; block publish on failures."""
    # TODO T1.2 — implement raw store validation
    raise NotImplementedError("validate: not yet implemented (task T1.2)")


@main.command()
def publish() -> None:
    """Write raw data to footfall-data repo and export static files."""
    # TODO T1.3 — implement publish step
    raise NotImplementedError("publish: not yet implemented (task T1.3)")


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
