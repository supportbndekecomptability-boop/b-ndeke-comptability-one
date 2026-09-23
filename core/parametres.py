"""
Gestion des parametres de l'application (cles-valeurs)
"""
from database import get_connection


CLE_SMTP_SERVER = "smtp_server"
CLE_SMTP_PORT = "smtp_port"
CLE_SMTP_USER = "smtp_user"
CLE_SMTP_PASSWORD = "smtp_password"
CLE_SMTP_FROM_NAME = "smtp_from_name"
CLE_DESTINATAIRES = "destinataires_rapports"

DEFAUTS = {
    CLE_SMTP_SERVER: "smtp.gmail.com",
    CLE_SMTP_PORT: "587",
    CLE_SMTP_USER: "",
    CLE_SMTP_PASSWORD: "",
    CLE_SMTP_FROM_NAME: "B-NDEKE Comptability One",
    CLE_DESTINATAIRES: "",
}


def get_parametre(cle, defaut=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT valeur FROM parametres WHERE cle = ?", (cle,))
    row = cursor.fetchone()
    conn.close()

    if row:
        return row["valeur"]
    return defaut if defaut is not None else DEFAUTS.get(cle, "")


def set_parametre(cle, valeur):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO parametres (cle, valeur, date_modification)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(cle) DO UPDATE SET
                valeur = excluded.valeur,
                date_modification = CURRENT_TIMESTAMP
        """, (cle, str(valeur) if valeur is not None else ""))
        conn.commit()
        return True
    except Exception as e:
        print(f"[Erreur set_parametre] {e}")
        return False
    finally:
        conn.close()


def get_config_email():
    return {
        "server": get_parametre(CLE_SMTP_SERVER),
        "port": int(get_parametre(CLE_SMTP_PORT) or 587),
        "user": get_parametre(CLE_SMTP_USER),
        "password": get_parametre(CLE_SMTP_PASSWORD),
        "from_name": get_parametre(CLE_SMTP_FROM_NAME),
        "destinataires": get_parametre(CLE_DESTINATAIRES),
    }


def set_config_email(server, port, user, password, from_name, destinataires):
    set_parametre(CLE_SMTP_SERVER, server)
    set_parametre(CLE_SMTP_PORT, str(port))
    set_parametre(CLE_SMTP_USER, user)
    set_parametre(CLE_SMTP_PASSWORD, password)
    set_parametre(CLE_SMTP_FROM_NAME, from_name)
    set_parametre(CLE_DESTINATAIRES, destinataires)


def email_est_configure():
    config = get_config_email()
    return bool(config["user"] and config["password"])