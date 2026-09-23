"""
OUTIL VENDEUR - Generation des cles d'activation B-NDEKE
ATTENTION : NE PAS DISTRIBUER AUX CLIENTS

Usage :
    python generer_licence.py
"""
from datetime import datetime, timedelta
import hmac
import hashlib


# ===== DOIT ETRE IDENTIQUE A core/licence.py =====
_SECRET = "BNDEKE2025COMPTABILITYONESECRETKEYv1"


def _hash_email(email):
    email = email.strip().lower()
    h = hashlib.sha256(email.encode("utf-8")).hexdigest()[:8].upper()
    return h


def _signature(client_code, expiration, email_client):
    email_hash = _hash_email(email_client)
    message = f"{client_code}-{expiration}-{email_hash}"
    sig = hmac.new(
        _SECRET.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()[:8].upper()
    return sig


def generer_cle(client_code, date_expiration, email_client):
    client_code = str(client_code).upper().replace("-", "").replace(" ", "")[:5]
    if len(client_code) < 3:
        client_code = client_code.ljust(3, "X")

    if isinstance(date_expiration, str):
        expiration = date_expiration
    else:
        expiration = date_expiration.strftime("%Y%m%d")

    sig = _signature(client_code, expiration, email_client)
    return f"BNDEKE-{client_code}-{expiration}-{sig}"


def main():
    print("=" * 60)
    print("  B-NDEKE Comptability One - GENERATEUR DE LICENCE")
    print("  (Usage vendeur uniquement)")
    print("=" * 60)
    print()

    while True:
        print("-" * 60)
        print("MENU :")
        print("  1. Generer une nouvelle licence")
        print("  2. Verifier une cle existante")
        print("  3. Quitter")
        print()

        choix = input("Votre choix (1, 2 ou 3) : ").strip()

        if choix == "3":
            print("\nAu revoir !")
            break

        if choix == "2":
            cle = input("Collez la cle a verifier : ").strip().upper()
            email = input("Email du client : ").strip().lower()
            try:
                from core.licence import verifier_cle
                ok, msg, info = verifier_cle(cle, email)
            except Exception as e:
                print(f"Erreur : {e}")
                input("Appuyez sur Entree pour continuer...")
                continue
            print()
            print("=" * 60)
            if ok:
                print("  CLE VALIDE")
                print("=" * 60)
                print(f"  Client         : {info['client_code']}")
                print(f"  Email          : {info['email']}")
                print(f"  Expire le      : {info['expiration'].strftime('%d/%m/%Y')}")
                print(f"  Jours restants : {info['jours_restants']}")
            else:
                print("  CLE INVALIDE")
                print("=" * 60)
                print(f"  {msg}")
            print()
            input("Appuyez sur Entree pour continuer...")
            continue

        if choix != "1":
            print("Choix invalide.\n")
            continue

        print()

        # Code client
        client = input("Code client (ex: JACQU, ECOLE, ABC23, max 5 car.) : ").strip().upper()
        if not client:
            print("Erreur : le code client est obligatoire.\n")
            continue

        # Email client
        email = input("Email de l'ecole (ex: contact@ecole.com) : ").strip().lower()
        if not email or "@" not in email or "." not in email:
            print("Erreur : email invalide.\n")
            continue

        # Duree
        print()
        print("Duree de la licence :")
        print("  1. 1 an (365 jours) - Recommande")
        print("  2. 6 mois (180 jours)")
        print("  3. 30 jours (essai)")
        print("  4. Personnalisee")

        duree_choix = input("Votre choix (1-4) : ").strip()

        if duree_choix == "1":
            jours = 365
        elif duree_choix == "2":
            jours = 180
        elif duree_choix == "3":
            jours = 30
        elif duree_choix == "4":
            try:
                jours = int(input("Nombre de jours : ").strip())
            except ValueError:
                print("Erreur : nombre invalide.\n")
                continue
        else:
            print("Choix invalide.\n")
            continue

        date_exp = datetime.now() + timedelta(days=jours)
        cle = generer_cle(client, date_exp, email)

        print()
        print("=" * 60)
        print("  LICENCE GENEREE")
        print("=" * 60)
        print()
        print(f"  Client       : {client}")
        print(f"  Email        : {email}")
        print(f"  Duree        : {jours} jours")
        print(f"  Expire le    : {date_exp.strftime('%d/%m/%Y')}")
        print()
        print(f"  CLE : {cle}")
        print()
        print("=" * 60)
        print(f"  Cette cle fonctionne avec l'email : {email}")
        print(f"  Elle peut etre utilisee sur 3 machines maximum.")
        print("=" * 60)
        print()

        input("Appuyez sur Entree pour continuer...")


if __name__ == "__main__":
    main()