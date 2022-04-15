import time

from animdl.core.cli.helpers import ensure_extraction
from animdl.core.cli.http_client import client
from animdl.core.codebase.providers import get_appropriate

from image import generate_image


def animepahe_one_piece(*, query="One Piece"):

    response = client.get("https://animepahe.com/api?m=search&l=8&q={}".format(query))

    if response.status_code != 200:
        return None

    if response.headers.get("content-disposition") != "application/json":
        return None

    return "https://animepahe.com/anime/{[session]}".format(
        response.json().get("data")[0]
    )


GOGOANIME_KEYS = "./api/gogoanime.json"


def scrape_keys():
    import regex
    import json
    import os

    page = client.get("https://goload.pro/streaming.php?id=MTgxNzk2").text

    on_page = regex.findall(r"(?:container|videocontent)-(\d+)", page)

    if not on_page:
        return

    key, iv, second_key = on_page

    out = {"key": key, "second_key": second_key, "iv": iv}

    with open(GOGOANIME_KEYS, "r") as current_keys:
        keys = json.load(current_keys)

    if out == keys:
        return

    with open(GOGOANIME_KEYS, "w") as current_keys:
        json.dump(out, current_keys)

    waifu = os.getenv("JUSTANOTHERWAIFU")

    if waifu is None:
        return

    client.post(
        waifu,
        json={
            "embeds": [
                {
                    "title": "GogoAnime's keys have updated",
                    "description": "KEY (encrypted-ajax): `{0[key]}`\nKEY (streams): {0[second_key]}\nIV: `{0[iv]}`".format(out),
                    "color": 0x7ad7f0,
                }
            ]
        },
    )

scrape_keys()

FAILED = ("./assets/failed.png", (218, 68, 83))
SUCCESS = ("./assets/success.png", (50, 198, 113))


animepahe = animepahe_one_piece()

site_check_index = {
    "nineanime": "https://9anime.to/watch/one-piece.ov8",
    "crunchyroll": "https://www.crunchyroll.com/one-piece",
    "allanime": "https://allanime.site/anime/ReooPAxPMsHM4KPMY",
    "animeout": "https://www.animeout.xyz/download-one-piece-episodes-latest/",
    "animixplay": "https://animixplay.to/v1/one-piece",
    "animtime": "https://animtime.com/title/5",
    "gogoanime": "https://gogoanime.cm/category/one-piece",
    "tenshi": "https://tenshi.moe/anime/kjfrhu3s",
    "twist": "https://twist.moe/a/one-piece",
    "kawaiifu": "https://kawaiifu.com/tv-series/one-piece-720p-hd.html",
    "haho": "https://haho.moe/anime/sjmjiywi",
    "zoro": "https://zoro.to/one-piece-100",
}


if animepahe:
    site_check_index.update(animepahe=animepahe)


def site_check(url):

    initial = time.perf_counter()

    try:
        links = get_appropriate(client, url, lambda r: r == 1)

        if not links:
            return generate_image(*FAILED, "No return")

        obtained_links = 0

        for link_cb, _ in links:
            for _ in ensure_extraction(client, link_cb):
                obtained_links += 1

        if not obtained_links:
            return generate_image(*FAILED, "No links returned")

        return generate_image(
            *SUCCESS,
            "{} url(s), {:.02f}s".format(obtained_links, time.perf_counter() - initial)
        )

    except Exception as _:
        return generate_image(*FAILED, "Project exception")


with open("./api/raw", "w") as raw_file:
    raw_file.write(
        client.get("http://crunchyroll.com/").cookies.get("session_id", "no cookie")
    )


for sitename, site in site_check_index.items():

    img = site_check(site)
    img.save("./api/providers/{}.png".format(sitename), format="png")
    img.close()
