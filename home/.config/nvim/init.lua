-- ============================================================
-- Neovim — estilo VS Code, ligero y transparente
-- ============================================================
vim.g.mapleader = " "
vim.g.maplocalleader = " "

require("core.options")
require("core.keymaps")
require("core.autocmds")
require("config.lazy")
require("core.theme").setup()
