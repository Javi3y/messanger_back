from src.base.domain.jobs import JobSpec
from src.messaging.workers.generate_messages_from_requests_csv import (
    generate_messages_from_requests_csv,
)

JOBS = {
    "generate_messages_from_requests_csv": JobSpec(
        job=generate_messages_from_requests_csv,
        interval=5.0,
        batch=5,
    ),
}
