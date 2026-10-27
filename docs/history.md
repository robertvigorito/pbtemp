# Prompt history

`pbtemp` remembers the answers from the most recently completed `init` or `merge` command. On the
next run, remembered values prefill the interactive prompts and feature checklist so that common
choices do not need to be entered repeatedly.

The history is a small JSON file in the operating system's user configuration directory. Its exact
location depends on the platform; `platformdirs` chooses the standard per-user application config
location. It is separate from the project being generated, so it can be reused across projects.
History contains prompt options such as project name, version, backend, line length, and selected
tools. It does not store project source files or credentials.

## How choices are selected

For `init`, values are combined in this order, from lowest to highest priority:

1. Built-in defaults (for example, MkDocs is on by default).
2. Saved history.
3. Explicit terminal options for this invocation.
4. The answers entered at the prompts.

For example, if saved history has `use_nuke=true`, this invocation preselects Nuke:

```sh
pbtemp init
```

This option overrides the saved value and defaults Nuke off for this run:

```sh
pbtemp init --no-use-nuke
```

The command still prompts you; the flag sets the initial checkbox value. Any final answer you choose
is what is saved after successful generation.

For `merge`, remembered choices fill in defaults that cannot be detected from the target project.
Values inferred from its `pyproject.toml` and existing files take precedence over history. Explicit
answers in the prompt then determine the current merge and become the latest saved choices.

## Inspect saved options

Both `dump` and `show` display the current saved options as JSON:

```sh
pbtemp history dump
pbtemp history show
```

Example output:

```json
{
  "build_backend": "uv_build",
  "line_length": 120,
  "project_name": "widget-tools",
  "use_mkdocs": true,
  "use_nuke": false,
  "use_pytest": true
}
```

If no history exists yet, the command reports that there are no saved prompt options. The output
contains only stored option values, not the internal file's schema metadata.

## Edit saved options

Run `edit` to reopen the interactive prompts with the current saved values selected:

```sh
pbtemp history edit
```

Review the text values and feature checklist, change what you want, and complete the prompts. The
new answers replace the old history. Cancelling the prompts leaves the stored history unchanged.

## Ignore history once

Use `--ignore-history` (or its alias `--no-history`) with either interactive command to avoid
loading saved choices for one run:

```sh
pbtemp init --ignore-history
pbtemp merge --output-dir ./existing-project --ignore-history
```

This does not delete history. It simply starts from built-in defaults (`init`) or detected project
settings (`merge`). After the prompts complete successfully, the new answers are saved as usual.

## Save behavior and errors

History is updated only after scaffold generation or merge succeeds. If writing the history file
fails, `pbtemp` prints a warning and keeps the successful project operation intact. If a saved file
is malformed or unreadable, `init` and `merge` warn and continue without the invalid remembered
values; a later successful run can replace it with valid history. `history dump` and `history show`
report errors rather than presenting malformed data as valid options.

`build-temp` is deliberately independent of history: it always uses the same fixed sample options
and does not change your saved answers.
