import requests
import logging
from urllib.parse import quote
from django.conf import settings

logger = logging.getLogger(__name__)


def _bytes_to_mib(value):
    if value is None:
        return None
    return round(value / 1024 / 1024, 1)


class RabbitMQClient:
    def __init__(self):
        self.base_url = settings.RABBITMQ_API_URL
        self.session = requests.Session()
        
    def _get(self, path):
        try:
            response = self.session.get(f"{self.base_url}{path}", timeout=5)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"RabbitMQ API error at {path}: {e}")
            return None

    def get_overview(self):
        return self._get("/overview")
    
    def get_health(self):
        return self._get("/health/checks/ready-to-serve-clients")

    def get_queues(self):
        return self._get("/queues")

    def get_nodes(self):
        return self._get("/nodes")

    def get_node_memory(self, node_name):
        return self._get(f"/nodes/{quote(node_name, safe='')}/memory")

    def get_status(self):
        overview = self.get_overview()
        queues = self.get_queues()
        health = self.get_health()
        nodes = self.get_nodes()

        # Broker health from ready-to-serve check
        status = health.get("status", "offline") if health else "offline"

        # Summary metrics (Topology existence)
        summary = {
            "connections": 0,
            "channels": 0,
            "queues": 0,
        }

        rabbitmq_version = None
        node_data = []
        memory = None

        if overview:
            rabbitmq_version = overview.get("rabbitmq_version")
            object_totals = overview.get("object_totals", {})

            summary = {
                "connections": object_totals.get("connections", 0),
                "channels": object_totals.get("channels", 0),
                "queues": object_totals.get("queues", 0),
            }

        if nodes:
            for node in nodes:
                node_data.append({
                    "name": node.get("name"),
                    "type": node.get("type"),
                    "running": node.get("running"),
                    "being_drained": node.get("being_drained"),
                })

            first_running_node = next((node for node in nodes if node.get("running")), nodes[0])
            memory_status = self.get_node_memory(first_running_node.get("name"))
            memory_totals = (memory_status or {}).get("memory", {}).get("total", {})
            memory = {
                "node": first_running_node.get("name"),
                "strategy": (memory_status or {}).get("memory", {}).get("strategy"),
                "erlang": memory_totals.get("erlang"),
                "erlang_mib": _bytes_to_mib(memory_totals.get("erlang")),
                "rss": memory_totals.get("rss"),
                "rss_mib": _bytes_to_mib(memory_totals.get("rss")),
                "allocated": memory_totals.get("allocated"),
                "allocated_mib": _bytes_to_mib(memory_totals.get("allocated")),
            }

        # Queue topology
        queue_data = []
        if queues:
            for q in queues:
                queue_data.append({
                    "name": q.get("name"),
                    "state": q.get("state"),
                })

        # Final response
        return {
            "status": status,
            "rabbitmq_version": rabbitmq_version,
            "summary": summary,
            "nodes": node_data,
            "memory": memory,
            "queues": queue_data,
        }
