# /// script
# requires-python = ">=3.12"
# dependencies = ["playwright", "python-dotenv"]
# ///
"""Download every document from Morgan Stanley at Work. Rerunnable: finished items are skipped.

    uv run download.py                        # all stages
    uv run download.py --stage docs,tax       # only these stages
    uv run download.py --refresh-grants       # regenerate the grant detail PDFs
    uv run download.py --home PATH            # home folder (default $MS_ATWORK_HOME or ~/.config/ms-atwork)

Stages: docs tax plan reports grants (the manifest is rebuilt at the end of every run).
The output folder and report IDs come from <home>/.env and <home>/reports.toml.
The user signs in by hand in the Edge window; the session cookie stays in memory only.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import re
import sys
import time
import zipfile
from datetime import date
from pathlib import Path
from urllib.parse import parse_qs, unquote, urlparse

from playwright.sync_api import sync_playwright

import browser as b
import config

# Set in main() once the home folder is known.
ROOT: Path
LEDGER: Path
SERVLET = "https://atwork.morganstanley.com/solium/servlet/"
UI = SERVLET + "ui/"
DL_PATTERN = "**/userCommonPrivateDynamicFileDownload.do*"
TIMEOUT_MS = 20_000
ATTEMPTS = 3  # 首次 + 重試 2 次
START_DATE = "2019-01-01"
DATE_RE = r"\d{2}-[A-Z][a-z]{2}-\d{4}"
CLICK_ROW = r"""([i,want])=>{const rs=[...document.querySelectorAll('tr')].filter(r=>r.querySelector('a[href="javascript:;"]'));
  const a=rs[i]&&rs[i].querySelector('a');if(!a)return 'none';const t=a.innerText.trim();if(t===want)a.click();return t;}"""
CATEGORY = {
    "Quarterly Statement": "對帳單",
    "Release Confirm": "交易確認",
    "Consolidated Confirm": "交易確認",
}


def mask(s: str) -> str:
    """遮罩長數字（員工編號、授予內部編號等），避免出現在記錄裡。"""
    return re.sub(r"\d{5,}", "#", s or "")


def log(msg: str) -> None:
    print(mask(msg) if msg.startswith("!") else msg, flush=True)


class SessionExpired(RuntimeError):
    pass


def retry(label, fn, attempts=ATTEMPTS, on_fail=None):
    last = None
    for i in range(attempts):
        try:
            return fn()
        except SessionExpired:
            raise
        except Exception as e:  # noqa: BLE001
            last = e
            log(f"! {label} 第 {i + 1} 次失敗：{type(e).__name__} {str(e)[:120]}")
            if on_fail and i + 1 < attempts:
                try:
                    on_fail()
                except Exception:  # noqa: BLE001
                    pass
            time.sleep(2)
    raise last


def safe_name(name: str) -> str:
    name = Path(name.replace("\\", "/")).name
    name = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name).strip(" .")
    return name or "unnamed"


def filename_from(headers: dict, url: str = "", fallback: str = "") -> str:
    cd = headers.get("content-disposition", "")
    m = re.search(r"filename\*\s*=\s*[^']*''([^;]+)", cd, re.I)
    if m:
        return safe_name(unquote(m.group(1).strip()))
    m = re.search(r'filename\s*=\s*"([^"]+)"', cd, re.I) or re.search(r"filename\s*=\s*([^;]+)", cd, re.I)
    if m:
        return safe_name(m.group(1).strip())
    fn = parse_qs(urlparse(url).query).get("fn", [""])[0]
    return safe_name(fn or fallback)


def check_file(data: bytes, headers: dict, label: str) -> None:
    ctype = headers.get("content-type", "").lower()
    if "text/html" in ctype and not headers.get("content-disposition"):
        low = data[:4000].lower()
        if b"login" in low or b"sign in" in low or b"session" in low:
            raise SessionExpired(f"{label}：回應是登入頁，session 可能已失效")
        raise RuntimeError(f"{label}：回應是 HTML，不是檔案")
    if not data:
        raise RuntimeError(f"{label}：空檔")


class Store:
    def __init__(self):
        ROOT.mkdir(parents=True, exist_ok=True)
        self.items: dict = json.loads(LEDGER.read_text("utf-8")) if LEDGER.exists() else {}
        self.failures: list[str] = []
        self.dups: list[str] = []
        self.new = 0
        self.skipped = 0

    def done(self, key: str) -> bool:
        it = self.items.get(key)
        if not it:
            return False
        p = ROOT / it["path"]
        return p.exists() and p.stat().st_size == it["size"]

    def flush(self) -> None:
        tmp = LEDGER.with_suffix(".tmp")
        tmp.write_text(json.dumps(self.items, ensure_ascii=False, indent=1), "utf-8")
        tmp.replace(LEDGER)

    def write(self, folder: str, name: str, data: bytes) -> tuple[Path, bool]:
        """依檔名存檔；同名同內容視為重複，同名不同內容加 _2、_3。回傳 (路徑, 是否重複)。"""
        d = ROOT / folder
        d.mkdir(parents=True, exist_ok=True)
        stem, suffix = Path(name).stem, Path(name).suffix
        digest = hashlib.sha256(data).digest()
        n = 1
        while True:
            p = d / (name if n == 1 else f"{stem}_{n}{suffix}")
            if not p.exists():
                part = p.with_name(p.name + ".part")
                part.write_bytes(data)
                part.replace(p)
                return p, False
            if p.stat().st_size == len(data) and hashlib.sha256(p.read_bytes()).digest() == digest:
                return p, True
            n += 1

    def record(self, key, folder, name, data, doc_type, doc_date="", posted="", source=""):
        path, dup = self.write(folder, name, data)
        rel = str(path.relative_to(ROOT))
        self.items[key] = {
            "category": folder.split("\\")[0], "type": doc_type, "doc_date": doc_date, "posted": posted,
            "path": rel, "size": path.stat().st_size, "source": source,
        }
        self.flush()
        if dup:
            self.dups.append(f"{doc_type} {doc_date} → {path.name}")
        self.new += 1
        log(f"  {'重複' if dup else '存檔'} {rel} ({len(data):,} bytes)")
        return path

    def fail(self, label: str, e: Exception) -> None:
        msg = f"{label}: {type(e).__name__} {str(e)[:150]}"
        self.failures.append(mask(msg))
        log("! 失敗 " + msg)

    def write_manifest(self) -> None:
        rows = sorted(self.items.values(), key=lambda r: (r["category"], r["type"], r["doc_date"], r["path"]))
        with (ROOT / "manifest.csv").open("w", newline="", encoding="utf-8-sig") as fh:
            w = csv.writer(fh)
            w.writerow(["分類", "文件類型", "文件日期", "張貼日期", "檔名", "大小", "來源"])
            for r in rows:
                w.writerow([r["category"], r["type"], r["doc_date"], r["posted"], Path(r["path"]).name, r["size"], r["source"]])


class Site:
    def __init__(self, pw, store: Store):
        self.pw = pw
        self.store = store
        b.ensure_browser()
        self.ctx = pw.chromium.connect_over_cdp(b.CDP_URL).contexts[0]
        self.page = b.wait_for_login(self.ctx)
        self._require_english()
        self.page.set_default_timeout(TIMEOUT_MS)
        self.captured: list[str] = []
        self.ctx.route(DL_PATTERN, self._capture)
        self._hb = None
        self._hc = None

    def _require_english(self):
        # 選擇器、日期格式和下載記錄的鍵值都依賴英文介面；其他語言會讓各階段逾時，
        # 或把已下載的文件當成新檔。
        if re.search(r"[^\x00-\x7f]", self.page.title()):
            raise SystemExit("網站介面不是英文：請在 Edge 視窗的 Profile 設定把語言改成 English 再重跑。")

    def _capture(self, route):
        # 只取網址，改由 session 直接 GET。不能 abort：網站是讓 iframe 導向此網址，
        # abort 會讓 iframe 掉到 chrome-error 頁；回 204 則 iframe 留在原頁。
        self.captured.append(route.request.url)
        route.fulfill(status=204, body="")

    def close(self):
        if self._hb:
            self._hb.close()

    # ---------- 共用 ----------
    def get(self, url: str, label: str):
        """帶 session cookie 直接 GET（等同 curl）。"""
        def go():
            r = self.ctx.request.get(url, timeout=TIMEOUT_MS)
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            data, headers = r.body(), r.headers
            check_file(data, headers, label)
            return data, headers
        return retry(label, go)

    def goto(self, path: str, frame_url: str, ready):
        """導覽並等 iframe 就緒；iframe 卡住就重新載入。"""
        def go():
            self.page.goto(UI + path, wait_until="domcontentloaded", timeout=TIMEOUT_MS)
            end = time.time() + 45
            while time.time() < end:
                for f in self.page.frames:
                    if frame_url in f.url:
                        try:
                            if ready(f):
                                return f
                        except Exception:  # noqa: BLE001
                            pass
                self.page.wait_for_timeout(500)
            raise TimeoutError(f"iframe 未就緒：{path}")
        return retry(f"開啟 {path}", go)

    def wait_capture(self, before: int, seconds: float = 20) -> str:
        end = time.time() + seconds
        while time.time() < end:
            if len(self.captured) > before:
                return self.captured[-1]
            self.page.wait_for_timeout(200)
        raise TimeoutError("等不到下載網址")

    def html_to_pdf(self, html: str) -> bytes:
        """把 GET 回來的 HTML 去掉 script 後離線轉 PDF（直接導覽該頁會卡住）。"""
        clean = re.sub(r"<script\b.*?</script>", "", html, flags=re.S | re.I)
        clean = re.sub(r"<head([^>]*)>", lambda m: f'<head{m.group(1)}><base href="{SERVLET}">', clean, count=1, flags=re.I)
        if self._hb is None:
            self._hb = self.pw.chromium.launch(channel="msedge", headless=True)
            self._hc = self._hb.new_context(java_script_enabled=False)
            self._hc.route("**/*", self._asset)
        page = self._hc.new_page()
        try:
            page.set_content(clean, wait_until="load", timeout=30_000)
            return page.pdf(format="A4", print_background=True)
        finally:
            page.close()

    def _asset(self, route):
        r = route.request
        if r.resource_type in ("stylesheet", "image", "font") and "morganstanley.com" in r.url:
            try:
                route.fulfill(response=self.ctx.request.fetch(r.url, timeout=15_000))
                return
            except Exception:  # noqa: BLE001
                pass
        route.abort()

    # ---------- Account Documents ----------
    def docs_frame(self):
        return self.goto("documents/index", "ParticipantDocumentsPage", lambda f: bool(self.pager(f)))

    @staticmethod
    def pager(f):
        t = f.evaluate(r"[...document.querySelectorAll('.gwt-HTML')].map(e=>e.innerText.trim()).filter(t=>/^\d+-\d+ of \d+$/.test(t))")
        return t[0] if t else ""

    @staticmethod
    def rows(f):
        js = r"""()=>[...document.querySelectorAll('tr')].filter(r=>r.querySelector('a[href="javascript:;"]'))
                 .map(r=>[...r.children].map(c=>c.innerText.trim()))"""
        return [r for r in f.evaluate(js) if len(r) >= 3 and re.fullmatch(DATE_RE, r[1]) and re.fullmatch(DATE_RE, r[2])]

    def next_page(self, f):
        cur = self.pager(f)
        f.locator('img[aria-label="Next page"]').first.click()
        end = time.time() + TIMEOUT_MS / 1000
        while time.time() < end:
            if self.pager(f) not in ("", cur) and self.rows(f):
                return
            self.page.wait_for_timeout(200)
        raise TimeoutError("翻頁逾時")

    def goto_doc_page(self, target: int):
        f = self.docs_frame()
        for _ in range(target):
            self.next_page(f)
        return f

    def stage_docs(self):
        s = self.store
        f = self.docs_frame()
        total = int(self.pager(f).split(" of ")[1])
        log(f"Account Documents 共 {total} 筆")
        seen: dict[str, int] = {}
        count = page_no = 0
        while True:
            for i, row in enumerate(self.rows(f)):
                dtype, ddate, posted = row[0], row[1], row[2]
                base = f"{dtype}|{ddate}|{posted}"
                seen[base] = seen.get(base, 0) + 1
                key = f"doc|{base}|{seen[base]}"
                count += 1
                if len(row) > 3 and row[3] not in ("N/A", ""):
                    log(f"! 注意：第 {count} 筆有 Inserts/Brochures：{row[3][:40]}")
                if s.done(key):
                    s.skipped += 1
                    continue
                try:
                    self.fetch_doc(f, i, row, key, count, total)
                except SessionExpired:
                    raise
                except Exception as e:  # noqa: BLE001
                    s.fail(f"{dtype} {ddate}", e)
                    f = retry("重載文件頁", lambda: self.goto_doc_page(page_no))
                time.sleep(1)
            nxt = f.locator('img[aria-label="Next page"]').first
            if nxt.get_attribute("aria-disabled") == "true":
                break
            page_no += 1
            retry("翻頁", lambda: self.next_page(f))
        log(f"Account Documents 清單 {count} 筆（網站總數 {total}）")
        if count != total:
            s.failures.append(f"清單筆數 {count} 與網站總數 {total} 不符")

    def fetch_doc(self, f, i, row, key, n, total):
        dtype, ddate, posted = row[0], row[1], row[2]
        label = f"[{n}/{total}] {dtype} {ddate}"

        def get_url():
            before = len(self.captured)
            got = f.evaluate(CLICK_ROW, [i, dtype])
            if got != dtype:
                raise RuntimeError(f"列內容與預期不符：{got}")
            return self.wait_capture(before)

        url = retry(label, get_url)
        data, headers = self.get(url, label)
        name = filename_from(headers, fallback=f"{dtype} {ddate}.pdf")
        folder = "稅務" if re.search(r"1042|W-?8", dtype, re.I) else CATEGORY.get(dtype, "其他")
        log(label)
        self.store.record(key, folder, name, data, dtype, ddate, posted, "Account Documents")

    # ---------- 稅務 ZIP ----------
    def stage_tax(self):
        s = self.store
        f = self.docs_frame()
        btn = f.get_by_text("Download tax information").first
        btn.click()
        self.page.wait_for_timeout(800)
        years = f.evaluate(r"[...document.querySelectorAll('div')].filter(e=>!e.children.length&&/^\d{4} tax year$/.test(e.innerText.trim())).map(e=>e.innerText.trim())")
        self.page.keyboard.press("Escape")
        log(f"Tax year：{years}")
        for label in years:
            key = f"taxzip|{label}"
            if s.done(key):
                s.skipped += 1
                continue
            try:
                def click_year():
                    before = len(self.captured)
                    item = f.get_by_text(label, exact=True).first
                    if not item.is_visible():
                        btn.click()
                        self.page.wait_for_timeout(800)
                    item.click()
                    return self.wait_capture(before, 40)

                url = retry(label, click_year)
                data, headers = self.get(url, label)
                if data[:2] != b"PK":
                    raise RuntimeError("不是 ZIP")
                name = filename_from(headers, fallback=f"{label}.zip")
                year = label[:4]
                with zipfile.ZipFile(io.BytesIO(data)) as z:
                    for m in z.infolist():
                        if not m.is_dir():
                            s.record(f"taxfile|{year}|{m.filename}", f"稅務\\{label}", safe_name(m.filename), z.read(m),
                                     "Tax year ZIP 內容", year, "", name)
                s.record(key, "稅務", name, data, "Tax year ZIP", year, "", "Download tax information")
            except SessionExpired:
                raise
            except Exception as e:  # noqa: BLE001
                s.fail(label, e)
            time.sleep(1)

    # ---------- 計畫文件 ----------
    def stage_plan(self):
        s = self.store
        f = self.docs_frame()
        for head in ("Plan Documents And Agreements", "Grant Agreements"):
            try:
                f.locator("td", has_text=re.compile("^" + head + r" \(\d+\)$")).first.click()
                self.page.wait_for_timeout(500)
            except Exception as e:  # noqa: BLE001
                log(f"! 展開 {head} 失敗：{type(e).__name__}")
        links = f.evaluate(r"""()=>{
          const heads=[...document.querySelectorAll('span,td')].filter(e=>!e.children.length&&/^(Plan Documents And Agreements( \(\d+\))?|Grant Agreements( \(\d+\))?|Guides And General Reference|Tax Documents)$/.test(e.innerText.trim()));
          const start=heads.find(e=>/^Plan Documents/.test(e.innerText.trim()));
          const out=[];
          for(const a of document.querySelectorAll('a')){
            if(!(start.compareDocumentPosition(a)&Node.DOCUMENT_POSITION_FOLLOWING))continue;
            let sec='';for(const h of heads){if(h.compareDocumentPosition(a)&Node.DOCUMENT_POSITION_FOLLOWING)sec=h.innerText.trim().replace(/ \(\d+\)$/,'');}
            const raw=a.getAttribute('href')||'';const text=a.innerText.trim();
            if(!text||raw==='javascript:void(0);')continue;
            out.push({sec,text,raw,href:a.href});
          }
          return out;}""")
        log(f"計畫／授予／指南連結 {len(links)} 個（去重前）")
        seen = set()
        for lk in links:
            sec, text, raw, href = lk["sec"], lk["text"], lk["raw"], lk["href"]
            if raw == "javascript:;":
                if sec != "Grant Agreements":  # Grant 區的是群組標題
                    self.plan_click(f, lk)
                continue
            q = parse_qs(urlparse(href).query)
            ident = (q.get("template_data_id") or q.get("template_id") or q.get("employeeGrantId") or [None])[0]
            ident = ident or f"page|{text[:60]}"
            key = f"plan|{ident}"
            if key in seen:
                continue
            seen.add(key)
            if s.done(key):
                s.skipped += 1
                continue
            folder = "稅務" if re.search(r"W-?8", text, re.I) else "計畫文件"
            try:
                self.plan_get(key, folder, sec, text, href)
            except SessionExpired:
                raise
            except Exception as e:  # noqa: BLE001
                s.fail(f"{sec} / {text[:40]}", e)
            time.sleep(1)

    def plan_get(self, key, folder, sec, text, href):
        s = self.store
        title = safe_name(text[:80])
        if "#" in href and "userGwtAction" in href:
            s.record(key, folder, title + ".pdf", self.gwt_popup_pdf(href), text[:80], "", "", sec + "（網頁轉 PDF）")
            return

        def go():
            r = self.ctx.request.get(href, timeout=TIMEOUT_MS)
            if r.status != 200:
                raise RuntimeError(f"HTTP {r.status}")
            return r.body(), r.headers

        data, headers = retry(text[:30], go)
        if data[:4] == b"%PDF" or headers.get("content-disposition"):
            s.record(key, folder, filename_from(headers, href, title + ".pdf"), data, text[:80], "", "", sec)
        elif "html" in headers.get("content-type", ""):
            pdf = self.html_to_pdf(data.decode("utf-8", "replace"))
            s.record(key, folder, title + ".pdf", pdf, text[:80], "", "", sec + "（網頁轉 PDF）")
        else:
            raise RuntimeError(f"未知回應 {headers.get('content-type')}")

    def gwt_popup_pdf(self, href) -> bytes:
        """GWT 彈窗（條款類）：開分頁等內容渲染，再把 DOM 離線轉 PDF。"""
        page = self.ctx.new_page()
        try:
            try:
                page.goto(href, wait_until="commit", timeout=TIMEOUT_MS)
            except Exception:  # noqa: BLE001
                pass
            end = time.time() + 30
            last = -1
            while time.time() < end:
                page.wait_for_timeout(1500)
                n = page.evaluate("document.body?document.body.innerText.length:0")
                if n > 200 and n == last:
                    break
                last = n
            if last <= 200:
                raise TimeoutError("彈窗內容未載入")
            return self.html_to_pdf(page.content())
        finally:
            page.close()

    def plan_click(self, f, lk):
        s = self.store
        key = f"plan|click|{lk['text'][:60]}"
        if s.done(key):
            s.skipped += 1
            return
        try:
            # 這類連結由站內 pdf.js 檢視器開啟，從回應取得網址後直接 GET
            def is_pdf(r):
                return "application/pdf" in r.headers.get("content-type", "").lower()

            with self.ctx.expect_event("response", is_pdf, timeout=30_000) as ri:
                f.get_by_role("link", name=lk["text"], exact=True).first.click()
            data, headers = self.get(ri.value.url, lk["text"])
            s.record(key, "計畫文件", filename_from(headers, fallback=safe_name(lk["text"]) + ".pdf"), data,
                     lk["text"][:80], "", "", lk["sec"])
        except SessionExpired:
            raise
        except Exception as e:  # noqa: BLE001
            s.fail(f"{lk['sec']} / {lk['text'][:40]}", e)

    # ---------- 報表 ----------
    def stage_reports(self):
        today = date.today().isoformat()
        self.report_statement(today)
        for name, rid in config.load_reports():
            for fmt, label, ext in (("pdf", "PDF", "pdf"), ("xlsx", "Excel Workbook (*.xlsx)", "xlsx")):
                key = f"report|{name}|{today}|{fmt}"
                if self.store.done(key):
                    self.store.skipped += 1
                    continue
                try:
                    retry(f"{name} {fmt}", lambda: self.run_report(key, name, rid, label, ext, today), attempts=2)
                except SessionExpired:
                    raise
                except Exception as e:  # noqa: BLE001
                    self.store.fail(f"{name} {fmt}", e)
                time.sleep(1)

    def run_report(self, key, name, rid, fmt_label, ext, today):
        f = self.goto(f"activity/reports/{rid}", "PtpExtractRunPage", lambda fr: fr.get_by_text("Run Report").last.is_visible())
        dates = f.locator("input.duet-date__input")
        has_period = f.locator("select").first.evaluate("e=>[...e.options].some(o=>o.text==='Custom')")
        if has_period:
            f.locator("select").first.select_option(label="Custom")
            self.page.wait_for_timeout(500)
            for idx, val in ((0, START_DATE), (1, today)):
                dates.nth(idx).fill(val)
                dates.nth(idx).press("Tab")
            got = (dates.nth(0).input_value(), dates.nth(1).input_value())
            if got != (START_DATE, today):
                raise RuntimeError(f"日期未生效 {got}")
            span = f"{START_DATE}_{today}"
        else:
            span = f"截至{today}"
        box = f.locator("tr", has_text="Show Withdrawal By Lot").locator('input[type="checkbox"]')
        if box.count():
            box.first.check()
        f.locator("select", has=f.locator("option", has_text="Printable Web Page")).first.select_option(label=fmt_label)
        before = len(self.captured)
        f.get_by_text("Run Report").last.click()
        # 報表產生後跳對話框，點 "click here" 才會導向下載網址
        f.get_by_text("click here").last.wait_for(state="visible", timeout=180_000)
        f.get_by_text("click here").last.click()
        url = self.wait_capture(before, TIMEOUT_MS / 1000)
        data, _ = self.get(url, name)
        if not data.startswith(b"%PDF" if ext == "pdf" else b"PK"):
            raise RuntimeError(f"內容不是 {ext}")
        self.store.record(key, "報表", f"{name} {span}.{ext}", data, name, today, "", "Reports")

    def report_statement(self, today):
        key = f"report|Account Summary|{today}|pdf"
        if self.store.done(key):
            self.store.skipped += 1
            return

        def run():
            self.goto("activity/reports/statement", "userStatement.do", lambda fr: fr.locator("input[type=submit]").first.is_visible())
            self.page.wait_for_timeout(4000)  # iframe 載入後會再換一次，等穩定後重新取得
            f = next(x for x in self.page.frames if "userStatement.do" in x.url)
            dates = f.locator("input.duet-date__input")
            for idx, val in ((0, START_DATE), (1, today)):
                dates.nth(idx).fill(val)
                dates.nth(idx).press("Tab")
            f.locator('input[name="view_as_radio_buttons"]').nth(1).check()
            got: list[bytes] = []

            def grab(route):
                # PDF 是以導覽回傳，事後讀不到內容，要在請求當下取得
                if not route.request.is_navigation_request():
                    route.fallback()
                    return
                resp = route.fetch(timeout=90_000)
                if resp.body()[:4] == b"%PDF":
                    got.append(resp.body())
                    route.fulfill(status=204, body="")
                else:
                    route.fulfill(response=resp)

            self.ctx.route("**/solium/servlet/**", grab)
            try:
                f.locator("input[type=submit]").first.click()
                end = time.time() + 90
                while not got and time.time() < end:
                    self.page.wait_for_timeout(300)
            finally:
                self.ctx.unroute("**/solium/servlet/**", grab)
            if not got:
                raise TimeoutError("等不到 Account Summary PDF")
            self.store.record(key, "報表", f"Account Summary {START_DATE}_{today}.pdf", got[0], "Account Summary", today, "", "Reports")

        try:
            retry("Account Summary", run, attempts=2)
        except SessionExpired:
            raise
        except Exception as e:  # noqa: BLE001
            self.store.fail("Account Summary", e)

    # ---------- 授予明細 ----------
    def stage_grants(self, refresh=False):
        s = self.store
        f = self.goto("portfolio/awards", "userEsoapAccountSummary", lambda fr: fr.locator("a[href*=esoapViewGrantDetail]").count() > 0)
        grants = f.evaluate("""()=>{const m=new Map();for(const a of document.querySelectorAll('a[href*=esoapViewGrantDetail]'))m.set(a.innerText.trim(),a.href);return [...m.entries()]}""")
        log(f"授予共 {len(grants)} 個")
        for gid, href in grants:
            key = f"grant|{gid}"
            if s.done(key) and not refresh:
                s.skipped += 1
                continue
            try:
                def run():
                    r = self.ctx.request.get(href, timeout=TIMEOUT_MS)
                    if r.status != 200:
                        raise RuntimeError(f"HTTP {r.status}")
                    html = r.text()
                    if "vest" not in html.lower():
                        raise SessionExpired(f"授予 {gid}：回應不是授予明細頁，session 可能已失效")
                    return self.html_to_pdf(html)

                pdf = retry(gid, run)
                (ROOT / "授予明細" / f"{gid}.pdf").unlink(missing_ok=True)
                s.record(key, "授予明細", f"{gid}.pdf", pdf, "授予明細", "", "", "Portfolio / Awards")
            except SessionExpired:
                raise
            except Exception as e:  # noqa: BLE001
                s.fail(f"授予 {gid}", e)
            time.sleep(1)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="docs,tax,plan,reports,grants")
    ap.add_argument("--refresh-grants", action="store_true")
    ap.add_argument("--home", help="ms-atwork home folder")
    args = ap.parse_args()
    global ROOT, LEDGER
    config.use_home(args.home)
    ROOT = config.output_dir()
    LEDGER = ROOT / ".download_state.json"
    store = Store()
    with sync_playwright() as pw:
        site = Site(pw, store)
        try:
            for st in args.stage.split(","):
                log(f"== 階段 {st} ==")
                try:
                    if st == "grants":
                        site.stage_grants(args.refresh_grants)
                    else:
                        getattr(site, f"stage_{st}")()
                except SessionExpired as e:
                    log(f"! {e}。請重新登入後再跑一次，已完成的會跳過。")
                    store.failures.append(str(e))
                    break
                except Exception as e:  # noqa: BLE001
                    store.fail(f"階段 {st}", e)
        finally:
            site.close()
            store.write_manifest()
    cats: dict[str, int] = {}
    for it in store.items.values():
        cats[it["category"]] = cats.get(it["category"], 0) + 1
    docs = sum(k.startswith("doc|") for k in store.items)
    print(json.dumps({"account_documents": docs, "分類筆數": cats, "本次新增": store.new, "本次跳過": store.skipped,
                      "重複": store.dups, "失敗": store.failures}, ensure_ascii=False, indent=1))
    return 1 if store.failures else 0


if __name__ == "__main__":
    sys.exit(main())
