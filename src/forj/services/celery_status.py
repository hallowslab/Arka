from .rabbitmq import RabbitMQClient


def get_celery_status():
    client = RabbitMQClient()
    rmq_status = client.get_status()

    # default safety (if API fails)
    if not rmq_status:
        return {
            "status": "offline",
            "rabbitmq_version": None,
            "summary": {
                "connections": 0,
                "channels": 0,
                "queues": 0,
            },
            "nodes": [],
            "memory": None,
            "queues": [],
        }

    return {
        "status": rmq_status.get("status", "offline"),
        "rabbitmq_version": rmq_status.get("rabbitmq_version"),
        "summary": rmq_status.get(
            "summary",
            {
                "connections": 0,
                "channels": 0,
                "queues": 0,
            },
        ),
        "nodes": rmq_status.get("nodes", []),
        "memory": rmq_status.get("memory"),
        "queues": rmq_status.get("queues", []),
    }
