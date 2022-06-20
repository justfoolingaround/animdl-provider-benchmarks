import json
import pathlib
import time

from animdl.core.cli.helpers import ensure_extraction
from animdl.core.cli.http_client import client
from animdl.core.codebase.providers import get_appropriate

from image import generate_image

API_PATH = pathlib.Path(".") / "api"
API_PATH.mkdir(exist_ok=True)

ASSETS_PATH = pathlib.Path(".") / "assets"
ASSETS_PATH.mkdir(exist_ok=True)


def animepahe_one_piece(*, query="One Piece"):

    response = client.get("https://animepahe.com/api?m=search&l=8&q={}".format(query))

    try:
        data = response.json()
    except json.JSONDecodeError:
        return None

    return f"https://animepahe.com/anime/{data['data'][0]['session']}"


GOGOANIME_KEYS = API_PATH / "gogoanime.json"


def scrape_keys():
    import json
    import os

    import regex

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
                    "description": "KEY (encrypted-ajax): `{0[key]}`\nKEY (streams): `{0[second_key]}`\nIV: `{0[iv]}`".format(
                        out
                    ),
                    "color": 0x7AD7F0,
                }
            ]
        },
    )


scrape_keys()

FAILED = (ASSETS_PATH / "failed.png", (218, 68, 83))
SUCCESS = (ASSETS_PATH / "success.png", (50, 198, 113))


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


if animepahe is not None:
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
            "{} url(s), {:.02f}s".format(obtained_links, time.perf_counter() - initial),
        )

    except Exception as _:
        return generate_image(*FAILED, "Project exception")


with open(API_PATH / "raw", "w") as raw_file:
    raw_file.write(
        client.get("http://crunchyroll.com/").cookies.get("session_id", "no cookie")
    )

PROVIDERS_API_PATH = API_PATH / "providers"


for sitename, site in site_check_index.items():
    with site_check(site) as image:
        image.save(PROVIDERS_API_PATH / f"{sitename}.png", format="png")
