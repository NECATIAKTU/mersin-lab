import json
from urllib.request import urlopen
from datetime import datetime, timezone
from pathlib import Path
URL = (
    "https://raw.githubusercontent.com/"
    "NECATIAKTU/tipster-pro-v18/main/"
    "v18_tahmin_arsivi.json"
)


def verileri_al():
    with urlopen(URL, timeout=30) as response:
        kayitlar = json.load(response)

    arsiv = Path(__file__).resolve().parent / "mersin_kalici_arsiv.json"
    with arsiv.open("r", encoding="utf-8") as dosya:
        gecmis = json.load(dosya)["maclar"]
    fikstur = []
    simdi = datetime.now(timezone.utc)

    for kayit in kayitlar:
        mac = kayit["mac"]
        veri = {
            "id": kayit["kimlik"],
            "lig": mac["lig_kodu"],
            "tarih": mac["tarih"],
            "ev": mac["ev_sahibi"],
            "dep": mac["deplasman"]
        }

        sonuc = kayit.get("sonuc") or {}
        tarih = datetime.fromisoformat(
            veri["tarih"].replace("Z", "+00:00")
        )

        if tarih > simdi:
            fikstur.append(veri)

    return {
        "gecmis": gecmis,
        "fikstur": fikstur
    }


if __name__ == "__main__":
    veri = verileri_al()
    print("Gecmis mac:", len(veri["gecmis"]))
    print("Guncel fikstur:", len(veri["fikstur"]))
