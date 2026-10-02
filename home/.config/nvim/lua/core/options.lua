local opt = vim.opt

-- Apariencia
opt.number = true
opt.relativenumber = false
opt.cursorline = true
opt.signcolumn = "yes"
opt.termguicolors = true
opt.showmode = false
opt.laststatus = 3
opt.cmdheight = 1
opt.pumheight = 12
opt.winborder = "rounded"

-- Cursor de terminal: línea vertical blanca y parpadeante en modo inserción.
local function set_terminal_cursor_highlight()
    vim.api.nvim_set_hl(0, "TerminalInsertCursor", { fg = "#ffffff", bg = "#ffffff" })
end

set_terminal_cursor_highlight()
vim.api.nvim_create_autocmd("ColorScheme", {
    group = vim.api.nvim_create_augroup("TerminalInsertCursor", { clear = true }),
    callback = set_terminal_cursor_highlight,
})
opt.guicursor = table.concat({
    "n-v-c-sm:block",
    "i-ci-ve:ver25",
    "r-cr-o:hor20",
    "t:ver25-TerminalInsertCursor-blinkwait300-blinkon500-blinkoff500",
}, ",")

-- Edición
opt.expandtab = true
opt.shiftwidth = 4
opt.tabstop = 4
opt.softtabstop = 4
opt.smartindent = true
opt.wrap = false
opt.breakindent = true
opt.scrolloff = 6
opt.sidescrolloff = 6

-- Búsqueda
opt.ignorecase = true
opt.smartcase = true
opt.incsearch = true
opt.hlsearch = true

-- Archivos / UX
opt.mouse = "a"
opt.clipboard = "unnamedplus"
opt.undofile = true
opt.swapfile = false
opt.backup = false
opt.writebackup = false
opt.confirm = true
opt.updatetime = 250
opt.timeoutlen = 400
opt.splitright = true
opt.splitbelow = true

opt.fillchars = {
    eob = " ",
    fold = " ",
    foldopen = "",
    foldclose = "",
    foldsep = " ",
    diff = "╱",
}

vim.diagnostic.config({
    underline = true,
    update_in_insert = false,
    severity_sort = true,
    virtual_text = { spacing = 2, prefix = "●" },
    float = { border = "rounded", source = true },
    signs = {
        text = {
            [vim.diagnostic.severity.ERROR] = "󰅚 ",
            [vim.diagnostic.severity.WARN]  = "󰀪 ",
            [vim.diagnostic.severity.INFO]  = "󰋽 ",
            [vim.diagnostic.severity.HINT]  = "󰌶 ",
        },
    },
})
