"""
Ecran d'activation de la licence - 2 etapes SIMPLIFIEES
L'ecole saisit directement son email + son code
Limite : 3 machines par code (via Google Sheets)
"""
import customtkinter as ctk
from tkinter import messagebox
from config import (
    COLOR_NAVY, COLOR_GOLD, APP_NAME, APP_VERSION,
    VENDEUR_EMAIL,
)
from core.licence import (
    activer_licence_avec_serveur,
    envoyer_demande_code,
    envoyer_confirmation_activation,
)


class ActivationWindow(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.activation_reussie = False

        self.email_client = ""
        self.cle_utilisee = ""
        self.nom_ecole = ""
        self.infos_ecole = {}

        self.title(f"{APP_NAME} - Activation")

        # Adapter a la taille de l'ecran
        sw = self.winfo_screenwidth()
        sh = self.winfo_screenheight()

        largeur = min(600, sw - 40)
        hauteur = min(640, sh - 60)

        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (sw // 2) - (largeur // 2)
        y = max(5, (sh // 2) - (hauteur // 2) - 20)
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self._quitter())

        self.conteneur = ctk.CTkFrame(self, fg_color="transparent")
        self.conteneur.pack(fill="both", expand=True)

        self._afficher_etape_activation()

    # =========================================================
    # ETAPE 1 : ACTIVATION
    # =========================================================
    def _afficher_etape_activation(self):
        self._vider_conteneur()

        card = ctk.CTkFrame(self.conteneur, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            card, text="B-NDEKE",
            font=("Segoe UI", 24, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(12, 0))

        ctk.CTkLabel(
            card, text="Comptability One",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 2))

        ctk.CTkLabel(
            card, text=f"Version {APP_VERSION}",
            font=("Segoe UI", 9),
            text_color="#999999",
        ).pack(pady=(0, 6))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).pack(fill="x", padx=40, pady=3)

        ctk.CTkLabel(
            card, text="ACTIVATION",
            font=("Segoe UI", 13, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(8, 3))

        ctk.CTkLabel(
            card,
            text="Entrez votre email et votre code d'activation",
            font=("Segoe UI", 10),
            text_color="#666666",
        ).pack(pady=(0, 8))

        ctk.CTkLabel(
            card, text="Adresse email de l'ecole",
            font=("Segoe UI", 10, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=40, pady=(0, 3), fill="x")

        self.entree_email = ctk.CTkEntry(
            card,
            font=("Segoe UI", 11),
            height=34,
            placeholder_text="exemple@ecole.com",
        )
        self.entree_email.pack(padx=40, pady=(0, 8), fill="x")

        ctk.CTkLabel(
            card, text="Code d'activation",
            font=("Segoe UI", 10, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=40, pady=(0, 3), fill="x")

        self.entree_cle = ctk.CTkEntry(
            card,
            font=("Consolas", 12, "bold"),
            height=36,
            placeholder_text="BNDEKE-XXXXX-YYYYMMDD-XXXXXXXX",
        )
        self.entree_cle.pack(padx=40, pady=(0, 6), fill="x")
        self.entree_cle.bind("<Return>", lambda e: self._activer())

        ctk.CTkButton(
            card,
            text="ACTIVER",
            font=("Segoe UI", 12, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=38,
            command=self._activer,
        ).pack(padx=40, pady=(8, 6), fill="x")

        self.label_message = ctk.CTkLabel(
            card, text="",
            font=("Segoe UI", 9),
            text_color="#666666",
            wraplength=500,
            justify="left",
        )
        self.label_message.pack(padx=40, pady=(0, 4))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).pack(fill="x", padx=40, pady=3)

        ctk.CTkLabel(
            card,
            text="Vous n'avez pas encore de code ?",
            font=("Segoe UI", 9, "bold"),
            text_color="#666666",
        ).pack(pady=(4, 3))

        ctk.CTkButton(
            card,
            text="Demander un code d'activation",
            font=("Segoe UI", 10),
            fg_color="#3498db",
            hover_color="#2980b9",
            height=30,
            command=self._demander_code,
        ).pack(padx=40, pady=(0, 6), fill="x")

        contact_frame = ctk.CTkFrame(card, fg_color="#F0F7FF", corner_radius=8)
        contact_frame.pack(fill="x", padx=40, pady=(3, 6))

        ctk.CTkLabel(
            contact_frame,
            text="Contact support :",
            font=("Segoe UI", 9, "bold"),
            text_color=COLOR_NAVY,
        ).pack(padx=12, pady=(5, 2), anchor="w")

        self.champ_email_contact = ctk.CTkEntry(
            contact_frame,
            font=("Consolas", 10),
            height=24,
            fg_color="white",
            text_color="#0066CC",
        )
        self.champ_email_contact.pack(fill="x", padx=12, pady=(0, 5))
        self.champ_email_contact.insert(0, VENDEUR_EMAIL)
        self.champ_email_contact.configure(state="readonly")

        ctk.CTkButton(
            card,
            text="Quitter",
            font=("Segoe UI", 10),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            height=26,
            command=self._quitter,
        ).pack(padx=40, pady=(3, 10), fill="x")

        self.after(300, lambda: self.entree_email.focus_set())

    def _activer(self):
        email = self.entree_email.get().strip().lower()
        cle = self.entree_cle.get().strip().upper()

        if not email or "@" not in email or "." not in email:
            self.label_message.configure(
                text="Veuillez saisir une adresse email valide.",
                text_color="#e74c3c",
            )
            return

        if not cle:
            self.label_message.configure(
                text="Veuillez coller votre code d'activation.",
                text_color="#e74c3c",
            )
            return

        self.email_client = email
        self.label_message.configure(
            text="Verification en cours...",
            text_color="#3498db",
        )
        self.update()

        try:
            ok, message, info = activer_licence_avec_serveur(cle, email)
        except Exception as e:
            ok = False
            message = f"Erreur inattendue : {e}"

        if ok:
            self.cle_utilisee = cle
            self.label_message.configure(text=message, text_color="#27ae60")
            self.update()
            self.after(1200, self._afficher_etape_ecole)
        else:
            self.label_message.configure(text=message, text_color="#e74c3c")

    def _demander_code(self):
        email = self.entree_email.get().strip().lower()

        if not email or "@" not in email or "." not in email:
            self.label_message.configure(
                text="Saisissez d'abord votre adresse email ci-dessus.",
                text_color="#e67e22",
            )
            return

        self.email_client = email
        self.label_message.configure(
            text="Envoi de la demande en cours...",
            text_color="#3498db",
        )
        self.update()

        try:
            ok, msg = envoyer_demande_code(email)
        except Exception:
            ok = False

        if ok:
            self.label_message.configure(
                text="Demande envoyee !\n"
                     "Vous recevrez votre code par email ou WhatsApp.",
                text_color="#27ae60",
            )
        else:
            self.label_message.configure(
                text=f"Envoyez un email a {VENDEUR_EMAIL}\n"
                     f"en indiquant : {email}",
                text_color="#e67e22",
            )

    # =========================================================
    # ETAPE 2 : INFORMATIONS DE L'ECOLE
    # =========================================================
    def _afficher_etape_ecole(self):
        self._vider_conteneur()

        card = ctk.CTkFrame(self.conteneur, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        ctk.CTkLabel(
            card, text="B-NDEKE",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(10, 0))

        ctk.CTkLabel(
            card, text="Comptability One",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 6))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).pack(fill="x", padx=40, pady=3)

        ctk.CTkLabel(
            card, text="INFORMATIONS DE L'ECOLE",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(8, 3))

        ctk.CTkLabel(
            card,
            text="Remplissez les informations de votre etablissement",
            font=("Segoe UI", 9),
            text_color="#666666",
        ).pack(pady=(0, 6))

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=15, pady=3)

        self.champs_ecole = {}

        self.champs_ecole["nom"] = self._ajouter_champ(
            zone, "Nom de l'ecole *",
            placeholder="Ex: Ecole Les Petits Genies"
        )
        self.champs_ecole["adresse"] = self._ajouter_champ(
            zone, "Adresse",
            placeholder="Ex: 15 Avenue de la Paix"
        )
        self.champs_ecole["ville"] = self._ajouter_champ(
            zone, "Ville / Province",
            placeholder="Ex: Kinshasa"
        )
        self.champs_ecole["pays"] = self._ajouter_champ(
            zone, "Pays",
            placeholder="Ex: RDC",
            valeur="RDC"
        )
        self.champs_ecole["telephone"] = self._ajouter_champ(
            zone, "Telephone",
            placeholder="Ex: +243 812 345 678"
        )
        self.champs_ecole["email"] = self._ajouter_champ(
            zone, "Email de l'ecole",
            placeholder="Ex: contact@ecole.com"
        )
        self.champs_ecole["directeur"] = self._ajouter_champ(
            zone, "Nom du directeur / responsable",
            placeholder="Ex: M. Jacques "
        )

        # ===== SECTION SECURITE / SAUVEGARDE CLOUD =====
        ctk.CTkFrame(zone, fg_color="#e0e0e0", height=1).pack(fill="x", padx=10, pady=(10, 6))

        ctk.CTkLabel(
            zone,
            text="SECURITE DES DONNEES",
            font=("Segoe UI", 10, "bold"),
            text_color=COLOR_NAVY,
        ).pack(padx=10, pady=(3, 3), anchor="w")

        self.var_cloud = ctk.StringVar(value="1")

        ctk.CTkCheckBox(
            zone,
            text="Activer la sauvegarde cloud securisee (recommande)",
            variable=self.var_cloud,
            onvalue="1",
            offvalue="0",
            font=("Segoe UI", 9, "bold"),
        ).pack(padx=15, pady=(3, 4), anchor="w")

        ctk.CTkLabel(
            zone,
            text=(
                "Vos donnees seront sauvegardees de maniere CHIFFREE sur le "
                "serveur B-NDEKE pour prevenir toute perte (panne, vol, etc.). "
                "Vous pouvez desactiver cette option a tout moment dans "
                "Parametres. B-NDEKE ne consultera jamais vos donnees sans "
                "votre autorisation ecrite."
            ),
            font=("Segoe UI", 8),
            text_color="#666666",
            wraplength=480,
            justify="left",
        ).pack(padx=15, pady=(0, 6), anchor="w")

        self.label_message_3 = ctk.CTkLabel(
            card, text="",
            font=("Segoe UI", 9),
            text_color="#666666",
            wraplength=500,
            justify="left",
        )
        self.label_message_3.pack(padx=40, pady=(3, 6))

        ctk.CTkButton(
            card,
            text="TERMINER",
            font=("Segoe UI", 12, "bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            height=38,
            command=self._terminer,
        ).pack(padx=40, pady=(3, 10), fill="x")

        self.after(300, lambda: self.champs_ecole["nom"].focus_set())

    def _ajouter_champ(self, parent, label, placeholder="", valeur=""):
        ctk.CTkLabel(
            parent, text=label,
            font=("Segoe UI", 9, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=10, pady=(4, 2), fill="x")

        entree = ctk.CTkEntry(
            parent,
            font=("Segoe UI", 10),
            height=30,
            placeholder_text=placeholder,
        )
        if valeur:
            entree.insert(0, valeur)
        entree.pack(padx=10, pady=(0, 3), fill="x")
        return entree

    def _terminer(self):
        nom_ecole = self.champs_ecole["nom"].get().strip()

        if not nom_ecole:
            self.label_message_3.configure(
                text="Le nom de l'ecole est obligatoire.",
                text_color="#e74c3c",
            )
            return

        self.nom_ecole = nom_ecole

        infos = {
            "Adresse": self.champs_ecole["adresse"].get().strip() or "-",
            "Ville": self.champs_ecole["ville"].get().strip() or "-",
            "Pays": self.champs_ecole["pays"].get().strip() or "-",
            "Telephone": self.champs_ecole["telephone"].get().strip() or "-",
            "Email ecole": self.champs_ecole["email"].get().strip() or "-",
            "Directeur": self.champs_ecole["directeur"].get().strip() or "-",
        }
        self.infos_ecole = infos

        self.label_message_3.configure(
            text="Enregistrement en cours...",
            text_color="#3498db",
        )
        self.update()

        try:
            from core.parametres import set_parametre
            set_parametre("ecole_nom", nom_ecole)
            set_parametre("ecole_adresse", infos.get("Adresse", ""))
            set_parametre("ecole_telephone", infos.get("Telephone", ""))
            set_parametre("ecole_email", infos.get("Email ecole", ""))
            set_parametre("ecole_directeur", infos.get("Directeur", ""))
        except Exception:
            pass

        # ===== SAUVEGARDE CLOUD (OPT-IN) =====
        try:
            from core.backup_cloud import (
                activer_sauvegarde_cloud,
                marquer_acceptation_cloud,
                sauvegarder_dans_cloud,
            )
            cloud_actif = (self.var_cloud.get() == "1")
            activer_sauvegarde_cloud(cloud_actif)
            if cloud_actif:
                marquer_acceptation_cloud()
                self.label_message_3.configure(
                    text="Sauvegarde cloud en cours...",
                    text_color="#3498db",
                )
                self.update()
                try:
                    ok_bk, msg_bk = sauvegarder_dans_cloud()
                    print(f"[BACKUP] {msg_bk}")
                except Exception as e:
                    print(f"[BACKUP] Ignore : {e}")
        except Exception as e:
            print(f"[BACKUP] Erreur activation cloud : {e}")

        try:
            envoyer_confirmation_activation(
                self.email_client,
                nom_ecole,
                self.cle_utilisee,
                infos,
            )
        except Exception:
            pass

        self.activation_reussie = True
        self.after(500, self._finaliser)

    def _finaliser(self):
        messagebox.showinfo(
            "Bienvenue",
            f"Activation reussie !\n\n"
            f"Bienvenue {self.nom_ecole}\n\n"
            f"L'application va maintenant demarrer."
        )
        self.destroy()

    def _vider_conteneur(self):
        for w in self.conteneur.winfo_children():
            w.destroy()

    def _quitter(self):
        self.activation_reussie = False
        self.destroy()