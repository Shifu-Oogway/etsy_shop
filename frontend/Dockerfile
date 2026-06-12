FROM node:20-alpine AS deps
WORKDIR /srv/frontend
COPY package.json ./
RUN npm install

FROM node:20-alpine AS build
WORKDIR /srv/frontend
COPY --from=deps /srv/frontend/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine
WORKDIR /srv/frontend
ENV NODE_ENV=production
COPY --from=build /srv/frontend/.next/standalone ./
COPY --from=build /srv/frontend/.next/static ./.next/static
EXPOSE 3000
CMD ["node", "server.js"]
