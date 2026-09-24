"""
Gestion des bulletins scolaires
- S'adapte AUTOMATIQUEMENT au pays de l'ecole (defini dans Parametres)
- Matieres saisies manuellement
- Notes par periode
- Options d'affichage configurables
"""
from database import get_connection


def init_tables():
    """Cree les tables si elles n'existent pas."""
    conn = get_connection()
    cur = conn.cursor()

    # ===== CONFIG BULLETINS (options locales ecrasant celles du pays) =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bulletins_config (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label_periode TEXT,
            nb_periodes INTEGER,
            bareme TEXT,
            note_max REAL,
            note_min REAL,
            seuil_admission REAL,
            mention_tb REAL,
            mention_b REAL,
            mention_ab REAL,
            mention_passable REAL,
            titre_bulletin TEXT,
            couleur_principale TEXT,
            couleur_accent TEXT,
            afficher_rang INTEGER DEFAULT 1,
            afficher_mention INTEGER DEFAULT 1,
            afficher_signatures INTEGER DEFAULT 1,
            afficher_appreciation INTEGER DEFAULT 1,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== MATIERES =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS matieres (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            coefficient REAL DEFAULT 1,
            niveau TEXT,
            ordre INTEGER DEFAULT 0,
            actif INTEGER DEFAULT 1,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== NOTES (periode au lieu de trimestre) =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            matiere_id INTEGER NOT NULL,
            periode INTEGER NOT NULL,
            annee_scolaire TEXT NOT NULL,
            note REAL DEFAULT 0,
            utilisateur_id INTEGER,
            date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(eleve_id, matiere_id, periode, annee_scolaire)
        )
    """)

    # ===== BULLETINS =====
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bulletins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            periode INTEGER NOT NULL,
            annee_scolaire TEXT NOT NULL,
            moyenne REAL DEFAULT 0,
            rang INTEGER,
            effectif INTEGER,
            appreciation TEXT,
            date_generation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(eleve_id, periode, annee_scolaire)
        )
    """)

    # ===== MIGRATIONS =====
    # matieres.ordre
    cur.execute("PRAGMA table_info(matieres)")
    cols_mat = [r[1] for r in cur.fetchall()]
    if "ordre" not in cols_mat:
        try:
            cur.execute("ALTER TABLE matieres ADD COLUMN ordre INTEGER DEFAULT 0")
            print("[MIGRATION] matieres : colonne 'ordre' ajoutee")
        except Exception as e:
            print(f"[MIGRATION] matieres.ordre : {e}")

    # notes.trimestre -> periode
    cur.execute("PRAGMA table_info(notes)")
    cols_notes = [r[1] for r in cur.fetchall()]
    if "periode" not in cols_notes and "trimestre" in cols_notes:
        try:
            cur.execute("ALTER TABLE notes RENAME COLUMN trimestre TO periode")
            print("[MIGRATION] notes : trimestre -> periode")
        except Exception as e:
            print(f"[MIGRATION] notes.periode : {e}")

    # bulletins.trimestre -> periode
    cur.execute("PRAGMA table_info(bulletins)")
    cols_bul = [r[1] for r in cur.fetchall()]
    if "periode" not in cols_bul and "trimestre" in cols_bul:
        try:
            cur.execute("ALTER TABLE bulletins RENAME COLUMN trimestre TO periode")
            print("[MIGRATION] bulletins : trimestre -> periode")
        except Exception as e:
            print(f"[MIGRATION] bulletins.periode : {e}")

    # Creer une ligne vide dans bulletins_config si table vide
    cur.execute("SELECT COUNT(*) as n FROM bulletins_config")
    if cur.fetchone()["n"] == 0:
        cur.execute("INSERT INTO bulletins_config (id) VALUES (1)")

    conn.commit()
    conn.close()


# ============================================================
# CONFIGURATION (fusion : pays de l'ecole + preferences locales)
# ============================================================
def get_config():
    """
    Retourne la config finale pour les bulletins.
    - Le PAYS de l'ecole (defini dans Parametres) fournit les valeurs par defaut
    - Les valeurs locales (bulletins_config) ecrasent les valeurs du pays si definies
    """
    defaults = {
        "pays": "",
        "systeme": "autre",
        "label_periode": "Periode",
        "nb_periodes": 3,
        "bareme": "sur20",
        "note_max": 20,
        "note_min": 0,
        "seuil_admission": 10,
        "mention_tb": 16,
        "mention_b": 14,
        "mention_ab": 12,
        "mention_passable": 10,
        "titre_bulletin": "BULLETIN DE NOTES",
        "couleur_principale": "#0F2C5C",
        "couleur_accent": "#27ae60",
        "afficher_rang": 1,
        "afficher_mention": 1,
        "afficher_signatures": 1,
        "afficher_appreciation": 1,
    }

    # 1. Charger le systeme du pays
    try:
        from core.ecole import get_pays_ecole
        from core.pays import get_config_pour_pays, get_systeme_pour_pays
        pays = get_pays_ecole() or ""
        sys_cfg = get_config_pour_pays(pays)
        sys_key = get_systeme_pour_pays(pays)

        defaults["pays"] = pays
        defaults["systeme"] = sys_key
        defaults["label_periode"] = sys_cfg.get("label_periode", "Periode")
        defaults["nb_periodes"] = sys_cfg.get("nb_periodes", 3)
        defaults["bareme"] = sys_cfg.get("bareme", "sur20")
        defaults["note_max"] = sys_cfg.get("note_max", 20)
        defaults["note_min"] = sys_cfg.get("note_min", 0)
        defaults["seuil_admission"] = sys_cfg.get("seuil_admission", 10)
        defaults["titre_bulletin"] = sys_cfg.get("titre_bulletin", "BULLETIN DE NOTES")
    except Exception as e:
        print(f"[BULLETINS] Erreur lecture pays : {e}")

    # 2. Ecraser avec les valeurs locales (si definies)
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM bulletins_config ORDER BY id LIMIT 1")
        row = cur.fetchone()
        conn.close()

        if row:
            local = dict(row)
            for k, v in local.items():
                if k in ("id", "date_creation"):
                    continue
                if v is not None and v != "":
                    defaults[k] = v
    except Exception as e:
        print(f"[BULLETINS] Erreur lecture config locale : {e}")

    return defaults


def set_config(**kwargs):
    """
    Met a jour la config locale (override).
    Utilise set_config(label_periode="Semestre", note_max=20, ...)
    """
    champs_valides = [
        "label_periode", "nb_periodes", "bareme", "note_max", "note_min",
        "seuil_admission", "mention_tb", "mention_b", "mention_ab",
        "mention_passable", "titre_bulletin", "couleur_principale",
        "couleur_accent", "afficher_rang", "afficher_mention",
        "afficher_signatures", "afficher_appreciation",
    ]
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM bulletins_config ORDER BY id LIMIT 1")
        row = cur.fetchone()
        if not row:
            cur.execute("INSERT INTO bulletins_config (id) VALUES (1)")
            conn.commit()
            cfg_id = 1
        else:
            cfg_id = row["id"]

        champs = []
        valeurs = []
        for k, v in kwargs.items():
            if k in champs_valides and v is not None:
                champs.append(f"{k} = ?")
                valeurs.append(v)

        if champs:
            valeurs.append(cfg_id)
            cur.execute(f"UPDATE bulletins_config SET {', '.join(champs)} WHERE id = ?",
                        valeurs)
            conn.commit()
        conn.close()
        return True, "Configuration enregistree"
    except Exception as e:
        return False, f"Erreur : {e}"


def mention_pour_note(moyenne):
    """Retourne la mention selon les seuils configures."""
    cfg = get_config()
    if moyenne >= float(cfg.get("mention_tb", 16) or 16):
        return "Tres Bien"
    if moyenne >= float(cfg.get("mention_b", 14) or 14):
        return "Bien"
    if moyenne >= float(cfg.get("mention_ab", 12) or 12):
        return "Assez Bien"
    if moyenne >= float(cfg.get("mention_passable", 10) or 10):
        return "Passable"
    return "Insuffisant"


# ============================================================
# MATIERES (saisie manuelle)
# ============================================================
def lister_matieres(niveau=None, actif=True):
    conn = get_connection()
    cur = conn.cursor()
    q = "SELECT * FROM matieres WHERE 1=1"
    params = []
    if actif:
        q += " AND actif = 1"
    if niveau:
        q += " AND (niveau = ? OR niveau IS NULL OR niveau = '')"
        params.append(niveau)
    q += " ORDER BY ordre, nom"
    cur.execute(q, params)
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows


def ajouter_matiere(nom, coefficient=1, niveau=None, ordre=0):
    nom = (nom or "").strip()
    if not nom:
        return False, "Le nom est obligatoire"
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO matieres (nom, coefficient, niveau, ordre)
            VALUES (?, ?, ?, ?)
        """, (nom, float(coefficient or 1), niveau, int(ordre or 0)))
        conn.commit()
        conn.close()
        return True, "Matiere ajoutee"
    except Exception as e:
        return False, f"Erreur : {e}"


def modifier_matiere(matiere_id, nom=None, coefficient=None, niveau=None,
                     ordre=None, actif=None):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM matieres WHERE id = ?", (matiere_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return False, "Matiere introuvable"

        n_nom = nom if nom is not None else row["nom"]
        n_coef = coefficient if coefficient is not None else row["coefficient"]
        n_niv = niveau if niveau is not None else row["niveau"]
        n_ord = ordre if ordre is not None else (row["ordre"] if "ordre" in row.keys() else 0)
        n_act = actif if actif is not None else row["actif"]

        cur.execute("""
            UPDATE matieres SET nom = ?, coefficient = ?, niveau = ?, ordre = ?, actif = ?
            WHERE id = ?
        """, (n_nom, float(n_coef or 1), n_niv, int(n_ord or 0), n_act, matiere_id))
        conn.commit()
        conn.close()
        return True, "Matiere modifiee"
    except Exception as e:
        return False, f"Erreur : {e}"


def supprimer_matiere(matiere_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("UPDATE matieres SET actif = 0 WHERE id = ?", (matiere_id,))
        conn.commit()
        conn.close()
        return True, "Matiere desactivee"
    except Exception as e:
        return False, f"Erreur : {e}"


# ============================================================
# NOTES
# ============================================================
def get_note(eleve_id, matiere_id, periode, annee):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM notes
            WHERE eleve_id = ? AND matiere_id = ?
              AND periode = ? AND annee_scolaire = ?
        """, (eleve_id, matiere_id, periode, annee))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception:
        return None


def enregistrer_note(eleve_id, matiere_id, periode, annee, note, utilisateur_id=None):
    try:
        note_val = float(note or 0)
        cfg = get_config()
        note_max = float(cfg.get("note_max", 20) or 20)
        note_min = float(cfg.get("note_min", 0) or 0)

        if note_val < note_min or note_val > note_max:
            return False, f"Note doit etre entre {note_min} et {note_max}"

        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO notes (eleve_id, matiere_id, periode, annee_scolaire, note, utilisateur_id)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(eleve_id, matiere_id, periode, annee_scolaire)
            DO UPDATE SET note = excluded.note,
                          utilisateur_id = excluded.utilisateur_id,
                          date_saisie = CURRENT_TIMESTAMP
        """, (eleve_id, matiere_id, periode, annee, note_val, utilisateur_id))
        conn.commit()
        conn.close()
        return True, "Note enregistree"
    except Exception as e:
        return False, f"Erreur : {e}"


def notes_eleve(eleve_id, periode, annee):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT matiere_id, note FROM notes
            WHERE eleve_id = ? AND periode = ? AND annee_scolaire = ?
        """, (eleve_id, periode, annee))
        rows = cur.fetchall()
        conn.close()
        return {r["matiere_id"]: r["note"] for r in rows}
    except Exception:
        return {}


def moyenne_eleve(eleve_id, periode, annee):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            SELECT n.note, m.coefficient
            FROM notes n
            JOIN matieres m ON m.id = n.matiere_id
            WHERE n.eleve_id = ? AND n.periode = ? AND n.annee_scolaire = ?
              AND m.actif = 1
        """, (eleve_id, periode, annee))
        rows = cur.fetchall()
        conn.close()
        total = 0
        coefs = 0
        for r in rows:
            total += (r["note"] or 0) * (r["coefficient"] or 1)
            coefs += (r["coefficient"] or 1)
        return round(total / coefs, 2) if coefs > 0 else 0
    except Exception:
        return 0


def rang_eleve(eleve_id, classe, periode, annee):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id FROM eleves WHERE classe = ? AND actif = 1", (classe,))
        ids = [r["id"] for r in cur.fetchall()]
        conn.close()

        moyennes = []
        for eid in ids:
            moyennes.append((eid, moyenne_eleve(eid, periode, annee)))
        moyennes.sort(key=lambda x: x[1], reverse=True)

        for i, (eid, _) in enumerate(moyennes, start=1):
            if eid == eleve_id:
                return i, len(moyennes)
        return None, len(moyennes)
    except Exception:
        return None, 0


# ============================================================
# COMPATIBILITE (ancienne fonction conservee mais inoffensive)
# ============================================================
def initialiser_matieres_par_defaut():
    """Ne fait rien : les matieres sont saisies manuellement."""
    return