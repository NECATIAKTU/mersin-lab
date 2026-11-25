import math
import statistics

LINES = (1.5, 2.5, 3.5, 4.5, 5.5, 6.5)


def poisson(mu):
    if not math.isfinite(mu) or mu < 0:
        raise ValueError("Gecersiz gol ortalamasi")

    p = math.exp(-mu)
    toplam = p
    sonuc = []

    for k in range(1, 7):
        p *= mu / k
        toplam += p
        sonuc.append(max(0, min(1, 1 - toplam)))

    return sonuc


def goller(maclar):
    return [
        m["ev_gol"] + m["dep_gol"]
        for m in maclar
    ]


def pusula(maclar):
    gs = goller(maclar)

    if len(gs) < 30:
        return None

    return [
        sum(g > c for g in gs) / len(gs)
        for c in LINES
    ]


def atlas(lig, ev, dep):
    if len(lig) < 20 or len(ev) < 5 or len(dep) < 5:
        return None

    mh = statistics.mean(m["ev_gol"] for m in lig)
    ma = statistics.mean(m["dep_gol"] for m in lig)

    def ort(maclar, alan, prior):
        return (
            sum(m[alan] for m in maclar) + 10 * prior
        ) / (len(maclar) + 10)

    h = (
        ort(ev, "ev_gol", mh)
        + ort(dep, "ev_gol", mh)
    ) / 2

    a = (
        ort(ev, "dep_gol", ma)
        + ort(dep, "dep_gol", ma)
    ) / 2

    return poisson(h + a)


def radar(lig, ev, dep):
    if len(lig) < 30 or len(ev) < 5 or len(dep) < 5:
        return None

    gs = goller(lig)
    ort = statistics.mean(gs)
    sapma = statistics.stdev(gs)

    if sapma == 0:
        return None

    ev_son = goller(sorted(
        ev, key=lambda m: m["tarih"]
    )[-5:])

    dep_son = goller(sorted(
        dep, key=lambda m: m["tarih"]
    )[-5:])

    takim_ort = statistics.mean(ev_son + dep_son)
    z = (takim_ort - ort) / sapma

    return {
        "sapma": round(z, 4),
        "lig_ortalama": ort,
        "takim_ortalama": takim_ort
    }


def tempo(maclar):
    gs = goller(maclar)

    if len(gs) < 30:
        return None

    mu = statistics.mean(gs)
    v = statistics.variance(gs)

    if v <= mu or mu == 0:
        return poisson(mu)

    r = mu * mu / (v - mu)
    p = (r / (r + mu)) ** r
    toplam = p
    sonuc = []

    for k in range(1, 7):
        p *= (r + k - 1) / k * mu / (r + mu)
        toplam += p
        sonuc.append(max(0, min(1, 1 - toplam)))

    return sonuc


def matrix(modeller):
    aktif = [m for m in modeller if m is not None]

    if len(aktif) < 2:
        return None

    def logit(p):
        p = max(0.000001, min(0.999999, p))
        return math.log(p / (1 - p))

    return [
        1 / (1 + math.exp(
            -statistics.mean(logit(m[i]) for m in aktif)
        ))
        for i in range(6)
    ]


def mersin(modeller):
    aktif = [m for m in modeller if m is not None]

    if len(aktif) < 2:
        return None

    return [
        statistics.mean(m[i] for m in aktif)
        for i in range(6)
    ]
