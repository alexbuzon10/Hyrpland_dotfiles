# Actualizar el repositorio

Los archivos de `home/` son plantillas. Las rutas que dependan del usuario deben
usar `__DOTFILES_HOME__`; `install.sh` lo sustituye por el directorio personal de
la maquina de destino.

Antes de confirmar cambios:

```bash
./scripts/check.sh
git diff --check
```

No se deben añadir historiales, claves SSH/GPG, perfiles de navegador, archivos
VPN, tokens, cookies, caches, bases de datos de aplicaciones ni binarios `.so`.
El modulo C de Waybar se compila durante la instalacion.
