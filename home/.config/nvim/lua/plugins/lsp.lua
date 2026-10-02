return {
    {
        "saghen/blink.cmp",
        version = "1.*",
        dependencies = { "rafamadriz/friendly-snippets" },
        opts = {
            keymap = { preset = "super-tab" },
            appearance = { nerd_font_variant = "mono" },
            completion = {
                documentation = {
                    auto_show = true,
                    auto_show_delay_ms = 250,
                    window = { border = "rounded" },
                },
                menu = {
                    border = "rounded",
                    draw = {
                        columns = {
                            { "kind_icon" },
                            { "label", "label_description", gap = 1 },
                            { "source_name" },
                        },
                    },
                },
                ghost_text = { enabled = true },
            },
            signature = {
                enabled = true,
                window = { border = "rounded" },
            },
            sources = { default = { "lsp", "path", "snippets", "buffer" } },
            fuzzy = { implementation = "prefer_rust" },
        },
    },

    {
        "neovim/nvim-lspconfig",
        dependencies = { "saghen/blink.cmp" },
        config = function()
            local capabilities = require("blink.cmp").get_lsp_capabilities()

            vim.lsp.config("lua_ls", {
                capabilities = capabilities,
                settings = {
                    Lua = {
                        runtime = { version = "LuaJIT" },
                        diagnostics = { globals = { "vim" } },
                        workspace = {
                            checkThirdParty = false,
                            library = { vim.env.VIMRUNTIME },
                        },
                        telemetry = { enable = false },
                    },
                },
            })

            local servers = {
                clangd = "clangd",
                pyright = "pyright-langserver",
                ts_ls = "typescript-language-server",
            }

            for name, executable in pairs(servers) do
                if vim.fn.executable(executable) == 1 then
                    vim.lsp.config(name, { capabilities = capabilities })
                    vim.lsp.enable(name)
                end
            end

            if vim.fn.executable("lua-language-server") == 1 then
                vim.lsp.enable("lua_ls")
            end

            vim.api.nvim_create_autocmd("LspAttach", {
                group = vim.api.nvim_create_augroup("CodeLikeLsp", { clear = true }),
                callback = function(event)
                    local map = function(lhs, rhs, desc)
                        vim.keymap.set("n", lhs, rhs, {
                            buffer = event.buf,
                            desc = desc,
                        })
                    end

                    map("K", vim.lsp.buf.hover, "Información")
                    map("gd", vim.lsp.buf.definition, "Ir a definición")
                    map("gD", vim.lsp.buf.declaration, "Ir a declaración")
                    map("gi", vim.lsp.buf.implementation, "Ir a implementación")
                    map("gr", vim.lsp.buf.references, "Referencias")
                    map("<F2>", vim.lsp.buf.rename, "Renombrar símbolo")
                    map("<F12>", vim.lsp.buf.definition, "Ir a definición")
                    map("<S-F12>", vim.lsp.buf.references, "Buscar referencias")
                    map("<leader>ca", vim.lsp.buf.code_action, "Acciones de código")
                    map("<leader>rn", vim.lsp.buf.rename, "Renombrar")
                    map("[d", function()
                        vim.diagnostic.jump({ count = -1, float = true })
                    end, "Diagnóstico anterior")
                    map("]d", function()
                        vim.diagnostic.jump({ count = 1, float = true })
                    end, "Diagnóstico siguiente")
                end,
            })
        end,
    },
}
