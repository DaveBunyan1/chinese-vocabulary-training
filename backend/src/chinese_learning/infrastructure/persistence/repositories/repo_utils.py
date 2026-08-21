import structlog
from opentelemetry import metrics

logger = structlog.get_logger(__name__)

# Obtain an OpenTelemetry Meter
meter = metrics.get_meter("chinese_learning.infrastructure.persistence")

# Define OTel Counters for repo metrics
repo_operations_counter = meter.create_counter(
    name="db.repository.operations.total",
    unit="{operation}",
    description="Total count of repository operations executed",
)


def record_repo_metric(operation: str, entity: str = "vocabulary_knowledge") -> None:
    """Helper to record operational metrics in OTel."""
    repo_operations_counter.add(1, {"operation": operation, "entity": entity})
