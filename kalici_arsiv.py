import json
from pathlib import Path
from datetime import datetime, timezone

YENI = Path("mersin_gecmis.json")
ARSIV = Path("mersin_kalici_arsiv.json")


def oku(dosya):
    veri = json.loads(
        dosya.read_text(encoding="utf-8")
    )

    maclar = veri["maclar"]

    if not isinstance(maclar, list):
        raise ValueError("Gecersiz veri")

    for mac in maclar:
        if not mac.get("lig") or not mac.get("id"):
            raise ValueError("Mac kimligi eksik")

    return maclar


def anahtar(mac):
    return (mac["lig"], str(mac["id"]))


def calistir():
    eski = oku(ARSIV) if ARSIV.exists() else []
    yeni = oku(YENI)

    if not yeni:
        raise ValueError("Yeni veri bos")

    kayitlar = {
        anahtar(mac): mac for mac in eski
    }

    onceki = len(kayitlar)
    eklenen = 0
    tekrar = 0
    farkli = 0

    for mac in yeni:
        key = anahtar(mac)

        if key in kayitlar:
            tekrar += 1

            if kayitlar[key] != mac:
                farkli += 1

            continue

        kayitlar[key] = mac
        eklenen += 1

    maclar = sorted(
        kayitlar.values(),
        key=lambda m: (
            m["tarih"], m["lig"], str(m["id"])
        )
    )

    rapor = {
        "sistem": "MERSIN LAB V06",
        "guncelleme": datetime.now(
            timezone.utc
        ).isoformat(),
        "mac_sayisi": len(maclar),
        "lig_sayisi": len({
            m["lig"] for m in maclar
        }),
        "maclar": maclar
    }

    gecici = ARSIV.with_suffix(".tmp")

    gecici.write_text(
        json.dumps(
            rapor,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    gecici.replace(ARSIV)

    print("ONCEKI MAC:", onceki)
    print("YENI EKLENEN:", eklenen)
    print("TEKRAR EDEN:", tekrar)
    print("FARKLI KAYIT:", farkli)
    print("TOPLAM ARSIV:", len(maclar))
    print("TOPLAM LIG:", rapor["lig_sayisi"])


if __name__ == "__main__":
    calistir()
