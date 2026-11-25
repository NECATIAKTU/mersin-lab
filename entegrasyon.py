import json
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from veri_baglantisi import verileri_al
from motorlar import pusula, atlas, radar, tempo, matrix, mersin
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
        takimlar[(lig, "h", mac["ev"].strip().casefold())].append(mac)
        takimlar[(lig, "a", mac["dep"].strip().casefold())].append(mac)

    return {
        "ligler": ligler,
        "takimlar": takimlar,
        "fikstur": veri["fikstur"],
        "mac_sayisi": len(gorulen)
    }
def hesapla(veri):
    sayac = defaultdict(int)

    for mac in veri["fikstur"]:
        lig = mac["lig"]

        gecmis = veri["ligler"].get(lig, [])

        ev = veri["takimlar"].get(
            (lig, "h", mac["ev"].strip().casefold()), []
        )

        dep = veri["takimlar"].get(
            (lig, "a", mac["dep"].strip().casefold()), []
        )

        p = pusula(gecmis)
        a = atlas(gecmis, ev, dep)
        r = radar(gecmis, ev, dep)
        t = tempo(gecmis)

        modeller = {
            "PUSULA X": p,
            "ATLAS X": a,
            "RADAR X": r,
            "TEMPO X": t,
            "MATRIX X": matrix([p, a, t]),
            "MERSIN": mersin([p, a, t])
        }

        for isim, sonuc in modeller.items():
            if sonuc is not None:
                sayac[isim] += 1

    print("MERSIN V12 MOTOR KONTROLU")

    for isim in (
        "PUSULA X", "ATLAS X", "RADAR X",
        "TEMPO X", "MATRIX X", "MERSIN"
    ):
        print(isim, "AKTIF MAC:", sayac[isim])
if __name__ == "__main__":
    veri = hazirla()
    print("MERSIN LAB V11")
    print("GECMIS MAC:", veri["mac_sayisi"])
    print("TOPLAM LIG:", len(veri["ligler"]))
    print("GUNCEL FIKSTUR:", len(veri["fikstur"]))
    hesapla(veri)
