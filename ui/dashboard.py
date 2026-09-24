"""
Tableau de bord principal de B-NDEKE Comptability One
Avec filtrage du menu selon le role de l'utilisateur.
Fenetre adaptative a l'ecran.
+ Filtrage des modules bloques par le gestionnaire.
"""
import customtkinter as ctk
from config import APP_NAME, APP_VERSION, COLOR_NAVY, COLOR_GOLD, COLOR_BG, format_montant
from ui.classes_ui import ClassesPage
from ui.frais_ui import FraisPage
from ui.eleves_ui import ElevesPage
from ui.paiements_ui import PaiementsPage
from ui.caisse_ui import CaissePage
from ui.personnel_ui import PersonnelPage
from ui.depenses_ui import DepensesPage
from ui.rapports_ui import RapportsPage
from ui.etats_ui import EtatsPage
from ui.export_ui import ExportPage
from ui.parametres_ui import ParametresPage
from ui.recouvrement_ui import RecouvrementPage
from ui.presences_ui import PresencesPage
from ui.presences_personnel_ui import PresencesPersonnelPage
from ui.dettes_ui import DettesPage
from ui.window_utils import setup_adaptive_window
from core.paiements import (
    total_caisse_eleves_jour,
    total_caisse_eleves_mois,
    total_caisse_personnel_mois,
    total_impayes_eleves,
)
from core.eleves import compter_eleves
from core.personnel import compter_personnel
from core.depenses import total_depenses_mois, compter_depenses
from core.session import supprimer_session
from core.budgets import get_budgets, liste_budgets
from core.permissions import menus_autorises, role_label, a_permission
from core.utilisateurs import get_fonctionnalites_bloquees


class DashboardWindow(ctk.CTk):
    def __init__(self, utilisateur):
        super().__init__()

        self.utilisateur = utilisateur
        self.deconnexion_demandee = False
        self.page_active = "Tableau de bord"

        self.title(f"{APP_NAME} v{APP_VERSION}")
        self.configure(fg_color=COLOR_BG)

        self.update_idletasks()
        setup_adaptive_window(
            self,
            largeur_max=1200,
            hauteur_max=700,
            marge_largeur=20,
            marge_hauteur=80,
            resizable=True,
        )

        self._construire_interface()

    def _construire_interface(self):
        # ===== SIDEBAR =====
        sidebar = ctk.CTkFrame(self, width=220, fg_color=COLOR_NAVY, corner_radius=0)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # --- En-tete fixe (titre) ---
        ctk.CTkLabel(
            sidebar, text="B-NDEKE",
            font=("Segoe UI", 20, "bold"),
            text_color="white",
        ).pack(pady=(20, 0))

        ctk.CTkLabel(
            sidebar, text="Comptability One",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_GOLD,
        ).pack(pady=(0, 5))

        # --- Pied fixe (role + utilisateur) ---
        ctk.CTkLabel(
            sidebar,
            text=role_label(self.utilisateur.get("role", "caissier")).upper(),
            font=("Segoe UI", 9),
            text_color=COLOR_GOLD,
        ).pack(side="bottom", pady=(0, 12))

        ctk.CTkLabel(
            sidebar, text=f"{self.utilisateur['nom_complet']}",
            font=("Segoe UI", 11, "bold"),
            text_color="white",
        ).pack(side="bottom", pady=(0, 3))

        # --- Zone scrollable pour les menus ---
        menu_scroll = ctk.CTkScrollableFrame(
            sidebar,
            fg_color="transparent",
            corner_radius=0,
            scrollbar_button_color="#1a3d75",
            scrollbar_button_hover_color="#2a5da5",
        )
        menu_scroll.pack(fill="both", expand=True, padx=0, pady=(5, 5))

        # ===== FILTRAGE DU MENU SELON LE ROLE =====
        tous_les_menus = [
            "Tableau de bord",
            "Classes",
            "Frais",
            "Eleves",
            "Paiements",
            "Caisse",
            "Depenses",
            "Personnel",
            "Presences",
            "Presences personnel",
            "Dettes",
            "Bulletins",
            "Recouvrement",
            "Rapports",
            "Etats financiers",
            "Export Excel",
            "Parametres",
        ]
        menus_ok = menus_autorises(self.utilisateur)
        menu_items = [m for m in tous_les_menus if m in menus_ok]

        # ===== FILTRAGE DES MODULES BLOQUES PAR LE GESTIONNAIRE =====
        user_id = self.utilisateur.get("id")
        bloques = get_fonctionnalites_bloquees(user_id)
        if bloques:
            menu_items = [m for m in menu_items if m not in bloques]
            print(f"[DASHBOARD] Modules bloques pour {self.utilisateur.get('email')}: {bloques}")

        # Badge : nombre de modules accessibles
        ctk.CTkLabel(
            menu_scroll,
            text=f"{len(menu_items)} module(s) accessible(s)",
            font=("Segoe UI", 9),
            text_color="#9aa4b2",
        ).pack(pady=(5, 10))

        self.boutons_menu = {}
        for texte in menu_items:
            btn = ctk.CTkButton(
                menu_scroll,
                text=f"  {texte}",
                font=("Segoe UI", 12),
                anchor="w",
                fg_color="transparent",
                hover_color="#1a3d75",
                height=32,
                corner_radius=6,
                command=lambda t=texte: self._changer_page(t),
            )
            btn.pack(padx=8, pady=1, fill="x")
            self.boutons_menu[texte] = btn

        self._mettre_a_jour_menu()

        # ===== ZONE PRINCIPALE =====
        zone = ctk.CTkFrame(self, fg_color=COLOR_BG, corner_radius=0)
        zone.pack(side="right", fill="both", expand=True)

        topbar = ctk.CTkFrame(zone, height=60, fg_color="white", corner_radius=0)
        topbar.pack(fill="x")
        topbar.pack_propagate(False)

        self.label_titre_page = ctk.CTkLabel(
            topbar, text=menu_items[0] if menu_items else "Tableau de bord",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_NAVY,
        )
        self.label_titre_page.pack(side="left", padx=25, pady=15)

        ctk.CTkButton(
            topbar, text="Se deconnecter",
            font=("Segoe UI", 11),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            height=32,
            command=self._se_deconnecter,
        ).pack(side="right", padx=25, pady=15)

        self.contenu = ctk.CTkFrame(zone, fg_color="transparent")
        self.contenu.pack(fill="both", expand=True, padx=25, pady=25)

        if menu_items:
            premiere_page = menu_items[0]
            self.page_active = premiere_page
            self.label_titre_page.configure(text=premiere_page)
            self._mettre_a_jour_menu()
            self._afficher_page(premiere_page)
        else:
            # Cas extreme : aucun module accessible
            ctk.CTkLabel(
                self.contenu,
                text="ACCES LIMITE",
                font=("Segoe UI", 20, "bold"),
                text_color="#e74c3c",
            ).pack(pady=(40, 10))
            ctk.CTkLabel(
                self.contenu,
                text="Tous vos modules ont ete bloques par le gestionnaire.\n"
                     "Contactez l'administration.",
                font=("Segoe UI", 13),
                text_color="#666666",
                justify="center",
            ).pack(pady=10)

    # ================== NAVIGATION ==================
    def _changer_page(self, nom_page):
        self.page_active = nom_page
        self.label_titre_page.configure(text=nom_page)
        self._mettre_a_jour_menu()
        self._afficher_page(nom_page)

    def _mettre_a_jour_menu(self):
        for texte, btn in self.boutons_menu.items():
            if texte == self.page_active:
                btn.configure(fg_color="#1a3d75")
            else:
                btn.configure(fg_color="transparent")

    def _vider_contenu(self):
        for widget in self.contenu.winfo_children():
            widget.destroy()

    def _afficher_page(self, nom_page):
        self._vider_contenu()

        if nom_page not in self.boutons_menu and nom_page != "Tableau de bord":
            ctk.CTkLabel(
                self.contenu,
                text=f"Acces refuse au module : {nom_page}",
                font=("Segoe UI", 16, "bold"),
                text_color="#e74c3c",
            ).pack(pady=40)
            return

        if nom_page == "Tableau de bord":
            self._page_tableau_de_bord()
        elif nom_page == "Classes":
            try:
                page = ClassesPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Frais":
            try:
                page = FraisPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Eleves":
            try:
                page = ElevesPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Paiements":
            try:
                page = PaiementsPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Caisse":
            try:
                page = CaissePage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Depenses":
            try:
                page = DepensesPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Personnel":
            try:
                page = PersonnelPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Presences":
            try:
                page = PresencesPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Presences personnel":
            try:
                page = PresencesPersonnelPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Dettes":
            try:
                page = DettesPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Bulletins":
            try:
                from ui.bulletins_ui import BulletinsPage
                page = BulletinsPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except ImportError:
                self._page_placeholder("Bulletins")
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Recouvrement":
            try:
                page = RecouvrementPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Rapports":
            try:
                page = RapportsPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Etats financiers":
            try:
                page = EtatsPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Export Excel":
            try:
                page = ExportPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        elif nom_page == "Parametres":
            try:
                page = ParametresPage(self.contenu, utilisateur=self.utilisateur)
                page.pack(fill="both", expand=True)
            except Exception as e:
                import traceback
                traceback.print_exc()
                ctk.CTkLabel(self.contenu, text=f"Erreur : {e}",
                             font=("Segoe UI", 14), text_color="red").pack(pady=20)
        else:
            self._page_placeholder(nom_page)

    # ================== PAGES ==================
    def _page_tableau_de_bord(self):
        scroll = ctk.CTkScrollableFrame(self.contenu, fg_color="transparent")
        scroll.pack(fill="both", expand=True)

        ctk.CTkLabel(
            scroll,
            text=f"Bienvenue, {self.utilisateur['nom_complet']} !",
            font=("Segoe UI", 22, "bold"),
            text_color=COLOR_NAVY,
        ).pack(anchor="w", pady=(0, 8))

        ctk.CTkLabel(
            scroll,
            text=f"Role : {role_label(self.utilisateur.get('role', 'caissier'))}",
            font=("Segoe UI", 12),
            text_color="#666666",
        ).pack(anchor="w", pady=(0, 20))

        try:
            recettes_jour = total_caisse_eleves_jour()
        except Exception:
            recettes_jour = 0
        try:
            impayes = total_impayes_eleves()
        except Exception:
            impayes = 0
        try:
            nb_eleves = compter_eleves()
        except Exception:
            nb_eleves = 0
        try:
            depenses_personnel_mois = total_caisse_personnel_mois()
        except Exception:
            depenses_personnel_mois = 0
        try:
            depenses_generales_mois = total_depenses_mois()
        except Exception:
            depenses_generales_mois = 0
        try:
            nb_personnel = compter_personnel()
        except Exception:
            nb_personnel = 0
        try:
            recettes_mois = total_caisse_eleves_mois()
        except Exception:
            recettes_mois = 0
        try:
            nb_depenses = compter_depenses()
        except Exception:
            nb_depenses = 0

        depenses_mois_total = depenses_personnel_mois + depenses_generales_mois
        benefice = recettes_mois - depenses_mois_total
        couleur_benefice = "#27ae60" if benefice >= 0 else "#e74c3c"

        cartes = ctk.CTkFrame(scroll, fg_color="transparent")
        cartes.pack(fill="x", pady=8)

        for titre, valeur, couleur, sous_titre in [
            ("Recettes du jour", format_montant(recettes_jour), "#27ae60",
             "Encaissements eleves"),
            ("Impayes", format_montant(impayes), "#e74c3c",
             "Solde total a recouvrer"),
            ("Eleves inscrits", str(nb_eleves), COLOR_NAVY,
             "Total actifs"),
            ("Depenses du mois", format_montant(depenses_mois_total), "#e67e22",
             f"Personnel + {nb_depenses} depense(s)"),
        ]:
            carte = ctk.CTkFrame(cartes, fg_color="white", corner_radius=12)
            carte.pack(side="left", expand=True, fill="both", padx=6)

            ctk.CTkLabel(carte, text=titre,
                         font=("Segoe UI", 11, "bold"), text_color="#888888").pack(pady=(18, 5))
            ctk.CTkLabel(carte, text=valeur,
                         font=("Segoe UI", 20, "bold"), text_color=couleur).pack(pady=(0, 3))
            ctk.CTkLabel(carte, text=sous_titre,
                         font=("Segoe UI", 9), text_color="#aaaaaa").pack(pady=(0, 15))

        cartes2 = ctk.CTkFrame(scroll, fg_color="transparent")
        cartes2.pack(fill="x", pady=(12, 10))

        for titre, valeur, couleur, sous_titre in [
            ("Personnel actif", str(nb_personnel), "#8e44ad",
             "Enseignants et staff"),
            ("Recettes du mois", format_montant(recettes_mois), "#16a085",
             "Encaissements eleves"),
            ("Benefice estime", format_montant(benefice), couleur_benefice,
             "Recettes - Depenses totales"),
        ]:
            carte = ctk.CTkFrame(cartes2, fg_color="white", corner_radius=12)
            carte.pack(side="left", expand=True, fill="both", padx=6)

            ctk.CTkLabel(carte, text=titre,
                         font=("Segoe UI", 11, "bold"), text_color="#888888").pack(pady=(18, 5))
            ctk.CTkLabel(carte, text=valeur,
                         font=("Segoe UI", 20, "bold"), text_color=couleur).pack(pady=(0, 3))
            ctk.CTkLabel(carte, text=sous_titre,
                         font=("Segoe UI", 9), text_color="#aaaaaa").pack(pady=(0, 15))

        if "Parametres" in self.boutons_menu or "Etats financiers" in self.boutons_menu:
            self._afficher_budgets(scroll)

    def _afficher_budgets(self, parent):
        try:
            data = get_budgets()
        except Exception as e:
            print(f"[DASHBOARD] Erreur budgets : {e}")
            return

        total = data.get("budget_total_annuel", 0) or 0

        ligne_titre = ctk.CTkFrame(parent, fg_color="transparent")
        ligne_titre.pack(fill="x", pady=(20, 8))

        ctk.CTkLabel(
            ligne_titre,
            text="Repartition budgetaire",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_NAVY,
        ).pack(side="left")

        if total > 0:
            ctk.CTkLabel(
                ligne_titre,
                text=f"Budget annuel : {format_montant(total)}",
                font=("Segoe UI", 12, "bold"),
                text_color="#666666",
            ).pack(side="right")

        cartes_b = ctk.CTkFrame(parent, fg_color="transparent")
        cartes_b.pack(fill="x", pady=(0, 15))

        for key, label, couleur in liste_budgets():
            b = data.get(key, {})
            pct = b.get("pourcentage", 0)
            montant = b.get("montant", 0)

            carte = ctk.CTkFrame(cartes_b, fg_color="white", corner_radius=12,
                                 border_width=2, border_color=couleur)
            carte.pack(side="left", expand=True, fill="both", padx=6)

            ctk.CTkLabel(
                carte, text=label,
                font=("Segoe UI", 12, "bold"),
                text_color=couleur,
            ).pack(pady=(18, 5))

            ctk.CTkLabel(
                carte, text=f"{int(pct)}%",
                font=("Segoe UI", 10),
                text_color="#888888",
            ).pack()

            ctk.CTkLabel(
                carte, text=format_montant(montant),
                font=("Segoe UI", 18, "bold"),
                text_color=couleur,
            ).pack(pady=(5, 8))

            nb_sous = len(b.get("sous_categories", {}))
            ctk.CTkLabel(
                carte, text=f"{nb_sous} sous-categorie(s)",
                font=("Segoe UI", 9),
                text_color="#aaaaaa",
            ).pack(pady=(0, 15))

        if total > 0:
            ctk.CTkButton(
                parent,
                text="Voir le detail des budgets",
                font=("Segoe UI", 11),
                fg_color="#e0e0e0", text_color="#333333",
                hover_color="#c0c0c0",
                height=34,
                command=lambda: self._changer_page("Parametres"),
            ).pack(anchor="e", pady=(0, 10))
        else:
            cadre_vide = ctk.CTkFrame(parent, fg_color="#FFF7E0", corner_radius=8)
            cadre_vide.pack(fill="x", pady=(0, 10))

            ctk.CTkLabel(
                cadre_vide,
                text=(
                    "Aucun budget n'a encore ete configure. "
                    "Allez dans Parametres > Budgets pour definir votre budget annuel."
                ),
                font=("Segoe UI", 10),
                text_color="#8B6914",
                justify="left",
            ).pack(padx=15, pady=10, anchor="w")

            ctk.CTkButton(
                parent,
                text="Configurer le budget",
                font=("Segoe UI", 11, "bold"),
                fg_color=COLOR_NAVY, hover_color="#1a3d75",
                height=34,
                command=lambda: self._changer_page("Parametres"),
            ).pack(anchor="e", pady=(0, 10))

    def _page_placeholder(self, nom_page):
        ctk.CTkLabel(self.contenu, text=f"{nom_page}",
                     font=("Segoe UI", 26, "bold"),
                     text_color=COLOR_NAVY).pack(anchor="w", pady=(20, 10))
        ctk.CTkLabel(self.contenu,
                     text="Ce module est en cours de developpement.",
                     font=("Segoe UI", 14), text_color="#888888").pack(anchor="w")

    def _se_deconnecter(self):
        self.deconnexion_demande = True
        supprimer_session()
        self.destroy()