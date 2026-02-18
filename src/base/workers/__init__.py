from src.base.domain.jobs import JobSpec
from src.base.workers.dispatch_outbox_events import dispatch_outbox_events

JOBS = {
    "dispatch_outbox_events": JobSpec(
        job=dispatch_outbox_events,
        interval=2.0,
        batch=50,
    ),
}
