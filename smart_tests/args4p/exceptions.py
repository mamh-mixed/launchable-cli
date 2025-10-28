class BadCmdLineException(Exception):
    '''
    Indicates that arguments given by the user are invalid.

    The message gets printed, and the CLI exists with non-zero.
    '''


class BadConfigException(Exception):
    '''
    Indicates that the option/command/argument declarations are invalid
    '''
