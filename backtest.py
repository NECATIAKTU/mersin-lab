import json
import math
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
from motorlar import (
    LINES, pusula, atlas, radar,
    tempo, matrix, mersin
)

ARSIV = Path(__file__).resolve().parent / "mersin_kalici_arsiv.json"


def tarih(s):
    return datetime.fromisoformat(
        s.replace("Z", "+00:00")
    )


def backtest():
    with ARSIV.open("r", encoding="utf-8") as f:
        ham = json.load(f)["maclar"]

    maclar = []
    gorulen = set()

    for mac in ham:
        kimlik = (mac["lig"], str(mac["id"]))

        if kimlik in gorulen:
            continue

        if any(
            type(mac.get(k)) is not int or mac[k] < 0
            for k in ("ev_gol", "dep_gol")
        ):
            continue

        gorulen.add(kimlik)
        maclar.append(mac)

    maclar.sort(key=lambda m: tarih(m["tarih"]))

    ligler = defaultdict(list)
    takimlar = defaultdict(list)
    istatistik = defaultdict(
        lambda: [0, 0.0, 0.0]
    )

    aktif = defaultdict(int)
    bekleyen = []
    cursor = 0

    for mac in maclar:
        zaman = tarih(mac["tarih"])

        while cursor < len(bekleyen):
            eski = bekleyen[cursor]

            if tarih(eski["tarih"]) + timedelta(hours=48) >= zaman:
                break

            lg = eski["lig"]
            ligler[lg].append(eski)

            takimlar[
                (lg, "h", eski["ev"].strip().casefold())
            ].append(eski)

            takimlar[
                (lg, "a", eski["dep"].strip().casefold())
            ].append(eski)

            cursor += 1

        lig = mac["lig"]
        gecmis = ligler[lig]

        ev = takimlar[
            (lig, "h", mac["ev"].strip().casefold())
        ]

        dep = takimlar[
            (lig, "a", mac["dep"].strip().casefold())
        ]

        p = pusula(gecmis)
        a = atlas(gecmis, ev, dep)
        r = radar(gecmis, ev, dep)
        t = tempo(gecmis)

        modeller = {
            "PUSULA X": p,
            "ATLAS X": a,
            "TEMPO X": t,
            "MATRIX X": matrix([p, a, t]),
            "MERSIN": mersin([p, a, t])
        }

        if r is not None:
            aktif["RADAR X"] += 1

        gol = mac["ev_gol"] + mac["dep_gol"]

        for isim, sonuc in modeller.items():
            if sonuc is None:
                continue

            if len(sonuc) != 6:
                raise ValueError("Gecersiz model uzunlugu")

            if any(
                not math.isfinite(q) or not 0 <= q <= 1
                for q in sonuc
            ):
                raise ValueError("Gecersiz olasilik")

            aktif[isim] += 1

            for i, c in enumerate(LINES):
                q = sonuc[i]
                gercek = int(gol > c)

                s = istatistik[(isim, c)]
                s[0] += 1
                s[1] += (q - gercek) ** 2
                s[2] += gercek

        bekleyen.append(mac)

    print("MERSIN LAB V13 BACKTEST")
    print("TOPLAM ARSIV:", len(maclar))

    for isim in (
        "PUSULA X", "ATLAS X", "RADAR X",
        "TEMPO X", "MATRIX X", "MERSIN"
    ):
        print("\nMOTOR:", isim)
        print("TEST EDILEN MAC:", aktif[isim])

        for c in LINES:
            n, hata, gercek = istatistik[(isim, c)]

            if n == 0:
                continue

            print(
                c,
                "BRIER:", round(hata / n, 5),
                "GOZLENEN UST %:",
                round(100 * gercek / n, 2)
            )


if __name__ == "__main__":
    backtest()
