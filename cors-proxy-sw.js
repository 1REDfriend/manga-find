// cors-proxy-sw.js
self.addEventListener('install', event => {
  self.skipWaiting();
});

self.addEventListener('activate', event => {
  event.waitUntil(clients.claim());
});

self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);
  
  // ตรวจสอบว่าเป็นคำขอรูปภาพจาก proxy หรือไม่
  if (url.pathname === '/proxy-image') {
    event.respondWith(handleProxyRequest(event.request));
  }
});

async function handleProxyRequest(request) {
  const url = new URL(request.url);
  const imageUrl = url.searchParams.get('url');
  
  if (!imageUrl) {
    return new Response('ต้องระบุพารามิเตอร์ URL', { status: 400 });
  }
  
  try {
    // สร้างคำขอใหม่ไปยัง URL ที่ต้องการ
    const response = await fetch(imageUrl, {
      headers: { 'Origin': self.location.origin }
    });
    
    // คัดลอก response แต่เพิ่ม CORS headers
    const headers = new Headers(response.headers);
    headers.set('Access-Control-Allow-Origin', '*');
    
    return new Response(response.body, {
      status: response.status,
      statusText: response.statusText,
      headers
    });
  } catch (error) {
    return new Response('ไม่สามารถโหลดรูปภาพได้', { status: 500 });
  }
} 