# Checklist de Exposicion

## 1. Levantar backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python scripts/seed_users.py
python -m uvicorn app.main:app --reload
```

Verificar:

- API: `http://127.0.0.1:8000`
- Docs: `http://127.0.0.1:8000/docs`
- Health: `http://127.0.0.1:8000/api/health`

## 2. Levantar frontend

```bash
cd frontend
npm install
npm.cmd run dev
```

Verificar:

- App: `http://127.0.0.1:3000`
- Login: `http://127.0.0.1:3000/login`

## 3. Usuarios de prueba

- Gerente: `gerente` / `Gerente12345`
- Jefe de operarios: `jefe` / `Jefe12345`
- Operario: `operario1` / `Operario12345`

## 4. Orden recomendado para demo

1. Entrar como `gerente`.
2. Mostrar que aparece el acceso a Auditoria.
3. Abrir `/logs` y explicar trazabilidad, filtros y privacidad.
4. Cerrar sesion.
5. Entrar como `jefe`.
6. Abrir `/users`.
7. Crear un operario de prueba.
8. Editar username o contrasena del operario.
9. Desactivar y reactivar el operario.
10. Cerrar sesion.
11. Entrar como `operario1`.
12. Cargar archivo STL.
13. Analizar compatibilidad.
14. Convertir a G-code.
15. Descargar `.nc`.
16. Cerrar sesion.
17. Volver como `gerente`.
18. Mostrar logs de login, carga, analisis, conversion, gestion de usuarios y logout.

## 5. Posibles errores y solucion

### Backend no levanta

- Revisar que el entorno virtual este activado.
- Ejecutar `pip install -r requirements.txt`.
- Confirmar que el puerto `8000` no este ocupado.
- Probar `python -m uvicorn app.main:app --reload`.

### Frontend no conecta

- Confirmar que el backend este en `http://127.0.0.1:8000`.
- Revisar `NEXT_PUBLIC_GCODER_API_URL`.
- Recargar el navegador despues de levantar backend.

### Token expirado

- Cerrar sesion desde la interfaz.
- Volver a iniciar sesion.
- Si persiste, limpiar `localStorage` del navegador.

### Base de datos sin usuarios

- Ejecutar:

```bash
cd backend
.venv\Scripts\activate
python scripts/seed_users.py
```

### Usuario inactivo

- Entrar como `jefe`.
- Ir a `/users`.
- Reactivar el operario.

### Error CORS

- Confirmar que el frontend corre en `http://localhost:3000`, `http://127.0.0.1:3000`, `http://localhost:3001` o `http://127.0.0.1:3001`.
- Revisar configuracion CORS en `backend/app/main.py`.

### Puerto ocupado

- Usar otro puerto para frontend:

```bash
npm.cmd run dev -- --port 3001
```

- Para backend, cambiar puerto:

```bash
python -m uvicorn app.main:app --reload --port 8001
```

Si se cambia el puerto backend, ajustar `NEXT_PUBLIC_GCODER_API_URL`.

## 6. Validacion previa

Backend:

```bash
cd backend
.venv\Scripts\activate
python -m pytest
```

Frontend:

```bash
cd frontend
npm.cmd run typecheck
npm.cmd run build
```
