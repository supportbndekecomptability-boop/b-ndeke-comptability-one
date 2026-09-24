"""
Helpers UI pour appliquer les permissions dans les pages.
"""
from core.permissions import a_permission, get_role


def peut(utilisateur, permission):
    """Raccourci : True si l'utilisateur a la permission."""
    return a_permission(utilisateur, permission)


def masquer_si_sans_permission(widget, utilisateur, permission):
    """Cache un widget si l'utilisateur n'a pas la permission."""
    if not a_permission(utilisateur, permission):
        try:
            widget.pack_forget()
        except Exception:
            try:
                widget.grid_forget()
            except Exception:
                pass
        return False
    return True


def desactiver_si_sans_permission(widget, utilisateur, permission):
    """Desactive un widget si l'utilisateur n'a pas la permission."""
    if not a_permission(utilisateur, permission):
        try:
            widget.configure(state="disabled")
        except Exception:
            pass
        return False
    return True


def creer_bouton_conditionnel(parent, utilisateur, permission, **kwargs):
    """Retourne un bouton si l'utilisateur a la permission, sinon None."""
    import customtkinter as ctk
    if not a_permission(utilisateur, permission):
        return None
    return ctk.CTkButton(parent, **kwargs)


def est_lecture_seule(utilisateur):
    """True si l'utilisateur est en lecture seule globale."""
    role = get_role(utilisateur)
    return role in ("directeur", "prefet")


def message_acces_refuse(parent, texte="Acces refuse pour votre role."):
    """Affiche un message d'acces refuse dans un conteneur."""
    import customtkinter as ctk
    ctk.CTkLabel(
        parent,
        text=texte,
        font=("Segoe UI", 14, "bold"),
        text_color="#e74c3c",
    ).pack(pady=20)


def filtrer_par_niveau(items, utilisateur, cle_niveau="niveau"):
    """Filtre une liste de dicts selon les niveaux autorises."""
    from core.permissions import niveaux_autorises
    niveaux = niveaux_autorises(utilisateur)
    if niveaux is None:
        return items

    resultat = []
    for item in items:
        val = item.get(cle_niveau) or ""
        if not val:
            continue
        niveaux_item = [v.strip() for v in str(val).split(",")]
        if any(n in niveaux for n in niveaux_item):
            resultat.append(item)
    return resultat


def classes_autorisees(utilisateur):
    """Retourne le set des noms de classes accessibles ou None."""
    from core.permissions import niveaux_autorises
    niveaux = niveaux_autorises(utilisateur)
    if niveaux is None:
        return None
    try:
        from core.classes import lister_classes
        return {c["nom"] for c in lister_classes() if c.get("niveau") in niveaux}
    except Exception:
        return set()


def filtrer_eleves_par_niveau(eleves, utilisateur):
    """Filtre une liste d'eleves selon les classes autorisees."""
    classes_ok = classes_autorisees(utilisateur)
    if classes_ok is None:
        return eleves
    return [e for e in eleves if e.get("classe") in classes_ok]
