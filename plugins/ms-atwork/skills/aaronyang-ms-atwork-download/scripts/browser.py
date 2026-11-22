"""啟動/連接專用 Edge（持久化 profile，有畫面），供下載腳本以 CDP 附加。

登入一律由使用者在視窗內手動完成；本工具不讀取、不儲存帳密。
CDP 埠只綁 127.0.0.1，跑完請關閉視窗。
"""
from __future__ import annotations

import os
import subprocess
import time
import urllib.request
from pathlib import Path

CDP_PORT = 9333
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
PROFILE = Path(os.environ["LOCALAPPDATA"]) / "ms-atwork-profile"
START_URL = "https://atwork.morganstanley.com"
LOGGED_IN_MARK = "/solium/servlet/ui/"
EDGE_CANDIDATES = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
]


def cdp_alive() -> bool:
    try:
        with urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=2) as r:
            return r.status == 200
    except OSError:
        return False


def ensure_browser() -> None:
    if cdp_alive():
        return
    exe = next((p for p in EDGE_CANDIDATES if Path(p).exists()), None)
    if exe is None:
        raise SystemExit("找不到 Microsoft Edge")
    PROFILE.mkdir(parents=True, exist_ok=True)
    subprocess.Popen(
        [
            exe,
            f"--user-data-dir={PROFILE}",
            f"--remote-debugging-port={CDP_PORT}",
            "--remote-debugging-address=127.0.0.1",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-features=msEdgeSidebarV2",
            START_URL,
        ],
        creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    for _ in range(40):
        if cdp_alive():
            return
        time.sleep(0.5)
    raise SystemExit("Edge 的 CDP 埠沒有回應")


def find_site_page(context):
    """回傳已登入的分頁；沒有就回傳 None。"""
    for page in context.pages:
        if LOGGED_IN_MARK in page.url:
            return page
    return None


def wait_for_login(context, timeout_s: int = 1800):
    deadline = time.time() + timeout_s
    announced = False
    while time.time() < deadline:
        page = find_site_page(context)
        if page is not None:
            return page
        if not announced:
            print("請在開啟的 Edge 視窗手動登入 Morgan Stanley at Work（含 MFA）……", flush=True)
            announced = True
        # 不能用 time.sleep：sync API 要靠 Playwright 呼叫才會處理事件，否則 page.url 不會更新
        if context.pages:
            context.pages[0].wait_for_timeout(2000)
        else:
            time.sleep(2)
    raise SystemExit("等待登入逾時")
