"""Kubernetes resource collector."""

from datetime import datetime, timezone
from typing import Optional
import click


RESOURCE_MAP = {
    "deployments": ("apps", "v1", "Deployment"),
    "daemonsets": ("apps", "v1", "DaemonSet"),
    "statefulsets": ("apps", "v1", "StatefulSet"),
    "services": ("", "v1", "Service"),
    "configmaps": ("", "v1", "ConfigMap"),
    "secrets": ("", "v1", "Secret"),
    "pods": ("", "v1", "Pod"),
    "pvcs": ("", "v1", "PersistentVolumeClaim"),
    "ingresses": ("networking.k8s.io", "v1", "Ingress"),
    "hpas": ("autoscaling", "v2", "HorizontalPodAutoscaler"),
}


class ResourceCollector:
    def __init__(
        self,
        kubeconfig: Optional[str] = None,
        context: Optional[str] = None,
        namespace: Optional[str] = None,
        resources: str = "all",
        redact_secrets: bool = False,
        verbose: bool = False,
    ):
        self.namespace = namespace
        self.redact_secrets = redact_secrets
        self.verbose = verbose
        self.resources = self._parse_resources(resources)

        from kubernetes import client, config as kube_config

        if kubeconfig or context:
            kube_config.load_kube_config(config_file=kubeconfig, context=context)
        else:
            try:
                kube_config.load_incluster_config()
            except Exception:
                kube_config.load_kube_config(config_file=kubeconfig)

        self._core = client.CoreV1Api()
        self._apps = client.AppsV1Api()
        self._networking = client.NetworkingV1Api()
        self._autoscaling = client.AutoscalingV2Api()
        self._dynamic = client.CustomObjectsApi()

        version_info = client.VersionApi().get_code()
        self._server_version = f"{version_info.major}.{version_info.minor}"

    def _parse_resources(self, resources_str: str):
        if resources_str.lower() == "all":
            return list(RESOURCE_MAP.keys())
        return [r.strip().lower() for r in resources_str.split(",") if r.strip().lower() in RESOURCE_MAP]

    def _log(self, msg: str):
        if self.verbose:
            click.echo(f"   {msg}")

    def collect(self) -> dict:
        ns = self.namespace
        data = {
            "metadata": {
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "namespace": ns or "all",
                "server_version": self._server_version,
            },
            "resources": {},
        }

        collectors = {
            "deployments": self._get_deployments,
            "daemonsets": self._get_daemonsets,
            "statefulsets": self._get_statefulsets,
            "services": self._get_services,
            "configmaps": self._get_configmaps,
            "secrets": self._get_secrets,
            "pods": self._get_pods,
            "pvcs": self._get_pvcs,
            "ingresses": self._get_ingresses,
            "hpas": self._get_hpas,
        }

        for resource in self.resources:
            if resource in collectors:
                self._log(f"Collecting {resource}...")
                try:
                    items = collectors[resource](ns)
                    data["resources"][resource] = items
                    self._log(f"  → {len(items)} {resource} found")
                except Exception as e:
                    self._log(f"  ⚠ Skipping {resource}: {e}")
                    data["resources"][resource] = []

        return data

    def _get_deployments(self, ns):
        if ns:
            items = self._apps.list_namespaced_deployment(ns).items
        else:
            items = self._apps.list_deployment_for_all_namespaces().items
        return [self._serialize_deployment(i) for i in items]

    def _serialize_deployment(self, d):
        spec = d.spec
        status = d.status
        return {
            "name": d.metadata.name,
            "namespace": d.metadata.namespace,
            "replicas": spec.replicas or 0,
            "ready_replicas": status.ready_replicas or 0,
            "image": self._get_images(spec.template.spec.containers),
            "labels": d.metadata.labels or {},
            "created_at": d.metadata.creation_timestamp.isoformat() if d.metadata.creation_timestamp else None,
            "strategy": spec.strategy.type if spec.strategy else None,
        }

    def _get_daemonsets(self, ns):
        if ns:
            items = self._apps.list_namespaced_daemon_set(ns).items
        else:
            items = self._apps.list_daemon_set_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "desired": i.status.desired_number_scheduled or 0,
                "ready": i.status.number_ready or 0,
                "image": self._get_images(i.spec.template.spec.containers),
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    def _get_statefulsets(self, ns):
        if ns:
            items = self._apps.list_namespaced_stateful_set(ns).items
        else:
            items = self._apps.list_stateful_set_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "replicas": i.spec.replicas or 0,
                "ready_replicas": i.status.ready_replicas or 0,
                "image": self._get_images(i.spec.template.spec.containers),
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    def _get_services(self, ns):
        if ns:
            items = self._core.list_namespaced_service(ns).items
        else:
            items = self._core.list_service_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "type": i.spec.type,
                "cluster_ip": i.spec.cluster_ip,
                "external_ip": (i.spec.external_i_ps or [None])[0] if i.spec.external_i_ps else None,
                "ports": [{"port": p.port, "protocol": p.protocol, "target_port": str(p.target_port)} for p in (i.spec.ports or [])],
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    def _get_configmaps(self, ns):
        if ns:
            items = self._core.list_namespaced_config_map(ns).items
        else:
            items = self._core.list_config_map_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "keys": list((i.data or {}).keys()),
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    def _get_secrets(self, ns):
        if ns:
            items = self._core.list_namespaced_secret(ns).items
        else:
            items = self._core.list_secret_for_all_namespaces().items
        result = []
        for i in items:
            keys = list((i.data or {}).keys())
            entry = {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "type": i.type,
                "keys": keys,
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            if not self.redact_secrets:
                entry["note"] = "Use --exclude-secrets to hide values"
            result.append(entry)
        return result

    def _get_pods(self, ns):
        if ns:
            items = self._core.list_namespaced_pod(ns).items
        else:
            items = self._core.list_pod_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "phase": i.status.phase,
                "node": i.spec.node_name,
                "image": self._get_images(i.spec.containers),
                "restarts": sum(
                    (cs.restart_count or 0)
                    for cs in (i.status.container_statuses or [])
                ),
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    def _get_pvcs(self, ns):
        if ns:
            items = self._core.list_namespaced_persistent_volume_claim(ns).items
        else:
            items = self._core.list_persistent_volume_claim_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "status": i.status.phase,
                "storage_class": i.spec.storage_class_name,
                "capacity": i.status.capacity.get("storage") if i.status.capacity else None,
                "access_modes": i.spec.access_modes or [],
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    def _get_ingresses(self, ns):
        if ns:
            items = self._networking.list_namespaced_ingress(ns).items
        else:
            items = self._networking.list_ingress_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "rules": [
                    {
                        "host": r.host,
                        "paths": [p.path for p in (r.http.paths if r.http else [])],
                    }
                    for r in (i.spec.rules or [])
                ],
                "tls": [t.hosts for t in (i.spec.tls or [])],
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    def _get_hpas(self, ns):
        if ns:
            items = self._autoscaling.list_namespaced_horizontal_pod_autoscaler(ns).items
        else:
            items = self._autoscaling.list_horizontal_pod_autoscaler_for_all_namespaces().items
        return [
            {
                "name": i.metadata.name,
                "namespace": i.metadata.namespace,
                "target": i.spec.scale_target_ref.name,
                "min_replicas": i.spec.min_replicas,
                "max_replicas": i.spec.max_replicas,
                "current_replicas": i.status.current_replicas,
                "created_at": i.metadata.creation_timestamp.isoformat() if i.metadata.creation_timestamp else None,
            }
            for i in items
        ]

    @staticmethod
    def _get_images(containers) -> list:
        if not containers:
            return []
        return [c.image for c in containers if c.image]
