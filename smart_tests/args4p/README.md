# User guide

## Option/argument annotations

To control how args4p passes option/argument values to your function, you can either use the `@args4p.option` or `@args4p.argument` decorators, or use the `Option` and `Argument` classes in type annotations.

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
