# Stage 1: Build the React static assets
FROM node:20-alpine AS build-stage

# Support custom API base URL at build time (Vite embeds env variables during build)
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

# Set workspace directory
WORKDIR /app

# Copy dependency packages definitions
COPY package*.json ./

# Install packages
RUN npm install

# Copy project source files
COPY . .

# Build the production bundle
RUN npm run build

# Stage 2: Serve built assets using Nginx
FROM nginx:alpine

# Copy custom Nginx virtual server config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy build output from Stage 1 to Nginx public html directory
COPY --from=build-stage /app/dist /usr/share/nginx/html

# Expose HTTP port 80
EXPOSE 80

# Run Nginx in the foreground
CMD ["nginx", "-g", "daemon off;"]
