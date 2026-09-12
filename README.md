# transporte-ms4 (Historial de Usuario)

Microservicio **sin base de datos** (Contrato Cero). Sólo **orquesta** MS1 + MS2 + MS3.
Es el "1 microservicio que no tenga base de datos y sólo consuma otros microservicios"
que exige el enunciado.

## Endpoints (todos bajo `/ms4`)

| Ruta | Compone |
|------|---------|
| `GET /ms4/health` | `{"status":"ok","servicio":"ms4"}` (no toca nada) |
| `GET /ms4/docs` | Swagger UI |
| `GET /ms4/usuarios/{id}/perfil` | MS1 usuario + MS2 últimos viajes + MS3 calificaciones |
| `GET /ms4/conductores/{id}/hoja-de-vida` | MS1 conductor y vehículos + MS2 viajes + MS3 resumen |
| `GET /ms4/viajes/{id}/detalle-completo` | MS2 viaje + MS1 pasajero y conductor + MS3 su calificación |

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

## Construir y publicar la imagen

```bash
docker build -t TU_USUARIO/transporte-ms4:1.0 .
docker login && docker push TU_USUARIO/transporte-ms4:1.0
```

Avísale a P1 el nombre/tag para el `docker-compose.prod.yml`. El repo debe quedar **público**.

## En producción (detrás del ALB)

`MS1_URL`, `MS2_URL`, `MS3_URL` apuntan a las rutas del ALB interno / API Gateway
(cada microservicio bajo su prefijo). Sin barra final.
