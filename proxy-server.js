const express = require('express');
const cors = require('cors');
const axios = require('axios');
const app = express();
const PORT = process.env.PORT || 35757;

// อนุญาต CORS จากทุกต้นทาง
app.use(cors());

// สร้าง endpoint สำหรับ proxy รูปภาพ
app.get('/proxy-image', async (req, res) => {
  try {
    const imageUrl = req.query.url;
    
    if (!imageUrl) {
      return res.status(400).send('ต้องระบุพารามิเตอร์ URL');
    }
    
    console.log(`Proxying request for: ${imageUrl}`);
    
    // ดาวน์โหลดรูปภาพจาก URL ที่ระบุ
    const response = await axios({
      method: 'GET',
      url: imageUrl,
      responseType: 'stream',
      headers: {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
      }
    });
    
    // ส่งต่อ content-type header
    res.set('Content-Type', response.headers['content-type']);
    res.set('Access-Control-Allow-Origin', '*');
    
    // ส่งข้อมูลรูปภาพกลับไปยังไคลเอนต์
    response.data.pipe(res);
  } catch (error) {
    console.error('เกิดข้อผิดพลาด:', error);
    res.status(500).send('ไม่สามารถโหลดรูปภาพได้');
  }
});

// เส้นทางหลักสำหรับตรวจสอบว่าเซิร์ฟเวอร์ทำงานอยู่
app.get('/', (req, res) => {
  res.send('CORS Proxy Server กำลังทำงาน');
});

// เริ่มต้นเซิร์ฟเวอร์
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Proxy server กำลังทำงานที่พอร์ต ${PORT}`);
}); 