import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

# Tus imports originales
from app.core.database import prisma
from app.api import auth, lotes, productos, pos, subastas, usuarios
# Importamos BINARY_PATHS para corregir el bug de Prisma en Render
from prisma import BINARY_PATHS


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("🔄 [Render-Fix] Configurando rutas dinámicas para el motor de Prisma...")

    # 1. Ruta absoluta exacta donde Render descargó los binarios en la caché
    cache_dir = Path(
        "/opt/render/.cache/prisma-python/binaries/5.17.0/393aa359c9ad4a4bb28630fb5613f9c281cde053")
    binary_name = "prisma-query-engine-debian-openssl-3.0.x"
    expected_binary = cache_dir / binary_name

    # 2. Forzar a Prisma a mirar esa carpeta antes de conectar
    if expected_binary.exists():
        print(f"✅ [Render-Fix] Motor encontrado en: {expected_binary}")
        BINARY_PATHS.query_engine = expected_binary
    else:
        print(
            "⚠️ [Render-Fix] No se detectó el binario en la caché global. Se usará la ruta por defecto.")

    # 3. Intentar conectar protegiendo el flujo con try-except
    try:
        print("🔄 Conectando a la base de datos...")
        await prisma.connect()
        print("🚀 Conexión exitosa a la base de datos con Prisma.")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO AL CONECTAR: {e}")
        print("⚠️ El servidor continuará encendido para evitar caídas de puerto en Render.")

    yield  # Aquí es donde la API se queda corriendo viva

    # Desconexión limpia al apagar el servidor
    try:
        if prisma.is_connected():
            await prisma.disconnect()
            print("🛑 Prisma desconectado correctamente.")
    except Exception as e:
        print(f"⚠️ Error al desconectar Prisma: {e}")


app = FastAPI(
    title="API DAppHACommerce / STGC",
    description="Backend principal con trazabilidad y gestión.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuración básica de CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar todas las rutas
app.include_router(lotes.router)
app.include_router(productos.router)
app.include_router(pos.router)
app.include_router(subastas.router)
app.include_router(usuarios.router)
app.include_router(auth.router)


@app.get("/", tags=["Health Check"])
def read_root():
    return {"status": "ok", "message": "API Backend operando correctamente"}
