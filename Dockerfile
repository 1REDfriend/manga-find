FROM oven/bun:latest

WORKDIR /app

# คัดลอกไฟล์ package.json และ proxy-server.js
COPY package.json .
COPY proxy-server.js .

# ติดตั้ง dependencies ด้วย Bun
RUN bun install

# รัน proxy server
CMD ["bun", "run", "proxy-server.js"]

# เปิด port 35757
EXPOSE 35757
