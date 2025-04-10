import requests
from bs4 import BeautifulSoup
import json
import os
import time
from urllib.parse import urlparse

class MangaScraper:
    def __init__(self, start_page, end_page, min_chapters, output_file='manga_results.json'):
        self.base_url = "https://www.oremanga.net/advance-search/page/{}/?title&author&yearx&status&type=Manga&order=popular&genre%5B0%5D=fantasy"
        self.start_page = start_page
        self.end_page = end_page
        self.min_chapters = min_chapters
        self.output_file = output_file
        self.checked_links = set()
        self.results = []
        
        # โหลดลิงก์ที่เคยตรวจสอบแล้ว (ถ้ามี)
        self.load_checked_links()
        # โหลดผลลัพธ์เก่า (ถ้ามี)
        self.load_results()
    
    def load_checked_links(self):
        """โหลดลิงก์ที่เคยตรวจสอบแล้วจากไฟล์"""
        if os.path.exists('checked_links.json'):
            with open('checked_links.json', 'r', encoding='utf-8') as f:
                self.checked_links = set(json.load(f))
    
    def save_checked_links(self):
        """บันทึกลิงก์ที่ตรวจสอบแล้ว"""
        with open('checked_links.json', 'w', encoding='utf-8') as f:
            json.dump(list(self.checked_links), f, ensure_ascii=False)
    
    def load_results(self):
        """โหลดผลลัพธ์เก่า (ถ้ามี)"""
        if os.path.exists(self.output_file):
            with open(self.output_file, 'r', encoding='utf-8') as f:
                self.results = json.load(f)
    
    def save_results(self):
        """บันทึกผลลัพธ์"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
    
    def get_manga_list_from_page(self, page_num):
        """ดึงรายการมังงะจากหน้าที่กำหนด"""
        url = self.base_url.format(page_num)
        try:
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            manga_links = []
            
            # หาลิงก์มังงะทุกเรื่องในหน้านั้น
            for link in soup.find_all('a', href=lambda href: href and '/series/' in href):
                profile_link = link.get('href')
                if profile_link not in self.checked_links:
                    # หารูปภาพของมังงะ
                    img_element = link.find('img')
                    img_url = img_element.get('src') if img_element else ''
                    manga_title = link.get('title', '')
                    
                    manga_links.append({
                        'name': manga_title,
                        'profile_link': profile_link,
                        'image_url': img_url
                    })
            
            return manga_links
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการดึงข้อมูลหน้า {page_num}: {e}")
            return []
    
    def check_manga_chapters(self, manga_info):
        """ตรวจสอบจำนวนตอนของมังงะ"""
        url = manga_info['profile_link']
        try:
            # เพิ่มลิงก์ลงในรายการที่ตรวจสอบแล้ว
            self.checked_links.add(url)
            
            response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            chapter_list = soup.find('ul', class_='series-chapterlist')
            
            if not chapter_list:
                return None
            
            chapters = chapter_list.find_all('li')
            chapter_count = len(chapters)
            
            if chapter_count >= self.min_chapters:
                # หาตอนล่าสุด
                latest_chapter_element = chapters[0].find('a')
                if latest_chapter_element:
                    latest_chapter_url = latest_chapter_element.get('href', '')
                    
                    # แก้ไขใหม่: ไม่ดึงเลขตอนจากข้อความ แต่ใช้จำนวน chapter_count แทน
                    manga_info['chapter'] = chapter_count
                    manga_info['chapter_count'] = chapter_count
                    manga_info['link'] = latest_chapter_url
                    
                    return manga_info
            
            return None
            
        except Exception as e:
            print(f"เกิดข้อผิดพลาดในการตรวจสอบ {url}: {e}")
            return None
    
    def run(self):
        """เริ่มการทำงาน scraping"""
        print(f"เริ่มต้นค้นหามังงะที่มีตอนมากกว่า {self.min_chapters} ตอน จากหน้า {self.start_page} ถึง {self.end_page}")
        
        for page_num in range(self.start_page, self.end_page + 1):
            print(f"กำลังตรวจสอบหน้า {page_num}...")
            manga_list = self.get_manga_list_from_page(page_num)
            
            for manga in manga_list:
                print(f"กำลังตรวจสอบ: {manga['name']}")
                result = self.check_manga_chapters(manga)
                
                if result:
                    print(f"พบมังงะที่มีตอนมากกว่า {self.min_chapters} ตอน: {result['name']} (มีทั้งหมด {result['chapter_count']} ตอน)")
                    self.results.append(result)
                    # บันทึกผลลัพธ์ทุกครั้งที่พบเรื่องที่ตรงเงื่อนไข
                    self.save_results()
                
                # บันทึกลิงก์ที่ตรวจสอบแล้ว
                self.save_checked_links()
                
                # หยุดสักครู่เพื่อไม่ให้ส่งคำขอถี่เกินไป
                time.sleep(1)
            
            print(f"ตรวจสอบหน้า {page_num} เสร็จสิ้น")
        
        print(f"การค้นหาเสร็จสิ้น! พบทั้งหมด {len(self.results)} เรื่องที่มีตอนมากกว่า {self.min_chapters} ตอน")
        print(f"บันทึกผลลัพธ์ลงในไฟล์: {self.output_file}")

if __name__ == "__main__":
    # ตั้งค่าพารามิเตอร์
    start_page = 1  # หน้าเริ่มต้น
    end_page = 105    # หน้าสุดท้าย
    min_chapters = 24  # จำนวนตอนขั้นต่ำที่ต้องการ
    
    scraper = MangaScraper(start_page, end_page, min_chapters)
    scraper.run()