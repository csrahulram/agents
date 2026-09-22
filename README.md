# Local Agent Team

A local team of seven small (~1 GB) models on Ollama that builds projects in a loop:
research → plan → execute → verify → improve. It is pure Python standard library, so there's nothing to `pip install`.

## Quick start
```powershell
python run.py setup                                  # pull models (~5 GB total)
python run.py new "CLI todo app in Python with add/list/done and JSON storage"
python run.py status
python run.py resume cli-todo-app-in-python-with-add-list-done --cycles 3
python run.py recall "json storage"                  # search long-term memory
```
Output goes to `workspace/<project>/`. See [ARCHITECTURE.md](ARCHITECTURE.md) for how it works.

## Tips for small models
- Give specific goals and name the language, files and features you want.
- Small, testable goals work best. Build large apps as a series of `new`/`resume` goals on the same `--name`.
- Watch `workspace/<p>/.agents/LOG.md`, and review the lessons the loop adds to `instructions/*.md`.

## Safety
With `allow_shell = true`, the planner's verify commands run in the project folder with a timeout.
They are model-generated, so set it to `false` if you don't want commands to run.
