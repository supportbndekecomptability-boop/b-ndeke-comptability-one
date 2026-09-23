"""
Ecran d'activation de la licence - 3 etapes
"""
import customtkinter as ctk
from tkinter import messagebox
from config import (
    COLOR_NAVY, COLOR_GOLD, APP_NAME, APP_VERSION,
    VENDEUR_EMAIL,
)
from core.licence import (
    verifier_cle, enregistrer_licence, enregistrer_date_activation,
    envoyer_demande_code, envoyer_confirmation_activation,
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
        largeur = 640
        hauteur = 700
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(10, (self.winfo_screenheight() // 2) - (hauteur // 2))
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self._quitter())

        self.conteneur = ctk.CTkFrame(self, fg_color="transparent")
        self.conteneur.pack(fill="both", expand=True)

        self._afficher_etape_1()

    # =========================================================
    # ETAPE 1
    # =========================================================
    def _afficher_etape_1(self):
        self._vider_conteneur()

        card = ctk.CTkFrame(self.conteneur, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card, text="B-NDEKE",
            font=("Segoe UI", 30, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(25, 0))

        ctk.CTkLabel(
            card, text="Comptability One",
            font=("Segoe UI", 15, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 3))

        ctk.CTkLabel(
            card, text=f"Version {APP_VERSION}",
            font=("Segoe UI", 10),
            text_color="#999999",
        ).pack(pady=(0, 12))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).pack(fill="x", padx=40, pady=5)

        ctk.CTkLabel(
            card, text="ETAPE 1 : DEMANDE DE CODE",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(12, 5))

        ctk.CTkLabel(
            card,
            text="Entrez votre adresse email pour demander votre code",
            font=("Segoe UI", 11),
            text_color="#666666",
        ).pack(pady=(0, 15))

        ctk.CTkLabel(
            card, text="Votre adresse email",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=50, pady=(0, 5), fill="x")

        self.entree_email = ctk.CTkEntry(
            card,
            font=("Segoe UI", 13),
            height=42,
            placeholder_text="exemple@ecole.com",
        )
        self.entree_email.pack(padx=50, pady=(0, 10), fill="x")
        self.entree_email.bind("<Return>", lambda e: self._envoyer_demande())

        ctk.CTkButton(
            card,
            text="DEMANDER LE CODE",
            font=("Segoe UI", 14, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=48,
            command=self._envoyer_demande,
        ).pack(padx=50, pady=(5, 15), fill="x")

        self.label_message_1 = ctk.CTkLabel(
            card, text="",
            font=("Segoe UI", 11),
            text_color="#666666",
            wraplength=520,
            justify="left",
        )
        self.label_message_1.pack(padx=50, pady=(0, 10))

        # ===== SECTION CONTACT EMAIL UNIQUEMENT =====
        contact_frame = ctk.CTkFrame(card, fg_color="#F0F7FF", corner_radius=10)
        contact_frame.pack(fill="x", padx=50, pady=(5, 10))

        ctk.CTkLabel(
            contact_frame,
            text="Si vous ne recevez rien, contactez-nous par email :",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_NAVY,
        ).pack(padx=15, pady=(12, 6), anchor="w")

        ligne_email = ctk.CTkFrame(contact_frame, fg_color="transparent")
        ligne_email.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(
            ligne_email,
            text="Email :",
            font=("Segoe UI", 11, "bold"),
            text_color="#333333",
            width=60,
            anchor="w",
        ).pack(side="left")

        self.champ_email_contact = ctk.CTkEntry(
            ligne_email,
            font=("Consolas", 12),
            height=32,
            fg_color="white",
            text_color="#0066CC",
        )
        self.champ_email_contact.pack(side="left", fill="x", expand=True, padx=(5, 0))
        self.champ_email_contact.insert(0, VENDEUR_EMAIL)
        self.champ_email_contact.configure(state="readonly")

        ctk.CTkButton(
            contact_frame,
            text="Copier l'adresse email",
            font=("Segoe UI", 11, "bold"),
            fg_color="#3498db",
            hover_color="#2980b9",
            height=34,
            command=self._copier_email,
        ).pack(padx=15, pady=(0, 12), fill="x")

        ctk.CTkButton(
            card,
            text="Quitter",
            font=("Segoe UI", 11),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            height=30,
            command=self._quitter,
        ).pack(padx=50, pady=(5, 20), fill="x")

        self.after(300, lambda: self.entree_email.focus_set())

    def _copier_email(self):
        try:
            self.clipboard_clear()
            self.clipboard_append(VENDEUR_EMAIL)
            self.update()
            self.label_message_1.configure(
                text="Adresse email copiee ! Collez-la dans votre messagerie.",
                text_color="#27ae60",
            )
        except Exception:
            pass

    def _envoyer_demande(self):
        email = self.entree_email.get().strip()

        if not email or "@" not in email or "." not in email:
            self.label_message_1.configure(
                text="Veuillez saisir une adresse email valide.",
                text_color="#e74c3c",
            )
            return

        self.email_client = email

        self.label_message_1.configure(
            text="Envoi de la demande en cours...",
            text_color="#3498db",
        )
        self.update()

        try:
            ok, msg = envoyer_demande_code(email)
        except Exception:
            ok = False

        if ok:
            self.label_message_1.configure(
                text="Demande envoyee. Vous recevrez votre code par email.",
                text_color="#27ae60",
            )
            self.after(900, self._afficher_etape_2)
        else:
            self.label_message_1.configure(
                text="Cliquez sur 'Copier l'adresse email' et envoyez-nous\n"
                     "un message directement.",
                text_color="#e67e22",
            )
            self.after(900, self._afficher_etape_2)

    # =========================================================
    # ETAPE 2
    # =========================================================
    def _afficher_etape_2(self):
        self._vider_conteneur()

        card = ctk.CTkFrame(self.conteneur, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card, text="B-NDEKE",
            font=("Segoe UI", 30, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(25, 0))

        ctk.CTkLabel(
            card, text="Comptability One",
            font=("Segoe UI", 15, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 12))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).pack(fill="x", padx=40, pady=5)

        ctk.CTkLabel(
            card, text="ETAPE 2 : ACTIVATION",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(12, 5))

        ctk.CTkLabel(
            card,
            text="Collez ici la cle d'activation recue",
            font=("Segoe UI", 11),
            text_color="#666666",
        ).pack(pady=(0, 15))

        info_email = ctk.CTkFrame(card, fg_color="#F0FFF4", corner_radius=8)
        info_email.pack(fill="x", padx=50, pady=(0, 15))

        ctk.CTkLabel(
            info_email,
            text=f"Demande envoyee depuis : {self.email_client}",
            font=("Segoe UI", 10),
            text_color="#2d7a2d",
        ).pack(padx=15, pady=8)

        ctk.CTkLabel(
            card, text="Cle d'activation",
            font=("Segoe UI", 12, "bold"),
            text_color="#333333",
            anchor="w",
        ).pack(padx=50, pady=(0, 5), fill="x")

        self.entree_cle = ctk.CTkEntry(
            card,
            font=("Consolas", 14, "bold"),
            height=46,
            placeholder_text="BNDEKE-XXXXX-YYYYMMDD-XXXXXXXX",
        )
        self.entree_cle.pack(padx=50, pady=(0, 10), fill="x")
        self.entree_cle.bind("<Return>", lambda e: self._activer_cle())

        self.label_message_2 = ctk.CTkLabel(
            card, text="",
            font=("Segoe UI", 11),
            text_color="#666666",
            wraplength=520,
            justify="left",
        )
        self.label_message_2.pack(padx=50, pady=(0, 15))

        ctk.CTkButton(
            card,
            text="ACTIVER",
            font=("Segoe UI", 14, "bold"),
            fg_color=COLOR_NAVY,
            hover_color="#1a3d75",
            height=48,
            command=self._activer_cle,
        ).pack(padx=50, pady=(5, 15), fill="x")

        ctk.CTkButton(
            card,
            text="Retour",
            font=("Segoe UI", 11),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            height=30,
            command=self._afficher_etape_1,
        ).pack(padx=50, pady=(0, 20), fill="x")

        self.after(300, lambda: self.entree_cle.focus_set())

    def _activer_cle(self):
        cle = self.entree_cle.get().strip().upper()

        if not cle:
            self.label_message_2.configure(
                text="Veuillez coller votre cle d'activation.",
                text_color="#e74c3c",
            )
            return

        ok, message, info = verifier_cle(cle)

        if ok:
            self.cle_utilisee = cle
            enregistrer_licence(cle)
            enregistrer_date_activation()

            self.label_message_2.configure(text=message, text_color="#27ae60")
            self.update()

            self.after(800, self._afficher_etape_3)
        else:
            self.label_message_2.configure(text=message, text_color="#e74c3c")

    # =========================================================
    # ETAPE 3
    # =========================================================
    def _afficher_etape_3(self):
        self._vider_conteneur()

        card = ctk.CTkFrame(self.conteneur, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            card, text="B-NDEKE",
            font=("Segoe UI", 30, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(20, 0))

        ctk.CTkLabel(
            card, text="Comptability One",
            font=("Segoe UI", 15, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 12))

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).pack(fill="x", padx=40, pady=5)

        ctk.CTkLabel(
            card, text="ETAPE 3 : INFORMATIONS DE L'ECOLE",
            font=("Segoe UI", 14, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(12, 5))

        ctk.CTkLabel(
            card,
            text="Remplissez les informations de votre etablissement",
            font=("Segoe UI", 11),
            text_color="#666666",
        ).pack(pady=(0, 12))

        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=20, pady=5)

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
            placeholder="Ex: M. Jean KABILA"
        )

        self.label_message_3 = ctk.CTkLabel(
            card, text="",
            font=("Segoe UI", 11),
            text_color="#666666",
            wraplength=520,
            justify="left",
        )
        self.label_message_3.pack(padx=50, pady=(5, 10))

        ctk.CTkButton(
            card,
            text="TERMINER",
            font=("Segoe UI", 14, "bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            height=48,
            command=self._terminer,
        ).pack(padx=50, pady=(5, 20), fill="x")

        self.after(300, lambda: self.champs_ecole["nom"].focus_set())

    def _ajouter_champ(self, parent, label, placeholder="", valeur=""):
        ctk.CTkLabel(
            parent, text=label,
            font=("Segoe UI", 11, "bold"),
            text_color="#333333", anchor="w",
        ).pack(padx=10, pady=(6, 3), fill="x")

        entree = ctk.CTkEntry(
            parent,
            font=("Segoe UI", 12),
            height=38,
            placeholder_text=placeholder,
        )
        if valeur:
            entree.insert(0, valeur)
        entree.pack(padx=10, pady=(0, 5), fill="x")
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

    # =========================================================
    # OUTILS
    # =========================================================
    def _vider_conteneur(self):
        for w in self.conteneur.winfo_children():
            w.destroy()

    def _quitter(self):
        self.activation_reussie = False
        self.destroy()