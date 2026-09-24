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

    # ===== CLASSES (STRUCTURE SCOLAIRE) =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niveau TEXT NOT NULL,
            sous_type TEXT,
            nom TEXT NOT NULL,
            ordre INTEGER DEFAULT 0,
            description TEXT,
            actif INTEGER DEFAULT 1,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(niveau, nom)
        )
    """)

    # ===== FRAIS (CATALOGUE) =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nom TEXT NOT NULL UNIQUE,
            description TEXT,
            montant_defaut REAL DEFAULT 0,
            categorie_budget TEXT DEFAULT '',
            dans_budget INTEGER DEFAULT 0,
            actif INTEGER DEFAULT 1,
            ordre INTEGER DEFAULT 0,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # ===== FRAIS PAR CLASSE (AFFECTATION) =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frais_classes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frais_id INTEGER NOT NULL,
            classe_id INTEGER NOT NULL,
            montant REAL DEFAULT 0,
            obligatoire INTEGER DEFAULT 1,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (frais_id) REFERENCES frais(id) ON DELETE CASCADE,
            FOREIGN KEY (classe_id) REFERENCES classes(id) ON DELETE CASCADE,
            UNIQUE(frais_id, classe_id)
        )
    """)

    # ===== FRAIS PAR DEFAUT (PAR NIVEAU / OPTION) =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frais_defauts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            niveau TEXT NOT NULL,
            sous_type TEXT,
            option_nom TEXT,
            frais_id INTEGER NOT NULL,
            montant REAL DEFAULT 0,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (frais_id) REFERENCES frais(id) ON DELETE CASCADE,
            UNIQUE(niveau, sous_type, option_nom, frais_id)
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

    # ===== FRAIS ELEVES (CE QUE L'ELEVE DOIT PAYER) =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS frais_eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            frais_id INTEGER NOT NULL,
            libelle TEXT NOT NULL,
            montant_initial REAL NOT NULL,
            montant_paye REAL DEFAULT 0,
            solde REAL NOT NULL,
            annee_libelle TEXT,
            statut TEXT DEFAULT 'en_cours',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (eleve_id) REFERENCES eleves(id),
            FOREIGN KEY (frais_id) REFERENCES frais(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ===== PAIEMENTS FRAIS ELEVES =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paiements_frais (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            frais_eleve_id INTEGER NOT NULL,
            numero_recu TEXT,
            montant REAL NOT NULL,
            mode_paiement TEXT DEFAULT 'especes',
            date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (frais_eleve_id) REFERENCES frais_eleves(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
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
            budget_sous_categorie TEXT DEFAULT '',
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

    # ===== PRESENCES ELEVES =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presences_eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            date_presence DATE NOT NULL,
            statut TEXT NOT NULL,
            motif TEXT,
            non_considere INTEGER DEFAULT 0,
            saisi_par INTEGER,
            date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (eleve_id) REFERENCES eleves(id),
            FOREIGN KEY (saisi_par) REFERENCES utilisateurs(id),
            UNIQUE(eleve_id, date_presence)
        )
    """)

    # ===== PRESENCES PERSONNEL =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS presences_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            date_presence DATE NOT NULL,
            statut TEXT NOT NULL,
            motif TEXT,
            non_considere INTEGER DEFAULT 0,
            saisi_par INTEGER,
            date_saisie TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id),
            FOREIGN KEY (saisi_par) REFERENCES utilisateurs(id),
            UNIQUE(personnel_id, date_presence)
        )
    """)

    # ===== RETENUES SUR SALAIRE =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS retenues_personnel (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            personnel_id INTEGER NOT NULL,
            date_retenue DATE NOT NULL,
            pourcentage REAL DEFAULT 0,
            montant_calcule REAL DEFAULT 0,
            motif TEXT,
            statut TEXT DEFAULT 'en_attente',
            utilisateur_id INTEGER,
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (personnel_id) REFERENCES personnel(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ===== DETTES ELEVES (REPORT D'ANNEE) =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS dettes_eleves (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            eleve_id INTEGER NOT NULL,
            annee_libelle TEXT NOT NULL,
            categorie TEXT DEFAULT 'Scolarite',
            montant_initial REAL NOT NULL,
            montant_paye REAL DEFAULT 0,
            solde REAL NOT NULL,
            motif TEXT,
            statut TEXT DEFAULT 'en_cours',
            date_creation TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (eleve_id) REFERENCES eleves(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ===== PAIEMENTS DETTES =====
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS paiements_dettes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            dette_id INTEGER NOT NULL,
            numero_recu TEXT,
            montant REAL NOT NULL,
            mode_paiement TEXT DEFAULT 'especes',
            date_paiement TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            utilisateur_id INTEGER,
            FOREIGN KEY (dette_id) REFERENCES dettes_eleves(id),
            FOREIGN KEY (utilisateur_id) REFERENCES utilisateurs(id)
        )
    """)

    # ============================================================
    # MIGRATIONS (pour les bases existantes)
    # ============================================================

    cursor.execute("PRAGMA table_info(eleves)")
    colonnes_eleves = [r[1] for r in cursor.fetchall()]
    if "frais_scolarite" not in colonnes_eleves:
        cursor.execute("ALTER TABLE eleves ADD COLUMN frais_scolarite REAL DEFAULT 0")
        print("[MIGRATION] Colonne frais_scolarite ajoutee a eleves")

    cursor.execute("PRAGMA table_info(personnel)")
    colonnes_pers = [r[1] for r in cursor.fetchall()]
    if "duree_contrat_mois" not in colonnes_pers:
        cursor.execute("ALTER TABLE personnel ADD COLUMN duree_contrat_mois INTEGER DEFAULT 12")
        print("[MIGRATION] Colonne duree_contrat_mois ajoutee a personnel")

    cursor.execute("PRAGMA table_info(paiements_personnel)")
    colonnes_pp = [r[1] for r in cursor.fetchall()]
    if "montant_avance_deduit" not in colonnes_pp:
        cursor.execute("ALTER TABLE paiements_personnel ADD COLUMN montant_avance_deduit REAL DEFAULT 0")
        print("[MIGRATION] Colonne montant_avance_deduit ajoutee a paiements_personnel")

    cursor.execute("PRAGMA table_info(depenses)")
    colonnes_dep = [r[1] for r in cursor.fetchall()]
    if "budget_sous_categorie" not in colonnes_dep:
        cursor.execute("ALTER TABLE depenses ADD COLUMN budget_sous_categorie TEXT DEFAULT ''")
        print("[MIGRATION] Colonne budget_sous_categorie ajoutee a depenses")

    cursor.execute("PRAGMA table_info(dettes_eleves)")
    colonnes_dettes = [r[1] for r in cursor.fetchall()]
    if "categorie" not in colonnes_dettes:
        cursor.execute("ALTER TABLE dettes_eleves ADD COLUMN categorie TEXT DEFAULT 'Scolarite'")
        print("[MIGRATION] Colonne categorie ajoutee a dettes_eleves")

    conn.commit()
    conn.close()
    print("[OK] Base de donnees initialisee")


if __name__ == "__main__":
    init_database()