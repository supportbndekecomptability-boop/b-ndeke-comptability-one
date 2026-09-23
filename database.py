"""
Gestion de la base de donnees SQLite de B-NDEKE Comptability One
"""
import sqlite3
from config import DB_PATH


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_database():
    conn = get_connection()
    cursor = conn.cursor()

    # ===== ECOLE =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS ecole (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL,
            adresse TEXT,
            telephone TEXT,
            email TEXT,
            logo TEXT,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== UTILISATEURS =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS utilisateurs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom_complet TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            mot_de_passe TEXT NOT NULL,
            role TEXT NOT NULL DEFAULT 'comptable',
            actif INTEGER DEFAULT 1,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== ELEVES =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            matricule TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            classe TEXT NOT NULL,
            sexe TEXT,
            date_naissance DATE,
            nom_parent TEXT,
            telephone_parent TEXT,
            frais_scolarite REAL DEFAULT 0,
            actif INTEGER DEFAULT 1,
            date_inscription TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== PERSONNEL =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            nom TEXT NOT NULL,
            prenom TEXT NOT NULL,
            fonction TEXT NOT NULL,
            sexe TEXT,
            telephone TEXT,
            email TEXT,
            salaire_mensuel REAL DEFAULT 0,
            duree_contrat_mois INTEGER DEFAULT 12,
            date_embauche DATE,
            actif INTEGER DEFAULT 1,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== PAIEMENTS ELEVES =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paiements_eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_recu TEXT UNIQUE NOT NULL,
            eleve_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            motif TEXT NOT NULL,
            mode_paiement TEXT NOT NULL,
            date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (eleve_id) REFERENCES eleves(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ===== PAIEMENTS PERSONNEL =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paiements_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_paie TEXT UNIQUE NOT NULL,
            personnel_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            motif TEXT NOT NULL,
            mode_paiement TEXT NOT NULL,
            montant_avance_deduit REAL DEFAULT 0,
            date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ===== DEPENSES =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS depenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            libelle TEXT NOT NULL,
            montant REAL NOT NULL,
            categorie TEXT NOT NULL,
            date_depense TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ===== PARAMETRES =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS parametres (
            cle TEXT PRIMARY KEY,
            valeur TEXT,
            date_modification TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== AVANCES SUR SALAIRE =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS avances_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            numero_avance TEXT UNIQUE NOT NULL,
            personnel_id INTEGER NOT NULL,
            montant REAL NOT NULL,
            montant_deduit REAL DEFAULT 0,
            motif TEXT,
            date_avance TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ===== MIGRATIONS =====

    # Migration : eleves -> frais_scolarite
    cursor.execute("PRAGMA table_info(eleves)")
    colonnes_eleves = [r[1] for r in cursor.fetchall()]
    if "frais_scolarite" not in colonnes_eleves:
        cursor.execute("ALTER TABLE eleves ADD COLUMN frais_scolarite REAL DEFAULT 0")
        print("[MIGRATION] Colonne frais_scolarite ajoutee a eleves")

    # Migration : personnel -> duree_contrat_mois
    cursor.execute("PRAGMA table_info(personnel)")
    colonnes_pers = [r[1] for r in cursor.fetchall()]
    if "duree_contrat_mois" not in colonnes_pers:
        cursor.execute("ALTER TABLE personnel ADD COLUMN duree_contrat_mois INTEGER DEFAULT 12")
        print("[MIGRATION] Colonne duree_contrat_mois ajoutee a personnel")

    # Migration : paiements_personnel -> montant_avance_deduit
    cursor.execute("PRAGMA table_info(paiements_personnel)")
    colonnes_pp = [r[1] for r in cursor.fetchall()]
    if "montant_avance_deduit" not in colonnes_pp:
        cursor.execute("ALTER TABLE paiements_personnel ADD COLUMN montant_avance_deduit REAL DEFAULT 0")
        print("[MIGRATION] Colonne montant_avance_deduit ajoutee a paiements_personnel")

    conn.commit()
    conn.close()
    print("[OK] Base de donnees initialisee")


if __name__ == "__main__":
    init_database()