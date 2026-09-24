"""
Interface Rapports - Impression PDF + Envoi email
Permissions : admin/gestionnaire peuvent configurer l'email
              autres roles peuvent generer et envoyer les rapports
"""
import os
import sys
import subprocess
import platform
from datetime import datetime
import customtkinter as ctk
from tkinter import messagebox, filedialog
from config import COLOR_NAVY, COLOR_GOLD, format_montant
from ui.permissions_ui import peut
from core.permissions import get_role
from core.parametres import (
    get_config_email, set_config_email, email_est_configure,
)
from core.rapports import (
    donnees_rapport_mensuel, donnees_rapport_impayes,
    donnees_rapport_dettes_personnel, donnees_rapport_journalier,
)
from services.pdf_service import (
    generer_pdf_rapport_mensuel, generer_pdf_rapport_impayes,
    generer_pdf_rapport_dettes_personnel, generer_pdf_rapport_journalier,
)
from services.email_service import envoyer_rapport_email, tester_configuration
from ui.pdf_viewer import PdfViewerWindow


class RapportsPage(ctk.CTkFrame):
    def __init__(self, parent, utilisateur=None):
        super().__init__(parent, fg_color="transparent")

        self.utilisateur = utilisateur or {}

        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True)

        self._construire_interface()

    # ================== PERMISSIONS ==================
    def _peut_configurer_email(self):
        """Seul admin/gestionnaire peut configurer le serveur SMTP."""
        return (peut(self.utilisateur, "peut_gerer_utilisateurs")
                or peut(self.utilisateur, "peut_gerer_permissions"))

    # ================== INTERFACE ==================
    def _construire_interface(self):
        # ===== EN-TETE =====
        ligne_top = ctk.CTkFrame(self.scroll, fg_color="transparent")
        ligne_top.pack(fill="x", pady=(0, 5))

        ctk.CTkLabel(
            ligne_top, text="Rapports",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        # Badge role
        role = get_role(self.utilisateur)
        if role == "admin" or role == "gestionnaire":
            info_role = "Vue : acces complet"
            couleur_role = "#27ae60"
        elif role == "comptable":
            info_role = "Vue : acces complet"
            couleur_role = "#e67e22"
        else:
            info_role = "Vue : lecture seule"
            couleur_role = "#3498db"

        ctk.CTkLabel(
            ligne_top,
            text=info_role,
            font=("Segoe UI", 10, "italic"),
            text_color=couleur_role,
        ).pack(side="right", pady=(8, 0))

        ctk.CTkLabel(
            self.scroll,
            text="Generez, imprimez ou envoyez les rapports par email",
            font=("Segoe UI", 13),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 15))

        # ===== CONFIGURATION EMAIL (visible uniquement pour admin/gestionnaire) =====
        if self._peut_configurer_email():
            config = get_config_email()
            configure = email_est_configure()

            dest_frame = ctk.CTkFrame(self.scroll, fg_color="white", corner_radius=10)
            dest_frame.pack(fill="x", pady=(0, 15))

            ligne_titre_email = ctk.CTkFrame(dest_frame, fg_color="transparent")
            ligne_titre_email.pack(fill="x", padx=15, pady=(10, 5))

            ctk.CTkLabel(
                ligne_titre_email,
                text="Configuration email",
                font=("Segoe UI", 12, "bold"),
                text_color=COLOR_NAVY,
            ).pack(side="left")

            if configure:
                ctk.CTkLabel(
                    ligne_titre_email,
                    text=f"  Configure : {config['user']}",
                    font=("Segoe UI", 10),
                    text_color="#27ae60",
                ).pack(side="left")

                ctk.CTkButton(
                    ligne_titre_email,
                    text="Modifier",
                    font=("Segoe UI", 11, "bold"),
                    fg_color="#e0e0e0",
                    text_color="#333333",
                    hover_color="#c0c0c0",
                    height=30,
                    width=100,
                    command=self._ouvrir_config_email,
                ).pack(side="right")
            else:
                ctk.CTkLabel(
                    ligne_titre_email,
                    text="  Non configure",
                    font=("Segoe UI", 10),
                    text_color="#e74c3c",
                ).pack(side="left")

                ctk.CTkButton(
                    ligne_titre_email,
                    text="Configurer maintenant",
                    font=("Segoe UI", 11, "bold"),
                    fg_color=COLOR_NAVY,
                    hover_color="#1a3d75",
                    height=30,
                    width=180,
                    command=self._ouvrir_config_email,
                ).pack(side="right")

            ctk.CTkLabel(
                dest_frame,
                text="Destinataires des rapports (separes par des virgules)",
                font=("Segoe UI", 10),
                text_color="#888888",
            ).pack(anchor="w", padx=15, pady=(2, 5))

            self.entree_destinataires = ctk.CTkEntry(
                dest_frame,
                font=("Segoe UI", 12),
                height=36,
                placeholder_text="chef@exemple.com, comptable@exemple.com",
            )
            self.entree_destinataires.pack(fill="x", padx=15, pady=(0, 8))
            self.entree_destinataires.insert(0, config.get("destinataires", ""))

            self.entree_destinataires.bind(
                "<FocusOut>",
                lambda e: self._sauvegarder_destinataires(),
            )

            ligne_smtp = ctk.CTkFrame(dest_frame, fg_color="transparent")
            ligne_smtp.pack(fill="x", padx=15, pady=(0, 12))

            ctk.CTkButton(
                ligne_smtp,
                text="Tester la configuration email",
                font=("Segoe UI", 11),
                fg_color="#e0e0e0",
                text_color="#333333",
                hover_color="#c0c0c0",
                height=30,
                width=220,
                command=self._tester_smtp,
            ).pack(side="right")
        else:
            # Pour les autres roles : juste un petit bandeau lecture seule
            cadre_info = ctk.CTkFrame(self.scroll, fg_color="#FFF7E0", corner_radius=8)
            cadre_info.pack(fill="x", pady=(0, 15))
            ctk.CTkLabel(
                cadre_info,
                text=("La configuration email est reservee aux administrateurs.\n"
                      "Vous pouvez ouvrir, imprimer et envoyer les rapports "
                      "si la configuration est deja faite."),
                font=("Segoe UI", 10),
                text_color="#8B6914",
                justify="left",
            ).pack(padx=15, pady=10, anchor="w")

            # Creer quand meme l'entree pour eviter les erreurs dans _get_destinataires
            self.entree_destinataires = None

        # ===== RAPPORTS DISPONIBLES =====
        ctk.CTkLabel(
            self.scroll, text="Rapports disponibles",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(5, 8))

        grid = ctk.CTkFrame(self.scroll, fg_color="transparent")
        grid.pack(fill="x", expand=False)

        grid.columnconfigure(0, weight=1)
        grid.columnconfigure(1, weight=1)

        self._creer_carte_rapport(
            grid, 0, 0,
            titre="Rapport Mensuel",
            description="Synthese complete du mois : recettes, depenses, benefice, impayes, paies du personnel.",
            couleur="#27ae60",
            on_generer=self._generer_rapport_mensuel,
        )

        self._creer_carte_rapport(
            grid, 0, 1,
            titre="Etat des Impayes",
            description="Liste detaillee des eleves avec solde restant a payer. Ideal pour les relances.",
            couleur="#e74c3c",
            on_generer=self._generer_rapport_impayes,
        )

        self._creer_carte_rapport(
            grid, 1, 0,
            titre="Dettes envers le Personnel",
            description="Situation des engagements et restes a payer au personnel (contrats en cours).",
            couleur="#8e44ad",
            on_generer=self._generer_rapport_dettes_personnel,
        )

        self._creer_carte_rapport(
            grid, 1, 1,
            titre="Rapport Journalier",
            description="Operations du jour : encaissements eleves, paies, depenses. A imprimer en fin de journee.",
            couleur="#e67e22",
            on_generer=self._generer_rapport_journalier,
        )

    def _creer_carte_rapport(self, parent, row, col, titre, description,
                              couleur, on_generer):
        carte = ctk.CTkFrame(parent, fg_color="white", corner_radius=12,
                             border_width=2, border_color=couleur)
        carte.grid(row=row, column=col, padx=6, pady=6, sticky="nsew")

        ctk.CTkLabel(
            carte, text=titre,
            font=("Segoe UI", 15, "bold"),
            text_color=couleur,
        ).pack(pady=(15, 6), padx=15)

        ctk.CTkLabel(
            carte, text=description,
            font=("Segoe UI", 11),
            text_color="#666666",
            wraplength=500,
            justify="left",
        ).pack(padx=15, pady=(0, 10))

        ligne_boutons = ctk.CTkFrame(carte, fg_color="transparent")
        ligne_boutons.pack(pady=(0, 15), padx=15)

        ctk.CTkButton(
            ligne_boutons,
            text="Ouvrir / Imprimer",
            font=("Segoe UI", 12, "bold"),
            fg_color=couleur,
            hover_color=couleur,
            height=36,
            width=155,
            command=on_generer,
        ).pack(side="left", padx=4)

        ctk.CTkButton(
            ligne_boutons,
            text="Envoyer par email",
            font=("Segoe UI", 12, "bold"),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            height=36,
            width=155,
            command=lambda: on_generer(envoi_email=True),
        ).pack(side="left", padx=4)

    # ================== ACTIONS ==================
    def _ouvrir_pdf(self, chemin, titre="Apercu du rapport"):
        try:
            PdfViewerWindow(self, chemin, titre=titre)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le PDF : {e}")

    def _get_destinataires(self):
        if self.entree_destinataires is None:
            # Non-admin : lire depuis la config sauvegardee
            try:
                config = get_config_email()
                texte = (config.get("destinataires") or "").strip()
            except Exception:
                texte = ""
        else:
            texte = self.entree_destinataires.get().strip()

        if not texte:
            return []
        return [d.strip() for d in texte.split(",") if d.strip()]

    def _tester_smtp(self):
        if not self._peut_configurer_email():
            messagebox.showerror("Acces refuse",
                                 "Seul un administrateur peut tester la configuration.")
            return
        ok, msg = tester_configuration()
        if ok:
            messagebox.showinfo("Test Email", f"Succes\n\n{msg}")
        else:
            messagebox.showerror("Test Email", f"Echec\n\n{msg}")

    def _sauvegarder_destinataires(self):
        if not self._peut_configurer_email():
            return
        try:
            from core.parametres import set_parametre, CLE_DESTINATAIRES
            set_parametre(CLE_DESTINATAIRES,
                          self.entree_destinataires.get().strip())
        except Exception:
            pass

    def _ouvrir_config_email(self):
        if not self._peut_configurer_email():
            messagebox.showerror("Acces refuse",
                                 "Seul un administrateur peut configurer l'email.")
            return
        ConfigEmailWindow(self, on_save=self._recharger)

    def _recharger(self):
        for w in self.scroll.winfo_children():
            w.destroy()
        self._construire_interface()

    def _finaliser(self, chemin, envoi_email, sujet, message_email):
        if envoi_email:
            destinataires = self._get_destinataires()
            if not destinataires:
                messagebox.showwarning(
                    "Aucun destinataire",
                    "Aucun destinataire configure.\n\n"
                    "Contactez un administrateur pour configurer les emails."
                )
                return

            rep = messagebox.askyesno(
                "Confirmer l'envoi",
                f"Envoyer le rapport a :\n\n" +
                "\n".join(f"- {d}" for d in destinataires) +
                "\n\nSujet : " + sujet
            )
            if not rep:
                return

            ok, msg = envoyer_rapport_email(
                destinataires, sujet, message_email, [chemin]
            )
            if ok:
                messagebox.showinfo("Email envoye", msg)
            else:
                messagebox.showerror("Erreur d'envoi", msg)
        else:
            self._ouvrir_pdf(chemin, titre=sujet)

    # ================== RAPPORTS ==================
    def _generer_rapport_mensuel(self, envoi_email=False):
        try:
            donnees = donnees_rapport_mensuel()
            chemin = generer_pdf_rapport_mensuel(donnees)

            mois_noms = ["", "Janvier", "Fevrier", "Mars", "Avril", "Mai", "Juin",
                         "Juillet", "Aout", "Septembre", "Octobre", "Novembre", "Decembre"]
            sujet = f"Rapport Mensuel - {mois_noms[donnees['mois']]} {donnees['annee']}"

            message = (
                f"Bonjour,\n\n"
                f"Veuillez trouver ci-joint le rapport mensuel "
                f"de {mois_noms[donnees['mois']]} {donnees['annee']}.\n\n"
                f"Resume :\n"
                f"- Recettes : {format_montant(donnees['recettes_totales'])}\n"
                f"- Depenses : {format_montant(donnees['depenses_totales'])}\n"
                f"- Benefice : {format_montant(donnees['benefice'])}\n"
                f"- Impayes : {format_montant(donnees['impayes']['total'])}\n\n"
                f"Cordialement."
            )

            self._finaliser(chemin, envoi_email, sujet, message)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur generation rapport : {e}")

    def _generer_rapport_impayes(self, envoi_email=False):
        try:
            donnees = donnees_rapport_impayes()
            chemin = generer_pdf_rapport_impayes(donnees)

            sujet = f"Etat des Impayes - {datetime.now().strftime('%d/%m/%Y')}"

            message = (
                f"Bonjour,\n\n"
                f"Veuillez trouver ci-joint l'etat des impayes au "
                f"{datetime.now().strftime('%d/%m/%Y')}.\n\n"
                f"Resume :\n"
                f"- Nombre d'eleves avec impayes : {donnees['nombre_impayes']}\n"
                f"- Total a recouvrer : {format_montant(donnees['total_impaye'])}\n\n"
                f"Cordialement."
            )

            self._finaliser(chemin, envoi_email, sujet, message)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur generation rapport : {e}")

    def _generer_rapport_dettes_personnel(self, envoi_email=False):
        try:
            donnees = donnees_rapport_dettes_personnel()
            chemin = generer_pdf_rapport_dettes_personnel(donnees)

            sujet = f"Dettes Personnel - {datetime.now().strftime('%d/%m/%Y')}"

            message = (
                f"Bonjour,\n\n"
                f"Veuillez trouver ci-joint l'etat des dettes envers le personnel.\n\n"
                f"Resume :\n"
                f"- Nombre de personnes concernees : {donnees['nombre']}\n"
                f"- Total a payer : {format_montant(donnees['total_dette'])}\n\n"
                f"Cordialement."
            )

            self._finaliser(chemin, envoi_email, sujet, message)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur generation rapport : {e}")

    def _generer_rapport_journalier(self, envoi_email=False):
        try:
            donnees = donnees_rapport_journalier()
            chemin = generer_pdf_rapport_journalier(donnees)

            sujet = f"Rapport Journalier - {donnees['date']}"

            message = (
                f"Bonjour,\n\n"
                f"Veuillez trouver ci-joint le rapport journalier "
                f"du {donnees['date']}.\n\n"
                f"Resume :\n"
                f"- Recettes eleves : {format_montant(donnees['total_recettes'])}\n"
                f"- Paiements personnel : {format_montant(donnees['total_personnel'])}\n"
                f"- Depenses generales : {format_montant(donnees['total_depenses'])}\n"
                f"- Solde du jour : {format_montant(donnees['solde_jour'])}\n\n"
                f"Cordialement."
            )

            self._finaliser(chemin, envoi_email, sujet, message)

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror("Erreur", f"Erreur generation rapport : {e}")


# ============================================================
# FENETRE DE CONFIGURATION EMAIL (inchangee)
# ============================================================
class ConfigEmailWindow(ctk.CTkToplevel):
    def __init__(self, parent, on_save=None):
        super().__init__(parent)

        self.on_save = on_save

        self.title("Configuration email")
        largeur = 560
        hauteur = 680
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = 20
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())

        self.transient(parent)
        self.after(100, self._activer_grab)

        self._construire_interface()

    def _activer_grab(self):
        try:
            self.grab_set()
            self.focus_force()
        except Exception:
            pass

    def _construire_interface(self):
        config = get_config_email()

        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        ligne_titre = ctk.CTkFrame(card, fg_color="transparent")
        ligne_titre.pack(fill="x", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            ligne_titre, text="Configuration email",
            font=("Segoe UI", 17, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        ctk.CTkButton(
            ligne_titre, text="X",
            font=("Segoe UI", 14, "bold"),
            width=32, height=32,
            fg_color="#e74c3c", hover_color="#c0392b",
            command=self.destroy,
        ).pack(side="right")

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        info = ctk.CTkFrame(zone, fg_color="#FFF7E0", corner_radius=8)
        info.pack(fill="x", padx=10, pady=(5, 10))

        ctk.CTkLabel(
            info,
            text=(
                "POUR GMAIL (recommande) :\n"
                "1. Allez sur myaccount.google.com/security\n"
                "2. Activez la validation en 2 etapes\n"
                "3. Allez sur myaccount.google.com/apppasswords\n"
                "4. Creez un mot de passe d'application 'B-NDEKE'\n"
                "5. Copiez le code de 16 caracteres\n"
                "6. Collez-le dans 'Mot de passe' ci-dessous"
            ),
            font=("Segoe UI", 10),
            text_color="#8B6914",
            justify="left",
        ).pack(padx=12, pady=10, anchor="w")

        ctk.CTkLabel(
            zone, text="Fournisseur email (serveur SMTP)",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=10, pady=(8, 4), fill="x")

        self.combo_serveur = ctk.CTkComboBox(
            zone,
            values=[
                "smtp.gmail.com",
                "smtp.office365.com",
                "smtp.mail.yahoo.com",
                "smtp.free.fr",
                "smtp.orange.fr",
                "Autre (champ ci-dessous)",
            ],
            font=("Segoe UI", 12),
            height=38,
            command=self._on_serveur_change,
        )
        self.combo_serveur.set(config["server"] or "smtp.gmail.com")
        self.combo_serveur.pack(padx=10, pady=(0, 6), fill="x")

        self.champs = {}

        self.champs["server"] = self._ajouter_champ(
            zone, "Serveur SMTP",
            valeur=config["server"]
        )

        self.champs["port"] = self._ajouter_champ(
            zone, "Port (587 pour TLS, 465 pour SSL)",
            valeur=str(config["port"])
        )

        self.champs["user"] = self._ajouter_champ(
            zone, "Adresse email d'envoi (votre email)",
            valeur=config["user"]
        )

        ctk.CTkLabel(
            zone, text="Mot de passe d'application",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=10, pady=(8, 4), fill="x")

        self.champs["password"] = ctk.CTkEntry(
            zone,
            font=("Segoe UI", 13),
            height=36,
            show="*",
            placeholder_text="xxxx xxxx xxxx xxxx",
        )
        if config["password"]:
            self.champs["password"].insert(0, config["password"])
        self.champs["password"].pack(padx=10, pady=(0, 5), fill="x")

        self.champs["from_name"] = self._ajouter_champ(
            zone, "Nom affiche comme expediteur",
            valeur=config["from_name"]
        )

        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=15, pady=(5, 12))

        ctk.CTkButton(
            boutons,
            text="Tester",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_GOLD,
            text_color="#333333",
            hover_color="#d9a500",
            height=42,
            width=120,
            command=self._tester,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            boutons,
            text="Annuler",
            font=("Segoe UI", 13),
            fg_color="#e74c3c",
            text_color="white",
            hover_color="#c0392b",
            height=42,
            width=100,
            command=self.destroy,
        ).pack(side="left", padx=5)

        ctk.CTkButton(
            boutons,
            text="Enregistrer",
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=42,
            command=self._enregistrer,
        ).pack(side="right", padx=(5, 0))

    def _on_serveur_change(self, choix):
        if choix and choix != "Autre (champ ci-dessous)":
            self.champs["server"].delete(0, "end")
            self.champs["server"].insert(0, choix)
            self.champs["port"].delete(0, "end")
            self.champs["port"].insert(0, "587")

    def _ajouter_champ(self, parent, label, valeur=""):
        ctk.CTkLabel(
            parent, text=label,
            font=("Segoe UI", 12, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=10, pady=(8, 4), fill="x")

        entree = ctk.CTkEntry(parent, font=("Segoe UI", 13), height=36)
        entree.insert(0, valeur)
        entree.pack(padx=10, pady=(0, 5), fill="x")
        return entree

    def _recup_config(self):
        return {
            "server": self.champs["server"].get().strip(),
            "port": self.champs["port"].get().strip(),
            "user": self.champs["user"].get().strip(),
            "password": self.champs["password"].get().strip(),
            "from_name": self.champs["from_name"].get().strip() or "B-NDEKE Comptability One",
        }

    def _tester(self):
        c = self._recup_config()

        if not c["user"] or not c["password"]:
            messagebox.showerror("Erreur", "Remplissez l'email et le mot de passe.")
            return

        try:
            port = int(c["port"]) if c["port"] else 587
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit etre un nombre.")
            return

        from core.parametres import set_config_email
        set_config_email(c["server"], port, c["user"], c["password"],
                         c["from_name"], "")

        ok, msg = tester_configuration()
        if ok:
            messagebox.showinfo("Test Email", f"Succes\n\n{msg}")
        else:
            messagebox.showerror("Test Email", f"Echec\n\n{msg}")

    def _enregistrer(self):
        c = self._recup_config()

        if not c["user"] or not c["password"]:
            messagebox.showerror("Erreur", "Remplissez l'email et le mot de passe.")
            return

        try:
            port = int(c["port"]) if c["port"] else 587
        except ValueError:
            messagebox.showerror("Erreur", "Le port doit etre un nombre.")
            return

        from core.parametres import set_config_email, get_parametre, CLE_DESTINATAIRES

        destinataires = get_parametre(CLE_DESTINATAIRES)

        set_config_email(c["server"], port, c["user"], c["password"],
                         c["from_name"], destinataires)

        messagebox.showinfo("Succes", "Configuration email enregistree !")
        if self.on_save:
            self.on_save()
        self.destroy()