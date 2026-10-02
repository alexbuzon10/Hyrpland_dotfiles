local M = {}

local state_file = vim.fn.stdpath("state") .. "/selected-colorscheme"
local fallback = "vscode"

local function save(colorscheme)
    vim.fn.mkdir(vim.fn.fnamemodify(state_file, ":h"), "p")
    vim.fn.writefile({ colorscheme }, state_file)
end

local function load()
    if vim.fn.filereadable(state_file) == 0 then
        return fallback
    end

    local lines = vim.fn.readfile(state_file, "", 1)
    local colorscheme = lines[1]

    if not colorscheme or not colorscheme:match("^[%w_.-]+$") then
        return fallback
    end

    return colorscheme
end

function M.setup()
    local colorscheme = load()
    local ok = pcall(vim.cmd.colorscheme, colorscheme)

    if not ok then
        vim.cmd.colorscheme(fallback)
    end

    vim.api.nvim_create_autocmd("ColorScheme", {
        group = vim.api.nvim_create_augroup("PersistentColorscheme", { clear = true }),
        callback = function(event)
            -- Telescope aplica temas temporalmente mientras se navega por la lista.
            -- Solo persistimos el tema confirmado, una vez cerrado el selector.
            if vim.bo.filetype ~= "TelescopePrompt" then
                save(event.match)
            end
        end,
    })
end

return M
