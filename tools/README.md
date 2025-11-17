# Documentation Generation Tools

## generate_reference.py

This script automatically generates AsciiDoc tables for CLI command options and arguments from the args4p command definitions.
This is meant to be used with https://github.com/cloudbees/docsite-cloudbees-smart-tests/blob/main/docs/modules/resources/pages/cli-reference.adoc

### Usage

```bash
uv run python tools/generate_reference.py path/to/reference.adoc
```

### How It Works

The script looks for special markers in the AsciiDoc file:

```asciidoc
// [generate:COMMAND_PATH]
... content to be replaced ...
// [/generate]
```

Where `COMMAND_PATH` is a space-separated command path like:
- `inspect subset`
- `record build`
- `subset`

The script will:
1. Parse the AsciiDoc file to find all `[generate:...]` markers
2. Resolve each command path to the actual Command object
3. Generate an AsciiDoc table from the command's options and arguments
4. Replace the content between the markers with the generated table

### Marking Sections for Generation

To mark a section for automatic generation, wrap it with markers:

```asciidoc
=== inspect subset

Display details of a subset request.

`smart-tests inspect subset --subset-id 26876`

// [generate:inspect subset]
[cols="1,2,1"]
|===
|Option |Description |Required

|`--subset-id` INT
|subset id
|Yes

|`--json`
|display JSON format
|No

|===
// [/generate]

Additional documentation...
```

### Benefits

- **Single Source of Truth**: Option/argument definitions live in code
- **Always Up-to-Date**: Regenerate docs whenever code changes
- **Human Control**: Manually written documentation is preserved
- **Easy Maintenance**: Just run the script to update all marked sections
