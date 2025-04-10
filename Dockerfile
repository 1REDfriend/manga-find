FROM oven/bun:1.0.25

WORKDIR /app

# ติดตั้ง http-server ผ่าน bun
RUN bun add -g http-server

EXPOSE 35756

CMD ["bunx", "http-server", "-p", "35756"]
