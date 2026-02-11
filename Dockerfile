# Stage 1: Build frontend
FROM node:20-alpine AS frontend-build
WORKDIR /app/frontend
COPY flight-scout/frontend/package*.json ./
RUN npm install
COPY flight-scout/frontend/ ./
RUN npm run build

# Stage 2: Run backend + serve frontend
FROM python:3.13-slim
WORKDIR /app

COPY flight-scout/backend/requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY flight-scout/backend/ ./
RUN rm -f uvicorn
COPY --from=frontend-build /app/frontend/dist ../frontend/dist

ENV PORT=8000
EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn main:app --host 0.0.0.0 --port $PORT"]
