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


def dogrula(saat):
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
    global_gecmis = []

    skorlar = defaultdict(
        lambda: [0, 0.0, 0.0, 0.0]
    )

    kalibrasyon = defaultdict(
        lambda: [0, 0.0, 0]
    )

    radar_gruplari = defaultdict(
        lambda: [0, 0]
    )

    bekleyen = []
    cursor = 0
    ortak_mac = 0

    for mac in maclar:
        zaman = tarih(mac["tarih"])

        while cursor < len(bekleyen):
            eski = bekleyen[cursor]

            if tarih(eski["tarih"]) + timedelta(hours=saat) >= zaman:
                break

            lg = eski["lig"]

            ligler[lg].append(eski)
            global_gecmis.append(eski)

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

        ref = pusula(global_gecmis)
        gol = mac["ev_gol"] + mac["dep_gol"]

        if r is not None:
            z = r["sapma"]

            if z >= 0.5:
                grup = "POZITIF"
            elif z <= -0.5:
                grup = "NEGATIF"
            else:
                grup = "NOTR"

            for c in LINES:
                s = radar_gruplari[(grup, c)]
                s[0] += 1
                s[1] += int(gol > c)

        if all(x is not None for x in (p, a, t, ref)):
            ortak_mac += 1

            modeller = {
                "REFERANS": ref,
                "PUSULA X": p,
                "ATLAS X": a,
                "TEMPO X": t,
                "MATRIX X": matrix([p, a, t]),
                "MERSIN": mersin([p, a, t])
            }

            for isim, sonuc in modeller.items():
                if len(sonuc) != len(LINES):
                    raise ValueError("Model uzunluk hatasi")

                for i, c in enumerate(LINES):
                    q = sonuc[i]

                    if not math.isfinite(q) or not 0 <= q <= 1:
                        raise ValueError("Olasilik hatasi")

                    gercek = int(gol > c)

                    s = skorlar[(isim, c)]
                    s[0] += 1
                    s[1] += (q - gercek) ** 2
                    s[2] += q
                    s[3] += gercek

                    dilim = min(9, int(q * 10))

                    k = kalibrasyon[
                        (isim, c, dilim)
                    ]

                    k[0] += 1
                    k[1] += q
                    k[2] += gercek

        bekleyen.append(mac)

    print("\nMERSIN LAB V14")
    print("GUVENLIK SAATI:", saat)
    print("TOPLAM ARSIV:", len(maclar))
    print("ORTAK TEST MACI:", ortak_mac)

    for isim in (
        "REFERANS", "PUSULA X", "ATLAS X",
        "TEMPO X", "MATRIX X", "MERSIN"
    ):
        print("\nMOTOR:", isim)

        for c in LINES:
            n, hata, tahmin, gercek = skorlar[(isim, c)]

            if not n:
                continue

            brier = hata / n
            rn, rh, _, _ = skorlar[("REFERANS", c)]
            referans = rh / rn

            beceri = (
                100 * (1 - brier / referans)
                if referans > 0 else None
            )

            print(
                c,
                "N:", n,
                "BRIER:", round(brier, 5),
                "BECERI %:", (
                    round(beceri, 2)
                    if beceri is not None else "NA"
                ),
                "ORT TAHMIN %:", round(100 * tahmin / n, 2),
                "GERCEK %:", round(100 * gercek / n, 2)
            )

    print("\nMERSIN KALIBRASYON")

    for c in LINES:
        for dilim in range(10):
            n, tahmin, gercek = kalibrasyon[
                ("MERSIN", c, dilim)
            ]

            if n == 0:
                continue

            print(
                c,
                "DILIM:", dilim * 10,
                "N:", n,
                "TAHMIN %:", round(100 * tahmin / n, 2),
                "GERCEK %:", round(100 * gercek / n, 2)
            )

    print("\nRADAR X SAPMA ARASTIRMASI")

    for grup in ("POZITIF", "NOTR", "NEGATIF"):
        for c in LINES:
            n, ust = radar_gruplari[(grup, c)]

            if n:
                print(
                    grup, c,
                    "MAC:", n,
                    "GERCEK UST %:",
                    round(100 * ust / n, 2)
                )


if __name__ == "__main__":
    dogrula(48)
    dogrula(72)
