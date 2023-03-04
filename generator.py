import json
import logging
import pathlib
import sys
import threading
import time
from collections import namedtuple
from queue import Queue

from animdl.core.cli.helpers import ensure_extraction
from animdl.core.cli.http_client import client
from animdl.core.codebase.providers import get_appropriate
from animdl.core.config import (
    ALLANIME,
    ANIMEOUT,
    ANIMEPAHE,
    ANIMTIME,
    GOGOANIME,
    HAHO,
    KAWAIIFU,
    MARIN,
    NINEANIME,
    ZORO,
)

from image import generate_image

status = namedtuple(
    "status",
    (
        "status",
        "message",
    ),
)

API_PATH = pathlib.Path(".") / "api"
API_PATH.mkdir(exist_ok=True)

ASSETS_PATH = pathlib.Path(".") / "assets"
ASSETS_PATH.mkdir(exist_ok=True)

LOGGING_FILE = "provider_run.dev_log"


class DeathThread(threading.Thread):

    kill_state = threading.Event()

    def run(self):
        sys.settrace(self.global_trace)
        return super().run()

    def global_trace(self, stack_frame, reason, *args, **kwargs):
        if reason == "call":
            return self.local_trace

    def local_trace(self, stack_frame, reason, *args, **kwargs):
        if self.kill_state.is_set() and reason == "line":
            raise SystemExit()
        return self.local_trace

    def kill(self):
        return self.kill_state.set()


logging.basicConfig(
    filename=LOGGING_FILE,
    filemode="a",
    format="%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s",
    datefmt="%H:%M:%S",
    level=logging.DEBUG,
)


logger = logging.getLogger("logging")


def fetch_animepahe_session(session, query="one piece"):

    response = session.get(
        "https://animepahe.com/api",
        params={"m": "search", "l": 8, "q": query},
    )

    try:
        data = response.json()
    except json.JSONDecodeError:
        return None

    return ANIMEPAHE + f"anime/{data['data'][0]['session']}"


FAILED = (ASSETS_PATH / "failed.png", (218, 68, 83))
SUCCESS = (ASSETS_PATH / "success.png", (50, 198, 113))


animepahe_session = fetch_animepahe_session(client)

site_check_index = {
    "nineanime": NINEANIME + "watch/one-piece.ov8",
    "allanime": ALLANIME + "anime/ReooPAxPMsHM4KPMY",
    "animeout": ANIMEOUT + "download-one-piece-episodes-latest/",
    "animtime": ANIMTIME + "title/5",
    "gogoanime": GOGOANIME + "category/one-piece",
    "kawaiifu": KAWAIIFU + "tv-series/one-piece-720p-hd.html",
    "haho": HAHO + "anime/sjmjiywi",
    "marin": MARIN + "anime/fntoucz2",
    "zoro": ZORO + "one-piece-100",
}


if animepahe_session is not None:
    site_check_index.update(animepahe=animepahe_session)


max_check_timeout_per = 60


def run_for_atmost(timeout):
    def decorator(func):
        def wrapper(*args, **kwargs):
            def run():
                func(*args, **kwargs)

            t = DeathThread(target=run)
            t.start()
            t.join(timeout)

            if t.is_alive():
                t.kill()
                raise TimeoutError(
                    f"{run!r} with ({(args, kwargs)}) took too long to run"
                )

            return t

        return wrapper

    return decorator


@run_for_atmost(max_check_timeout_per)
def attempt_scraping_for(session, url, *, result: Queue) -> status:

    initial = time.perf_counter()

    try:
        links = get_appropriate(session, url, lambda r: r == 1)
        obtained_links = 0

        for link_cb, _ in links:
            for _ in ensure_extraction(client, link_cb):
                obtained_links += 1

        if not obtained_links:
            result.put(status(False, "No urls obtained"))

        result.put(
            status(
                True, f"{obtained_links} url(s), {time.perf_counter() - initial:02f}s"
            )
        )

    except Exception as exception:
        logger.error(f"Failed to scrape {url!r} with {exception!r}", exc_info=True)
        result.put(status(False, f"Internal error"))


PROVIDERS_API_PATH = API_PATH / "providers"
PROVIDERS_API_PATH.mkdir(exist_ok=True)


for sitename, site in site_check_index.items():

    result = Queue()

    try:
        attempt_scraping_for(client, site, result=result)
        if result.empty():
            raise RuntimeError("Result queue is empty")

        state = result.get()
    except (TimeoutError, RuntimeError):
        state = status(False, "Provider took too long")

    if state.status:
        image = generate_image(*SUCCESS, state.message)
    else:
        image = generate_image(*FAILED, state.message)

    image.save(PROVIDERS_API_PATH / f"{sitename}.png")
