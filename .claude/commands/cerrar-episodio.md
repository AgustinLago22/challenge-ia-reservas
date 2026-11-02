---
description: Cierra un episodio de delegación. Corre las pruebas, guarda la evidencia y actualiza el progreso.
argument-hint: <número de episodio, p. ej. 1>
---

Cerrá el episodio $ARGUMENTS siguiendo estos pasos, en orden y sin saltear ninguno:

1. Ejecutá las pruebas y guardá la salida **real** (sin editar) con:
   `.venv/Scripts/python -m pytest -v 2>&1 | tee docs/evidencia/episodio-$ARGUMENTS-pytest.txt`
   Agregá al final del archivo una línea con la fecha, `python --version` y `git rev-parse --short HEAD`.
2. Si alguna prueba falla, **no la ocultes**: informala tal cual y no sigas al paso 4
   hasta que el humano decida qué hacer.
3. En `docs/PROGRESO.md` actualizá: estado del episodio, qué se ejecutó (comando y
   resultado observado), qué quedó sin ejecutar y por qué, pendientes y próximo paso.
4. En `docs/DECISIONES.md`, completá la ficha del Episodio $ARGUMENTS **solo** en los
   campos del agente (acción/resultado, archivos tocados, evidencia). Dejá
   "Decisión humana" y "Motivo" como `[COMPLETAR POR EL HUMANO]`.
5. Mostrame `git status` y `git diff --stat` y proponé un mensaje de commit con el formato
   `episodio $ARGUMENTS: <resumen>`. No hagas commit hasta que yo lo apruebe.
