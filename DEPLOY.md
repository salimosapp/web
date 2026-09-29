# Deploy de la web pública

La web va a su propio servicio de Render, apuntando a **la misma base Neon** que
el panel admin. Esa base compartida es lo que une las dos apps: aprobás un
evento en el panel y aparece acá.

## Antes de empezar

Hacé los pasos 1, 2 y 3 de `admin/DEPLOY.md` (Neon, copiar los datos, desplegar
el panel). Esta guía solo cubre lo que es distinto.

El orden importa: **esta web no crea las tablas**. Solo las lee, así que si
arranca contra una base vacía te va a tirar un error de "relation eventos does
not exist". Las crea el panel, en su primer arranque (`inicializar_db()` en
`app.py`), o el `pg_dump` del paso 2. Por eso el panel va primero.

Son dos archivos y vas a necesitar el mismo Neon:

- `admin/DEPLOY.md` → base de datos + deploy del panel
- `web/DEPLOY.md` → este, el deploy de la web

## Configuración en Render

1. En Render: **New + → Web Service** → elegí el repo `salimosapp/web`.

2. Configuración:

   | Campo         | Valor                                              |
   | ------------- | -------------------------------------------------- |
   | Name          | `salimos-web`                                      |
   | Region        | **La misma que usaste para el panel**              |
   | Runtime       | Python                                             |
   | Build command  | `pip install -r requirements.txt`                  |
   | Start command  | `gunicorn app:app --workers 1 --threads 4 --timeout 120` |
   | Instance type | Free                                               |

   El start command también está en el `Procfile`, así que Render debería
   tomarlo solo.

3. En **Environment**, cargá estas seis:

   ```
   DB_HOST     = (el host de Neon)
   DB_PORT     = 5432
   DB_NAME     = neondb
   DB_USER     = (el usuario de Neon)
   DB_PASSWORD = (la contraseña de Neon)
   DB_SSLMODE  = require
   ```

   **Son las mismas seis que cargaste en el servicio del panel.** Copiégalas de
   ahí, no las reescribas. Si en un servicio queda un carácter distinto, esa app
   lee otra base y el nexo se rompe: aprobás un evento en el panel y no aparece
   acá.

4. **Create Web Service**. Te queda una URL tipo
   `https://salimos-web.onrender.com`.

## Diferencias con el panel

- **No lleva clave de IA.** Esta web no usa IA para nada; solo lee de la base.
  No cargues `AI_API_KEY` ni `AI_MODEL`.
- **No lleva variables de login.** Esta web es pública, se supone que la ve
  cualquiera. El login vive solo en el panel, así que acá no va ni
  `ADMIN_PASSWORD` ni `SECRET_KEY`.
- **Timeout más corto** (120 en vez de 300). El panel puede tardar mucho con el
  scraping; esta web solo hace consultas, que son rápidas.

## Cosas que esta web no tiene y conviene saber

- **No escribe nada en la base.** Toda escritura (scraping, aprobación,
  edición) pasa por el panel. Si alguna vez tocás esta web esperando guardar
  algo, no va a pasar: no hay código que lo haga, por diseño.
- **Solo muestra eventos aprobados y futuros.** El filtro está en
  `backend/eventos.py` y es `aprobado = true AND fecha_hora >= NOW()`. Los
  eventos que dejás pendientes en el panel no aparecen acá, ni siquiera
  borrando caché.
- **Sin login, expuesto a internet.** Cualquiera que conozca la URL puede ver
  la agenda. Es lo esperado para un sitio público, pero si no querés que se vea
  todavía, la opción es no publicarla hasta que esté lista.
- **Arranque en frío**: si no entra nadie por 15 minutos, Render apaga el
  servidor y la próxima visita tarda 30-60 segundos en levantar.

## Volver a trabajar en local

`app.py` lee `HOST` y `PORT` del entorno, con `0.0.0.0:5001` por defecto. El
5001 es a propósito: el panel usa el 5000, así que podés tener las dos apps
corriendo en la misma máquina al mismo tiempo.

```bash
python app.py
```

Y abrí <http://127.0.0.1:5001>.
