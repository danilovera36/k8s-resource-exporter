# k8s-resource-exporter

CLI to export cluster resources into YAML, JSON, or standalone HTML reports.

[![CI](https://github.com/danilovera36/k8s-resource-exporter/actions/workflows/ci.yml/badge.svg)](https://github.com/danilovera36/k8s-resource-exporter)
[![Python 3.9+](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

![HTML Report Preview](https://raw.githubusercontent.com/danilovera36/k8s-resource-exporter/main/examples/preview.png)

---

## Features

- 📦 Exports **10 resource types**: Deployments, DaemonSets, StatefulSets, Services, ConfigMaps, Secrets, Pods, Ingresses, HPAs, PVCs
- 📊 **Interactive HTML report** — shareable without kubectl access
- 🔒 Secret key redaction (`--exclude-secrets`)
- 🌐 Multi-namespace or single-namespace export
- ⚡ Works with any cluster via `kubeconfig` or in-cluster config (for CI/CD)
- 📁 Outputs YAML, JSON, or standalone HTML

---

## Usage

```bash
# Install
pip install k8s-resource-exporter

# Export all resources as HTML (default)
k8s-exporter export

# Export a specific namespace as JSON
k8s-exporter export -n production -f json -o prod-report.json

# Export with secret values redacted
k8s-exporter export --exclude-secrets

# List available Kubernetes contexts
k8s-exporter list-contexts
```

---

## 📦 Installation

**From PyPI:**
```bash
pip install k8s-resource-exporter
```

**From source:**
```bash
git clone https://github.com/your-username/k8s-resource-exporter.git
cd k8s-resource-exporter
pip install -e .
```

---

## 🔧 Usage

```
Usage: k8s-exporter export [OPTIONS]

Options:
  -n, --namespace TEXT            Target namespace. Omit for all namespaces.
  -f, --format [yaml|json|html]   Output format. [default: html]
  -o, --output TEXT               Output file path.
  --kubeconfig TEXT               Path to kubeconfig. [env: KUBECONFIG]
  --context TEXT                  Kubernetes context to use.
  -r, --resources TEXT            Comma-separated resources to export.
                                  Options: deployments, services, configmaps,
                                  secrets, ingresses, hpas, daemonsets,
                                  statefulsets, pods, pvcs, or 'all'.
  --exclude-secrets               Redact Secret values.
  -v, --verbose                   Show detailed progress.
```

### Examples

```bash
# Export only deployments and services
k8s-exporter export -r deployments,services -f yaml

# Use a specific context
k8s-exporter export --context staging-cluster -f html -o staging-report.html

# Run inside a CI pipeline (reads in-cluster config automatically)
k8s-exporter export -f json -o cluster-state.json
```

---

## 📄 HTML Report

The HTML report is a **self-contained, single-file** dark-mode dashboard that includes:

- 🟢 Deployment health overview (ready replicas vs desired)
- ⚠️ Alerts for unhealthy workloads
- Summary counters per resource type
- Searchable/sortable tables for every resource

No server required — open it in any browser.

---

## 🔐 Secret Handling

By default, the exporter lists **Secret names and key names only** (values are never exported in plain text). Use `--exclude-secrets` to also hide key names if you're sharing reports externally.

---

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/my-feature`)
3. Commit your changes (`git commit -m 'feat: add my feature'`)
4. Push to the branch (`git push origin feature/my-feature`)
5. Open a Pull Request

---

## 📝 License

MIT © [Danilo Vera](https://github.com/danilovera36)
