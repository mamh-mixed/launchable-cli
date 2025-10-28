# User guide

## Option/argument annotations

To control how args4p passes option/argument values to your function, you can either use the `@args4p.option` or `@args4p.argument` decorators, or use the `Option` and `Argument` in parameter annotations.

    @args4p.option('-v', 'verbose', ...)
    @args4p.command
    def foo(verbose: bool, ...):
        ...

    import smart_tests.args4p.typer as typer
    
    @args4p.command
    def foo(verbose: Annotated[bool, typer.Option('-v', ...)

The only difference between those two variants is that the former requires the parameter name be passed as string, while the latter takes that from the actual parameter declaration.

These invocations take the following parameters:

**\*param_decls: List[str]**: The first portion of the invocation is a var-arg of strings, and they designate the names of options. When used as a decorator, this list must be followed by the parameter name itself.

If just the parameter name is given but no option names are given, the option name is generated from the parameter name.

    # this creates the --verbose option
    @args4p.option("verbose")
    def f (verbose: bool):
        ...

    # same
    def f (verbose: Annotated[bool, args4p.Option()]):
        ...

Arguments would take the parameter name if used as a decorator, or nothing if used as annotation.

**help**: Human readable description of the option, used to render the help message

**type**: Specify the type of the option/argument. The type is individual, meaning even if you allow the option/argument to be specified multiple times, the type of option/argument is always that of a single value (e.g., `int`, not `List[int]`)

You can also specify any `Callable` that takes a `str` and produces a value of your desired type. This is handy for defining custom types.

If this parameter is omitted, the type is inferred from the type annotation of the function parameter, with the following massaging:

- if the type is optional, such as `str|None` or `Optional[str]`, the type is inferred as the non-None type (e.g., `str` in this case)

**default**: Default value if the option/argument is not provided. bool options are treated as having `False` as the default.

**required**: Whether the option/argument is required. Default is `False`.

**metavar**: User-friendly name for the option value place holder, used in help messages.

**multiple**: Whether the option/argument can be specified multiple times. Default is `False`. If true, the parameter type must be a list type (e.g. `List[str]`)

**hidden**: If true, this option is hidden from help messages.

## Group (sub-commands)
This library encourages organizing a complex CLI through sub-commands,
ala `git`, like this:

```
@args4p.group
@args4p.option('-v', 'verbose', ...)
def cli(verbose: bool):
    return {'verbose': verbose}

@cli.command   # NOT args4p.command
@args4p.argument('name')
def subcmd1(parent, name):
    if parent.verbose:
        print(f"Hello {name}")
```

Sub-commands receive the result of the parent command as its first argument. This allows you to pass options to the parent command and access them in the sub-command.

A particularly useful idiom is to create a group out of a class initializer, like this:

```
class App:
    def __init__(self, verbose: Annotated[bool,Option('-v')]):
        self.verbose = verbose

cli=Group(App)

@cli.command   # NOT args4p.command
@args4p.argument('name')
def subcmd1(app: App, name):
    if app.verbose:
        print(f"Hello {name}")
```

(Note that decorators won't work with this idiom, so you have to use annotations.)


Alternatively, use `Group.add_command` to add a top-level command as a sub-command to a group.

```
@args4p.command
def subcmd2(...):
    ...

cli.add_command(subcmd2)
```
