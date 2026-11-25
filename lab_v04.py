import json
import statistics
from datetime import datetime
from veri_baglantisi import verileri_al


def tarih(s):
    return datetime.fromisoformat(
        s.replace("Z", "+00:00")
    )


def gecmis_hazirla(veri, kesim):
    sonuc = []

    for mac in veri["gecmis"]:
        dogrulama = mac.get("dogrulama_zamani")

        if not dogrulama:
            continue

        if tarih(dogrulama) < kesim:
            if tarih(mac["tarih"]) < kesim:
                sonuc.append(mac)

    return sonuc


def lig_analizi(maclar):
    if not maclar:
        return None

    goller = [
        m["ev_gol"] + m["dep_gol"]
        for m in maclar
    ]

    return {
        "mac_sayisi": len(goller),
        "gol_ortalamasi": statistics.mean(goller),
        "gol_medyan": statistics.median(goller),
        "gol_dagilimi": {
            str(i): goller.count(i)
            for i in sorted(set(goller))
        }
    }


def arastirma():
    veri = verileri_al()
    ligler = {}

    for mac in veri["gecmis"]:
        ligler.setdefault(mac["lig"], []).append(mac)

    rapor = {
        "sistem": "MERSIN LAB V04",
        "mod": "Bagimsiz istatistik arastirmasi",
        "gecmis_mac": len(veri["gecmis"]),
        "fikstur_mac": len(veri["fikstur"]),
        "ligler": {
            lig: lig_analizi(maclar)
            for lig, maclar in ligler.items()
        }
    }

    return rapor


if __name__ == "__main__":
    print(json.dumps(
        arastirma(),
        ensure_ascii=False,
        indent=2
    ))
