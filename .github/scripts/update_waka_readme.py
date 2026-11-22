import base64
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime


START = "<!--START_SECTION:waka-->"
END = "<!--END_SECTION:waka-->"


def format_date(value):
    return datetime.fromisoformat(value.replace("Z", "+00:00")).strftime("%d %B %Y")


def make_graph(percent, length=25):
    proportion = percent / 100 * length
    filled = int(proportion + 0.5)
    return ">" * filled + "-" * (length - filled)


def generate(stats):
    title = f"From: {format_date(stats['start'])} - To: {format_date(stats['end'])}"
    lines = [title, "", f"Total Time: {stats['human_readable_total']}"]
    languages = stats.get("languages") or []
    pad_len = max((len(language["name"]) for language in languages[:6]), default=0)

    for language in languages[:6]:
        name = language["name"].ljust(pad_len)
        time = language["text"]
        percent = float(language["percent"])
        bar = make_graph(percent)
        lines.append(
            f"{name}   {time:<22}{bar}   {percent:.2f} %"
        )

    return "\n".join(lines)


def fetch_stats(token):
    if token.startswith("waka_"):
        authorization = "Bear" + "er " + token
    else:
        authorization = "Basic " + base64.b64encode(token.encode()).decode()

    url = "https://wakatime.com/api/v1/users/current/stats/all_time"
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": authorization,
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)["data"]
    except urllib.error.HTTPError as error:
        raise RuntimeError(
            f"WakaTime API returned {error.code} {error.reason}; "
            "verify that WAKATIME_API_KEY contains a read-enabled OAuth access token"
        ) from error
    except urllib.error.URLError as error:
        raise RuntimeError(f"Could not reach WakaTime API: {error.reason}") from error


def update_readme(readme, stats):
    pattern = re.compile(
        rf"{re.escape(START)}\s*\n```txt\n.*?\n```\n\s*\n?{re.escape(END)}",
        re.DOTALL,
    )
    replacement = f"{START}\n\n```txt\n{generate(stats)}\n```\n\n{END}"
    updated, replacements = pattern.subn(replacement, readme)
    if replacements != 1:
        raise RuntimeError("README must contain exactly one waka stats section")
    return updated


def main():
    token = os.environ.get("WAKATIME_API_KEY", "").strip()
    if not token:
        raise RuntimeError("WAKATIME_API_KEY is missing")

    with open("README.md", encoding="utf-8") as file:
        readme = file.read()

    updated = update_readme(readme, fetch_stats(token))
    with open("README.md", "w", encoding="utf-8") as file:
        file.write(updated)


if __name__ == "__main__":
    try:
        main()
    except RuntimeError as error:
        print(error, file=sys.stderr)
        sys.exit(1)
