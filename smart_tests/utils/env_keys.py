import os

REPORT_ERROR_KEY = "SMART_TESTS_REPORT_ERROR"
TOKEN_KEY = "SMART_TESTS_TOKEN"
ORGANIZATION_KEY = "SMART_TESTS_ORGANIZATION"
WORKSPACE_KEY = "SMART_TESTS_WORKSPACE"
BASE_URL_KEY = "SMART_TESTS_BASE_URL"
SKIP_TIMEOUT_RETRY = "SMART_TESTS_SKIP_TIMEOUT_RETRY"
COMMIT_TIMEOUT = "SMART_TESTS_COMMIT_TIMEOUT"
SKIP_CERT_VERIFICATION = "SMART_TESTS_SKIP_CERT_VERIFICATION"
SESSION_DIR_KEY = "SMART_TESTS_SESSION_DIR"
CALLER_KEY = "SMART_TESTS_CALLER"

# Legacy token key for backward compatibility
LEGACY_TOKEN_KEY = "LAUNCHABLE_TOKEN"


def get_token():
    """Get token with backward compatibility for LAUNCHABLE_TOKEN."""
    return os.getenv(TOKEN_KEY) or os.getenv(LEGACY_TOKEN_KEY)


def detect_ci_provider() -> str:
    if os.environ.get("GITHUB_ACTIONS"):
        return "github-actions"
    if os.environ.get("JENKINS_URL"):
        return "jenkins"
    if os.environ.get("CIRCLECI"):
        return "circleci"
    if os.environ.get("CODEBUILD_BUILD_ID"):
        return "codebuild"
    return ""
