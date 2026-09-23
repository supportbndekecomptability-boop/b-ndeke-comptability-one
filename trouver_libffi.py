"""
Trouve où libffi est chargée par Python
"""
import ctypes
import _ctypes
import sys
import os

print("=" * 60)
print("DIAGNOSTIC libffi")
print("=" * 60)
print()

# 1. Emplacement de _ctypes.pyd
print(f"Python : {sys.executable}")
print(f"Version : {sys.version}")
print()

# 2. Chercher le module _ctypes
print(f"_ctypes.pyd : {_ctypes.__file__}")
print()

# 3. Lister les DLLs chargées par le processus
print("DLLs chargees contenant 'ffi' :")
try:
    import psutil
    p = psutil.Process(os.getpid())
    for dll in p.memory_maps():
        if "ffi" in dll.path.lower():
            print(f"  {dll.path}")
except ImportError:
    print("  (psutil non installe - on utilise une autre methode)")

# 4. Charger manuellement libffi pour voir où elle est
print()
print("Recherche de libffi dans les chemins systeme :")
chemins_a_tester = [
    os.path.dirname(sys.executable),
    os.path.join(os.path.dirname(sys.executable), "DLLs"),
    os.path.join(os.path.dirname(sys.executable), "Library", "bin"),
    r"C:\Windows\System32",
]

for chemin in chemins_a_tester:
    if os.path.exists(chemin):
        for f in os.listdir(chemin):
            if "ffi" in f.lower() and f.endswith(".dll"):
                print(f"  TROUVE : {os.path.join(chemin, f)}")

# 5. Test de chargement
print()
print("Test de chargement de _ctypes :")
try:
    from ctypes import CDLL
    test = CDLL(None)
    print("  [OK] ctypes fonctionne")
except Exception as e:
    print(f"  [ERREUR] {e}")