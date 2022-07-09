# Simple Checklist tool

Simple Checklist tool that forces you to confirm execution of step before going to the next 
one.

## Format

```md
# Name of Workflow
;; Comment
;; Second one

1. First task
Task description goes in here.
2. Next task
3. ! Required task
4. ? Optional task

```

## Usage

```sh
python checklist.py checklist_file.txt
python checklist.py --reset checklist_file.txt
```
