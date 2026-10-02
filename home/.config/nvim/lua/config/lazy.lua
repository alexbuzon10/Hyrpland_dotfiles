local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
local uv = vim.uv or vim.loop

if not uv.fs_stat(lazypath) then
    local out = vim.fn.system({
        "git", "clone", "--filter=blob:none",
        "https://github.com/folke/lazy.nvim.git",
        "--branch=stable",
        lazypath,
    })
    if vim.v.shell_error ~= 0 then
        error("No se pudo instalar lazy.nvim:\n" .. out)
    end
end

vim.opt.rtp:prepend(lazypath)

require("lazy").setup({
    spec = {
	{ import = "plugins" },
        { import = "plugins.ui" },
        { import = "plugins.editor" },
        { import = "plugins.lsp" },
        { import = "plugins.treesitter" },
    },
    install = { colorscheme = { "vscode", "onedark" } },
    checker = { enabled = true, notify = false },
    change_detection = { notify = false },
    ui = { border = "rounded" },
})
