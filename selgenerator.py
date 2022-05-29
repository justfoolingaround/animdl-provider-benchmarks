import io
import json
import os
import pathlib
import re
import zipfile

import httpx
from selenium.common.exceptions import JavascriptException
from selenium.webdriver import Chrome, ChromeOptions

BASE_URL = "https://vizcloud.cloud"
CHROME_LOCATION_PATH = pathlib.Path("C:\\Program Files\\Google\\Chrome\\Application\\")
CHROME_DRIVER_STORAGE_URL = "https://chromedriver.storage.googleapis.com/"


client = httpx.Client()

def waifu_alert(cipher_key, cipher_key_function, *, exptn: JavascriptException=None):
    waifu = os.getenv("JUSTANOTHERWAIFU")

    if waifu is None:
        return


    if cipher_key is None:

        text = "\u002b"

        if cipher_key_function is not None:
            text += f"\n\nGeneration JS function: `{cipher_key_function}`"

        if exptn is not None:
            text += f"\n\nExact JS exception that we seem to have obtained: \n`{exptn!r}`"


        return client.post(
            waifu,
            json={
                "content": "<@!742641737213673483>",
                "embeds": [
                    {
                        "title": "Cipher key generation failed.",
                        "description": text,
                        "color": 0x765bff,
                    }
                ]
            },
        )

    return client.post(
        waifu,
        json={
            "embeds": [
                {
                    "title": "Cipher key generation successful",
                    "description": f"Cipher key: `{cipher_key}`",
                    "color": 0x765bff,
                }
            ]
        },
    )



def get_chromedriver_file_regex(*, file="chromedriver_win32.zip"):
    for chrome_dll in CHROME_LOCATION_PATH.glob("*/chrome.dll"):
        prefix, _ = chrome_dll.parent.name.rsplit(".", 1)
        return re.escape(prefix) + r"\.\d+/" + re.escape(file)


matches = re.findall(
    get_chromedriver_file_regex(), client.get(CHROME_DRIVER_STORAGE_URL).text
)

if not matches:
    raise SystemExit(0)

latest = matches[-1]


chrome_driver = io.BytesIO(client.get(CHROME_DRIVER_STORAGE_URL + latest).content)
exe_io = io.BytesIO()

with zipfile.ZipFile(chrome_driver) as zip_file:
    with zip_file.open("chromedriver.exe", "r") as zipped_exe:
        exe_io = zipped_exe.read()

with open("./chromedriver.exe", "wb") as exe:
    exe.write(exe_io)


def trace_origin(script_js, function_name):

    search_regex = re.compile(
        rf"\s*{re.escape(function_name)}\s*=\s*(.+?)\s*(?:[;,]|$)"
    )

    match = search_regex.search(script_js)

    if match and not any(
        match.group(1).startswith(_) for _ in ["function", "(function"]
    ):
        return trace_origin(script_js, match.group(1))

    return function_name


script_js_regex = re.compile(
    r'<script type="text/javascript" src="(?P<script_js>(.*?)\?v=(\d+))"></script>'
)

deobfuscated_js_function_regex = re.compile(r"_0x[0-9a-f]+(?=\()")

cipher_key_regex = re.compile(r"this\['a'\]\((.+?)\)(?=,\()")
table_regex = re.compile(r"[;:,]var _0x[a-f0-9]+=(\[.+?\]\[.*?\]\(''\))(?:$|;)")


script_js_url = BASE_URL + script_js_regex.search(
    client.get(BASE_URL + "/embed/2EYDX1968J1Q").text
).group("script_js")

script_js = client.get(script_js_url).text

core_string, _ = cipher_key_regex.search(script_js).group(1).rsplit(",", 1)

cipher_key_function = deobfuscated_js_function_regex.sub(
    lambda match: trace_origin(script_js, match.group(0)),
    core_string,
)

table_function = deobfuscated_js_function_regex.sub(
    lambda match: trace_origin(script_js, match.group(0)),
    table_regex.search(script_js).group(1),
)


opts = ChromeOptions()
opts.binary_location = (CHROME_LOCATION_PATH / "chrome.exe").as_posix()
opts.headless = True

driver = Chrome(options=opts)


driver.get(BASE_URL + "/embed/2EYDX1968J1Q")

exptn = None


try:
    cipher_key = driver.execute_script(f"return {cipher_key_function}")
except JavascriptException as _:
    cipher_key = None
    exptn = _

waifu_alert(
    cipher_key,
    cipher_key_function,
    exptn=exptn,
)

with open("api/selgen.json", "w") as json_file:
    json.dump(
        {
            "cipher_key": cipher_key,
        },
        json_file,
        indent=4,
    )
