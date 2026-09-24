# transporte-ms4 (Historial de Usuario)

Microservicio **sin base de datos** (Contrato Cero). Sólo **orquesta** MS1 + MS2 + MS3.
Es el "1 microservicio que no tenga base de datos y sólo consuma otros microservicios"
que exige el enunciado.

> **Despliegue completo del proyecto en AWS (paso a paso):** ver la
> [guía principal](https://github.com/Limepal/MS1-Usuarios-y-Conductores#readme).

## Endpoints (todos bajo `/ms4`)

| Ruta | Compone |
|------|---------|
| `GET /ms4/health` | `{"status":"ok","servicio":"ms4"}` (no toca nada) |
| `GET /ms4/docs` | Swagger UI |
| `GET /ms4/usuarios/{id}/perfil` | MS1 usuario + MS2 últimos viajes + MS3 calificaciones |
| `GET /ms4/conductores/{id}/hoja-de-vida` | MS1 conductor y vehículos + MS2 viajes + MS3 resumen |
| `GET /ms4/viajes/{id}/detalle-completo` | MS2 viaje + MS1 pasajero y conductor + MS3 su calificación |

Llamadas que hace: `GET {MS1}/usuarios/{id}`, `GET {MS1}/conductores/{id}`, `GET {MS1}/conductores/{id}/vehiculos`,
`GET {MS2}/viajes?pasajeroId=…|conductorId=…&limit=10` (los filtros de MS2 van en camelCase), `GET {MS2}/viajes/{id}`,
`GET {MS3}/calificaciones?pasajero_id=…|viaje_id=…` y `GET {MS3}/conductores/{id}/resumen`.

## Regla de tolerancia (clave)

Timeout 5 s y **un reintento** por llamada. Si un servicio no responde, su bloque va
en `null` y se agrega `"advertencias": ["ms2 no disponible"]`. **Nunca un 500.** Es lo
que evita que la demo se caiga entera si un contenedor se reinicia.

## Variables de entorno

```
MS1_URL   http://localhost:8001/ms1     (o el ALB/API Gateway en prod)
MS2_URL   http://localhost:8002/ms2
MS3_URL   http://localhost:8003/ms3
```

## Correr en local

```bash
pip install -r requirements.txt
MS1_URL=http://localhost:8001/ms1 MS2_URL=http://localhost:8002/ms2 MS3_URL=http://localhost:8003/ms3 \
  uvicorn app.main:app --host 0.0.0.0 --port 8004
curl http://localhost:8004/ms4/health
```

## Con Docker

```bash
docker build -t ms4img .
docker run -d --name ms4 --network host \
  -e MS1_URL=http://localhost:8001/ms1 -e MS2_URL=http://localhost:8002/ms2 -e MS3_URL=http://localhost:8003/ms3 ms4img
```

## En producción (AWS)

En mv-prod-a y mv-prod-b, `desplegar-prod.sh` (repo de MS1) clona este repo, construye `ms4img` y lo
levanta con `docker compose` en **red host**, de modo que llega a MS1, MS2 y MS3 por `localhost:800N`
en la misma MV. El ALB interno enruta `/ms4/*` a `tg-ms4` y el API Gateway lo expone por HTTPS.
