# YAML Format Manual

[English](yaml.md) | [日本語](yaml-ja.md)

This document defines the YAML format used by `sync_form.py`.

## Overview

- Finds an existing form by `path` + `title`
- Updates the form when exactly one match exists, or creates a new form when no match exists
- Automatically creates folders when `path` is specified

## Top-Level Fields

```yaml
title: Form title
documentTitle: Document name on Drive (optional)
description: Form description (optional)
path: /Forms/Business Surveys (optional)
questions:
  - title: Question 1
    type: short
```

- `title`:
  - Required
  - Form title
  - Used as the search key
- `documentTitle`:
  - Optional
  - Applied only when creating a new form
  - Not changed during updates
- `description`:
  - Optional
  - Form description
- `path`:
  - Optional
  - Destination folder path on Google Drive
  - Defaults to the Drive root when omitted
- `questions`:
  - Optional (no questions when omitted)
  - Array of question objects

## Question Objects

Each question uses the following format.

```yaml
- title: Question text
  type: short | paragraph | radio | checkbox | dropdown
  required: true | false   # Optional (default: false)
  description: Help text    # Optional
  options:                  # Required for radio/checkbox/dropdown
    - Option A
    - Option B
  shuffle: true | false     # Only valid for radio/checkbox
```

### Requirements by Type

- `short`
  - Single-line text
  - Does not use `options`
- `paragraph`
  - Multi-line text
  - Does not use `options`
- `radio`
  - Radio buttons
  - Requires `options`
  - `shuffle` is optional
- `checkbox`
  - Checkboxes
  - Requires `options`
  - `shuffle` is optional
- `dropdown`
  - Dropdown
  - Requires `options`
  - `shuffle` is ignored

## Update Behavior

When an existing form is found, the script performs the following steps.

1. Updates the title and description
2. Deletes all existing questions
3. Recreates questions from YAML `questions`
4. Moves the form to the specified folder when `path` is set

## Form Matching Rules

- Search condition: matching `title` under `path`
- 0 matches: create a new form
- 1 match: update the existing form
- 2 or more matches: fail with an ambiguity error

## Common Error Cases

- Missing `title`
- Unsupported `type` (anything other than `short/paragraph/radio/checkbox/dropdown`)
- Missing `options` for `radio/checkbox/dropdown`
- Multiple forms with the same name under the same `path`

## Notes

- If multiple folders with the same name exist in a folder path, the script fails with an ambiguity error.

## Complete Example

```yaml
title: Survey
documentTitle: 2026Q2 Business Improvement Survey
description: A survey to help guide future business improvements
path: /Forms/Business Surveys

questions:
  - title: What is your age range?
    type: radio
    required: true
    options:
      - Under 20
      - 20-30
      - 31-40
      - 41-50
      - 51 or older
    shuffle: true

  - title: Which tools do you use for work? (Select all that apply)
    type: checkbox
    required: true
    options:
      - Excel
      - Google Sheets
      - Slack
      - Microsoft Teams
      - Other

  - title: Which tool do you use most often?
    type: dropdown
    options:
      - Excel
      - Google Sheets
      - Slack

  - title: Please share any additional comments
    type: paragraph
    required: false
    description: Enter free-form text
```
