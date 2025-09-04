# Solución de Warnings en tjAdminPy

## Warning: pkg_resources deprecated

**Problema:**
```
UserWarning: pkg_resources is deprecated as an API. See https://setuptools.pypa.io/en/latest/pkg_resources.html. The pkg_resources package is slated for removal as early as 2025-11-30.
```

**Causa:**
- La librería `couchdb` versión 1.2 usa `pkg_resources` (método obsoleto)
- `setuptools` >= 81 emite este warning
- No hay versión más nueva de `couchdb` disponible

**Solución aplicada:**
```python
import warnings
# Suprimir warning específico de pkg_resources deprecation
warnings.filterwarnings("ignore", message="pkg_resources is deprecated as an API")
```

**Ubicación:** `couchdb_utils.py` líneas 3-5

**Estado:** ✅ Resuelto
**Impacto:** ❌ Ninguno en funcionalidad
**Urgencia:** 🟡 Baja (warning cosmético)

## Alternativas futuras

1. **Cambiar librería CouchDB** cuando haya versión actualizada
2. **Pin setuptools** a versión < 81 si es necesario
3. **Migrar a alternativas** como `requests` para comunicación directa

## Warnings normales de Streamlit

Los siguientes warnings son normales y se pueden ignorar:
- `missing ScriptRunContext` - aparece cuando se ejecuta fuera de `streamlit run`
- `Session state does not function` - normal en contexto de testing

**Fecha:** 2025-09-02
**Versiones:**
- CouchDB: 1.2
- setuptools: 80.9.0
- Python: 3.12