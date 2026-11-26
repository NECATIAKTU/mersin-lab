import math
from datetime import datetime, timezone, timedelta

from performans import (
    ROOT, ARSIV, MODELLER,
    CIZGILER, oku, yaz,
    tarih, anahtar, gecerli_model
)

SKORLAR = ROOT / "mersin_kalici_arsiv.json"
RAPOR = ROOT / "mersin_performans.json"

ESIKLER = {
    "1.5": 75,
    "2.5": 65,
    "3.5": 65,
    "4.5": 65,
    "5.5": 65,
    "6.5": 65
}


def ozet(kayitlar):

    dogru = sum(
        r["sonuc"] == "DOGRU"
        for r in kayitlar
    )

    yanlis = sum(
        r["sonuc"] == "YANLIS"
        for r in kayitlar
    )

    bekleyen = sum(
        r["sonuc"] == "BEKLIYOR"
        for r in kayitlar
    )

    pas = sum(
        r["sonuc"] == "PAS"
        for r in kayitlar
    )

    toplam = dogru + yanlis

    return {
        "toplam": len(kayitlar),
        "dogru": dogru,
        "yanlis": yanlis,
        "bekleyen": bekleyen,
        "pas": pas,
        "degerlendirilen": toplam,
        "basari": (
            round(100 * dogru / toplam, 2)
            if toplam else None
        )
    }


def brier(kayitlar):

    hatalar = [
        r["brier"]
        for r in kayitlar
        if r.get("brier") is not None
    ]

    return (
        round(sum(hatalar) / len(hatalar), 6)
        if hatalar else None
    )


def donem(kayitlar, baslangic, simdi):

    return [
        r for r in kayitlar
        if baslangic <= tarih(r["tarih"]) <= simdi
    ]


def secim(veri):

    for c in reversed(CIZGILER):

        if veri[c] >= ESIKLER[c]:
            return c

    return None


def radar_sonucu(veri, gol):

    if veri["sapma"] >= 0.5:
        yon = "POZITIF"

    elif veri["sapma"] <= -0.5:
        yon = "NEGATIF"

    else:
        return "NOTR", "PAS"

    if gol is None:
        return yon, "BEKLIYOR"

    ortalama = veri["lig_ortalama"]

    if yon == "POZITIF":
        dogru = gol > ortalama
    else:
        dogru = gol < ortalama

    return yon, (
        "DOGRU" if dogru else "YANLIS"
    )


def calistir():

    simdi = datetime.now(timezone.utc)

    bugun = simdi.replace(
        hour=0,
        minute=0,
        second=0,
        microsecond=0
    )

    tahminler = oku(ARSIV)["maclar"]
    skorlar = oku(SKORLAR)["maclar"]

    gercekler = {}

    for mac in skorlar:

        ev = mac.get("ev_gol")
        dep = mac.get("dep_gol")

        if (
            type(ev) is int
            and type(dep) is int
            and ev >= 0
            and dep >= 0
        ):
            gercekler[anahtar(mac)] = mac

    sonuc = {}

    for model in MODELLER:

        kayitlar = []

        cizgi_kayitlari = {
            c: [] for c in CIZGILER
        }

        yetersiz = 0
        gorulen = set()

        for mac in tahminler:

            kimlik = anahtar(mac)

            if kimlik in gorulen:
                continue

            gorulen.add(kimlik)

            baslangic = tarih(mac["tarih"])
            kilit = tarih(mac["kilit_zamani"])

            hesaplama = tarih(
                mac["hesaplama_zamani"]
            )

            if not (
                hesaplama <= kilit
                < baslangic
                and kilit <= simdi
            ):
                continue

            veri = mac.get(
                "motorlar", {}
            ).get(model)

            if not gecerli_model(model, veri):
                yetersiz += 1
                continue

            skor = gercekler.get(kimlik)

            if skor and (
                tarih(skor["tarih"]) != baslangic
                or baslangic >= simdi
            ):
                skor = None

            gol = (
                skor["ev_gol"] + skor["dep_gol"]
                if skor else None
            )

            kayit = {
                "id": mac["id"],
                "lig": mac["lig"],
                "tarih": mac["tarih"],
                "ev_sahibi": mac["ev_sahibi"],
                "deplasman": mac["deplasman"],
                "kilit_zamani":
                    mac["kilit_zamani"],
                "skor": (
                    str(skor["ev_gol"])
                    + "-"
                    + str(skor["dep_gol"])
                    if skor else None
                )
            }

            if model == "RADAR X":

                yon, karar = radar_sonucu(
                    veri, gol
                )

                kayit["secim"] = yon
                kayit["sapma"] = veri["sapma"]
                kayit["sonuc"] = karar

                kayitlar.append(kayit)
                continue

            tercih = secim(veri)

            kayit["secim"] = tercih

            kayit["yuzde"] = (
                veri[tercih]
                if tercih else None
            )

            if tercih is None:
                kayit["sonuc"] = "PAS"

            elif gol is None:
                kayit["sonuc"] = "BEKLIYOR"

            elif gol > float(tercih):
                kayit["sonuc"] = "DOGRU"

            else:
                kayit["sonuc"] = "YANLIS"

            kayitlar.append(kayit)

            for c in CIZGILER:

                yuzde = veri[c]
                p = yuzde / 100

                gercek = (
                    int(gol > float(c))
                    if gol is not None
                    else None
                )

                if yuzde < ESIKLER[c]:
                    karar = "PAS"

                elif gercek is None:
                    karar = "BEKLIYOR"

                elif gercek:
                    karar = "DOGRU"

                else:
                    karar = "YANLIS"

                cizgi_kayitlari[c].append({
                    "tarih": mac["tarih"],
                    "sonuc": karar,
                    "brier": (
                        (p - gercek) ** 2
                        if gercek is not None
                        else None
                    )
                })

        rapor = ozet(kayitlar)

        rapor["yetersiz_veri"] = yetersiz

        rapor["gunluk"] = ozet(
            donem(kayitlar, bugun, simdi)
        )

        rapor["haftalik"] = ozet(
            donem(
                kayitlar,
                simdi - timedelta(days=7),
                simdi
            )
        )

        rapor["aylik"] = ozet(
            donem(
                kayitlar,
                simdi - timedelta(days=30),
                simdi
            )
        )

        rapor["cizgiler"] = {}

        if model != "RADAR X":

            for c in CIZGILER:

                grup = cizgi_kayitlari[c]

                rapor["cizgiler"][c] = {
                    **ozet(grup),
                    "brier": brier(grup)
                }

            rapor["brier"] = brier([
                r
                for grup in cizgi_kayitlari.values()
                for r in grup
            ])

        else:
            rapor["brier"] = None

        rapor["kayitlar"] = kayitlar

        sonuc[model] = rapor

        print("=" * 40)
        print(model)
        print("DOGRU:", rapor["dogru"])
        print("YANLIS:", rapor["yanlis"])
        print("BEKLEYEN:", rapor["bekleyen"])
        print("PAS:", rapor["pas"])
        print("BASARI:", rapor["basari"])
        print("BRIER:", rapor["brier"])

    yaz(RAPOR, {
        "sistem": "MERSIN LAB V17",
        "mod": "DENEYSEL PERFORMANS",
        "guncelleme": simdi.isoformat(),
        "esikler": ESIKLER,
        "modeller": sonuc
    })

    print("=" * 40)
    print("PERFORMANS RAPORU KAYDEDILDI")


if __name__ == "__main__":
    calistir()
