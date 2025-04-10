FROM oven/bun:latest

WORKDIR ./

# ติดตั้ง http-server ด้วย npm เพราะเสถียรกว่าใน container
RUN bun install -g http-server

EXPOSE 35756

CMD ["http-server", "-p", "35756"]
