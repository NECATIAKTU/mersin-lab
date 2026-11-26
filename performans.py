import json
import math
from pathlib import Path
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parent

PANEL = ROOT / "mersin_panel.json"
ARSIV = ROOT / "mersin_tahmin_arsivi.json"

MODELLER = (
    "PUSULA X",
    "ATLAS X",
    "RADAR X",
    "MATRIX X",
    "TEMPO X",
    "MERSIN"
)

CIZGILER = (
    "1.5", "2.5", "3.5",
    "4.5", "5.5", "6.5"
)


def tarih(deger):
    sonuc = datetime.fromisoformat(
        deger.replace("Z", "+00:00")
    )

    if sonuc.tzinfo is None:
        raise ValueError("Saat dilimi eksik")

    return sonuc.astimezone(timezone.utc)


def oku(dosya):
    return json.loads(
        dosya.read_text(encoding="utf-8")
    )


def yaz(dosya, veri):
    gecici = dosya.with_suffix(".tmp")

    gecici.write_text(
        json.dumps(
            veri,
            ensure_ascii=False,
            indent=2,
            allow_nan=False
        ),
        encoding="utf-8"
    )

    gecici.replace(dosya)


def anahtar(mac):
    return (
        str(mac["lig"]),
        str(mac["id"])
    )


def gecerli_model(isim, veri):

    if not isinstance(veri, dict):
        return False

    if isim == "RADAR X":
        alanlar = (
            "sapma",
            "lig_ortalama",
            "takim_ortalama"
        )

        return all(
            type(veri.get(k)) in (int, float)
            and math.isfinite(veri[k])
            for k in alanlar
        )

    return all(
        type(veri.get(c)) in (int, float)
        and math.isfinite(veri[c])
        and 0 <= veri[c] <= 100
        for c in CIZGILER
    )


def kaydet():

    simdi = datetime.now(timezone.utc)

    eski = (
        oku(ARSIV)["maclar"]
        if ARSIV.exists()
        else []
    )

    yeni = oku(PANEL)["maclar"]

    kayitlar = {
        anahtar(m): m
        for m in eski
    }

    eklenen = 0

    for mac in yeni:

        try:
            baslangic = tarih(mac["tarih"])
            hesaplama = tarih(
                mac["hesaplama_zamani"]
            )

            kimlik = anahtar(mac)

        except (KeyError, ValueError, TypeError):
            continue

        if not hesaplama <= simdi < baslangic:
            continue

        if kimlik in kayitlar:
            continue

        motorlar = {}

        for isim in MODELLER:

            veri = mac.get(
                "motorlar", {}
            ).get(isim)

            motorlar[isim] = (
                veri
                if gecerli_model(isim, veri)
                else None
            )

        if not any(
            v is not None
            for v in motorlar.values()
        ):
            continue

        kayitlar[kimlik] = {
            "id": mac["id"],
            "lig": mac["lig"],
            "tarih": mac["tarih"],
            "ev_sahibi": mac["ev_sahibi"],
            "deplasman": mac["deplasman"],
            "hesaplama_zamani":
                mac["hesaplama_zamani"],
            "kilit_zamani": simdi.isoformat(),
            "motorlar": motorlar
        }

        eklenen += 1

    maclar = sorted(
        kayitlar.values(),
        key=lambda m: (
            tarih(m["tarih"]),
            str(m["lig"]),
            str(m["id"])
        )
    )

    rapor = {
        "sistem": "MERSIN LAB V17",
        "guncelleme": simdi.isoformat(),
        "toplam_mac": len(maclar),
        "maclar": maclar
    }

    yaz(ARSIV, rapor)

    print("=" * 45)
    print("MERSIN LAB V17")
    print("KALICI TAHMIN ARSIVI")
    print("=" * 45)

    print("Yeni kayit:", eklenen)
    print("Toplam kayit:", len(maclar))

    for isim in MODELLER:

        adet = sum(
            m["motorlar"].get(isim) is not None
            for m in maclar
        )

        print(isim, ":", adet)

    print("ARSIV BASARIYLA KAYDEDILDI")


if __name__ == "__main__":
    kaydet()
