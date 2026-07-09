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
    print("🔄 [Render-Fix] Buscando motor de Prisma copiado localmente...")

    # Ahora buscamos el archivo directamente en la carpeta del backend
    local_binary = Path("./backend/prisma-query-engine-debian-openssl-3.0.x")
    # Si usas Root Directory "backend" en Render, prueba cambiar la ruta a Path("./prisma-query-engine-debian-openssl-3.0.x")

    if local_binary.exists():
        print(
            f"✅ [Render-Fix] Motor local encontrado y activado: {local_binary}")
        BINARY_PATHS.query_engine = local_binary.resolve()
    else:
        print("⚠️ [Render-Fix] No se encontró el binario local en ./backend/.")

    try:
        print("🔄 Conectando a la base de datos...")
        await prisma.connect()
        print("🚀 Conexión exitosa a la base de datos con Prisma.")
    except Exception as e:
        print(f"❌ ERROR CRÍTICO AL CONECTAR: {e}")
        print("⚠️ El servidor continuará encendido para evitar caídas de puerto en Render.")

    yield

    if prisma.is_connected():
        await prisma.disconnect()


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
