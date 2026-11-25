# Goldbach Infinity

Panel web + worker computacional continuo para investigar la conjetura fuerte de Goldbach.

## Despliegue en Render
1. Sube esta carpeta a un repositorio de GitHub.
2. En Render, crea un **Blueprint** y conecta el repositorio que contiene `render.yaml`.
3. Render creará un servicio web y un disco persistente montado en `/var/data`.
4. Abre la URL del servicio. El dashboard se actualiza cada 1,5 segundos.

El `render.yaml` usa un plan con disco persistente. Los planes gratuitos pueden dormir o no ofrecer disco persistente; para ejecución continua y guardar el progreso necesitas un servicio siempre activo con almacenamiento persistente.

## Ajustes
- `BLOCK_SIZE`: cantidad de números pares por lote (por defecto 200.000).
- `PAUSE_SECONDS`: pausa entre lotes.
- `DB_PATH`: ruta de la base de datos.

## Limitaciones matemáticas y de rendimiento
No existe un proceso que termine de comprobar infinitos números. El servicio va avanzando mientras esté ejecutándose y tenga recursos. La versión incluida es demostrativa y usa una búsqueda sencilla de parejas de primos; el rendimiento bajará mucho al aumentar los números. No es una demostración de Goldbach.
