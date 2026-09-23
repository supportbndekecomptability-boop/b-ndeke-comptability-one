"""
Frame scrollable horizontalement ET verticalement
Compatible CustomTkinter
"""
import tkinter as tk
import customtkinter as ctk
from config import COLOR_NAVY


class HorizontalScrollFrame(ctk.CTkFrame):
    """Un cadre avec defilement horizontal (et vertical).
    Utilise pour les tableaux larges.
    """

    def __init__(self, parent, fg_color="white", corner_radius=10, height=400):
        super().__init__(parent, fg_color=fg_color, corner_radius=corner_radius)

        # Canvas interne pour le defilement
        self.canvas = tk.Canvas(
            self,
            bg="white",
            highlightthickness=0,
            height=height,
        )
        self.canvas.pack(side="top", fill="both", expand=True)

        # Scrollbar verticale
        self.vsb = ctk.CTkScrollbar(
            self,
            orientation="vertical",
            command=self.canvas.yview,
        )
        self.vsb.pack(side="right", fill="y")
        self.canvas.configure(yscrollcommand=self.vsb.set)

        # Scrollbar horizontale
        self.hsb = ctk.CTkScrollbar(
            self,
            orientation="horizontal",
            command=self.canvas.xview,
        )
        self.hsb.pack(side="bottom", fill="x")
        self.canvas.configure(xscrollcommand=self.hsb.set)

        # Frame interne qui contient le contenu
        self.interior = tk.Frame(self.canvas, bg="white")
        self.canvas_window = self.canvas.create_window(
            (0, 0),
            window=self.interior,
            anchor="nw",
        )

        # Mise a jour automatique du scroll quand la taille change
        self.interior.bind("<Configure>", self._on_interior_configure)

        # Support de la molette de la souris
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.interior.bind("<MouseWheel>", self._on_mousewheel)

        # Shift + molette = scroll horizontal
        self.canvas.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)
        self.interior.bind("<Shift-MouseWheel>", self._on_shift_mousewheel)

    def _on_interior_configure(self, event=None):
        """Ajuste la zone scrollable quand le contenu change de taille"""
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_mousewheel(self, event):
        """Scroll vertical avec la molette"""
        self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _on_shift_mousewheel(self, event):
        """Scroll horizontal avec Shift + molette"""
        self.canvas.xview_scroll(int(-1 * (event.delta / 120)), "units")

    def clear(self):
        """Vide tout le contenu"""
        for widget in self.interior.winfo_children():
            widget.destroy()
        self.canvas.configure(scrollregion=(0, 0, 0, 0))