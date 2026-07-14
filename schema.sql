CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_number TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL CHECK (category IN ('Diamant', 'Pierre précieuse')),
    stone_type TEXT NOT NULL,
    variety TEXT,
    natural_or_lab TEXT,
    shape TEXT,
    weight_ct REAL,
    dimensions_mm TEXT,
    color_grade TEXT,
    clarity_grade TEXT,
    cut_grade TEXT,
    polish TEXT,
    symmetry TEXT,
    fluorescence TEXT,
    origin TEXT,
    treatment TEXT,
    issue_date TEXT,
    comments TEXT,
    image_filename TEXT,
    pdf_filename TEXT,
    status TEXT NOT NULL DEFAULT 'Actif' CHECK (status IN ('Actif', 'Suspendu', 'Archivé')),
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_reports_report_number ON reports(report_number);
CREATE INDEX IF NOT EXISTS idx_reports_category ON reports(category);
