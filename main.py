from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

if sys.platform == "win32" and sys.stdout.encoding and sys.stdout.encoding.lower() in ("cp1252", "ansi_x3.4-1968"):
    try:
        sys.stdout.reconfigure(errors="replace")
    except (ValueError, AttributeError):
        pass

import typer
from rich import print as rprint
from rich.box import ASCII2, MINIMAL
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.progress import BarColumn, Progress, TextColumn, TimeElapsedColumn
from rich.prompt import Confirm
from rich.table import Table
from rich.text import Text

from core.categories import _get_extension
from core.config import Config, load_config, save_default_config, DEFAULT_CATEGORIES
from core.organizer import organize as run_organize
from core.reporter import Report, load_report, REPORT_FILE, TEXT_REPORT_FILE
from core.scanner import scan_directory, FileInfo
from utils.helpers import format_duration, human_readable_size, resolve_base_path
from utils.logger import setup_logging, get_logger
from utils.manifest import load_latest_manifest, undo_manifest
from utils.watcher import start_watching

app = typer.Typer(
    name="sfop",
    help="Smart File Organizer Pro — automatically organize messy folders into structured categories.",
    rich_markup_mode="rich",
    no_args_is_help=True,
)
console = Console()

_USE_ASCII = not sys.stdout.isatty() or sys.platform == "win32"


def _safe_progress(*, transient: bool = True) -> Progress:
    return Progress(
        TextColumn("[cyan]  {task.description}..."),
        BarColumn() if sys.stdout.isatty() else TextColumn(""),
        TimeElapsedColumn(),
        console=console,
        transient=transient,
    )


def _table(**kwargs) -> Table:
    kwargs.setdefault("box", ASCII2)
    return Table(**kwargs)


def _load_config_and_merge(
    config_path: Optional[str] = None,
    path: Optional[str] = None,
    apply: Optional[bool] = None,
    recursive: Optional[bool] = None,
    no_logs: Optional[bool] = None,
) -> Config:
    if config_path:
        cfg = load_config(Path(config_path))
    else:
        cfg = load_config()
    return cfg.merge_cli(path=path, apply=apply, recursive=recursive, no_logs=no_logs)


def _show_report(report: Report) -> None:
    summary_panel = Panel(
        f"[bold cyan]Summary Dashboard[/]\n\n"
        f"[white]Base path:[/] [yellow]{report.base_path}[/]\n"
        f"[white]Files scanned:[/] [bold]{report.total_scanned}[/]\n"
        f"[white]Files moved:[/] [green]{report.files_moved}[/]\n"
        f"[white]Files skipped:[/] {report.files_skipped}\n"
        f"[white]Duplicates (renamed):[/] [magenta]{report.duplicates_handled}[/]\n"
        f"[white]Content duplicates:[/] [magenta]{report.content_duplicates}[/]\n"
        f"[white]Errors:[/] [red]{len(report.errors)}[/]\n"
        f"[white]Time:[/] [cyan]{format_duration(report.time_taken)}[/]",
        title="[bold]Smart File Organizer Pro[/]",
        border_style="bright_blue",
    )
    console.print(summary_panel)

    if report.manifest_entries:
        table = _table(title="Recent Moves", border_style="blue", show_lines=True)
        table.add_column("Source", style="cyan", no_wrap=True)
        table.add_column("Destination", style="green", no_wrap=True)
        for entry in report.manifest_entries[:15]:
            src_short = Path(entry.get("src", "")).name
            dest_short = Path(entry.get("dest", "")).name
            table.add_row(src_short, dest_short)
        if len(report.manifest_entries) > 15:
            table.add_row(f"... and {len(report.manifest_entries) - 15} more", "")
        console.print(table)

    if report.errors:
        error_panel = Panel(
            "\n".join(f"[red][ERROR][/] {err}" for err in report.errors[:10]),
            title="Errors",
            border_style="red",
        )
        console.print(error_panel)


def _show_preview_table(
    grouped: dict[str, list[FileInfo]],
    target: Path,
) -> None:
    total_files = sum(len(files) for files in grouped.values())
    if total_files == 0:
        console.print("[yellow]No files found to organize.[/]")
        return

    console.print(f"[bold]Preview: {total_files} files to organize[/]")
    for category in sorted(grouped.keys()):
        files = grouped[category]
        dest_dir = target / category
        rprint(f"\n[bold cyan]{category}/[/]  →  [green]{dest_dir}[/]")
        for fi in files:
            rprint(f"  [white]{fi.name:<30}[/] [yellow]{human_readable_size(fi.size):>8}[/]")
    console.print()
    size_total = sum(fi.size for files in grouped.values() for fi in files)
    rprint(f"[bold]Total:[/] {total_files} files, {human_readable_size(size_total)}")


def _group_by_category(files: list[FileInfo]) -> dict[str, list[FileInfo]]:
    grouped: dict[str, list[FileInfo]] = {}
    for fi in files:
        grouped.setdefault(fi.category, []).append(fi)
    return grouped


@app.command()
def organize(
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="Directory to organize (overrides config)",
    ),
    apply: bool = typer.Option(
        False, "--apply", "-a", help="Actually move files (default is dry-run preview)",
    ),
    recursive: Optional[bool] = typer.Option(
        None, "--recursive", "-r", help="Scan subdirectories recursively",
    ),
    no_logs: bool = typer.Option(
        False, "--no-logs", help="Disable logging for this run",
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to custom config.json",
    ),
) -> None:
    cfg = _load_config_and_merge(config_path, path, apply, recursive, no_logs)
    target = resolve_base_path(cfg.base_path)

    if not target.exists():
        console.print(f"[red]Error:[/] Directory not found: {target}")
        raise typer.Exit(1)

    logger = setup_logging(create_logs=cfg.create_logs, log_level=cfg.log_level)
    logger.info("Starting organize command — path=%s, apply=%s", target, not cfg.dry_run)

    rprint(f"\n[bold blue]== Smart File Organizer Pro ==[/]")
    rprint(f"  Path: [yellow]{target}[/]")
    rprint(f"  Mode: {'[red]APPLY[/]' if not cfg.dry_run else '[green]DRY RUN[/]'}")
    rprint(f"  Recursive: {cfg.recursive}\n")

    with _safe_progress() as progress:
        progress.add_task("[cyan]Scanning files", total=None)
        files = scan_directory(target, cfg.categories, recursive=cfg.recursive)

    grouped = _group_by_category(files)

    if not files:
        console.print("[yellow]No files found to organize.[/]")
        return

    _show_preview_table(grouped, target)

    if cfg.dry_run:
        if not Confirm.ask("\n[yellow]Proceed with organization?[/]", default=False):
            rprint("[red]Cancelled.[/]")
            report = Report(
                base_path=target,
                total_scanned=len(files),
                files_moved=0,
                files_skipped=0,
            )
            if cfg.create_logs:
                from core.reporter import save_report_json as _rj, save_report as _sr
                _rj(report, REPORT_FILE)
                _sr(report, TEXT_REPORT_FILE)
            _show_report(report)
            return
        cfg.dry_run = False

    with _safe_progress(transient=False) as progress:
        task = progress.add_task("[cyan]Organizing files", total=len(files))
        report = run_organize(cfg)
        progress.update(task, completed=len(files))

    _show_report(report)
    logger.info(
        "Organize complete — moved=%d, skipped=%d, errors=%d",
        report.files_moved,
        report.files_skipped,
        len(report.errors),
    )


@app.command()
def preview(
    path: Optional[str] = typer.Option(
        None, "--path", "-p", help="Directory to preview",
    ),
    recursive: Optional[bool] = typer.Option(
        None, "--recursive", "-r", help="Scan subdirectories recursively",
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to custom config.json",
    ),
) -> None:
    cfg = _load_config_and_merge(config_path, path, apply=False, recursive=recursive)
    target = resolve_base_path(cfg.base_path)

    if not target.exists():
        console.print(f"[red]Error:[/] Directory not found: {target}")
        raise typer.Exit(1)

    rprint(f"\n[bold blue]== Preview Mode ==[/]")
    rprint(f"  Path: [yellow]{target}[/]")
    rprint(f"  Recursive: {cfg.recursive}\n")

    with _safe_progress() as progress:
        progress.add_task("[cyan]Scanning files", total=None)
        files = scan_directory(target, cfg.categories, recursive=cfg.recursive)

    if not files:
        console.print("[yellow]No files found to organize.[/]")
        return

    grouped = _group_by_category(files)
    _show_preview_table(grouped, target)
    rprint("[dim]Run [bold]sfop organize --apply[/] to actually move these files.[/]")


@app.command()
def report() -> None:
    report_data = load_report(REPORT_FILE)
    if report_data is None:
        console.print("[yellow]No previous report found. Run [bold]organize[/] first.[/]")
        return
    _show_report(report_data)


@app.command()
def stats(
    path: Optional[str] = typer.Option(
        ".", "--path", "-p", help="Directory to analyze",
    ),
    recursive: Optional[bool] = typer.Option(
        False, "--recursive", "-r", help="Scan subdirectories recursively",
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to custom config.json",
    ),
) -> None:
    if config_path:
        cfg = load_config(Path(config_path))
    else:
        cfg = load_config()
    cfg = cfg.merge_cli(path=path, recursive=recursive)
    target = resolve_base_path(cfg.base_path)

    if not target.exists():
        console.print(f"[red]Error:[/] Directory not found: {target}")
        raise typer.Exit(1)

    with _safe_progress() as progress:
        progress.add_task("[cyan]Scanning files", total=None)
        files = scan_directory(target, cfg.categories, recursive=cfg.recursive)

    if not files:
        console.print("[yellow]No files found.[/]")
        return

    table = _table(title=f"Statistics: {target.name}", border_style="bright_blue")
    table.add_column("Category", style="bold cyan")
    table.add_column("Count", justify="right", style="white")
    table.add_column("Total Size", justify="right", style="yellow")
    table.add_column("Avg Size", justify="right", style="green")

    grouped = _group_by_category(files)
    grand_total = 0
    grand_size = 0

    for category in sorted(grouped.keys()):
        cat_files = grouped[category]
        count = len(cat_files)
        total_size = sum(fi.size for fi in cat_files)
        avg_size = total_size / count if count > 0 else 0
        table.add_row(
            category,
            str(count),
            human_readable_size(total_size),
            human_readable_size(int(avg_size)),
        )
        grand_total += count
        grand_size += total_size

    table.add_row(
        "[bold]Total[/]",
        f"[bold]{grand_total}[/]",
        f"[bold]{human_readable_size(grand_size)}[/]",
        "",
        style="bold",
    )
    console.print(table)


@app.command()
def undo() -> None:
    manifest = load_latest_manifest()
    if manifest is None or not manifest.entries:
        console.print("[yellow]No previous organization manifest found. Nothing to undo.[/]")
        return

    rprint(f"\n[bold yellow]== Undo Last Organization ==[/]")
    rprint(f"  Run ID: [cyan]{manifest.run_id}[/]")
    rprint(f"  Entries: {len(manifest.entries)}\n")

    table = _table(border_style="yellow")
    table.add_column("Current Location", style="green")
    table.add_column("Will Restore To", style="cyan")
    for entry in manifest.entries[:10]:
        if not entry.error:
            table.add_row(Path(entry.dest).name, Path(entry.src).name)
    if len(manifest.entries) > 10:
        table.add_row(f"... and {len(manifest.entries) - 10} more", "")
    console.print(table)

    if not Confirm.ask("\n[red]Restore files to original locations?[/]", default=False):
        rprint("[yellow]Undo cancelled.[/]")
        return

    with _safe_progress() as progress:
        progress.add_task("[yellow]Restoring files", total=None)
        result = undo_manifest(manifest)

    rprint(f"\n[green]+ {result['restored']} files restored[/]")
    if result["failed"] > 0:
        rprint(f"[red]- {result['failed']} files could not be restored[/]")


@app.command()
def init(
    path: str = typer.Option(
        "config.json", "--path", "-p", help="Where to create the config file",
    ),
) -> None:
    config_path = Path(path)
    if config_path.exists():
        if not Confirm.ask(f"[yellow]{config_path} already exists. Overwrite?[/]", default=False):
            rprint("[yellow]Cancelled.[/]")
            return
    save_default_config(config_path)
    rprint(f"[green][OK] Created default config: {config_path.resolve()}[/]")


@app.command()
def watch(
    path: Optional[str] = typer.Option(
        ".", "--path", "-p", help="Directory to watch",
    ),
    recursive: Optional[bool] = typer.Option(
        None, "--recursive", "-r", help="Watch subdirectories recursively",
    ),
    config_path: Optional[str] = typer.Option(
        None, "--config", "-c", help="Path to custom config.json",
    ),
) -> None:
    if config_path:
        cfg = load_config(Path(config_path))
    else:
        cfg = load_config()
    cfg = cfg.merge_cli(path=path, recursive=recursive)
    target = cfg.base_path.resolve()

    if not target.exists():
        console.print(f"[red]Error:[/] Directory not found: {target}")
        raise typer.Exit(1)

    logger = setup_logging(create_logs=cfg.create_logs, log_level=cfg.log_level)
    cfg.dry_run = False

    rprint(f"[bold blue]== Watch Mode ==[/]")
    rprint(f"  Watching: [yellow]{target}[/]")
    rprint(f"  Recursive: {cfg.recursive}")
    rprint(f"  [dim]Press Ctrl+C to stop...[/]\n")

    try:
        start_watching(cfg)
    except KeyboardInterrupt:
        rprint("\n[yellow]Watch stopped.[/]")
    except Exception as e:
        console.print(f"[red]Error:[/] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
