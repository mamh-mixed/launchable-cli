from enum import Enum


class Command(Enum):
    VERIFY = 'VERIFY'
    RECORD_TESTS = 'RECORD_TESTS'
    RECORD_BUILD = 'RECORD_BUILD'
    RECORD_SESSION = 'RECORD_SESSION'
    SUBSET = 'SUBSET'
    COMMIT = 'COMMIT'
    DETECT_FLAKE = 'DETECT_FLAKE'
    GATE = 'GATE'
    UPDATE_ALIAS = 'UPDATE_ALIAS'
    RECORD_DEPLOYMENT = 'RECORD_DEPLOYMENT'
    UNKNOWN = 'UNKNOWN'

    # when you add a new constant here, the server also needs to get a new constant in cli_tracking.proto

    def display_name(self):
        return self.value.lower().replace('_', ' ')
