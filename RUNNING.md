# Running the Packaged Build

This guide covers building and running the packaged application (Windows,
macOS, and Linux) produced by the GitHub Actions workflow
(`.github/workflows/build.yml`) or by the local build scripts in `scripts/`.

## Building

### Via GitHub Actions (manual)

Go to **Actions → Build application → Run workflow** and pick the machine from
the dropdown. It uploads an artifact per target:

| Target          | Runner               | Artifact              | Binary name         |
|-----------------|----------------------|-----------------------|---------------------|
| `windows`       | `windows-latest`     | `bulk_emailer-windows` | `bulk_emailer.exe` |
| `macos-arm64`   | `macos-latest`       | `bulk_emailer-macos-arm64` | `bulk_emailer` |
| `macos-intel`   | `macos-13`           | `bulk_emailer-macos-intel` | `bulk_emailer` |
| `linux`         | `ubuntu-latest`      | `bulk_emailer-linux`  | `bulk_emailer`      |

The workflow runs only on manual dispatch — it does not trigger on push.

### Locally

Run the script for your OS from the repo root (each creates `src/.venv`,
installs `requirements-build.txt`, and produces `src/dist/`):

```bash
./scripts/build-macos.sh    # macOS (native architecture)
./scripts/build-linux.sh    # Linux
scripts\build-windows.bat   # Windows
```

> PyInstaller cannot cross-compile: a macOS build only works for the Mac
> architecture it was built on (Apple Silicon vs Intel). Use the matching CI
> target if you need the other architecture or another OS.

## 1. What the executable does on launch

On startup the executable automatically:

1. Applies any pending database migrations (`migrate`).
2. Collects static assets (`collectstatic`).
3. Starts the Django development server.

It then listens on **`http://127.0.0.1:8000`** by default. Because this is a
one-file PyInstaller build, the first launch extracts the bundled files to a
temporary directory, so startup is noticeably slower the first time.

## 2. How to run it

Open a terminal, change into the folder that contains the binary, and run it:

```powershell
# Windows
.\bulk_emailer.exe
```

```bash
# macOS / Linux
./bulk_emailer
```

> macOS: if you downloaded the binary from a browser, macOS quarantines it.
> Remove the flag first (or right-click → Open):
> ```bash
> xattr -dr com.apple.quarantine bulk_emailer
> ```

Leave the terminal open while the app is running. Open a browser and go to:

```
http://127.0.0.1:8000
```

To stop the server, press `Ctrl+C` in the terminal.

> Tip: running from a terminal is recommended so you can see logs and stop the
> process cleanly.

### Overriding host and port

The app binds to `127.0.0.1:8000` by default. To change it, set environment
variables before launching:

```powershell
# Windows
$env:BULK_EMAILER_HOST = "0.0.0.0"
$env:BULK_EMAILER_PORT = "9000"
.\bulk_emailer.exe
```

```bash
# macOS / Linux
BULK_EMAILER_HOST=0.0.0.0 BULK_EMAILER_PORT=9000 ./bulk_emailer
```

Use `0.0.0.0` only if you need other machines on your network to reach it
(and keep in mind this is the development server, not a production server).

## 3. Configuration (`.env`)

Create a file named `.env` **in the same folder as the binary**. The app reads
it via `python-decouple` on startup. A minimal `.env` looks like:

```ini
SECRET_KEY=change-me-to-a-long-random-string
DEBUG=True
DJANGO_SETTINGS_MODULE=config.settings.dev
```

### All supported variables

| Variable                | Default                 | Purpose |
|-------------------------|-------------------------|---------|
| `SECRET_KEY`            | `django-insecure-ddd1`  | Django secret key. Set a strong value in production. |
| `DEBUG`                 | `True`                  | Toggles Django debug mode (`True`/`False`). |
| `DJANGO_SETTINGS_MODULE`| `config.settings.dev`   | Which settings module to load. Leave as-is. |
| `BLOCK_EMAIL`           | `False`                 | If `True`, outgoing email sending is disabled. |
| `DEBUG_EMAIL`           | `False`                 | If `True`, enables email debugging output. |
| `TWILIO_SID`            | `test`                  | Twilio Account SID (for SMS sending). |
| `TWILIO_TOKEN`          | `test`                  | Twilio Auth Token (for SMS sending). |

> Note: email delivery settings (SendGrid / ZeptoMail / SMTP host, username,
> password, sender, etc.) are **not** configured via `.env`. They are entered
> through the web interface when you set up a mail manager in the app.

## 4. First-time setup

### Create an admin/superuser (optional)

The database is created fresh next to the binary (`db.sqlite3`) on first run.
To create a superuser for the Django admin, run:

```powershell
# Windows
.\bulk_emailer.exe createsuperuser
```

```bash
# macOS / Linux
./bulk_emailer createsuperuser
```

Follow the prompts, then log in at `http://127.0.0.1:8000/admin/`.

### Other management commands

Any Django management command can be run by passing it as an argument, for
example:

```powershell
# Windows
.\bulk_emailer.exe migrate
.\bulk_emailer.exe collectstatic
.\bulk_emailer.exe shell
```

```bash
# macOS / Linux
./bulk_emailer migrate
./bulk_emailer collectstatic
./bulk_emailer shell
```

## 5. Files created next to the binary

The app keeps writable data outside the read-only bundle:

| Path              | Purpose |
|-------------------|---------|
| `db.sqlite3`      | SQLite database. |
| `logs/`           | Application log files (`debug.log`, `error.log`). |
| `media/`          | Uploaded/processed files. |
| `static/`         | Collected static assets. |
| `.env`            | Your configuration (created by you). |

Do not delete these while the app is running.

## 6. Troubleshooting

- **Windows Defender / SmartScreen prompt** — the `.exe` is unsigned. Click
  "More info" → "Run anyway" if prompted.
- **macOS Gatekeeper** — an unsigned binary downloaded from a browser is
  quarantined. Run `xattr -dr com.apple.quarantine bulk_emailer` (or
  right-click → Open).
- **Windows Firewall prompt** — you only need to allow it if you bound the
  server to `0.0.0.0` and want other devices to connect.
- **Port already in use** — something else is on the chosen port. Stop it or
  set `BULK_EMAILER_PORT` to a free port.
- **Nothing happens / slow start** — first launch of a one-file build takes a
  while to extract; wait a few seconds and watch the console.
- **`.env` not being read** — make sure it is in the same directory as the
  binary, not a parent or subfolder.
- **"Bad CPU type" / architecture mismatch** — a build only runs on the
  architecture it was built for. Use the matching macOS target
  (arm64 vs intel) for your machine.
