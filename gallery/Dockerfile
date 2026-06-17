FROM node:20-slim

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci --omit=dev

COPY server.js .
COPY public ./public
COPY gallery ./gallery

ENV FLAG=GCUP{Placeholder}

EXPOSE 3000

CMD ["node", "server.js"]
