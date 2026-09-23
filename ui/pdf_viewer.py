"""
Afficheur PDF integre a l'application
Avec impression directe Windows (sans lecteur PDF externe)
"""
import os
import platform
import subprocess
import customtkinter as ctk
from tkinter import messagebox
from PIL import Image, ImageTk

try:
    import fitz  # PyMuPDF
    PYMUPDF_OK = True
except ImportError:
    PYMUPDF_OK = False

try:
    import win32print
    import win32ui
    from PIL import ImageWin
    WIN32PRINT_OK = True
except ImportError:
    WIN32PRINT_OK = False

from config import COLOR_NAVY, COLOR_GOLD


class PdfViewerWindow(ctk.CTkToplevel):
    """Fenetre d'affichage du PDF integree a l'app"""

    def __init__(self, parent, chemin_pdf, titre="Apercu du rapport"):
        super().__init__(parent)

        self.chemin_pdf = chemin_pdf
        self.titre_fenetre = titre
        self.doc = None
        self.page_actuelle = 0
        self.nb_pages = 0
        self.zoom = 1.5
        self.photo = None

        if not os.path.exists(chemin_pdf):
            messagebox.showerror("Erreur", f"Fichier introuvable :\n{chemin_pdf}")
            self.destroy()
            return

        if not PYMUPDF_OK:
            messagebox.showerror(
                "Module manquant",
                "PyMuPDF n'est pas installe.\n\n"
                "Executez : python -m pip install pymupdf"
            )
            self.destroy()
            return

        try:
            self.doc = fitz.open(chemin_pdf)
            self.nb_pages = len(self.doc)
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'ouvrir le PDF :\n{e}")
            self.destroy()
            return

        self.title(titre)
        largeur = 950
        hauteur = 750
        self.geometry(f"{largeur}x{hauteur}")
        self.configure(fg_color="#E8ECEF")

        x = (self.winfo_screenwidth() // 2) - (largeur // 2)
        y = max(20, (self.winfo_screenheight() // 2) - (hauteur // 2))
        self.geometry(f"{largeur}x{hauteur}+{x}+{y}")

        self.bind("<Escape>", lambda e: self.destroy())

        self._construire_interface()
        self._afficher_page()

        self.after(100, self._activer_grab)

    def _activer_grab(self):
        try:
            self.transient(self.master)
            self.focus_force()
        except Exception:
            pass

    def _construire_interface(self):
        # ===== BARRE D'OUTILS =====
        toolbar = ctk.CTkFrame(self, height=60, fg_color=COLOR_NAVY, corner_radius=0)
        toolbar.pack(fill="x", side="top")
        toolbar.pack_propagate(False)

        ctk.CTkLabel(
            toolbar,
            text=self.titre_fenetre,
            font=("Segoe UI", 14, "bold"),
            text_color="white",
        ).pack(side="left", padx=15)

        ctk.CTkButton(
            toolbar, text="◀",
            font=("Segoe UI", 14, "bold"),
            width=40, height=34,
            fg_color="#1a3d75", hover_color="#2a5d95",
            command=self._page_precedente,
        ).pack(side="left", padx=3)

        self.label_page = ctk.CTkLabel(
            toolbar,
            text=f"Page 1 / {self.nb_pages}",
            font=("Segoe UI", 12, "bold"),
            text_color="white",
            width=110,
        )
        self.label_page.pack(side="left", padx=5)

        ctk.CTkButton(
            toolbar, text="▶",
            font=("Segoe UI", 14, "bold"),
            width=40, height=34,
            fg_color="#1a3d75", hover_color="#2a5d95",
            command=self._page_suivante,
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            toolbar, text="-",
            font=("Segoe UI", 16, "bold"),
            width=40, height=34,
            fg_color="#1a3d75", hover_color="#2a5d95",
            command=self._zoom_moins,
        ).pack(side="left", padx=(15, 3))

        self.label_zoom = ctk.CTkLabel(
            toolbar,
            text=f"{int(self.zoom * 100)}%",
            font=("Segoe UI", 11, "bold"),
            text_color=COLOR_GOLD,
            width=60,
        )
        self.label_zoom.pack(side="left", padx=3)

        ctk.CTkButton(
            toolbar, text="+",
            font=("Segoe UI", 16, "bold"),
            width=40, height=34,
            fg_color="#1a3d75", hover_color="#2a5d95",
            command=self._zoom_plus,
        ).pack(side="left", padx=3)

        ctk.CTkButton(
            toolbar,
            text="Imprimer",
            font=("Segoe UI", 12, "bold"),
            fg_color="#27ae60",
            hover_color="#229954",
            width=110, height=34,
            command=self._imprimer,
        ).pack(side="right", padx=(5, 15))

        ctk.CTkButton(
            toolbar,
            text="Fermer",
            font=("Segoe UI", 12, "bold"),
            fg_color="#e74c3c",
            hover_color="#c0392b",
            width=90, height=34,
            command=self.destroy,
        ).pack(side="right", padx=5)

        # ===== CANVAS =====
        canvas_frame = ctk.CTkFrame(self, fg_color="white", corner_radius=0)
        canvas_frame.pack(fill="both", expand=True)

        import tkinter as tk
        self.canvas = tk.Canvas(
            canvas_frame,
            bg="#E8ECEF",
            highlightthickness=0,
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        self.scroll_v = ctk.CTkScrollbar(
            canvas_frame,
            orientation="vertical",
            command=self.canvas.yview,
        )
        self.scroll_v.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.scroll_v.set)

        self.scroll_h = ctk.CTkScrollbar(
            self,
            orientation="horizontal",
            command=self.canvas.xview,
        )
        self.scroll_h.pack(fill="x", side="bottom")
        self.canvas.configure(xscrollcommand=self.scroll_h.set)

        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Control-MouseWheel>", self._on_ctrl_mousewheel)

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_ctrl_mousewheel(self, event):
        if event.delta > 0:
            self._zoom_plus()
        else:
            self._zoom_moins()

    def _afficher_page(self):
        if not self.doc:
            return

        try:
            page = self.doc[self.page_actuelle]
            mat = fitz.Matrix(self.zoom, self.zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)

            from io import BytesIO
            img = Image.open(BytesIO(pix.tobytes("ppm")))
            self.photo = ImageTk.PhotoImage(img)

            self.canvas.delete("all")
            self.canvas.create_image(0, 0, anchor="nw", image=self.photo)
            self.canvas.configure(scrollregion=self.canvas.bbox("all"))

            self.label_page.configure(
                text=f"Page {self.page_actuelle + 1} / {self.nb_pages}"
            )
            self.label_zoom.configure(text=f"{int(self.zoom * 100)}%")

        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d'affichage :\n{e}")

    def _page_precedente(self):
        if self.page_actuelle > 0:
            self.page_actuelle -= 1
            self._afficher_page()

    def _page_suivante(self):
        if self.page_actuelle < self.nb_pages - 1:
            self.page_actuelle += 1
            self._afficher_page()

    def _zoom_plus(self):
        if self.zoom < 4.0:
            self.zoom += 0.25
            self._afficher_page()

    def _zoom_moins(self):
        if self.zoom > 0.5:
            self.zoom -= 0.25
            self._afficher_page()

     # ===== IMPRESSION =====
    def _imprimer(self):
        """Ouvre la boite de dialogue d'impression"""
        if not self.doc:
            return

        try:
            from ui.print_dialog import PrintDialog
            PrintDialog(
                self,
                self.chemin_pdf,
                nb_pages=self.nb_pages,
                page_actuelle=self.page_actuelle + 1,
            )
        except Exception as e:
            messagebox.showerror("Erreur", f"Erreur d'ouverture :\n{e}")
        if not self.doc:
            return

        # Essayer l'impression directe via win32print
        if WIN32PRINT_OK and platform.system() == "Windows":
            try:
                self._imprimer_direct()
                return
            except Exception as e:
                # Si echec, fallback sur les methodes classiques
                print(f"[Impression directe echouee] {e}")
                self._imprimer_fallback()
        else:
            self._imprimer_fallback()

    def _imprimer_direct(self):
        """Impression directe via l'API Windows (pas de lecteur PDF requis)"""
        try:
            printer_name = win32print.GetDefaultPrinter()
        except Exception as e:
            messagebox.showerror(
                "Aucune imprimante",
                f"Aucune imprimante par defaut trouvee.\n\n{e}\n\n"
                "Installez une imprimante dans Windows."
            )
            return

        # Confirmation
        rep = messagebox.askyesno(
            "Imprimer",
            f"Imprimer le rapport sur :\n\n{printer_name}\n\n"
            f"({self.nb_pages} page(s))"
        )
        if not rep:
            return

        try:
            # Creer un contexte d'imprimante
            hDC = win32ui.CreateDC()
            hDC.CreatePrinterDC(printer_name)

            # Dimensions imprimante en pixels
            printer_width = hDC.GetDeviceCaps(110)   # HORZRES
            printer_height = hDC.GetDeviceCaps(111)  # VERTRES

            hDC.StartDoc(os.path.basename(self.chemin_pdf))

            for page_num in range(self.nb_pages):
                page = self.doc[page_num]

                # Rendu haute resolution (300 DPI approx : zoom 3.0)
                mat = fitz.Matrix(3.0, 3.0)
                pix = page.get_pixmap(matrix=mat, alpha=False)

                from io import BytesIO
                img = Image.open(BytesIO(pix.tobytes("ppm")))

                hDC.StartPage()

                # Adapter l'image a la taille de la page imprimable
                img_width, img_height = img.size
                ratio = min(printer_width / img_width,
                            printer_height / img_height)
                new_width = int(img_width * ratio)
                new_height = int(img_height * ratio)

                # Centrer sur la page
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

            messagebox.showinfo(
                "Impression",
                f"Rapport envoye a l'imprimante :\n\n{printer_name}\n\n"
                f"Les pages vont s'imprimer."
            )

        except Exception as e:
            messagebox.showerror(
                "Erreur d'impression",
                f"Impossible d'imprimer :\n\n{e}"
            )

    def _imprimer_fallback(self):
        """Methode de secours : ouvre le PDF avec l'app par defaut"""
        try:
            if platform.system() == "Windows":
                os.startfile(self.chemin_pdf, "print")
            elif platform.system() == "Darwin":
                subprocess.Popen(["open", self.chemin_pdf])
            else:
                subprocess.Popen(["xdg-open", self.chemin_pdf])
        except Exception as e:
            messagebox.showerror(
                "Erreur",
                f"Impossible d'imprimer.\n\n"
                f"Verifiez qu'une imprimante est installee.\n\n{e}"
            )

    def destroy(self):
        try:
            if self.doc:
                self.doc.close()
        except Exception:
            pass
        super().destroy()