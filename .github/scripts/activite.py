"""Génère activite/serie.svg et activite/calendrier.svg à partir du calendrier
de contributions renvoyé par l'API GraphQL de GitHub (fichier JSON en argument)."""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

FOND, TEXTE, SOUS_TEXTE = "#1a1b27", "#ffffff", "#a9b1d6"
NIVEAUX = {"NONE": "#2a2e3f", "FIRST_QUARTILE": "#0b4f52", "SECOND_QUARTILE": "#037c80",
           "THIRD_QUARTILE": "#00a3a5", "FOURTH_QUARTILE": "#00BABC"}
MOIS = "janv. févr. mars avr. mai juin juil. août sept. oct. nov. déc.".split()


def series(jours, aujourdhui):
    """(série actuelle, plus longue série) à partir de [(date, nb), ...] triés."""
    plus_longue = courante = 0
    for _, nb in jours:
        courante = courante + 1 if nb else 0
        plus_longue = max(plus_longue, courante)
    actuelle = 0
    for j, nb in reversed(jours):
        if j > aujourdhui or (j == aujourdhui and not nb):
            continue  # la journée en cours n'est pas finie, elle ne casse pas la série
        if not nb:
            break
        actuelle += 1
    return actuelle, plus_longue


def carte_serie(total, actuelle, plus_longue):
    blocs = [(total, "Contributions (1 an)"), (actuelle, "Série actuelle"), (plus_longue, "Plus longue série")]
    textes = "".join(
        f'<text x="{82 + i * 165}" y="88" font-size="30" font-weight="700" fill="{"#00BABC" if i == 1 else TEXTE}" text-anchor="middle">{v}</text>'
        f'<text x="{82 + i * 165}" y="120" font-size="13" fill="{SOUS_TEXTE}" text-anchor="middle">{l}</text>'
        for i, (v, l) in enumerate(blocs))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="495" height="160" viewBox="0 0 495 160" role="img" '
            f'aria-label="{total} contributions, série actuelle {actuelle} jours, plus longue {plus_longue} jours">'
            f'<rect width="495" height="160" rx="8" fill="{FOND}"/>'
            f'<g font-family="Segoe UI, Ubuntu, sans-serif">{textes}</g></svg>')


def calendrier(semaines):
    c, pas, marge_g, marge_h = 11, 14, 30, 28
    largeur, hauteur = marge_g + len(semaines) * pas + 10, marge_h + 7 * pas + 10
    cases, mois, dernier_mois = [], [], None
    for x, semaine in enumerate(semaines):
        premier = date.fromisoformat(semaine[0]["date"])
        if premier.month != dernier_mois and x < len(semaines) - 2:
            mois.append(f'<text x="{marge_g + x * pas}" y="18">{MOIS[premier.month - 1]}</text>')
            dernier_mois = premier.month
        for jour in semaine:
            y = (date.fromisoformat(jour["date"]).weekday() + 1) % 7  # dimanche en haut, comme GitHub
            cases.append(f'<rect x="{marge_g + x * pas}" y="{marge_h + y * pas}" width="{c}" height="{c}" rx="2" '
                         f'fill="{NIVEAUX[jour["contributionLevel"]]}"><title>{jour["date"]} : {jour["contributionCount"]}</title></rect>')
    jours = "".join(f'<text x="0" y="{marge_h + y * pas + 9}">{n}</text>' for y, n in ((1, "lun"), (3, "mer"), (5, "ven")))
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{largeur}" height="{hauteur}" viewBox="0 0 {largeur} {hauteur}" '
            f'role="img" aria-label="Calendrier des contributions"><rect width="100%" height="100%" rx="8" fill="{FOND}"/>'
            f'<g font-family="Segoe UI, Ubuntu, sans-serif" font-size="10" fill="{SOUS_TEXTE}">{"".join(mois)}{jours}</g>'
            f'{"".join(cases)}</svg>')


def main(fichier, dossier):
    cal = json.loads(Path(fichier).read_text())["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    semaines = [s["contributionDays"] for s in cal["weeks"]]
    jours = [(date.fromisoformat(j["date"]), j["contributionCount"]) for s in semaines for j in s]
    sortie = Path(dossier)
    sortie.mkdir(exist_ok=True)
    (sortie / "serie.svg").write_text(carte_serie(cal["totalContributions"], *series(jours, date.today())))
    (sortie / "calendrier.svg").write_text(calendrier(semaines))


def _test():
    d = date(2026, 11, 7)
    j = lambda *nbs: [(d - timedelta(len(nbs) - 1 - i), n) for i, n in enumerate(nbs)]
    assert series(j(1, 1, 0, 1, 1, 1), d) == (3, 3)
    assert series(j(1, 1, 1, 1, 0, 1, 0), d) == (1, 4)  # aujourd'hui à 0 ne casse pas la série
    assert series(j(1, 0, 0), d) == (0, 1)


if __name__ == "__main__":
    _test()
    main(*sys.argv[1:3])
