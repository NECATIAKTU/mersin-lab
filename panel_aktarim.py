import json
import math
from pathlib import Path
from datetime import datetime, timezone

from entegrasyon import hazirla
from motorlar import (
    LINES, pusula, atlas, radar,
    tempo, matrix, mersin
)

CIKTI = Path(__file__).resolve().parent / "mersin_panel.json"


def yuzdeler(sonuc):
    if sonuc is None:
        return None

    if len(sonuc) != len(LINES):
        raise ValueError("Model uzunluk hatasi")

    if any(
        not math.isfinite(p) or not 0 <= p <= 1
        for p in sonuc
    ):
        raise ValueError("Gecersiz olasilik")

    return {
        str(c): round(p * 100, 2)
        for c, p in zip(LINES, sonuc)
    }


def aktar():
    veri = hazirla()
    simdi = datetime.now(timezone.utc)
    kayitlar = []
    gorulen = set()

    for mac in veri["fikstur"]:
        baslangic = datetime.fromisoformat(
            mac["tarih"].replace("Z", "+00:00")
        )

        if baslangic <= simdi:
            continue

        kimlik = (mac["lig"], str(mac["id"]))

        if kimlik in gorulen:
            continue

        gorulen.add(kimlik)

        lig = mac["lig"]

        gecmis = veri["ligler"].get(lig, [])

        ev = veri["takimlar"].get(
            (lig, "h", mac["ev"].strip().casefold()),
            []
        )

        dep = veri["takimlar"].get(
            (lig, "a", mac["dep"].strip().casefold()),
            []
        )

        p = pusula(gecmis)
        a = atlas(gecmis, ev, dep)
        r = radar(gecmis, ev, dep)
        t = tempo(gecmis)

        mx = matrix([p, a, t])
        ms = mersin([p, a, t])

        kayitlar.append({
            "id": mac["id"],
            "lig": lig,
            "tarih": mac["tarih"],
            "ev_sahibi": mac["ev"],
            "deplasman": mac["dep"],
            "hesaplama_zamani": simdi.isoformat(),
            "durum": "DENEYSEL" if ms is not None
                     else "YETERSIZ_VERI",
            "lig_gecmis_mac": len(gecmis),
            "ev_gecmis_mac": len(ev),
            "dep_gecmis_mac": len(dep),
            "motorlar": {
                "PUSULA X": yuzdeler(p),
                "ATLAS X": yuzdeler(a),
                "RADAR X": r,
                "TEMPO X": yuzdeler(t),
                "MATRIX X": yuzdeler(mx),
                "MERSIN": yuzdeler(ms)
            },
            "olasiliklar": yuzdeler(ms)
        })

    aktif = sum(
        m["olasiliklar"] is not None
        for m in kayitlar
    )

    if not kayitlar or not aktif:
        raise RuntimeError(
            "Gecerli cikti yok. Eski dosya korundu."
        )

    rapor = {
        "sistem": "MERSIN LAB V15",
        "mod": "DENEYSEL ARASTIRMA",
        "guncelleme": simdi.isoformat(),
        "gecmis_mac": veri["mac_sayisi"],
        "toplam_lig": len(veri["ligler"]),
        "toplam_fikstur": len(kayitlar),
        "aktif_mac": aktif,
        "yetersiz_veri": len(kayitlar) - aktif,
        "maclar": kayitlar
    }

    gecici = CIKTI.with_suffix(".tmp")

    gecici.write_text(
        json.dumps(
            rapor,
            ensure_ascii=False,
            indent=2,
            allow_nan=False
        ),
        encoding="utf-8"
    )

    gecici.replace(CIKTI)

    print("MERSIN LAB V15 PANEL AKTARIM")
    print("TOPLAM FIKSTUR:", len(kayitlar))
    print("AKTIF MAC:", aktif)
    print("YETERSIZ VERI:", len(kayitlar) - aktif)
    print("DOSYA:", CIKTI.name)


if __name__ == "__main__":
    aktar()
