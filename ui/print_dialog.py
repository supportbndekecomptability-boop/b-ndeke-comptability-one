"""
Boite de dialogue d'impression personnalisee
"""
import os
import platform
import subprocess
import customtkinter as ctk
from tkinter import messagebox

try:
    import win32print
    import win32ui
    from PIL import Image, ImageWin
    WIN32PRINT_OK = True
except ImportError:
    WIN32PRINT_OK = False

try:
    import fitz  # PyMuPDF
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

from config import COLOR_NAVY, COLOR_GOLD


class PrintDialog(ctk.CTkToplevel):
    """Boite de dialogue d'impression style Word"""

    def __init__(self, parent, chemin_pdf, nb_pages=1, page_actuelle=1):
        super().__init__(parent)

        self.chemin_pdf = chemin_pdf
        self.nb_pages = nb_pages
        self.page_actuelle = page_actuelle
        self.resultat = None  # None = annule, sinon dict de parametres

        self.title("Imprimer")
        largeur = 520
        hauteur = 620
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#F5F7FB")
        self.resizable(False, False)

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(30, (self.winfo_screenheight() // 2) - (hauteur // 2))
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self._annuler())

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
        card = ctk.CTkFrame(self, fg_color="white", corner_radius=15)
        card.pack(fill="both", expand=True, padx=15, pady=15)

        # Titre
        ctk.CTkLabel(
            card, text="Imprimer",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_NAVY,
        ).pack(pady=(20, 5), padx=20, anchor="w")

        ctk.CTkFrame(card, fg_color="#e0e0e0", height=1).pack(fill="x", padx=20, pady=(5, 15))

        # Zone scrollable pour le contenu
        zone = ctk.CTkScrollableFrame(card, fg_color="transparent", corner_radius=0)
        zone.pack(fill="both", expand=True, padx=5, pady=5)

        # ===== 1. IMPRIMANTE =====
        ctk.CTkLabel(
            zone, text="Imprimante",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
            anchor="w",
        ).pack(padx=15, pady=(10, 5), fill="x")

        imprimantes = self._get_imprimantes()

        if not imprimantes:
            ctk.CTkLabel(
                zone,
                text="Aucune imprimante detectee.\n\n"
                     "Installez une imprimante dans Windows\n"
                     "(Panneau de configuration > Peripheriques > Imprimantes)",
                font=("Segoe UI", 11),
                text_color="#e74c3c",
                justify="left",
            ).pack(padx=15, pady=10, anchor="w")

            ctk.CTkButton(
                card,
                text="Fermer",
                font=("Segoe UI", 13, "bold"),
                fg_color="#e74c3c",
                hover_color="#c0392b",
                height=42,
                command=self._annuler,
            ).pack(padx=20, pady=(5, 20), fill="x")
            return

        self.combo_imprimante = ctk.CTkComboBox(
            zone,
            values=imprimantes,
            font=("Segoe UI", 11),
            height=38,
        )

        # Imprimante par defaut
        try:
            defaut = win32print.GetDefaultPrinter()
        except Exception:
            defaut = imprimantes[0]

        self.combo_imprimante.set(defaut if defaut in imprimantes else imprimantes[0])
        self.combo_imprimante.pack(padx=15, pady=(0, 10), fill="x")

        # ===== 2. NOMBRE DE COPIES =====
        ctk.CTkLabel(
            zone, text="Nombre de copies",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
            anchor="w",
        ).pack(padx=15, pady=(10, 5), fill="x")

        ligne_copies = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_copies.pack(padx=15, pady=(0, 10), fill="x")

        ctk.CTkButton(
            ligne_copies, text="-",
            font=("Segoe UI", 15, "bold"),
            width=40, height=36,
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0",
            command=lambda: self._changer_copies(-1),
        ).pack(side="left")

        self.var_copies = ctk.StringVar(value="1")

        self.entree_copies = ctk.CTkEntry(
            ligne_copies,
            textvariable=self.var_copies,
            font=("Segoe UI", 14, "bold"),
            width=80, height=36,
            justify="center",
        )
        self.entree_copies.pack(side="left", padx=5)

        ctk.CTkButton(
            ligne_copies, text="+",
            font=("Segoe UI", 15, "bold"),
            width=40, height=36,
            fg_color="#e0e0e0", text_color="#333333",
            hover_color="#c0c0c0",
            command=lambda: self._changer_copies(1),
        ).pack(side="left")

        ctk.CTkLabel(
            ligne_copies, text="  copie(s)",
            font=("Segoe UI", 11),
            text_color="#666666",
        ).pack(side="left")

        # ===== 3. PAGES =====
        ctk.CTkLabel(
            zone, text="Pages a imprimer",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
            anchor="w",
        ).pack(padx=15, pady=(10, 5), fill="x")

        self.var_pages = ctk.StringVar(value="toutes")

        ctk.CTkRadioButton(
            zone,
            text=f"Toutes les pages ({self.nb_pages} page(s))",
            variable=self.var_pages,
            value="toutes",
            font=("Segoe UI", 11),
            radiobutton_width=18,
            radiobutton_height=18,
        ).pack(padx=20, pady=3, anchor="w")

        ctk.CTkRadioButton(
            zone,
            text=f"Page actuelle (page {self.page_actuelle})",
            variable=self.var_pages,
            value="actuelle",
            font=("Segoe UI", 11),
            radiobutton_width=18,
            radiobutton_height=18,
        ).pack(padx=20, pady=3, anchor="w")

        ligne_plage = ctk.CTkFrame(zone, fg_color="transparent")
        ligne_plage.pack(padx=20, pady=3, anchor="w", fill="x")

        ctk.CTkRadioButton(
            ligne_plage,
            text="Plage :",
            variable=self.var_pages,
            value="plage",
            font=("Segoe UI", 11),
            radiobutton_width=18,
            radiobutton_height=18,
        ).pack(side="left")

        self.entree_debut = ctk.CTkEntry(
            ligne_plage,
            font=("Segoe UI", 11),
            width=50, height=30,
            placeholder_text="1",
            justify="center",
        )
        self.entree_debut.pack(side="left", padx=(10, 3))

        ctk.CTkLabel(
            ligne_plage, text="a",
            font=("Segoe UI", 11),
        ).pack(side="left")

        self.entree_fin = ctk.CTkEntry(
            ligne_plage,
            font=("Segoe UI", 11),
            width=50, height=30,
            placeholder_text=str(self.nb_pages),
            justify="center",
        )
        self.entree_fin.pack(side="left", padx=(3, 0))

        # ===== 4. OPTIONS =====
        ctk.CTkLabel(
            zone, text="Options",
            font=("Segoe UI", 12, "bold"),
            text_color=COLOR_NAVY,
            anchor="w",
        ).pack(padx=15, pady=(15, 5), fill="x")

        self.var_couleur = ctk.StringVar(value="couleur")

        ctk.CTkRadioButton(
            zone,
            text="Noir et blanc",
            variable=self.var_couleur,
            value="nb",
            font=("Segoe UI", 11),
            radiobutton_width=18,
            radiobutton_height=18,
        ).pack(padx=20, pady=3, anchor="w")

        ctk.CTkRadioButton(
            zone,
            text="Couleur (si supporte)",
            variable=self.var_couleur,
            value="couleur",
            font=("Segoe UI", 11),
            radiobutton_width=18,
            radiobutton_height=18,
        ).pack(padx=20, pady=3, anchor="w")

        # ===== INFO =====
        info = ctk.CTkFrame(zone, fg_color="#F0F7FF", corner_radius=8)
        info.pack(fill="x", padx=15, pady=(15, 10))

        ctk.CTkLabel(
            info,
            text="L'impression envoie directement le rapport a l'imprimante.\n"
                 "Assurez-vous que l'imprimante est allumee et connectee.",
            font=("Segoe UI", 10),
            text_color="#555555",
            justify="left",
        ).pack(padx=12, pady=10, anchor="w")

        # ===== BOUTONS =====
        boutons = ctk.CTkFrame(card, fg_color="transparent")
        boutons.pack(fill="x", padx=20, pady=(5, 15))

        ctk.CTkButton(
            boutons,
            text="Annuler",
            font=("Segoe UI", 13),
            fg_color="#e0e0e0",
            text_color="#333333",
            hover_color="#c0c0c0",
            height=44,
            width=130,
            command=self._annuler,
        ).pack(side="left", padx=(0, 5))

        ctk.CTkButton(
            boutons,
            text="IMPRIMER",
            font=("Segoe UI", 13, "bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            height=44,
            command=self._imprimer,
        ).pack(side="right", padx=(5, 0))

    # ================== HELPERS ==================
    def _get_imprimantes(self):
        """Liste toutes les imprimantes installees"""
        if not WIN32PRINT_OK:
            return []
        try:
            imprimantes = [
                p[2] for p in win32print.EnumPrinters(
                    win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
                )
            ]
            return sorted(set(imprimantes))
        except Exception as e:
            print(f"[Erreur enum imprimantes] {e}")
            return []

    def _changer_copies(self, delta):
        try:
            val = int(self.var_copies.get())
        except ValueError:
            val = 1
        val = max(1, min(99, val + delta))
        self.var_copies.set(str(val))

    # ================== ACTIONS ==================
    def _annuler(self):
        self.resultat = None
        self.destroy()

    def _imprimer(self):
        # Recuperer les parametres
        imprimante = self.combo_imprimante.get().strip()

        if not imprimante:
            messagebox.showerror("Erreur", "Veuillez selectionner une imprimante.")
            return

        try:
            copies = int(self.var_copies.get())
            if copies < 1 or copies > 99:
                raise ValueError()
        except ValueError:
            messagebox.showerror("Erreur", "Le nombre de copies doit etre entre 1 et 99.")
            return

        # Determiner les pages
        mode_pages = self.var_pages.get()
        pages = []

        if mode_pages == "toutes":
            pages = list(range(1, self.nb_pages + 1))
        elif mode_pages == "actuelle":
            pages = [self.page_actuelle]
        elif mode_pages == "plage":
            try:
                debut = int(self.entree_debut.get().strip() or "1")
                fin = int(self.entree_fin.get().strip() or str(self.nb_pages))
                if debut < 1 or fin > self.nb_pages or debut > fin:
                    raise ValueError()
                pages = list(range(debut, fin + 1))
            except ValueError:
                messagebox.showerror(
                    "Erreur",
                    f"Plage invalide.\n\n"
                    f"Entrez des numeros entre 1 et {self.nb_pages}."
                )
                return

        couleur = self.var_couleur.get() == "couleur"

        # Lancer l'impression
        self._executer_impression(imprimante, copies, pages, couleur)

    def _executer_impression(self, imprimante, copies, pages, couleur):
        """Execute l'impression reel"""
        if not WIN32PRINT_OK:
            messagebox.showerror(
                "Erreur",
                "Le module d'impression (pywin32) n'est pas installe.\n\n"
                "Executez : python -m pip install pywin32"
            )
            return

        if not PYMUPDF_OK:
            messagebox.showerror("Erreur", "PyMuPDF n'est pas installe.")
            return

        # Desactiver le bouton pour eviter double-clic
        self.update()

        try:
            doc = fitz.open(self.chemin_pdf)

            # Creer le contexte d'impression
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(imprimante)

            # Dimensions imprimante
            printer_width = hDC.GetDeviceCaps(110)   # HORZRES
            printer_height = hDC.GetDeviceCaps(111)  # VERTRES

            hDC.StartDoc(os.path.basename(self.chemin_pdf))

            # Pour chaque copie
            for copie in range(copies):
                # Pour chaque page
                for page_num in pages:
                    page = doc[page_num - 1]

                    # Rendu haute resolution
                    mat = fitz.Matrix(3.0, 3.0)
                    pix = page.get_pixmap(matrix=mat, alpha=False)

                    from io import BytesIO
                    img = Image.open(BytesIO(pix.tobytes("ppm")))

                    # Convertir en noir et blanc si demande
                    if not couleur:
                        img = img.convert("L").convert("RGB")

                    hDC.StartPage()

                    img_width, img_height = img.size
                    ratio = min(printer_width / img_width,
                                printer_height / img_height)
                    new_width = int(img_width * ratio)
                    new_height = int(img_height * ratio)

                    x_offset = (printer_width - new_width) // 2
                    y_offset = (printer_height - new_height) // 2

                    dib = ImageWin.Dib(img)
                    dib.draw(
                        hDC.GetHandleOutput(),
                        (x_offset, y_offset,
                         x_offset + new_width, y_offset + new_height)
                    )

                    hDC.EndPage()

            hDC.EndDoc()
            hDC.DeleteDC()
            doc.close()

            total_pages = len(pages) * copies

            messagebox.showinfo(
                "Impression envoyee",
                f"Rapport envoye a l'imprimante :\n\n"
                f"{imprimante}\n\n"
                f"{len(pages)} page(s) x {copies} copie(s) = {total_pages} page(s) imprimee(s)"
            )

            self.resultat = {
                "imprimante": imprimante,
                "copies": copies,
                "pages": pages,
                "couleur": couleur,
            }
            self.destroy()

        except Exception as e:
            import traceback
            traceback.print_exc()
            messagebox.showerror(
                "Erreur d'impression",
                f"Impossible d'imprimer :\n\n{e}\n\n"
                f"Verifiez que l'imprimante est allumee et connectee."
            )