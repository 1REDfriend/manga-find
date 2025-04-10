FROM oven/bun:latest

WORKDIR ./

# ติดตั้ง dependencies ด้วย Bun
RUN bun install

# เปิด port 35757
EXPOSE 35757

# รัน proxy server
CMD ["bun", "run", "proxy-server.js"]

