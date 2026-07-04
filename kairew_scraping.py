#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
kairew_scraping.py
Scraper สำหรับ https://kairew.com

ดึงข้อมูลทั้งหมดจาก /api/search/books/all แล้ว merge เข้าไฟล์ JSON
(default: manga_results.json) โดยอัพเดทเฉพาะเรื่องที่มีตอนใหม่กว่า

การใช้งาน:
    python kairew_scraping.py
    python kairew_scraping.py --output manga_results.json --fresh-kairew

ต้องติดตั้ง:
    pip install cloudscraper beautifulsoup4
"""

import json
import os
import re
import sys
from typing import Any, Dict, List, Tuple
from urllib.parse import unquote

try:
    import cloudscraper
except ImportError:
    print("ERROR: ต้องมี cloudscraper → pip install cloudscraper")
    sys.exit(1)

try:
    from bs4 import BeautifulSoup
except ImportError:
    print("ERROR: ต้องมี beautifulsoup4 → pip install beautifulsoup4")
    sys.exit(1)


BASE_URL = "https://kairew.com"
SEARCH_URL = f"{BASE_URL}/search"
API_URL = f"{BASE_URL}/api/search/books/all?clear_cache=false&debug=false"


class KairewScraper:
    def __init__(self, output_file: str = "manga_results.json"):
        self.output_file = output_file
        self.results: List[Dict[str, Any]] = []
        self.session = cloudscraper.create_scraper(
            browser={"browser": "chrome", "platform": "windows", "mobile": False}
        )
        self.load_results()

    # ------------------ IO ------------------
    def load_results(self):
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, "r", encoding="utf-8") as f:
                    self.results = json.load(f)
                print(f"[INFO] โหลดข้อมูลเก่า: {len(self.results)} รายการ")
            except Exception as e:
                print(f"[WARN] โหลด {self.output_file} ไม่สำเร็จ: {e}")
                self.results = []

    def save_results(self):
        with open(self.output_file, "w", encoding="utf-8") as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        print(f"[INFO] บันทึกผลลัพธ์ลง {self.output_file} (ทั้งหมด {len(self.results)} รายการ)")

    # ------------------ Auth (สดใหม่ทุกครั้ง) ------------------
    def _get_tokens(self) -> Tuple[str, str]:
        """เข้าหน้า /search เพื่อผ่าน Cloudflare + ดึง CSRF/XSRF token ล่าสุด"""
        resp = self.session.get(SEARCH_URL, timeout=30)
        resp.raise_for_status()

        xsrf = unquote(self.session.cookies.get("XSRF-TOKEN", ""))

        soup = BeautifulSoup(resp.text, "html.parser")
        meta = soup.find("meta", attrs={"name": "csrf-token"})
        csrf = meta.get("content", "") if meta else ""

        return csrf, xsrf

    def _headers(self, csrf: str, xsrf: str) -> Dict[str, str]:
        # ไม่ set user-agent เอง! ต้องปล่อยให้ตรงกับตัวที่ cloudscraper
        # ใช้ตอนแก้ Cloudflare challenge (cf_clearance ผูกกับ UA นั้น)
        # ถ้า override UA ตรงนี้ Cloudflare จะเห็นว่า UA ไม่ตรง แล้วเตะ 403
        return {
            "accept": "application/json, text/plain, */*",
            "x-requested-with": "XMLHttpRequest",
            "x-csrf-token": csrf,
            "x-xsrf-token": xsrf,
            "referer": SEARCH_URL,
        }

    # ------------------ Fetch ------------------
    def fetch_all_books(self) -> List[Dict[str, Any]]:
        print("[INFO] กำลังผ่าน Cloudflare และดึง token...")
        try:
            csrf, xsrf = self._get_tokens()
        except Exception as e:
            print(f"[ERROR] เข้าเว็บไม่สำเร็จ: {e}")
            return []

        print("[INFO] กำลังเรียก API...")
        try:
            resp = self.session.get(API_URL, headers=self._headers(csrf, xsrf), timeout=120)
            resp.raise_for_status()
            payload = resp.json()
        except Exception as e:
            print(f"[ERROR] เรียก API ล้มเหลว: {e}")
            return []

        if not payload.get("success"):
            print("[WARN] API ตอบ success=false")
            return []

        books = payload.get("data", {}).get("books", [])
        print(f"[INFO] ดึงข้อมูลสำเร็จ: {len(books)} เรื่อง")
        return books

    # ------------------ Transform ------------------
    def _slugify(self, text: str) -> str:
        if not text:
            return ""
        text = str(text).lower().strip()
        text = re.sub(r"[^a-z0-9]+", "-", text)
        return re.sub(r"-+", "-", text).strip("-")

    def _build_book_url(self, b: Dict[str, Any]) -> str:
        writer_id = b.get("writer_id")
        book_id = b.get("id")
        name_url = self._slugify((b.get("original") or {}).get("name_url", ""))

        if writer_id and book_id and name_url:
            return f"{BASE_URL}/cartoon/{writer_id}/{book_id}-{name_url}"
        if book_id:
            return f"{BASE_URL}/cartoon/{book_id}"
        return BASE_URL

    def transform_book(self, b: Dict[str, Any]) -> Dict[str, Any]:
        writer = b.get("writer") or {}
        orig = b.get("original") or {}
        img = b.get("image") or {}
        cat = b.get("category") or {}

        profile_link = self._build_book_url(b)

        try:
            ch_num = float(b.get("share_episode_count") or 0)
        except (TypeError, ValueError):
            ch_num = 0.0
        chapter_text = f"Chapter {int(ch_num) if ch_num == int(ch_num) else ch_num}"

        item = {
            "name": (b.get("name") or "").strip(),
            "chapter": ch_num,
            "chapter_text": chapter_text,
            "profile_link": profile_link,
            "link": profile_link,
            "image_url": img.get("path", ""),

            "source": "kairew.com",
            "kairew_id": b.get("id"),
            "chapter_count": int(ch_num),
            "share_episode_count": b.get("share_episode_count"),

            "writer": writer.get("name") or writer.get("username"),
            "writer_username": writer.get("username"),
            "writer_id": b.get("writer_id"),

            "original_name": orig.get("name"),
            "original_name_url": orig.get("name_url"),

            "category": cat.get("value"),
            "type": b.get("type"),
            "status": b.get("status"),
            "book_status": b.get("book_status"),

            "view_count": b.get("view_count"),
            "like_count": b.get("like_count"),
            "comment_count": b.get("comment_count"),
            "bookmark_count": b.get("bookmark_count"),
            "rating": b.get("rating"),

            "tags": b.get("tags", []),
            "excerpt": b.get("excerpt"),
            "description": b.get("description"),

            "episode_last_at": b.get("episode_last_at"),
            "updated_at": b.get("updated_at"),
            "created_at": b.get("created_at"),

            "is_age_18_plus": b.get("is_age_18_plus"),
            "is_feed": b.get("is_feed"),
        }
        return {k: v for k, v in item.items() if v not in (None, "", [], {})}

    # ------------------ Merge ------------------
    def smart_append(self, new_books: List[Dict[str, Any]]):
        if not new_books:
            print("[INFO] ไม่มีรายการใหม่จาก Kairew")
            return

        existing_map = {
            (item.get("name") or "").strip().lower(): idx
            for idx, item in enumerate(self.results)
            if item.get("name")
        }

        added = updated = 0
        for raw in new_books:
            item = self.transform_book(raw)
            name = item.get("name", "")
            if not name:
                continue

            key = name.strip().lower()
            new_ch = item.get("chapter", 0)

            if key in existing_map:
                idx = existing_map[key]
                old = self.results[idx]
                if new_ch > old.get("chapter", 0):
                    old.update(item)
                    updated += 1
            else:
                self.results.append(item)
                existing_map[key] = len(self.results) - 1
                added += 1

        print(f"[INFO] เพิ่มใหม่ {added} เรื่อง, อัพเดท {updated} เรื่อง")

    # ------------------ Run ------------------
    def run(self):
        print("=" * 60)
        print("Kairew Scraper เริ่มทำงาน")
        print(f"Output: {self.output_file}")
        print("=" * 60)

        books = self.fetch_all_books()
        if not books:
            print("[ERROR] ไม่สามารถดึงข้อมูลจาก Kairew ได้")
            return

        self.smart_append(books)
        self.save_results()
        print("\n[เสร็จสิ้น]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Kairew.com manga/cartoon scraper")
    parser.add_argument("--output", "-o", default="manga_results.json",
                         help="ไฟล์ JSON ผลลัพธ์ (default: manga_results.json)")
    parser.add_argument("--fresh-kairew", action="store_true",
                         help="ลบรายการเก่าที่มี source=kairew.com ก่อนเพิ่มใหม่")
    args = parser.parse_args()

    scraper = KairewScraper(output_file=args.output)

    if args.fresh_kairew:
        before = len(scraper.results)
        scraper.results = [r for r in scraper.results if r.get("source") != "kairew.com"]
        removed = before - len(scraper.results)
        if removed:
            print(f"[INFO] ลบรายการเก่าของ kairew ออก {removed} รายการ")

    scraper.run()
