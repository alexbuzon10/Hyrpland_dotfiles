# Neovim estilo VS Code

Configuración para Arch Linux + Kitty + Nerd Font.

## Incluye

- VS Code Dark+ con fondo transparente.
- Explorer lateral (`nvim-tree`).
- Pestañas (`bufferline`).
- Statusline (`lualine`).
- Búsqueda de archivos/texto/comandos (`Telescope`).
- Git en el gutter (`gitsigns`).
- IntelliSense (`blink.cmp`).
- LSP moderno de Neovim.
- Treesitter actual.
- Panel de Problemas (`Trouble`).
- Terminal integrada.
- Agente Codex integrado en un panel lateral.
- Comentarios, autopairs y formateo.

## Dependencias Arch

Mínimo recomendado:

```bash
sudo pacman -S --needed \
  neovim git ripgrep fd tree-sitter-cli clang lua-language-server
```

Opcional para Python y TypeScript:

```bash
sudo pacman -S --needed \
  pyright typescript typescript-language-server
```

Formatters opcionales:

```bash
sudo pacman -S --needed stylua ruff prettier
```

## Instalación

```bash
mv ~/.config/nvim ~/.config/nvim.backup 2>/dev/null || true
mkdir -p ~/.config/nvim
cp -r /RUTA/nvim-code-like/* ~/.config/nvim/
nvim
```

En el primer arranque `lazy.nvim` descargará los plugins.

## Atajos

| Tecla | Acción |
|---|---|
| `Ctrl+B` | Explorer |
| `Ctrl+P` | Buscar archivo |
| `Ctrl+Shift+F` | Buscar en proyecto |
| `Ctrl+Shift+P` | Paleta de comandos |
| `Ctrl+S` | Guardar |
| `Ctrl+W` | Cerrar buffer |
| `Ctrl+Tab` | Buffer siguiente |
| `Ctrl+Shift+Tab` | Buffer anterior |
| `Alt+↑ / Alt+↓` | Mover línea/selección |
| `Ctrl+/` | Comentar/descomentar (Kitty lo entrega como `Ctrl+_`) |
| `F2` | Renombrar símbolo |
| `F12` | Ir a definición |
| `Shift+F12` | Referencias |
| `Space c a` | Acciones de código |
| `Alt+Shift+F` | Formatear |
| `Ctrl+Shift+M` | Problemas |
| `Ctrl+\` | Terminal |
| `Space a c` | Abrir/cerrar Codex AI |
| `Space a f` | Enviar archivo y línea activos a Codex |
| `Space a a` | Abrir terminal y Codex simultáneamente |
| `Space` | Leader |

También puedes abrir el agente con `:Codex`. Codex se inicia en la raíz Git
del proyecto actual, recibe el archivo activo al iniciar y conserva la sesión
mientras alternas el panel. Tras cambiar de archivo, usa `Space a f` o
`:CodexFile` para actualizar su contexto.

## Transparencia

`vscode.nvim` está configurado con `transparent = true` y también se desactiva el fondo propio de NvimTree. El fondo principal lo renderiza Kitty.

## LSP

Se activa automáticamente solo si el servidor está instalado y en `PATH`:

- `clangd` → C/C++
- `lua-language-server` → Lua
- `pyright-langserver` → Python
- `typescript-language-server` → JavaScript/TypeScript

Diagnóstico:

```vim
:checkhealth vim.lsp
```

Plugins:

```vim
:Lazy
```
