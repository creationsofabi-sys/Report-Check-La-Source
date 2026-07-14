from __future__ import annotations

import os
import secrets
import sqlite3
from datetime import date
from functools import wraps
from pathlib import Path
from typing import Any

from flask import (
    Flask,
    abort,
    flash,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.utils import secure_filename

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "reports.db"
UPLOAD_DIR = BASE_DIR / "static" / "uploads"
ALLOWED_IMAGE_EXTENSIONS = {"png", "jpg", "jpeg", "webp"}
ALLOWED_PDF_EXTENSIONS = {"pdf"}

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.getenv("LS_SECRET_KEY", secrets.token_hex(32)),
    MAX_CONTENT_LENGTH=12 * 1024 * 1024,
    UPLOAD_FOLDER=str(UPLOAD_DIR),
)


def get_db() -> sqlite3.Connection:
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    return db


def init_db() -> None:
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    with get_db() as db:
        db.executescript((BASE_DIR / "schema.sql").read_text(encoding="utf-8"))
        count = db.execute("SELECT COUNT(*) AS total FROM reports").fetchone()["total"]
        if count == 0:
            db.executemany(
                """
                INSERT INTO reports (
                    report_number, category, stone_type, variety, natural_or_lab,
                    shape, weight_ct, dimensions_mm, color_grade, clarity_grade,
                    cut_grade, polish, symmetry, fluorescence, origin, treatment,
                    issue_date, comments, status
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                [
                    (
                        "LS-DIA-2026-0001", "Diamant", "Diamant", "Brillant", "Naturel",
                        "Rond brillant", 1.02, "6.48 × 6.52 × 3.95 mm", "G", "VS1",
                        "Excellent", "Excellent", "Excellent", "Faible", "—", "Aucun traitement détecté",
                        "2026-07-13", "Inscription laser du numéro de rapport sur le rondiste.", "Actif"
                    ),
                    (
                        "LS-GEM-2026-0001", "Pierre précieuse", "Saphir", "Saphir bleu", "Synthétique",
                        "Ovale", 2.35, "8.10 × 6.05 × 4.10 mm", "Bleu royal", "Œil propre",
                        "Très bon", "Excellent", "Très bon", "—", "Laboratoire", "Croissance synthétique déclarée",
                        "2026-07-13", "Pierre enregistrée dans la base interne La Source.", "Actif"
                    ),
                ],
            )


def normalize_report_number(value: str) -> str:
    return "".join(value.strip().upper().split())


def allowed_file(filename: str, allowed: set[str]) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed


def save_upload(field_name: str, allowed: set[str], prefix: str) -> str | None:
    file = request.files.get(field_name)
    if not file or not file.filename:
        return None
    if not allowed_file(file.filename, allowed):
        raise ValueError(f"Format de fichier non autorisé pour {field_name}.")
    extension = file.filename.rsplit(".", 1)[1].lower()
    filename = secure_filename(f"{prefix}-{secrets.token_hex(6)}.{extension}")
    file.save(UPLOAD_DIR / filename)
    return filename


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("admin_authenticated"):
            return redirect(url_for("admin_login", next=request.path))
        return view(*args, **kwargs)

    return wrapped


@app.context_processor
def inject_globals() -> dict[str, Any]:
    return {"current_year": date.today().year}


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/check")
def check_report():
    report_number = normalize_report_number(request.form.get("report_number", ""))
    if not report_number:
        flash("Veuillez saisir un numéro de rapport.", "error")
        return redirect(url_for("index"))
    return redirect(url_for("report_detail", report_number=report_number))


@app.get("/report/<report_number>")
def report_detail(report_number: str):
    normalized = normalize_report_number(report_number)
    with get_db() as db:
        report = db.execute(
            "SELECT * FROM reports WHERE report_number = ?", (normalized,)
        ).fetchone()
    if report is None:
        return render_template("not_found.html", report_number=normalized), 404
    return render_template("report.html", report=report)


@app.get("/uploads/<path:filename>")
def uploaded_file(filename: str):
    return send_from_directory(UPLOAD_DIR, filename)


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        expected_user = os.getenv("LS_ADMIN_USER", "admin")
        expected_password = os.getenv("LS_ADMIN_PASSWORD", "2002")
        if secrets.compare_digest(username, expected_user) and secrets.compare_digest(password, expected_password):
            session["admin_authenticated"] = True
            flash("Connexion administrateur réussie.", "success")
            return redirect(request.args.get("next") or url_for("admin_dashboard"))
        flash("Identifiants incorrects.", "error")
    return render_template("admin_login.html")


@app.get("/admin/logout")
def admin_logout():
    session.clear()
    flash("Vous êtes déconnecté.", "success")
    return redirect(url_for("index"))


@app.get("/admin")
@admin_required
def admin_dashboard():
    query = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql = "SELECT * FROM reports WHERE 1=1"
    params: list[Any] = []
    if query:
        sql += " AND (report_number LIKE ? OR stone_type LIKE ? OR variety LIKE ?)"
        token = f"%{query}%"
        params.extend([token, token, token])
    if category in {"Diamant", "Pierre précieuse"}:
        sql += " AND category = ?"
        params.append(category)
    sql += " ORDER BY created_at DESC"
    with get_db() as db:
        reports = db.execute(sql, params).fetchall()
    return render_template("admin_dashboard.html", reports=reports, query=query, category=category)


def form_payload() -> dict[str, Any]:
    number = normalize_report_number(request.form.get("report_number", ""))
    category = request.form.get("category", "")
    stone_type = request.form.get("stone_type", "").strip()
    if not number or category not in {"Diamant", "Pierre précieuse"} or not stone_type:
        raise ValueError("Numéro, catégorie et type de pierre sont obligatoires.")

    weight_raw = request.form.get("weight_ct", "").strip().replace(",", ".")
    weight = float(weight_raw) if weight_raw else None

    fields = [
        "variety", "natural_or_lab", "shape", "dimensions_mm", "color_grade",
        "clarity_grade", "cut_grade", "polish", "symmetry", "fluorescence",
        "origin", "treatment", "issue_date", "comments", "status",
    ]
    payload: dict[str, Any] = {
        "report_number": number,
        "category": category,
        "stone_type": stone_type,
        "weight_ct": weight,
    }
    for field in fields:
        payload[field] = request.form.get(field, "").strip()
    if payload["status"] not in {"Actif", "Suspendu", "Archivé"}:
        payload["status"] = "Actif"
    return payload


@app.route("/admin/reports/new", methods=["GET", "POST"])
@admin_required
def admin_report_new():
    if request.method == "POST":
        try:
            payload = form_payload()
            image_filename = save_upload("image", ALLOWED_IMAGE_EXTENSIONS, payload["report_number"])
            pdf_filename = save_upload("pdf", ALLOWED_PDF_EXTENSIONS, payload["report_number"])
            with get_db() as db:
                db.execute(
                    """
                    INSERT INTO reports (
                        report_number, category, stone_type, variety, natural_or_lab,
                        shape, weight_ct, dimensions_mm, color_grade, clarity_grade,
                        cut_grade, polish, symmetry, fluorescence, origin, treatment,
                        issue_date, comments, image_filename, pdf_filename, status
                    ) VALUES (
                        :report_number, :category, :stone_type, :variety, :natural_or_lab,
                        :shape, :weight_ct, :dimensions_mm, :color_grade, :clarity_grade,
                        :cut_grade, :polish, :symmetry, :fluorescence, :origin, :treatment,
                        :issue_date, :comments, :image_filename, :pdf_filename, :status
                    )
                    """,
                    {**payload, "image_filename": image_filename, "pdf_filename": pdf_filename},
                )
            flash("Rapport créé avec succès.", "success")
            return redirect(url_for("admin_dashboard"))
        except sqlite3.IntegrityError:
            flash("Ce numéro de rapport existe déjà.", "error")
        except (ValueError, TypeError) as exc:
            flash(str(exc), "error")
    return render_template("admin_form.html", report=None)


@app.route("/admin/reports/<int:report_id>/edit", methods=["GET", "POST"])
@admin_required
def admin_report_edit(report_id: int):
    with get_db() as db:
        report = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
    if report is None:
        abort(404)

    if request.method == "POST":
        try:
            payload = form_payload()
            image_filename = save_upload("image", ALLOWED_IMAGE_EXTENSIONS, payload["report_number"])
            pdf_filename = save_upload("pdf", ALLOWED_PDF_EXTENSIONS, payload["report_number"])
            current_image = report["image_filename"]
            current_pdf = report["pdf_filename"]
            with get_db() as db:
                db.execute(
                    """
                    UPDATE reports SET
                        report_number = :report_number,
                        category = :category,
                        stone_type = :stone_type,
                        variety = :variety,
                        natural_or_lab = :natural_or_lab,
                        shape = :shape,
                        weight_ct = :weight_ct,
                        dimensions_mm = :dimensions_mm,
                        color_grade = :color_grade,
                        clarity_grade = :clarity_grade,
                        cut_grade = :cut_grade,
                        polish = :polish,
                        symmetry = :symmetry,
                        fluorescence = :fluorescence,
                        origin = :origin,
                        treatment = :treatment,
                        issue_date = :issue_date,
                        comments = :comments,
                        status = :status,
                        image_filename = :image_filename,
                        pdf_filename = :pdf_filename,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = :id
                    """,
                    {
                        **payload,
                        "id": report_id,
                        "image_filename": image_filename or current_image,
                        "pdf_filename": pdf_filename or current_pdf,
                    },
                )
            flash("Rapport mis à jour.", "success")
            return redirect(url_for("admin_dashboard"))
        except sqlite3.IntegrityError:
            flash("Ce numéro de rapport appartient déjà à un autre rapport.", "error")
        except (ValueError, TypeError) as exc:
            flash(str(exc), "error")

    return render_template("admin_form.html", report=report)


@app.post("/admin/reports/<int:report_id>/delete")
@admin_required
def admin_report_delete(report_id: int):
    with get_db() as db:
        report = db.execute("SELECT * FROM reports WHERE id = ?", (report_id,)).fetchone()
        if report is None:
            abort(404)
        db.execute("DELETE FROM reports WHERE id = ?", (report_id,))
    flash("Rapport supprimé.", "success")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(413)
def file_too_large(_error):
    flash("Le fichier dépasse la limite de 12 Mo.", "error")
    return redirect(request.referrer or url_for("index"))


init_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)
