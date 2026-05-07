from enum import Enum


class Command(Enum):
    VERIFY = 'VERIFY'
    RECORD_TESTS = 'RECORD_TESTS'
    RECORD_BUILD = 'RECORD_BUILD'
    RECORD_SESSION = 'RECORD_SESSION'
    RECORD_ATTACHMENT = 'RECORD_ATTACHMENT'
    RECORD_DEPLOYMENT = 'RECORD_DEPLOYMENT'
    SUBSET = 'SUBSET'
    COMMIT = 'COMMIT'
    DETECT_FLAKE = 'DETECT_FLAKE'
    GATE = 'GATE'
    UPDATE_ALIAS = 'UPDATE_ALIAS'
    INSPECT_MODEL = 'INSPECT_MODEL'
    INSPECT_SUBSET = 'INSPECT_SUBSET'
    STATS_TEST_SESSIONS = 'STATS_TEST_SESSIONS'
    COMPARE_SUBSETS = 'COMPARE_SUBSETS'
    GET_DOCS = 'GET_DOCS'
    UNKNOWN = 'UNKNOWN'

    # when you add a new constant here, the server also needs to get a new constant in cli_tracking.proto

    def display_name(self):
        return self.value.lower().replace('_', ' ')
