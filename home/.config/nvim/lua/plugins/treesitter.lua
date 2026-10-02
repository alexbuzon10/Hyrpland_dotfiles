return {
    {
        "nvim-treesitter/nvim-treesitter",
        lazy = false,
        build = ":TSUpdate",
        config = function()
            local ts = require("nvim-treesitter")
            ts.setup({})

            local function set_bash_highlights()
                -- Bash captura por separado el `$` y el nombre de la variable.
                -- Enlazamos las expansiones al grupo amarillo; las asignaciones
                -- conservan el grupo normal de variable (rojo en onedark_vivid).
                vim.api.nvim_set_hl(0, "@punctuation.special.bash", { link = "@variable.builtin" })
                vim.api.nvim_set_hl(0, "@variable.expansion.bash", { link = "@variable.builtin" })

                -- Delimitadores de sustituciones de comando: `$(comando)`.
                -- Es intencionadamente fijo para distinguirse en VS Code y OneDark.
                vim.api.nvim_set_hl(0, "@punctuation.command-substitution.bash", { fg = "#e06cdb" })

                -- Color exclusivo para los comandos, tanto externos como built-ins.
                local command_color = "#e89a5e"
                vim.api.nvim_set_hl(0, "@function.call.bash", { fg = command_color })
                vim.api.nvim_set_hl(0, "@function.builtin.bash", { fg = command_color })

                -- Opciones de comandos (`-r`, `--recursive`, `--color=auto`).
                vim.api.nvim_set_hl(0, "@argument.option.bash", { fg = "#8aa6c8" })
            end

            set_bash_highlights()

            vim.api.nvim_create_autocmd("ColorScheme", {
                group = vim.api.nvim_create_augroup("BashTreesitterHighlights", { clear = true }),
                callback = set_bash_highlights,
            })

            ts.install({
                "bash",
                "c",
                "cpp",
                "lua",
                "python",
                "javascript",
                "typescript",
                "json",
                "html",
                "css",
                "markdown",
                "markdown_inline",
                "vim",
                "vimdoc",
            })

            vim.api.nvim_create_autocmd("FileType", {
                pattern = {
                    "sh", "c", "cpp", "lua", "python",
                    "javascript", "javascriptreact",
                    "typescript", "typescriptreact",
                    "json", "html", "css", "markdown", "vim", "vimdoc",
                },
                callback = function()
                    pcall(vim.treesitter.start)
                end,
            })
        end,
    },
}
