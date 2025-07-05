import requests
from bs4 import BeautifulSoup
import json
import os
import time
import re

class MangaScraper:
    def __init__(self, output_file='manga_results.json'):
        self.base_url = "https://xn--72cas2cj6a4hf4b5a8oc.com/manga/?page={}&status=&type=manga&order="
        self.output_file = output_file
        self.results = []
        
        # โหลดผลลัพธ์เก่า (ถ้ามี)
        self.load_results()
    
    def load_results(self):
        """โหลดผลลัพธ์เก่า (ถ้ามี)"""
        if os.path.exists(self.output_file):
            try:
                with open(self.output_file, 'r', encoding='utf-8') as f:
                    self.results = json.load(f)
            except json.JSONDecodeError:
                self.results = []
    
    def save_results(self):
        """บันทึกผลลัพธ์"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
    
    def extract_number_from_chapter(self, chapter_text):
        """ดึงตัวเลขจากข้อความตอน"""
        # ใช้ regex เพื่อดึงตัวเลขจากข้อความ เช่น "Chapter 41.2" จะได้ 41.2
        match = re.search(r'(\d+(\.\d+)?)', chapter_text)
        if match:
            return float(match.group(1))
        return 0
    
    def get_manga_list_from_page(self, page_num):
        """ดึงรายการมังงะจากหน้าที่กำหนด"""
        url = self.base_url.format(page_num)
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            # ตรวจสอบว่าหน้าเป็น 404 หรือไม่
            if "404" in response.url or response.status_code == 404:
                print(f"พบหน้า 404 ที่หน้า {page_num}")
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            manga_items = []
            
            # หาทุกบล็อกมังงะตาม class "bsx"
            for bsx_div in soup.find_all('div', class_='bsx'):
                try:
                    # หา tag a ที่เป็นลิงก์ไปยังหน้ามังงะ
                    a_tag = bsx_div.find('a')
                    if not a_tag:
                        continue
                    
                    # ดึงลิงก์โปรไฟล์และชื่อเรื่อง
                    profile_link = a_tag.get('href', '')
                    title = a_tag.get('title', '')
                    
                    # ดึงชื่อมังงะจาก class "tt"
                    title_div = bsx_div.find('div', class_='tt')
                    if title_div:
                        title = title_div.text.strip()
                    
                    # ดึงตอนล่าสุดจาก class "epxs"
                    chapter_div = bsx_div.find('div', class_='epxs')
                    chapter_text = chapter_div.text.strip() if chapter_div else ''
                    chapter_number = self.extract_number_from_chapter(chapter_text)
                    
                    # ดึง URL รูปภาพจาก class "ts-post-image wp-post-image"
                    img_tag = bsx_div.find('img', class_='ts-post-image')
                    if not img_tag:
                        img_tag = bsx_div.find('img')
                    image_url = img_tag.get('src', '') if img_tag else ''
                    
                    manga_items.append({
                        'name': title,
                        'chapter': chapter_number,
                        'chapter_text': chapter_text,
                        'profile_link': profile_link,
                        'link': profile_link,  # ลิงก์อ่านและลิงก์โปรไฟล์เป็นลิงก์เดียวกันตามที่ระบุ
                        'image_url': image_url
                    })
                    
                except Exception as e:
                    print(f"เกิดข้อผิดพลาดในการดึงข้อมูลมังงะ: {e}")
            
            return manga_items
        
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการดึงข้อมูลหน้า {page_num}: {e}")
            return []
    
    def run(self):
        """เริ่มการทำงาน scraping"""
        page_num = 1
        has_more_pages = True
        
        print("เริ่มต้นดึงข้อมูลมังงะ")
        
        while has_more_pages:
            print(f"กำลังตรวจสอบหน้า {page_num}...")
            manga_list = self.get_manga_list_from_page(page_num)
            
            if manga_list is None:
                print(f"ไม่พบข้อมูลหรือพบหน้า 404 ที่หน้า {page_num} - จบการทำงาน")
                has_more_pages = False
                break
            
            if not manga_list:
                print(f"ไม่พบรายการมังงะในหน้า {page_num} - จบการทำงาน")
                has_more_pages = False
                break
            
            print(f"พบมังงะจำนวน {len(manga_list)} เรื่องในหน้า {page_num}")
            
            # เพิ่มข้อมูลใหม่ลงในผลลัพธ์
            self.results.extend(manga_list)
            
            # บันทึกข้อมูลทุกครั้งที่พบเรื่องใหม่
            self.save_results()
            
            # หยุดสักครู่เพื่อไม่ให้ส่งคำขอถี่เกินไป
            time.sleep(1)
            
            # เพิ่มเลขหน้า
            page_num += 1
        
        print(f"การดึงข้อมูลเสร็จสิ้น! พบทั้งหมด {len(self.results)} เรื่อง")
        print(f"บันทึกผลลัพธ์ลงในไฟล์: {self.output_file}")

if __name__ == "__main__":
    # สร้าง json ใหม่
    if os.path.exists('manga_results.json'):
        os.remove('manga_results.json')
    
    scraper = MangaScraper()
    scraper.run()
