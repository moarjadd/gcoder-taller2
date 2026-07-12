# Guia de Pruebas Funcionales

Sistema: G-Coder V2  
Objetivo: validar los flujos principales de autenticacion, roles, conversion, auditoria y gestion de usuarios antes de la exposicion academica.

| Codigo de prueba | Rol | Caso de prueba | Pasos | Resultado esperado | Estado |
|---|---|---|---|---|---|
| PF-01 | gerente | Login gerente correcto | Abrir `/login`; ingresar `gerente` y `Gerente12345`; enviar formulario. | El sistema redirige al conversor, muestra usuario gerente y acceso a Auditoria. | Pendiente |
| PF-02 | jefe_operarios | Login jefe correcto | Abrir `/login`; ingresar `jefe` y `Jefe12345`; enviar formulario. | El sistema redirige al conversor, muestra usuario jefe y acceso a Usuarios. | Pendiente |
| PF-03 | operario | Login operario correcto | Abrir `/login`; ingresar `operario1` y `Operario12345`; enviar formulario. | El sistema redirige al conversor y no muestra Auditoria ni Usuarios. | Pendiente |
| PF-04 | cualquiera | Login incorrecto | Abrir `/login`; usar un usuario valido con contrasena incorrecta. | La interfaz muestra error de credenciales y no permite entrar. | Pendiente |
| PF-05 | gerente | Gerente accede a logs | Iniciar sesion como gerente; entrar a `/logs`; aplicar filtros si hay datos. | Se muestra tabla de logs globales con fecha, usuario, rol, accion, estado y detalle. | Pendiente |
| PF-06 | operario | Operario no accede a logs | Iniciar sesion como operario; navegar manualmente a `/logs`. | Se muestra acceso denegado o se bloquea la ruta. | Pendiente |
| PF-07 | jefe_operarios | Jefe crea operario | Iniciar sesion como jefe; abrir `/users`; crear un usuario operario con contrasena valida. | El operario aparece en la lista y queda activo. | Pendiente |
| PF-08 | jefe_operarios | Jefe no crea gerente | Intentar crear un usuario con rol gerente desde API o validar que la UI no ofrezca esa opcion. | El backend responde 403 y la UI solo permite rol operario. | Pendiente |
| PF-09 | jefe_operarios | Jefe desactiva operario | Abrir `/users`; seleccionar un operario activo; presionar Desactivar. | El usuario queda inactivo y se registra `USER_DEACTIVATED`. | Pendiente |
| PF-10 | operario | Operario inactivo no inicia sesion | Desactivar un operario; intentar iniciar sesion con sus credenciales. | El login falla con error de credenciales o usuario inactivo. | Pendiente |
| PF-11 | operario | Operario carga archivo 3D | Iniciar sesion como operario; cargar un archivo `.stl`. | El archivo aparece en la interfaz y se habilita el analisis. | Pendiente |
| PF-12 | operario | Operario analiza archivo | Con un STL cargado, presionar Analizar. | El sistema muestra validacion de malla y compatibilidad CNC. | Pendiente |
| PF-13 | operario | Operario convierte archivo a `.nc` | Tras analisis compatible, generar G-code y descargar `.nc`. | Se muestra G-code, reporte y se descarga un archivo `.nc`. | Pendiente |
| PF-14 | gerente | Logs registran carga, analisis y conversion | Hacer PF-11 a PF-13; volver como gerente a `/logs`. | Aparecen `FILE_UPLOADED`, `ANALYZE_SUCCESS`, `GCODE_GENERATION_STARTED`, `PARAMETERS_USED`, `CONVERT_SUCCESS` y `GCODE_EXPORTED`. | Pendiente |
| PF-15 | cualquiera | Logout registra cierre de sesion | Iniciar sesion; presionar Cerrar sesion; entrar como gerente a logs. | La sesion local se limpia y existe evento `LOGOUT`. | Pendiente |

## Notas de privacidad durante pruebas

- No registrar contrasenas en evidencias visibles.
- No capturar tokens completos en screenshots.
- Usar archivos STL de prueba sin datos personales.
- Si se muestra un nombre de archivo, verificar que sea solo nombre base y extension.
