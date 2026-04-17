# Poli Home — Integración para Home Assistant

Integración personalizada para controlar cerraduras eléctricas **Poli Home** (ASSA ABLOY Chile) desde Home Assistant.

## Dispositivos compatibles

- **Hub Poli Connect** — Controlador WiFi para cerraduras eléctricas
- **Cerradura Eléctrica 3010** — Cerradura sobreponer eléctrica 12-16V
- Cualquier dispositivo compatible con la app Poli Home

## Funcionalidades

| Entidad | Descripción |
|---|---|
| **Cerradura** | Aparece como candado en HomeKit/Matter. La acción de "desbloquear" acciona la cerradura momentánea. |
| **Sensor "Conexión"** | Estado online/offline del dispositivo |
| **Sensor "Batería baja"** | Alerta cuando la batería está baja |

## Instalación

### Vía HACS (recomendado)

1. Abre HACS en Home Assistant
2. Ve a **Integraciones** → menú ⋮ → **Repositorios personalizados**
3. Agrega este repositorio con categoría **Integración**
4. Busca "Poli Home" e instala
5. Reinicia Home Assistant
6. Ve a **Configuración** → **Integraciones** → **Agregar integración** → **Poli Home**

### Instalación manual

1. Copia la carpeta `custom_components/poli_home` a tu directorio de configuración de Home Assistant
2. Reinicia Home Assistant
3. Ve a **Configuración** → **Integraciones** → **Agregar integración** → **Poli Home**

## Configuración

Solo necesitas tu **email** y **contraseña** de la app Poli Home. La integración descubrirá todos tus dispositivos automáticamente.

## Notas técnicas

- La API de Poli Home es proporcionada por Yale Connect (ASSA ABLOY)
- La cerradura solo soporta acción de **apertura momentánea** (no tiene estado de cerrado/abierto persistente)
- El estado de los dispositivos se actualiza cada 60 segundos
- Se requiere conexión a internet ya que la comunicación es vía cloud

## Licencia

MIT
