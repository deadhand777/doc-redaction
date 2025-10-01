# Getting started

Here's how to set up `doc-redaction` for local development.
Please note this documentation assumes you already have `uv` and `Git` installed and ready to go.

1. Clone the repository:

```bash
git clone https://github.com/deadhand777/doc-redaction.git
```

2. Now install the environment. Navigate into the directory

```bash
cd doc-redaction
```

Then, install and activate the environment with:

```bash
uv sync
```

3. Install pre-commit to run linters/formatters at commit time:

```bash
uv run pre-commit install
```

Congratulations, now your setup is completed!

4. Run the workflow with on a sample PDF document:

```bash
uv run src/doc_redaction/workflow.py --key spielbank_rocketbase_vertrag
```
