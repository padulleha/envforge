# envforge

> Snapshot and restore environment variable sets across projects and machines.

---

## Installation

```bash
pip install envforge
```

Or with pipx for isolated installs:

```bash
pipx install envforge
```

---

## Usage

**Save the current environment as a named snapshot:**

```bash
envforge save myproject
```

**List saved snapshots:**

```bash
envforge list
```

**Restore a snapshot into your current shell:**

```bash
eval "$(envforge load myproject)"
```

**Delete a snapshot:**

```bash
envforge delete myproject
```

Snapshots are stored locally in `~/.envforge/` as encrypted JSON files. You can also export and import snapshots to share them across machines:

```bash
envforge export myproject > myproject.env.json
envforge import myproject.env.json
```

---

## Why envforge?

Switching between projects often means juggling different API keys, database URLs, and config flags. `envforge` lets you capture your entire environment in one command and restore it just as quickly — no more sourcing `.env` files by hand or losing track of which variables belong where.

---

## License

This project is licensed under the [MIT License](LICENSE).

---

*Contributions and issues welcome. Open a PR or file a bug on [GitHub](https://github.com/yourname/envforge).*