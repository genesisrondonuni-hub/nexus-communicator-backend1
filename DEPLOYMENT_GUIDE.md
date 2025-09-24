# Guía de Despliegue en Render.com - Nexus Communicator Backend

Esta guía te llevará paso a paso para desplegar el backend de Nexus Communicator en Render.com usando GitHub.

## 📋 Requisitos Previos

- Cuenta en [GitHub](https://github.com)
- Cuenta en [Render.com](https://render.com)
- Código del backend subido a un repositorio de GitHub

## 🚀 Paso 1: Preparar el Repositorio en GitHub

### 1.1 Crear Repositorio en GitHub

1. Ve a GitHub y crea un nuevo repositorio
2. Nombre sugerido: `nexus-communicator-backend`
3. Hazlo público o privado según tus preferencias

### 1.2 Subir el Código

```bash
# Inicializar Git (si no está inicializado)
git init

# Agregar archivos
git add .

# Hacer commit
git commit -m "Backend completo de Nexus Communicator"

# Agregar origen remoto
git remote add origin https://github.com/tu-usuario/nexus-communicator-backend.git

# Subir código
git push -u origin main
```

### 1.3 Verificar Archivos Necesarios

Asegúrate de que tu repositorio contenga estos archivos esenciales:

- ✅ `requirements.txt` - Dependencias de Python
- ✅ `render.yaml` - Configuración de Render
- ✅ `Procfile` - Configuración alternativa
- ✅ `src/main.py` - Aplicación principal
- ✅ `.gitignore` - Archivos a ignorar

## 🌐 Paso 2: Configurar Render.com

### 2.1 Crear Cuenta y Conectar GitHub

1. Ve a [Render.com](https://render.com)
2. Crea una cuenta o inicia sesión
3. Conecta tu cuenta de GitHub
4. Autoriza a Render para acceder a tus repositorios

### 2.2 Crear Web Service

1. **Dashboard de Render** → "New" → "Web Service"
2. **Conectar Repositorio**: Selecciona `nexus-communicator-backend`
3. **Configuración Básica**:
   - **Name**: `nexus-communicator-backend`
   - **Environment**: `Python 3`
   - **Region**: Selecciona la más cercana a tus usuarios
   - **Branch**: `main`

### 2.3 Configuración de Build y Deploy

Render detectará automáticamente el archivo `render.yaml`, pero si prefieres configuración manual:

- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `gunicorn src.main:app`
- **Python Version**: `3.11.0` (o la versión que prefieras)

### 2.4 Variables de Entorno

En la sección "Environment Variables", agrega:

| Variable | Valor | Descripción |
|----------|-------|-------------|
| `FLASK_ENV` | `production` | Modo de producción |
| `SECRET_KEY` | `[Auto-generated]` | Clave secreta (Render la genera) |
| `FRONTEND_URL` | `https://tu-frontend.netlify.app` | URL de tu frontend |

**Nota**: `DATABASE_URL` se configurará automáticamente cuando agregues la base de datos.

## 🗄️ Paso 3: Configurar Base de Datos PostgreSQL

### 3.1 Crear Base de Datos

1. **Dashboard de Render** → "New" → "PostgreSQL"
2. **Configuración**:
   - **Name**: `nexus-communicator-db`
   - **Database Name**: `nexus_communicator`
   - **User**: `nexus_user`
   - **Region**: La misma que tu Web Service
   - **Plan**: Free (para empezar)

### 3.2 Conectar Base de Datos al Web Service

1. Ve a tu Web Service en Render
2. **Environment Variables** → "Add Environment Variable"
3. **Key**: `DATABASE_URL`
4. **Value**: Selecciona "From Database" → `nexus-communicator-db` → "Internal Database URL"

## ⚙️ Paso 4: Desplegar la Aplicación

### 4.1 Iniciar Deploy

1. **Configuración completa** → "Create Web Service"
2. Render comenzará automáticamente el proceso de build y deploy
3. **Tiempo estimado**: 3-5 minutos

### 4.2 Monitorear el Deploy

En la pestaña "Logs" podrás ver:
```
==> Building...
Installing dependencies from requirements.txt
==> Build successful
==> Starting service...
✅ Base de datos inicializada correctamente
🚀 Iniciando Nexus Communicator Backend...
📍 Puerto: 10000
🔧 Modo debug: False
🗄️ Base de datos: PostgreSQL (Producción)
==> Service is live
```

### 4.3 Verificar Funcionamiento

Una vez desplegado, tu backend estará disponible en:
```
https://nexus-communicator-backend.onrender.com
```

**Pruebas básicas**:
- `GET /health` → Debe retornar `{"status": "healthy"}`
- `GET /` → Debe mostrar información de la API

## 🔧 Paso 5: Configuración Post-Deploy

### 5.1 Configurar CORS para Frontend

Si tu frontend está en Netlify, actualiza la variable de entorno:
```
FRONTEND_URL=https://tu-app.netlify.app
```

### 5.2 Probar Endpoints Principales

```bash
# Verificar salud
curl https://nexus-communicator-backend.onrender.com/health

# Probar registro de usuario
curl -X POST https://nexus-communicator-backend.onrender.com/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Test User","email":"test@example.com","password":"password123"}'
```

### 5.3 Configurar Dominio Personalizado (Opcional)

1. **Settings** → "Custom Domains"
2. Agregar tu dominio personalizado
3. Configurar DNS según las instrucciones de Render

## 📊 Paso 6: Monitoreo y Mantenimiento

### 6.1 Logs y Debugging

- **Logs en tiempo real**: Pestaña "Logs" en Render
- **Métricas**: Pestaña "Metrics" para CPU, memoria, requests
- **Alertas**: Configurar notificaciones por email

### 6.2 Actualizaciones

Para actualizar el backend:
```bash
# Hacer cambios en el código
git add .
git commit -m "Actualización del backend"
git push origin main
```

Render detectará automáticamente los cambios y redesplegará.

### 6.3 Escalamiento

Para manejar más tráfico:
1. **Settings** → "Scaling"
2. Aumentar el plan (Starter, Standard, Pro)
3. Configurar auto-scaling si es necesario

## 🔒 Paso 7: Seguridad y Mejores Prácticas

### 7.1 Variables de Entorno Sensibles

- ✅ Nunca hardcodees API keys en el código
- ✅ Usa variables de entorno para credenciales
- ✅ Regenera `SECRET_KEY` periódicamente

### 7.2 Base de Datos

- ✅ Habilita backups automáticos en PostgreSQL
- ✅ Usa conexiones SSL (habilitado por defecto)
- ✅ Monitorea el uso de la base de datos

### 7.3 HTTPS y Dominios

- ✅ Render proporciona HTTPS automáticamente
- ✅ Usa dominios personalizados para producción
- ✅ Configura redirects HTTP → HTTPS

## 🚨 Solución de Problemas Comunes

### Error: "Build Failed"

**Causa**: Dependencias faltantes o incompatibles
**Solución**:
```bash
# Verificar requirements.txt
pip freeze > requirements.txt
git add requirements.txt
git commit -m "Actualizar dependencias"
git push origin main
```

### Error: "Service Unavailable"

**Causa**: Aplicación no se inicia correctamente
**Solución**:
1. Revisar logs en Render
2. Verificar que `gunicorn src.main:app` funcione localmente
3. Comprobar variables de entorno

### Error: "Database Connection Failed"

**Causa**: Base de datos no conectada o credenciales incorrectas
**Solución**:
1. Verificar que `DATABASE_URL` esté configurada
2. Comprobar que la base de datos esté en la misma región
3. Revisar logs de la base de datos

### Error: "CORS Policy"

**Causa**: Frontend no autorizado para hacer requests
**Solución**:
1. Verificar `FRONTEND_URL` en variables de entorno
2. Actualizar configuración de CORS en `src/main.py`

## 📈 Optimización de Performance

### 7.1 Configuración de Gunicorn

Para mejor performance, puedes personalizar Gunicorn:
```bash
# En lugar de: gunicorn src.main:app
# Usar: gunicorn --workers 4 --timeout 120 src.main:app
```

### 7.2 Caching

Para aplicaciones con mucho tráfico:
1. Implementar Redis para cache
2. Usar CDN para archivos estáticos
3. Optimizar consultas de base de datos

### 7.3 Monitoreo

- Configurar alertas para errores 5xx
- Monitorear tiempo de respuesta
- Revisar uso de memoria y CPU

## 🎯 Checklist Final

Antes de considerar el deploy completo:

- [ ] ✅ Backend desplegado y funcionando
- [ ] ✅ Base de datos PostgreSQL conectada
- [ ] ✅ Variables de entorno configuradas
- [ ] ✅ Endpoint `/health` responde correctamente
- [ ] ✅ Registro de usuarios funciona
- [ ] ✅ CORS configurado para frontend
- [ ] ✅ Logs sin errores críticos
- [ ] ✅ Dominio personalizado configurado (opcional)
- [ ] ✅ Backups de base de datos habilitados

## 📞 Soporte

Si encuentras problemas durante el despliegue:

1. **Logs de Render**: Primera fuente de información
2. **Documentación de Render**: [render.com/docs](https://render.com/docs)
3. **Soporte técnico**: soporte@nexuscommunicator.com
4. **GitHub Issues**: Para reportar bugs específicos

## 🎉 ¡Felicitaciones!

Tu backend de Nexus Communicator está ahora desplegado y listo para conectar con el frontend. La URL de tu API es:

```
https://nexus-communicator-backend.onrender.com
```

Asegúrate de actualizar la configuración de tu frontend para usar esta URL como `VITE_API_BASE_URL`.

---

**Última actualización**: Diciembre 2024  
**Versión de la guía**: 1.0.0

