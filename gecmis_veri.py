import json
import time
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from pathlib import Path

LIGLER = [
    "eng.1", "esp.1", "ger.1",
    "ita.1", "fra.1", "tur.1"
]

GUN = 7
CIKTI = Path("mersin_gecmis.json")


def indir(lig, gun):
    tarih = gun.strftime("%Y%m%d")

    url = (
        "https://site.api.espn.com/apis/site/v2/"
        f"sports/soccer/{lig}/scoreboard"
        f"?dates={tarih}&limit=500"
    )

    req = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )

    with urlopen(req, timeout=20) as cevap:
        return json.load(cevap)


def ayikla(veri, lig):
    maclar = []

    for m in veri.get("events", []):
        durum = m.get("status", {}).get("type", {})

        if durum.get("name") != "STATUS_FULL_TIME":
            continue

        try:
            takimlar = m["competitions"][0]["competitors"]

            ev = next(
                t for t in takimlar
                if t["homeAway"] == "home"
            )

            dep = next(
                t for t in takimlar
                if t["homeAway"] == "away"
            )

            maclar.append({
                "id": str(m["id"]),
                "lig": lig,
                "tarih": m["date"],
                "ev": ev["team"]["displayName"],
                "dep": dep["team"]["displayName"],
                "ev_id": str(ev["team"]["id"]),
                "dep_id": str(dep["team"]["id"]),
                "ev_gol": int(ev["score"]),
                "dep_gol": int(dep["score"])
            })

        except (KeyError, ValueError, TypeError,
                IndexError, StopIteration):
            continue

    return maclar


def calistir():
    bugun = datetime.now(timezone.utc).date()

    kayitlar = {}
    hatalar = []

    for lig in LIGLER:
        lig_maclari = {}

        for i in range(1, GUN + 1):
            gun = bugun - timedelta(days=i)

            try:
                veri = indir(lig, gun)

                for mac in ayikla(veri, lig):
                    key = (lig, mac["id"])
                    lig_maclari[key] = mac
                    kayitlar[key] = mac

            except Exception as hata:
                hatalar.append((lig, str(gun)))
                print(lig, gun, "HATA:", hata)

            time.sleep(0.3)

        print(lig, "MAC:", len(lig_maclari))

    if hatalar or not kayitlar:
        raise RuntimeError(
            "Veri eksik. Arsiv degistirilmedi."
        )

    rapor = {
        "sistem": "MERSIN LAB V05",
        "kaynak": "ESPN",
        "olusturulma": datetime.now(
            timezone.utc
        ).isoformat(),
        "mac_sayisi": len(kayitlar),
        "maclar": list(kayitlar.values())
    }

    CIKTI.write_text(
        json.dumps(
            rapor,
            indent=2,
            ensure_ascii=False
        ),
        encoding="utf-8"
    )

    print("TOPLAM GECMIS MAC:", len(kayitlar))


if __name__ == "__main__":
    calistir()
