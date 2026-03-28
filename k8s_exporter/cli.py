# k8s-resource-exporter CLI

import click
import sys
from pathlib import Path
from datetime import datetime

from .collector import ResourceCollector
from .reporter import Reporter


@click.group()
@click.version_option(version="1.0.0")
def cli():
    """k8s-resource-exporter — Export Kubernetes cluster resources to structured reports.

    Supports YAML, JSON, and interactive HTML output formats.
    Works with any cluster accessible via your kubeconfig.
    """
    pass


@cli.command()
@click.option(
    "--namespace", "-n",
    default=None,
    help="Target namespace. Omit to export all namespaces.",
)
@click.option(
    "--format", "-f",
    "output_format",
    type=click.Choice(["yaml", "json", "html"], case_sensitive=False),
    default="html",
    show_default=True,
    help="Output format.",
)
@click.option(
    "--output", "-o",
    default=None,
    help="Output file path. Defaults to cluster-report-<timestamp>.<ext>",
)
@click.option(
    "--kubeconfig",
    default=None,
    envvar="KUBECONFIG",
    help="Path to kubeconfig file. Defaults to ~/.kube/config.",
)
@click.option(
    "--context",
    default=None,
    help="Kubernetes context to use.",
)
@click.option(
    "--resources", "-r",
    default="all",
    help=(
        "Comma-separated list of resources to export. "
        "Options: deployments,services,configmaps,secrets,ingresses,hpas,daemonsets,statefulsets,pods,pvcs. "
        "Use 'all' for everything."
    ),
)
@click.option(
    "--exclude-secrets",
    is_flag=True,
    default=False,
    help="Redact Secret values (keys are shown, values replaced with ****).",
)
@click.option(
    "--verbose", "-v",
    is_flag=True,
    default=False,
    help="Show detailed progress.",
)
def export(namespace, output_format, output, kubeconfig, context, resources, exclude_secrets, verbose):
    """Export cluster resources to a report file."""

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    ext_map = {"yaml": "yaml", "json": "json", "html": "html"}

    if output is None:
        output = f"cluster-report-{timestamp}.{ext_map[output_format.lower()]}"

    output_path = Path(output)

    click.echo(click.style("🔍  k8s-resource-exporter", fg="cyan", bold=True))
    click.echo(f"   Connecting to cluster...")

    try:
        collector = ResourceCollector(
            kubeconfig=kubeconfig,
            context=context,
            namespace=namespace,
            resources=resources,
            redact_secrets=exclude_secrets,
            verbose=verbose,
        )
        data = collector.collect()
    except Exception as e:
        click.echo(click.style(f"✗  Failed to connect: {e}", fg="red"), err=True)
        sys.exit(1)

    click.echo(f"   Generating {output_format.upper()} report → {output_path}")

    reporter = Reporter(data=data, fmt=output_format.lower())
    reporter.write(output_path)

    total = sum(len(v) for v in data["resources"].values())
    click.echo(click.style(f"✓  Done! Exported {total} resources to {output_path}", fg="green"))


@cli.command()
@click.option(
    "--kubeconfig",
    default=None,
    envvar="KUBECONFIG",
    help="Path to kubeconfig file.",
)
def list_contexts(kubeconfig):
    """List available Kubernetes contexts."""
    try:
        from kubernetes import config as kube_config
        contexts, active = kube_config.list_kube_config_contexts(config_file=kubeconfig)
        click.echo(click.style("Available contexts:", bold=True))
        for ctx in contexts:
            name = ctx["name"]
            marker = click.style(" ◀ active", fg="green") if ctx["name"] == active["name"] else ""
            click.echo(f"  • {name}{marker}")
    except Exception as e:
        click.echo(click.style(f"✗  {e}", fg="red"), err=True)
        sys.exit(1)


def main():
    cli()


if __name__ == "__main__":
    main()
