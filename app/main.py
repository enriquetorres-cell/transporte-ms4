"""MS4 · Historial de Usuario (Contrato Cero).
Microservicio SIN base de datos: sólo orquesta MS1 + MS2 + MS3.
Todas las rutas bajo /ms4. Swagger en /ms4/docs.

Regla de tolerancia (Contrato §): timeout 5 s y un reintento por llamada.
Si un servicio no responde, su bloque va en null y se agrega una advertencia.
NUNCA devuelve 500 por culpa de un servicio caído.
"""
import os
import httpx
from fastapi import FastAPI

PREFIX = "/ms4"
TIMEOUT = 5.0

MS1 = os.environ.get("MS1_URL", "http://localhost:8001/ms1")
MS2 = os.environ.get("MS2_URL", "http://localhost:8002/ms2")
MS3 = os.environ.get("MS3_URL", "http://localhost:8003/ms3")

app = FastAPI(
    title="MS4 - Historial de Usuario",
    version="1.0.0",
    docs_url=f"{PREFIX}/docs",
    openapi_url=f"{PREFIX}/openapi.json",
)


@app.get(f"{PREFIX}/health")
def health():
    return {"status": "ok", "servicio": "ms4"}


async def pedir(cliente, url, avisos, etiqueta):
    """Llamada tolerante: reintenta 1 vez, nunca lanza; agrega advertencia si falla."""
    for _ in range(2):
        try:
            r = await cliente.get(url, timeout=TIMEOUT)
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r.json()
        except httpx.HTTPError:
            continue
    avisos.append(f"{etiqueta} no disponible")
    return None


# MS2 (Spring) filtra por parámetros camelCase (pasajeroId, conductorId); con
# pasajero_id/conductor_id los ignora y devuelve viajes de cualquier persona.
@app.get(PREFIX + "/usuarios/{usuario_id}/perfil")
async def perfil(usuario_id: int):
    """Perfil del pasajero: datos (MS1) + últimos viajes (MS2) + calificaciones (MS3)."""
    avisos = []
    async with httpx.AsyncClient() as c:
        usuario = await pedir(c, f"{MS1}/usuarios/{usuario_id}", avisos, "ms1")
        viajes = await pedir(c, f"{MS2}/viajes?pasajeroId={usuario_id}&limit=10", avisos, "ms2")
        calif = await pedir(c, f"{MS3}/calificaciones?pasajero_id={usuario_id}&limit=10", avisos, "ms3")
    return {
        "usuario": usuario,
        "ultimos_viajes": (viajes or {}).get("items"),
        "calificaciones": (calif or {}).get("items"),
        "advertencias": avisos,
    }


@app.get(PREFIX + "/conductores/{conductor_id}/hoja-de-vida")
async def hoja_de_vida(conductor_id: int):
    """Hoja de vida del conductor: datos y vehículos (MS1) + viajes (MS2) + resumen (MS3)."""
    avisos = []
    async with httpx.AsyncClient() as c:
        conductor = await pedir(c, f"{MS1}/conductores/{conductor_id}", avisos, "ms1")
        vehiculos = await pedir(c, f"{MS1}/conductores/{conductor_id}/vehiculos", avisos, "ms1")
        viajes = await pedir(c, f"{MS2}/viajes?conductorId={conductor_id}&limit=10", avisos, "ms2")
        resumen = await pedir(c, f"{MS3}/conductores/{conductor_id}/resumen", avisos, "ms3")
    return {
        "conductor": conductor,
        "vehiculos": vehiculos or [],   # MS1 /vehiculos ya devuelve una lista
        "ultimos_viajes": (viajes or {}).get("items"),
        "resumen_calificaciones": resumen,
        "advertencias": avisos,
    }


@app.get(PREFIX + "/viajes/{viaje_id}/detalle-completo")
async def detalle_completo(viaje_id: int):
    """Detalle de un viaje (MS2) + pasajero y conductor (MS1) + su calificación (MS3)."""
    avisos = []
    async with httpx.AsyncClient() as c:
        viaje = await pedir(c, f"{MS2}/viajes/{viaje_id}", avisos, "ms2")
        pasajero = conductor = None
        if viaje:
            if viaje.get("pasajero_id"):
                pasajero = await pedir(c, f"{MS1}/usuarios/{viaje['pasajero_id']}", avisos, "ms1")
            if viaje.get("conductor_id"):
                conductor = await pedir(c, f"{MS1}/conductores/{viaje['conductor_id']}", avisos, "ms1")
        calif = await pedir(c, f"{MS3}/calificaciones/{viaje_id}", avisos, "ms3")
    return {
        "viaje": viaje,
        "pasajero": pasajero,
        "conductor": conductor,
        "calificacion": calif,
        "advertencias": avisos,
    }
