"""Utils to help handle credentials for various third-party services.

If you there are credentials that needs to be written to a file or set to a different environment variable, this is the place to do it.

If a credentials object/json needs to be constructed from values in env vars or other sources, this is the place to do it.

"""
import os
from typing import Optional

from opentelemetry import trace

tracer = trace.get_tracer(__name__)


def load_gcp_credentials(save_path: Optional[str] = None) -> bool:
    """Returns a GCP credentials object.

    Args:
        save_path (str): Path inc filename to save the credentials JSON to. Default `./.streamlit/gcp_credentials.json`
    """
    span = trace.get_current_span()

    success = False
    credentials_json = "<env var DOCQ_GCP_KEYS_JSON not set>"
    try:
        credentials_json = os.environ["DOCQ_GCP_KEYS_JSON"]
    except KeyError as e:
        success = False
        span.add_event("Failed to access env var DOCQ_GCP_KEYS_JSON", attributes={"error": str(e)})
        span.record_exception(e)

    path = save_path or "./.streamlit/gcp_credentials.json"

    try:
        with open(path, "w") as f:
            f.write(credentials_json)
            success = True
            span.add_event("Wrote GCP credentials to file successfully", attributes={"file_path": path})
    except IOError as e:
        success = False
        span.add_event("Failed to write GCP credentials to file", attributes={"error": str(e), "file_path": path})
        span.record_exception(e)

    # note: this will only be available to the current process thread. coroutine code will not have access.
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = path

    return success

def setup_all_service_credentials() -> None:
    """Setup all service credentials."""
    with tracer.start_as_current_span("docq.services.credential_utils.setup_all_service_credentials") as span:
        load_gcp_credentials()
        span.add_event("GCP credentials loaded")