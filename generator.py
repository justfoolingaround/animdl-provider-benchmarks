import time

from animdl.core.cli.helpers import ensure_extraction
from animdl.core.cli.http_client import client
from animdl.core.codebase.providers import get_appropriate

from image import generate_image


def animepahe_one_piece(*, query="One Piece"):
    return "https://animepahe.com/anime/{[session]}".format(client.get(
        'https://animepahe.com/api?m=search&l=8&q={}'.format(query)
    ).json().get('data')[0])


FAILED = ("./assets/failed.png", (218, 68, 83))
SUCCESS = ("./assets/success.png", (50, 198, 113))

site_check_index = {
    'nineanime': 'https://9anime.to/watch/one-piece.ov8',
    'animepahe': animepahe_one_piece(),
    'crunchyroll': 'https://www.crunchyroll.com/one-piece',
    'allanime': 'https://allanime.site/anime/ReooPAxPMsHM4KPMY',
    'animeout': 'https://www.animeout.xyz/download-one-piece-episodes-latest/',
    'animixplay': 'https://animixplay.to/v1/one-piece',
    'animtime': 'https://animtime.com/title/5',
    'gogoanime': 'https://gogoanime.cm/category/one-piece',
    'tenshi': 'https://tenshi.moe/anime/kjfrhu3s',
    'twist': 'https://twist.moe/a/one-piece',
    'kawaiifu': 'https://kawaiifu.com/tv-series/one-piece-720p-hd.html',
    'haho': 'https://haho.moe/anime/sjmjiywi',
    'zoro': 'https://zoro.to/one-piece-100',
}

def site_check(url):
    
    initial = time.perf_counter()
    
    try:
        links = (get_appropriate(client, url, lambda r: r == 1))
        
        if not links:
            return generate_image(*FAILED, "No return")

        obtained_links = 0

        for link_cb, _ in links:
            for _ in ensure_extraction(client, link_cb):
                obtained_links += 1

        if not obtained_links:
            return generate_image(
                *FAILED, "No links returned"
            )


        return generate_image(
            *SUCCESS, "{} url(s), {:.02f}s".format(obtained_links, time.perf_counter() - initial)
        )


    except Exception as _:
        return generate_image(
            *FAILED, "Project exception"
        )


for sitename, site in site_check_index.items():
    
    img = site_check(site)
    img.save(
        "./api/providers/{}.png".format(sitename), format="png"
    )
    img.close()

with open('./api/raw', 'w') as raw_file:
    raw_file.write(client.get('http://crunchyroll.com/').cookies.get('session_id'))
