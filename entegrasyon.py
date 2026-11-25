import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from veri_baglantisi import verileri_al

ARSIV = Path(__file__).resolve().parent / "mersin_kalici_arsiv.json"

def tarih(s):
    return datetime.fromisoformat(
        s.replace("Z", "+00:00")
    )

def hazirla():
    veri = verileri_al()
    ligler = defaultdict(list)
    takimlar = defaultdict(list)
    simdi = datetime.now(timezone.utc)
    gorulen = set()

    for mac in veri["gecmis"]:
        kimlik = (mac["lig"], str(mac["id"]))

        if kimlik in gorulen:
            continue

        if tarih(mac["tarih"]) >= simdi:
            continue

        if any(
            type(mac.get(k)) is not int or mac[k] < 0
            for k in ("ev_gol", "dep_gol")
        ):
            continue

        gorulen.add(kimlik)
        lig = mac["lig"]

        ligler[lig].append(mac)
        takimlar[(lig, "h", mac["ev_id"])].append(mac)
        takimlar[(lig, "a", mac["dep_id"])].append(mac)

    return {
        "ligler": ligler,
        "takimlar": takimlar,
        "fikstur": veri["fikstur"],
        "mac_sayisi": len(gorulen)
    }

if __name__ == "__main__":
    veri = hazirla()
    print("MERSIN LAB V11")
    print("GECMIS MAC:", veri["mac_sayisi"])
    print("TOPLAM LIG:", len(veri["ligler"]))
    print("GUNCEL FIKSTUR:", len(veri["fikstur"]))
