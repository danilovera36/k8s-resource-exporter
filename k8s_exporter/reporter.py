"""Report generator: YAML, JSON, and HTML output formats."""

import json
import yaml
from pathlib import Path
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, select_autoescape


class Reporter:
    def __init__(self, data: dict, fmt: str):
        self.data = data
        self.fmt = fmt

    def write(self, path: Path):
        path = Path(path)
        if self.fmt == "json":
            path.write_text(json.dumps(self.data, indent=2, default=str), encoding="utf-8")
        elif self.fmt == "yaml":
            path.write_text(yaml.dump(self.data, sort_keys=False, default_flow_style=False), encoding="utf-8")
        elif self.fmt == "html":
            self._write_html(path)

    def _write_html(self, path: Path):
        tmpl_dir = Path(__file__).parent / "templates"
        env = Environment(
            loader=FileSystemLoader(str(tmpl_dir)),
            autoescape=select_autoescape(["html"]),
        )
        tmpl = env.get_template("report.html.j2")

        # Compute summary stats
        resources = self.data["resources"]
        summary = {k: len(v) for k, v in resources.items()}
        total = sum(summary.values())

        # Health indicators for deployments
        unhealthy = []
        for dep in resources.get("deployments", []):
            if dep.get("replicas", 0) != dep.get("ready_replicas", 0):
                unhealthy.append(dep)

        html = tmpl.render(
            metadata=self.data["metadata"],
            resources=resources,
            summary=summary,
            total=total,
            unhealthy_deployments=unhealthy,
            generated_at=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        )
        path.write_text(html, encoding="utf-8")
