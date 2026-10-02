local map = vim.keymap.set

map({ "n", "i" }, "<C-s>", "<Esc><cmd>w<CR>", { desc = "Guardar archivo" })
map("n", "<C-q>", "<cmd>qa<CR>", { desc = "Salir de Neovim" })
map("n", "<C-f>", "/", { desc = "Buscar en archivo" })
map("n", "<Esc>", "<cmd>nohlsearch<CR>", { desc = "Quitar resaltado" })

-- Navegación entre ventanas
map("n", "<C-h>", "<C-w>h", { desc = "Ventana izquierda" })
map("n", "<C-j>", "<C-w>j", { desc = "Ventana abajo" })
map("n", "<C-k>", "<C-w>k", { desc = "Ventana arriba" })
map("n", "<C-l>", "<C-w>l", { desc = "Ventana derecha" })

-- Buffers estilo pestañas de Code
map("n", "]b", "<cmd>bnext<CR>", { desc = "Buffer siguiente" })
map("n", "[b", "<cmd>bprevious<CR>", { desc = "Buffer anterior" })
map("n", "<C-Tab>", "<cmd>bnext<CR>", { desc = "Pestaña siguiente" })
map("n", "<C-S-Tab>", "<cmd>bprevious<CR>", { desc = "Pestaña anterior" })
map("n", "<C-w>", "<cmd>bdelete<CR>", { desc = "Cerrar archivo" })

-- Alt+↑ / Alt+↓ como VS Code
map("n", "<A-Up>", "<cmd>move .-2<CR>==", { desc = "Mover línea arriba" })
map("n", "<A-Down>", "<cmd>move .+1<CR>==", { desc = "Mover línea abajo" })
map("v", "<A-Up>", ":move '<-2<CR>gv=gv", { desc = "Mover selección arriba" })
map("v", "<A-Down>", ":move '>+1<CR>gv=gv", { desc = "Mover selección abajo" })

map("v", "<", "<gv")
map("v", ">", ">gv")

map("n", "<A-S-Down>", "yyp", { desc = "Duplicar línea" })

map("n", "<leader>w", "<cmd>w<CR>", { desc = "Guardar" })
map("n", "<leader>q", "<cmd>bdelete<CR>", { desc = "Cerrar buffer" })
