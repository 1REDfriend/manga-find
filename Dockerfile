FROM oven/bun:latest

WORKDIR /app

# ก๊อปปี้ไฟล์ทั้งหมด
COPY . .

EXPOSE 35756

# ใช้ bunx โหลดและรันแพ็กเกจ serve ทันที (ชี้ไปที่โฟลเดอร์ public ด้วยพอร์ต 35756)
CMD ["bunx", "serve", "public", "-l", "35756"]