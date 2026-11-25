import json
from urllib.request import urlopen
from datetime import datetime, timezone

URL = (
    "https://raw.githubusercontent.com/"
    "NECATIAKTU/tipster-pro-v18/main/"
    "v18_tahmin_arsivi.json"
)


def verileri_al():
    with urlopen(URL, timeout=30) as response:
        kayitlar = json.load(response)

    gecmis = []
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

        if (
            kayit.get("durum") == "DOGRULANDI"
            and sonuc.get("durum") == "TAMAMLANDI"
            and kayit.get("sonuc_dogrulama_zamani_utc")
        ):
            gecmis.append({
                **veri,
                "ev_gol": sonuc["ev_gol"],
                "dep_gol": sonuc["dep_gol"],
                "dogrulama_zamani": kayit[
                    "sonuc_dogrulama_zamani_utc"
                ]
            })

        elif tarih > simdi:
            fikstur.append(veri)

    return {
        "gecmis": gecmis,
        "fikstur": fikstur
    }


if __name__ == "__main__":
    veri = verileri_al()
    print("Gecmis mac:", len(veri["gecmis"]))
    print("Guncel fikstur:", len(veri["fikstur"]))
