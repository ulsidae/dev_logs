import os,re
import secrets
import sqlite3,json
import mimetypes
import hashlib,logging
from pathlib import Path
from datetime import datetime, timezone
from contextlib import contextmanager

from flask import (
    Flask,
    request,redirect,url_for,
    render_template_string,send_file,
    jsonify,abort,
    session,
    flash,
    g
)
from werkzeug.utils import secure_filename
from werkzeug.exceptions import RequestEntityTooLarge


APP_NAME = "CRUD_TEST"

BASE_DIR = Path(__file__).resolve().parent
STORAGE_DIR = (BASE_DIR / "storage").resolve()
DB_PATH = BASE_DIR / "crud_test.db"

MAX_UPLOAD_SIZE = 25 * 1024 * 1024
MAX_TEXT_SIZE = 2 * 1024 * 1024
MAX_FILENAME_LENGTH = 120
MAX_SEARCH_LENGTH = 100

BLOCKED_NAMES = {
    ".env",
    ".git",
    ".gitignore",
    ".gitattributes",
    "id_rsa",
    "id_rsa.pub",
    "authorized_keys",
    "known_hosts"
}

TEXT_EXTENSIONS = {
    "txt", "md", "markdown", "json", "xml", "html", "htm",
    "css", "js", "mjs", "cjs", "ts", "tsx", "jsx",
    "py", "pyw", "java", "c", "h", "cpp", "hpp",
    "cs", "go", "rs", "rb", "php", "sql", "sh",
    "bat", "ps1", "yaml", "yml", "toml", "ini",
    "cfg", "conf", "csv", "log"
}


app = Flask(__name__)

app.config.update(
    SECRET_KEY=os.environ.get(
        "CRUD_TEST_SECRET",
        secrets.token_hex(32)
    ),
    MAX_CONTENT_LENGTH=MAX_UPLOAD_SIZE,
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=False
)

STORAGE_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s"
)

logger = logging.getLogger(APP_NAME)


@contextmanager
def database():
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row

    connection.execute(
        "PRAGMA foreign_keys = ON"
    )

    connection.execute(
        "PRAGMA journal_mode = WAL"
    )

    try:
        yield connection
        connection.commit()

    except Exception:
        connection.rollback()
        raise

    finally:
        connection.close()


def initialize_database():
    with database() as db:
        db.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT NOT NULL,
                action TEXT NOT NULL,
                path TEXT NOT NULL,
                details TEXT,
                ip TEXT,
                created_at TEXT NOT NULL
            )
        """)

        db.execute("""
            CREATE INDEX IF NOT EXISTS idx_audit_created
            ON audit_log(created_at DESC)
        """)


def utc_now():
    return datetime.now(
        timezone.utc
    ).isoformat(
        timespec="seconds"
    )


def request_id():
    if not hasattr(g, "request_id"):
        g.request_id = secrets.token_hex(8)

    return g.request_id


def audit(action, path, details=None):
    payload = (
        json.dumps(
            details,
            ensure_ascii=False
        )
        if details
        else None
    )

    with database() as db:
        db.execute(
            """
            INSERT INTO audit_log
            (
                request_id,
                action,
                path,
                details,
                ip,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                request_id(),
                action,
                path,
                payload,
                request.remote_addr,
                utc_now()
            )
        )

    logger.info(
        "request=%s action=%s path=%s",
        request_id(),
        action,
        path
    )


def get_csrf_token():
    token = session.get("_csrf_token")

    if not token:
        token = secrets.token_urlsafe(32)
        session["_csrf_token"] = token

    return token


def validate_csrf():
    submitted = request.form.get(
        "_csrf",
        ""
    )

    expected = session.get(
        "_csrf_token",
        ""
    )

    if not submitted:
        abort(403)

    if (
        not expected
        or not secrets.compare_digest(
            submitted,
            expected
        )
    ):
        abort(403)


def safe_storage_path(relative=""):
    relative = str(
        relative or ""
    )

    relative = relative.replace(
        "\\",
        "/"
    )

    relative = relative.lstrip("/")

    if "\x00" in relative:
        abort(400)

    candidate = (
        STORAGE_DIR / relative
    ).resolve()

    try:
        candidate.relative_to(
            STORAGE_DIR
        )

    except ValueError:
        abort(403)

    return candidate


def relative_path(path):
    resolved = Path(path).resolve()

    try:
        return resolved.relative_to(
            STORAGE_DIR
        ).as_posix()

    except ValueError:
        abort(403)


def is_blocked_name(name):
    lowered = name.lower()

    if lowered in BLOCKED_NAMES:
        return True

    if lowered.startswith(".git"):
        return True

    return False


def sanitize_name(name):
    name = secure_filename(
        name or ""
    )

    name = name.strip()

    if not name:
        abort(400)

    if len(name) > MAX_FILENAME_LENGTH:
        abort(400)

    if is_blocked_name(name):
        abort(403)

    if name in {".", ".."}:
        abort(400)

    if re.search(
        r"[\x00-\x1f\x7f]",
        name
    ):
        abort(400)

    return name


def ensure_inside_storage(path):
    try:
        path.resolve().relative_to(
            STORAGE_DIR
        )

    except ValueError:
        abort(403)

    return path


def reject_symlink(path):
    try:
        current = path

        while current != STORAGE_DIR:
            if current.is_symlink():
                abort(403)

            current = current.parent

    except OSError:
        abort(403)


def validate_target(path):
    ensure_inside_storage(path)
    reject_symlink(path)

    return path


def format_size(size):
    size = float(size)

    units = [
        "B",
        "KB",
        "MB",
        "GB",
        "TB"
    ]

    for unit in units:
        if (
            size < 1024
            or unit == units[-1]
        ):
            return f"{size:.1f} {unit}"

        size /= 1024

    return "0 B"


def directory_stats():
    files = 0
    folders = 0
    total_size = 0

    for root, directories, filenames in os.walk(
        STORAGE_DIR
    ):
        folders += len(directories)

        for filename in filenames:
            path = Path(root) / filename

            try:
                if path.is_symlink():
                    continue

                stat = path.stat()

                files += 1
                total_size += stat.st_size

            except OSError:
                continue

    return {
        "files": files,
        "folders": folders,
        "size": format_size(total_size)
    }


def is_text_file(path):
    extension = (
        path.suffix
        .lower()
        .lstrip(".")
    )

    if extension in TEXT_EXTENSIONS:
        return True

    try:
        with path.open("rb") as stream:
            sample = stream.read(4096)

        if b"\x00" in sample:
            return False

        sample.decode("utf-8")

        return True

    except (
        OSError,
        UnicodeDecodeError
    ):
        return False


def file_hash(path):
    digest = hashlib.sha256()

    try:
        with path.open("rb") as stream:
            while chunk := stream.read(
                1024 * 1024
            ):
                digest.update(chunk)

        return digest.hexdigest()

    except OSError:
        return None


def atomic_write(path, content):
    temporary = path.with_name(
        f".{path.name}.{secrets.token_hex(8)}.tmp"
    )

    try:
        with temporary.open(
            "w",
            encoding="utf-8",
            newline=""
        ) as stream:

            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())

        os.replace(
            temporary,
            path
        )

    finally:
        try:
            temporary.unlink(
                missing_ok=True
            )

        except OSError:
            pass


def unique_filename(directory, filename):
    original = Path(filename)

    stem = original.stem
    suffix = original.suffix

    candidate = directory / filename

    if not candidate.exists():
        return candidate

    for number in range(1, 10000):
        candidate = (
            directory
            / f"{stem} ({number}){suffix}"
        )

        if not candidate.exists():
            return candidate

    abort(409)


def build_breadcrumbs(relative):
    relative = relative.strip("/")

    if not relative:
        return []

    parts = relative.split("/")

    result = []
    current = []

    for part in parts:
        current.append(part)

        result.append({
            "name": part,
            "path": "/".join(current)
        })

    return result


@app.before_request
def before_request():
    request_id()

    if request.path.startswith(
        "/static/"
    ):
        return

    if request.method == "POST":
        content_type = (
            request.content_type
            or ""
        )

        if (
            "multipart/form-data"
            not in content_type
            and
            "application/x-www-form-urlencoded"
            not in content_type
        ):
            abort(415)


@app.after_request
def security_headers(response):
    response.headers[
        "X-Content-Type-Options"
    ] = "nosniff"

    response.headers[
        "X-Frame-Options"
    ] = "DENY"

    response.headers[
        "Referrer-Policy"
    ] = "no-referrer"

    response.headers[
        "Permissions-Policy"
    ] = (
        "camera=(), "
        "microphone=(), "
        "geolocation=()"
    )

    response.headers[
        "Cache-Control"
    ] = "no-store"

    return response


@app.context_processor
def inject_globals():
    return {
        "app_name": APP_NAME,
        "csrf": get_csrf_token(),
        "request_id": request_id()
    }


@app.route("/")
def index():
    relative = request.args.get(
        "path",
        ""
    ).strip()

    query = (
        request.args.get(
            "q",
            ""
        )
        .strip()
        [:MAX_SEARCH_LENGTH]
    )

    sort = request.args.get(
        "sort",
        "name"
    )

    current = validate_target(
        safe_storage_path(relative)
    )

    if (
        not current.exists()
        or not current.is_dir()
    ):
        abort(404)

    entries = []

    try:
        children = list(
            current.iterdir()
        )

    except OSError:
        abort(403)

    for child in children:
        if child.name.startswith("."):
            continue

        if is_blocked_name(
            child.name
        ):
            continue

        if (
            query
            and query.lower()
            not in child.name.lower()
        ):
            continue

        try:
            validate_target(child)
            stat = child.stat()

        except OSError:
            continue

        directory = child.is_dir()

        entries.append({
            "name": child.name,
            "path": relative_path(child),
            "directory": directory,
            "size": (
                0
                if directory
                else stat.st_size
            ),
            "size_display": (
                "—"
                if directory
                else format_size(
                    stat.st_size
                )
            ),
            "modified": datetime.fromtimestamp(
                stat.st_mtime
            ).strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
            "extension": (
                child.suffix
                .lower()
                .lstrip(".")
            ),
            "mime": (
                mimetypes.guess_type(
                    child.name
                )[0]
                or "application/octet-stream"
            )
        })

    if sort == "size":
        entries.sort(
            key=lambda item: (
                not item["directory"],
                item["size"]
            )
        )

    elif sort == "modified":
        entries.sort(
            key=lambda item: item["modified"],
            reverse=True
        )

    else:
        entries.sort(
            key=lambda item: (
                not item["directory"],
                item["name"].lower()
            )
        )

    parent = str(
        Path(relative).parent
    ).replace(
        "\\",
        "/"
    )

    if parent == ".":
        parent = ""

    return render_template_string(
        PAGE,
        view="index",
        current_path=relative,
        parent=parent,
        breadcrumbs=build_breadcrumbs(
            relative
        ),
        entries=entries,
        query=query,
        sort=sort,
        stats=directory_stats()
    )


@app.route(
    "/create/file",
    methods=["GET", "POST"]
)
def create_file():
    relative = request.args.get(
        "path",
        request.form.get(
            "path",
            ""
        )
    )

    directory = validate_target(
        safe_storage_path(relative)
    )

    if not directory.is_dir():
        abort(404)

    if request.method == "POST":
        validate_csrf()

        filename = sanitize_name(
            request.form.get(
                "filename",
                ""
            )
        )

        content = request.form.get(
            "content",
            ""
        )

        encoded = content.encode(
            "utf-8"
        )

        if len(encoded) > MAX_TEXT_SIZE:
            abort(413)

        target = ensure_inside_storage(
            directory / filename
        )

        if target.exists():
            flash(
                "An item with that name already exists.",
                "error"
            )

            return redirect(
                url_for(
                    "create_file",
                    path=relative
                )
            )

        validate_target(target)

        atomic_write(
            target,
            content
        )

        audit(
            "create_file",
            relative_path(target),
            {
                "size": len(encoded)
            }
        )

        flash(
            "File created successfully."
        )

        return redirect(
            url_for(
                "index",
                path=relative
            )
        )

    return render_template_string(
        PAGE,
        view="create_file",
        current_path=relative
    )


@app.route(
    "/create/folder",
    methods=["GET", "POST"]
)
def create_folder():
    relative = request.args.get(
        "path",
        request.form.get(
            "path",
            ""
        )
    )

    directory = validate_target(
        safe_storage_path(relative)
    )

    if not directory.is_dir():
        abort(404)

    if request.method == "POST":
        validate_csrf()

        name = sanitize_name(
            request.form.get(
                "name",
                ""
            )
        )

        target = ensure_inside_storage(
            directory / name
        )

        if target.exists():
            flash(
                "An item with that name already exists.",
                "error"
            )

            return redirect(
                url_for(
                    "create_folder",
                    path=relative
                )
            )

        validate_target(target)

        target.mkdir()

        audit(
            "create_folder",
            relative_path(target)
        )

        flash(
            "Folder created successfully."
        )

        return redirect(
            url_for(
                "index",
                path=relative
            )
        )

    return render_template_string(
        PAGE,
        view="create_folder",
        current_path=relative
    )


@app.route(
    "/edit",
    methods=["GET", "POST"]
)
def edit_file():
    relative = request.args.get(
        "path",
        request.form.get(
            "path",
            ""
        )
    )

    target = validate_target(
        safe_storage_path(relative)
    )

    if not target.is_file():
        abort(404)

    if not is_text_file(target):
        flash(
            "This file cannot be edited as text.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    if request.method == "POST":
        validate_csrf()

        content = request.form.get(
            "content",
            ""
        )

        encoded = content.encode(
            "utf-8"
        )

        if len(encoded) > MAX_TEXT_SIZE:
            abort(413)

        before = file_hash(target)

        atomic_write(
            target,
            content
        )

        after = file_hash(target)

        audit(
            "edit_file",
            relative_path(target),
            {
                "before": before,
                "after": after,
                "bytes": len(encoded)
            }
        )

        flash(
            "File saved successfully."
        )

        parent = (
            target.parent
            .relative_to(
                STORAGE_DIR
            )
            .as_posix()
        )

        if parent == ".":
            parent = ""

        return redirect(
            url_for(
                "index",
                path=parent
            )
        )

    try:
        if target.stat().st_size > MAX_TEXT_SIZE:
            abort(413)

        content = target.read_text(
            encoding="utf-8"
        )

    except UnicodeDecodeError:
        flash(
            "The file is not valid UTF-8 text.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    parent = (
        target.parent
        .relative_to(
            STORAGE_DIR
        )
        .as_posix()
    )

    if parent == ".":
        parent = ""

    return render_template_string(
        PAGE,
        view="edit",
        path=relative,
        filename=target.name,
        content=content,
        parent=parent
    )


@app.route(
    "/delete",
    methods=["POST"]
)
def delete():
    validate_csrf()

    relative = request.form.get(
        "path",
        ""
    )

    target = validate_target(
        safe_storage_path(relative)
    )

    if target == STORAGE_DIR:
        abort(403)

    if not target.exists():
        flash(
            "Item not found.",
            "error"
        )

        return redirect(
            url_for("index")
        )

    target_type = (
        "directory"
        if target.is_dir()
        else "file"
    )

    parent = (
        target.parent
        .relative_to(
            STORAGE_DIR
        )
        .as_posix()
    )

    if parent == ".":
        parent = ""

    try:
        if target.is_dir():
            children = sorted(
                target.rglob("*"),
                key=lambda item: len(
                    item.parts
                ),
                reverse=True
            )

            for child in children:
                validate_target(child)

                if (
                    child.is_file()
                    or child.is_symlink()
                ):
                    child.unlink()

                elif child.is_dir():
                    child.rmdir()

            target.rmdir()

        else:
            target.unlink()

    except OSError:
        abort(403)

    audit(
        "delete",
        relative,
        {
            "type": target_type
        }
    )

    flash(
        "Item deleted successfully."
    )

    return redirect(
        url_for(
            "index",
            path=parent
        )
    )


@app.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():
    if request.method == "POST":
        validate_csrf()

        uploaded = request.files.get(
            "file"
        )

        if (
            not uploaded
            or not uploaded.filename
        ):
            flash(
                "No file selected.",
                "error"
            )

            return redirect(
                url_for("upload")
            )

        filename = sanitize_name(
            uploaded.filename
        )

        target = unique_filename(
            STORAGE_DIR,
            filename
        )

        validate_target(target)

        try:
            uploaded.save(target)

        except OSError:
            abort(500)

        try:
            size = target.stat().st_size

        except OSError:
            abort(500)

        audit(
            "upload",
            relative_path(target),
            {
                "size": size,
                "mime": (
                    mimetypes.guess_type(
                        target.name
                    )[0]
                )
            }
        )

        flash(
            f"Uploaded as {target.name}."
        )

        return redirect(
            url_for("index")
        )

    return render_template_string(
        PAGE,
        view="upload"
    )


@app.route("/download")
def download():
    relative = request.args.get(
        "path",
        ""
    )

    target = validate_target(
        safe_storage_path(relative)
    )

    if not target.is_file():
        abort(404)

    audit(
        "download",
        relative
    )

    return send_file(
        target,
        as_attachment=True,
        download_name=target.name
    )


@app.route("/api/files")
def api_files():
    relative = request.args.get(
        "path",
        ""
    )

    directory = validate_target(
        safe_storage_path(relative)
    )

    if not directory.is_dir():
        return jsonify({
            "error": "directory_not_found",
            "request_id": request_id()
        }), 404

    result = []

    try:
        children = list(
            directory.iterdir()
        )

    except OSError:
        abort(403)

    for child in children:
        if child.name.startswith("."):
            continue

        if is_blocked_name(
            child.name
        ):
            continue

        try:
            validate_target(child)
            stat = child.stat()

        except OSError:
            continue

        is_directory = child.is_dir()

        result.append({
            "name": child.name,
            "path": relative_path(child),
            "type": (
                "directory"
                if is_directory
                else "file"
            ),
            "size": (
                None
                if is_directory
                else stat.st_size
            ),
            "mime": (
                None
                if is_directory
                else (
                    mimetypes.guess_type(
                        child.name
                    )[0]
                    or "application/octet-stream"
                )
            ),
            "modified": datetime.fromtimestamp(
                stat.st_mtime,
                timezone.utc
            ).isoformat()
        })

    result.sort(
        key=lambda item: (
            item["type"] != "directory",
            item["name"].lower()
        )
    )

    return jsonify({
        "application": APP_NAME,
        "path": relative,
        "count": len(result),
        "items": result,
        "request_id": request_id()
    })


@app.route("/api/audit")
def api_audit():
    limit = request.args.get(
        "limit",
        50,
        type=int
    )

    limit = max(
        1,
        min(
            limit,
            200
        )
    )

    with database() as db:
        rows = db.execute(
            """
            SELECT
                id,
                request_id,
                action,
                path,
                details,
                ip,
                created_at
            FROM audit_log
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,)
        ).fetchall()

    return jsonify({
        "count": len(rows),
        "items": [
            dict(row)
            for row in rows
        ],
        "request_id": request_id()
    })


@app.errorhandler(
    RequestEntityTooLarge
)
def request_too_large(error):
    return render_template_string(
        ERROR_PAGE,
        code=413,
        message="Payload too large."
    ), 413


@app.errorhandler(400)
def bad_request(error):
    return render_template_string(
        ERROR_PAGE,
        code=400,
        message="Bad request."
    ), 400


@app.errorhandler(403)
def forbidden(error):
    return render_template_string(
        ERROR_PAGE,
        code=403,
        message="Access denied."
    ), 403


@app.errorhandler(404)
def not_found(error):
    return render_template_string(
        ERROR_PAGE,
        code=404,
        message="Resource not found."
    ), 404


@app.errorhandler(405)
def method_not_allowed(error):
    return render_template_string(
        ERROR_PAGE,
        code=405,
        message="Method not allowed."
    ), 405


@app.errorhandler(409)
def conflict(error):
    return render_template_string(
        ERROR_PAGE,
        code=409,
        message="Resource conflict."
    ), 409


@app.errorhandler(413)
def payload_too_large(error):
    return render_template_string(
        ERROR_PAGE,
        code=413,
        message="Payload too large."
    ), 413


@app.errorhandler(415)
def unsupported_media(error):
    return render_template_string(
        ERROR_PAGE,
        code=415,
        message="Unsupported media type."
    ), 415


@app.errorhandler(500)
def server_error(error):
    logger.exception(
        "request=%s internal_error",
        request_id()
    )

    return render_template_string(
        ERROR_PAGE,
        code=500,
        message="Internal server error."
    ), 500


PAGE = """
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>
<meta
    name="theme-color"
    content="#0b0f14"
>
<title>{{ app_name }}</title>

<style>
:root{
--bg:#0b0f14;
--panel:#121821;
--panel2:#171f2a;
--border:#26303d;
--text:#e8edf3;
--muted:#7f8998;
--primary:#687cff;
--green:#2c9a75;
--red:#d05268;
--yellow:#a57b2e;
}

*{
box-sizing:border-box
}

body{
margin:0;
background:var(--bg);
color:var(--text);
font-family:
Inter,
ui-sans-serif,
system-ui,
-apple-system,
BlinkMacSystemFont,
"Segoe UI",
sans-serif;
}

a{
color:inherit;
text-decoration:none
}

button,
input,
textarea,
select{
font:inherit
}

.shell{
width:min(1200px,94%);
margin:32px auto
}

.topbar{
display:flex;
align-items:center;
justify-content:space-between;
gap:20px;
margin-bottom:22px
}

.brand{
display:flex;
gap:12px;
align-items:center
}

.mark{
width:44px;
height:44px;
display:grid;
place-items:center;
border-radius:13px;
background:
linear-gradient(
135deg,
#687cff,
#4d5ed4
);
font-weight:900
}

h1{
margin:0;
font-size:27px
}

.subtitle{
color:var(--muted);
font-size:13px;
margin-top:4px
}

.card{
background:var(--panel);
border:1px solid var(--border);
border-radius:16px;
padding:20px;
margin-bottom:17px
}

.stats{
display:grid;
grid-template-columns:
repeat(3,1fr);
gap:12px;
margin-bottom:17px
}

.stat{
background:var(--panel);
border:1px solid var(--border);
border-radius:14px;
padding:17px
}

.stat-label{
font-size:11px;
letter-spacing:.08em;
color:var(--muted)
}

.stat-value{
font-size:25px;
font-weight:800;
margin-top:6px
}

.toolbar{
display:flex;
align-items:center;
gap:8px;
flex-wrap:wrap
}

input,
textarea,
select{
width:100%;
background:#0c1118;
border:1px solid #303a48;
border-radius:9px;
padding:11px 12px;
color:var(--text)
}

input:focus,
textarea:focus,
select:focus{
outline:none;
border-color:var(--primary);
box-shadow:
0 0 0 3px
#687cff18
}

.search{
flex:1;
min-width:230px
}

button,
.btn{
border:0;
border-radius:9px;
padding:10px 14px;
background:var(--primary);
color:#fff;
cursor:pointer;
display:inline-flex;
align-items:center;
justify-content:center;
font-size:13px
}

button:hover,
.btn:hover{
filter:brightness(1.1)
}

.secondary{
background:#293340
}

.success{
background:var(--green)
}

.danger{
background:var(--red)
}

.warning{
background:var(--yellow)
}

.breadcrumb{
display:flex;
align-items:center;
flex-wrap:wrap;
gap:8px;
color:var(--muted);
font-size:14px
}

.breadcrumb a{
color:#94a3ff
}

table{
width:100%;
border-collapse:collapse
}

th{
padding:11px 8px;
border-bottom:1px solid var(--border);
text-align:left;
font-size:11px;
color:var(--muted);
letter-spacing:.06em
}

td{
padding:13px 8px;
border-bottom:1px solid #202935;
font-size:14px;
vertical-align:middle
}

tr:last-child td{
border-bottom:0
}

.icon{
font-size:20px
}

.name{
font-weight:650
}

.subtext{
font-size:11px;
color:var(--muted);
margin-top:3px
}

.actions{
display:flex;
gap:6px;
flex-wrap:wrap
}

.empty{
padding:60px 15px;
text-align:center;
color:var(--muted)
}

.field{
margin-bottom:17px
}

label{
display:block;
font-size:12px;
color:#aab4c1;
margin-bottom:7px
}

textarea{
min-height:430px;
resize:vertical;
font-family:
"JetBrains Mono",
Consolas,
monospace;
line-height:1.55
}

.flash{
padding:12px 14px;
border-radius:10px;
background:#193d31;
border:1px solid #296650;
color:#83e0bd;
margin-bottom:17px;
font-size:13px
}

.flash.error{
background:#411f28;
border-color:#703744;
color:#ff9eac
}

.drop{
border:1px dashed #3a4655;
border-radius:13px;
padding:35px;
text-align:center;
color:var(--muted)
}

.drop input{
margin-top:15px
}

.form-actions{
display:flex;
gap:8px
}

.code{
background:#0c1118;
border:1px solid var(--border);
border-radius:10px;
padding:15px;
overflow:auto;
font-family:Consolas,monospace
}

@media(max-width:720px){

.shell{
width:94%;
margin:20px auto
}

.topbar{
align-items:flex-start
}

.stats{
grid-template-columns:1fr
}

table{
display:block;
overflow-x:auto;
white-space:nowrap
}

.actions{
flex-wrap:nowrap
}

}
</style>
</head>

<body>

<div class="shell">

<header class="topbar">

<div class="brand">

<div class="mark">
C
</div>

<div>

<h1>
{{ app_name }}
</h1>

<div class="subtitle">
Single-file Flask File Management System
</div>

</div>

</div>

<a
    class="btn"
    href="{{ url_for('upload') }}"
>
Upload
</a>

</header>


{% with messages =
get_flashed_messages(
with_categories=true
)
%}

{% for category, message in messages %}

<div
    class="flash
    {{ 'error'
    if category == 'error'
    else '' }}"
>
{{ message }}
</div>

{% endfor %}

{% endwith %}


{% if view == "index" %}

<div class="stats">

<div class="stat">
<div class="stat-label">
FILES
</div>

<div class="stat-value">
{{ stats.files }}
</div>
</div>


<div class="stat">
<div class="stat-label">
FOLDERS
</div>

<div class="stat-value">
{{ stats.folders }}
</div>
</div>


<div class="stat">
<div class="stat-label">
STORAGE
</div>

<div class="stat-value">
{{ stats.size }}
</div>
</div>

</div>


<div class="card">

<div class="breadcrumb">

<a href="{{ url_for('index') }}">
Root
</a>

{% for crumb in breadcrumbs %}

<span>/</span>

<a
    href="{{ url_for(
        'index',
        path=crumb.path
    ) }}"
>
{{ crumb.name }}
</a>

{% endfor %}

</div>

</div>


<div class="card">

<form
    method="get"
    class="toolbar"
>

<input
    type="hidden"
    name="path"
    value="{{ current_path }}"
>

<input
    class="search"
    name="q"
    value="{{ query }}"
    maxlength="100"
    placeholder="Search files and folders"
>

<select
    name="sort"
    style="width:auto"
>

<option
    value="name"
    {% if sort == "name" %}
    selected
    {% endif %}
>
Name
</option>

<option
    value="size"
    {% if sort == "size" %}
    selected
    {% endif %}
>
Size
</option>

<option
    value="modified"
    {% if sort == "modified" %}
    selected
    {% endif %}
>
Modified
</option>

</select>

<button>
Search
</button>

<a
    class="btn secondary"
    href="{{ url_for(
        'index',
        path=current_path
    ) }}"
>
Clear
</a>

</form>

</div>


<div class="card">

<div
    class="toolbar"
    style="margin-bottom:17px"
>

<a
    class="btn success"
    href="{{ url_for(
        'create_folder',
        path=current_path
    ) }}"
>
+ Folder
</a>

<a
    class="btn secondary"
    href="{{ url_for(
        'create_file',
        path=current_path
    ) }}"
>
+ File
</a>

</div>


{% if entries %}

<table>

<thead>

<tr>

<th>
Type
</th>

<th>
Name
</th>

<th>
Size
</th>

<th>
Modified
</th>

<th>
Actions
</th>

</tr>

</thead>


<tbody>

{% for item in entries %}

<tr>

<td class="icon">
{{ "📁"
if item.directory
else "📄" }}
</td>


<td>

{% if item.directory %}

<a
    class="name"
    href="{{ url_for(
        'index',
        path=item.path
    ) }}"
>
{{ item.name }}
</a>

{% else %}

<div class="name">
{{ item.name }}
</div>

{% endif %}


<div class="subtext">

{{
"Folder"
if item.directory
else item.mime
}}

</div>

</td>


<td>
{{ item.size_display }}
</td>


<td>
{{ item.modified }}
</td>


<td>

<div class="actions">

{% if item.directory %}

<a
    class="btn secondary"
    href="{{ url_for(
        'index',
        path=item.path
    ) }}"
>
Open
</a>

{% else %}

{% if item.extension in [
"txt",
"md",
"json",
"html",
"css",
"js",
"py",
"java",
"c",
"cpp",
"h",
"hpp",
"go",
"rs",
"php",
"sql",
"yaml",
"yml",
"xml",
"csv",
"log"
] %}

<a
    class="btn secondary"
    href="{{ url_for(
        'edit_file',
        path=item.path
    ) }}"
>
Edit
</a>

{% endif %}


<a
    class="btn"
    href="{{ url_for(
        'download',
        path=item.path
    ) }}"
>
Download
</a>

{% endif %}


<form
    method="post"
    action="{{ url_for('delete') }}"
    onsubmit="
        return confirm(
            'Delete this item permanently?'
        )
    "
>

<input
    type="hidden"
    name="_csrf"
    value="{{ csrf }}"
>

<input
    type="hidden"
    name="path"
    value="{{ item.path }}"
>

<button class="danger">
Delete
</button>

</form>

</div>

</td>

</tr>

{% endfor %}

</tbody>

</table>

{% else %}

<div class="empty">
No files or folders found.
</div>

{% endif %}

</div>


{% elif view == "create_file" %}

<div class="card">

<div class="breadcrumb">

<a
    href="{{ url_for(
        'index',
        path=current_path
    ) }}"
>
← Back
</a>

</div>

</div>


<div class="card">

<form method="post">

<input
    type="hidden"
    name="_csrf"
    value="{{ csrf }}"
>

<input
    type="hidden"
    name="path"
    value="{{ current_path }}"
>


<div class="field">

<label>
FILE NAME
</label>

<input
    name="filename"
    maxlength="120"
    placeholder="example.txt"
    required
>

</div>


<div class="field">

<label>
CONTENT
</label>

<textarea
    name="content"
    placeholder="Enter file content..."
></textarea>

</div>


<div class="form-actions">

<button>
Create File
</button>

<a
    class="btn secondary"
    href="{{ url_for(
        'index',
        path=current_path
    ) }}"
>
Cancel
</a>

</div>

</form>

</div>


{% elif view == "create_folder" %}

<div class="card">

<div class="breadcrumb">

<a
    href="{{ url_for(
        'index',
        path=current_path
    ) }}"
>
← Back
</a>

</div>

</div>


<div class="card">

<form method="post">

<input
    type="hidden"
    name="_csrf"
    value="{{ csrf }}"
>

<input
    type="hidden"
    name="path"
    value="{{ current_path }}"
>


<div class="field">

<label>
FOLDER NAME
</label>

<input
    name="name"
    maxlength="120"
    placeholder="New Folder"
    required
>

</div>


<div class="form-actions">

<button class="success">
Create Folder
</button>

<a
    class="btn secondary"
    href="{{ url_for(
        'index',
        path=current_path
    ) }}"
>
Cancel
</a>

</div>

</form>

</div>


{% elif view == "edit" %}

<div class="card">

<div class="breadcrumb">

<a
    href="{{ url_for(
        'index',
        path=parent
    ) }}"
>
← Back
</a>

<span>
/
</span>

<span>
{{ filename }}
</span>

</div>

</div>


<div class="card">

<form method="post">

<input
    type="hidden"
    name="_csrf"
    value="{{ csrf }}"
>

<input
    type="hidden"
    name="path"
    value="{{ path }}"
>


<div class="field">

<label>
FILE
</label>

<input
    value="{{ filename }}"
    disabled
>

</div>


<div class="field">

<label>
CONTENT
</label>

<textarea
    name="content"
    maxlength="2097152"
>{{ content }}</textarea>

</div>


<div class="form-actions">

<button>
Save Changes
</button>

<a
    class="btn secondary"
    href="{{ url_for(
        'index',
        path=parent
    ) }}"
>
Cancel
</a>

</div>

</form>

</div>


{% elif view == "upload" %}

<div class="card">

<form
    method="post"
    enctype="multipart/form-data"
>

<input
    type="hidden"
    name="_csrf"
    value="{{ csrf }}"
>


<div class="drop">

<div style="font-size:36px">
📤
</div>

<div style="margin-top:8px">
Select a file to upload
</div>

<div
    style="
        font-size:11px;
        margin-top:5px
    "
>
Maximum size: 25 MB
</div>

<input
    type="file"
    name="file"
    required
>

</div>


<div
    class="form-actions"
    style="margin-top:17px"
>

<button>
Upload File
</button>

<a
    class="btn secondary"
    href="{{ url_for('index') }}"
>
Cancel
</a>

</div>

</form>

</div>

{% endif %}


<div
    style="
        text-align:center;
        color:#4f5967;
        font-size:10px;
        margin:25px 0
    "
>
{{ app_name }}
· Request
{{ request_id }}
</div>

</div>

</body>
</html>
"""


ERROR_PAGE = """
<!doctype html>

<html lang="en">

<head>

<meta charset="utf-8">

<meta
    name="viewport"
    content="width=device-width,initial-scale=1"
>

<title>
{{ code }} · CRUD_TEST
</title>

<style>

body{
margin:0;
min-height:100vh;
display:grid;
place-items:center;
background:#0b0f14;
color:#e8edf3;
font-family:Arial,sans-serif
}

main{
text-align:center
}

h1{
font-size:80px;
margin:0
}

p{
color:#7f8998
}

a{
color:#8795ff;
text-decoration:none
}

</style>

</head>

<body>

<main>

<h1>
{{ code }}
</h1>

<p>
{{ message }}
</p>

<a href="/">
Return to CRUD_TEST
</a>

</main>

</body>

</html>
"""


if __name__ == "__main__":
    initialize_database()

    app.run(
        host="127.0.0.1",
        port=int(
            os.environ.get(
                "PORT",
                5000
            )
        ),
        debug=False
    )
