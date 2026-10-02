return {
    {
        "nvim-telescope/telescope.nvim",
        dependencies = { "nvim-lua/plenary.nvim", "nvim-tree/nvim-web-devicons" },
        cmd = "Telescope",
        keys = {
            {
                "<C-p>",
                function() require("telescope.builtin").find_files({ hidden = true }) end,
                desc = "Buscar archivo",
            },
            {
                "<C-S-f>",
                function() require("telescope.builtin").live_grep() end,
                desc = "Buscar en proyecto",
            },
            {
                "<C-S-p>",
                function() require("telescope.builtin").commands() end,
                desc = "Paleta de comandos",
            },
            {
                "<leader>ff",
                function() require("telescope.builtin").find_files({ hidden = true }) end,
                desc = "Buscar archivo",
            },
            {
                "<leader>fg",
                function() require("telescope.builtin").live_grep() end,
                desc = "Buscar en proyecto",
            },
            {
                "<leader>fb",
                function() require("telescope.builtin").buffers() end,
                desc = "Buscar buffer",
            },
            {
                "<leader>fc",
                function() require("telescope.builtin").commands() end,
                desc = "Paleta de comandos",
            },
            {
                "<leader>fh",
                function() require("telescope.builtin").help_tags() end,
                desc = "Ayuda",
            },
            {
                "<leader>ut",
                function()
                    require("telescope.builtin").colorscheme({ enable_preview = true })
                end,
                desc = "Seleccionar tema",
            },
        },
        opts = {
            defaults = {
                prompt_prefix = "   ",
                selection_caret = "  ",
                path_display = { "smart" },
                sorting_strategy = "ascending",
                layout_config = { prompt_position = "top" },
                border = true,
            },
        },
    },

    {
        "lewis6991/gitsigns.nvim",
        event = { "BufReadPre", "BufNewFile" },
        opts = {
            signs = {
                add = { text = "▎" },
                change = { text = "▎" },
                delete = { text = "" },
                topdelete = { text = "" },
                changedelete = { text = "▎" },
                untracked = { text = "▎" },
            },
            current_line_blame = false,
            on_attach = function(bufnr)
                local gs = require("gitsigns")
                vim.keymap.set("n", "]c", function() gs.nav_hunk("next") end,
                    { buffer = bufnr, desc = "Cambio Git siguiente" })
                vim.keymap.set("n", "[c", function() gs.nav_hunk("prev") end,
                    { buffer = bufnr, desc = "Cambio Git anterior" })
                vim.keymap.set("n", "<leader>gp", gs.preview_hunk,
                    { buffer = bufnr, desc = "Previsualizar cambio Git" })
            end,
        },
    },

    {
        "numToStr/Comment.nvim",
        event = "VeryLazy",
        opts = {},
        config = function(_, opts)
            require("Comment").setup(opts)
            local api = require("Comment.api")

            -- Kitty suele enviar Ctrl+/ como Ctrl+_.
            vim.keymap.set("n", "<C-_>", function()
                api.toggle.linewise.current()
            end, { desc = "Comentar línea" })

            vim.keymap.set("x", "<C-_>", function()
                vim.api.nvim_feedkeys(
                    vim.api.nvim_replace_termcodes("<Esc>", true, false, true),
                    "nx",
                    false
                )
                api.toggle.linewise(vim.fn.visualmode())
            end, { desc = "Comentar selección" })
        end,
    },

    {
        "windwp/nvim-autopairs",
        event = "InsertEnter",
        opts = {},
    },

    {
        "akinsho/toggleterm.nvim",
        version = "*",
        cmd = { "ToggleTerm", "DevTerminal", "Codex", "CodexFile", "CodexWorkspace" },
        keys = {
            { "<leader>t", "<cmd>DevTerminal<CR>", desc = "Terminal" },
            { "<C-\\>", "<cmd>DevTerminal<CR>", desc = "Terminal" },
            { "<leader>aa", "<cmd>CodexWorkspace<CR>", desc = "Terminal + Codex" },
            { "<leader>ac", "<cmd>Codex<CR>", desc = "Codex AI" },
            { "<leader>af", "<cmd>CodexFile<CR>", desc = "Enviar archivo activo a Codex" },
        },
        config = function()
            require("toggleterm").setup({
                size = 15,
                open_mapping = [[<C-\>]],
                direction = "horizontal",
                shade_terminals = false,
                start_in_insert = true,
                persist_size = true,
                persist_mode = true,
            })

            local Terminal = require("toggleterm.terminal").Terminal
            local codex_bin = vim.fn.exepath("codex")
            local initial_context
            local project_dir = vim.fn.getcwd()
            local shell, codex
            local saved_layout
            local saved_windows
            local saved_sizes

            local function window_set()
                local result = {}
                for _, window in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
                    local buffer = vim.api.nvim_win_get_buf(window)
                    if vim.bo[buffer].filetype ~= "toggleterm" then
                        result[window] = true
                    end
                end
                return result
            end

            local function same_window_set(left, right)
                for window in pairs(left or {}) do
                    if not right[window] then return false end
                end
                for window in pairs(right) do
                    if not (left or {})[window] then return false end
                end
                return true
            end

            local function normalize_auxiliary_layout()
                local windows = vim.api.nvim_tabpage_list_wins(0)
                if #windows == 1 then
                    vim.api.nvim_win_set_width(windows[1], vim.o.columns)
                    vim.api.nvim_win_set_height(windows[1], vim.o.lines)
                    return
                end
                pcall(vim.cmd, "wincmd =")
                local editors = {}
                for _, window in ipairs(windows) do
                    local buffer = vim.api.nvim_win_get_buf(window)
                    local filetype = vim.bo[buffer].filetype
                    if vim.bo[buffer].buftype == "" and filetype ~= "NvimTree" and filetype ~= "trouble" then
                        table.insert(editors, window)
                    end
                end
                if #editors == 1 then
                    vim.api.nvim_win_set_width(editors[1], vim.o.columns)
                    vim.api.nvim_win_set_height(editors[1], vim.o.lines)
                end
                for _, window in ipairs(windows) do
                    local buffer = vim.api.nvim_win_get_buf(window)
                    local filetype = vim.bo[buffer].filetype
                    if filetype == "NvimTree" then
                        vim.api.nvim_win_set_width(window, 34)
                    elseif filetype == "trouble" then
                        vim.api.nvim_win_set_height(window, 10)
                    end
                end
            end

            local function remember_editor_size()
                local shell_open = shell and shell:is_open()
                local codex_open = codex and codex:is_open()
                if not shell_open and not codex_open and not saved_layout then
                    saved_layout = vim.fn.winrestcmd()
                    saved_windows = window_set()
                    saved_sizes = {}
                    for window in pairs(saved_windows) do
                        saved_sizes[window] = {
                            height = vim.api.nvim_win_get_height(window),
                            width = vim.api.nvim_win_get_width(window),
                        }
                    end
                end
            end

            local function restore_editor_sizes()
                vim.schedule(function()
                    if (shell and shell:is_open()) or (codex and codex:is_open()) then
                        return
                    end
                    local current_windows = window_set()
                    if saved_layout and saved_layout ~= "" and same_window_set(saved_windows, current_windows) then
                        pcall(vim.cmd, saved_layout)
                        local has_saved_trouble = false
                        for window in pairs(saved_sizes or {}) do
                            if vim.api.nvim_win_is_valid(window)
                                and vim.bo[vim.api.nvim_win_get_buf(window)].filetype == "trouble" then
                                has_saved_trouble = true
                                break
                            end
                        end
                        for window, size in pairs(saved_sizes or {}) do
                            if vim.api.nvim_win_is_valid(window) then
                                local buffer = vim.api.nvim_win_get_buf(window)
                                local filetype = vim.bo[buffer].filetype
                                if filetype ~= "NvimTree" and filetype ~= "trouble" then
                                    vim.api.nvim_win_set_width(window, size.width)
                                    vim.api.nvim_win_set_height(window, has_saved_trouble and vim.o.lines or size.height)
                                end
                            end
                        end
                        for window, size in pairs(saved_sizes or {}) do
                            if vim.api.nvim_win_is_valid(window) then
                                local filetype = vim.bo[vim.api.nvim_win_get_buf(window)].filetype
                                if filetype == "NvimTree" or filetype == "trouble" then
                                    vim.api.nvim_win_set_width(window, size.width)
                                    vim.api.nvim_win_set_height(window, size.height)
                                end
                            end
                        end
                    else
                        normalize_auxiliary_layout()
                    end
                    saved_layout = nil
                    saved_windows = nil
                    saved_sizes = nil
                end)
            end

            shell = Terminal:new({
                direction = "horizontal",
                hidden = true,
                dir = project_dir,
                on_open = function(term)
                    vim.cmd("wincmd J")
                    vim.cmd("resize 15")
                    vim.cmd("startinsert!")
                    vim.keymap.set("t", "<Esc><Esc>", [[<C-\\><C-n>]], {
                        buffer = term.bufnr,
                        desc = "Salir del modo terminal",
                    })
                    vim.keymap.set("t", "<C-\\>", "<cmd>DevTerminal<CR>", {
                        buffer = term.bufnr,
                        desc = "Cerrar terminal",
                    })
                end,
                on_close = function(term)
                    if term.window and vim.api.nvim_win_is_valid(term.window) then
                        vim.wo[term.window].winfixheight = false
                        vim.wo[term.window].winfixwidth = false
                        vim.api.nvim_win_set_height(term.window, 1)
                    end
                    restore_editor_sizes()
                end,
            })

            local function current_file_context()
                local buffer = vim.api.nvim_get_current_buf()
                local path = vim.api.nvim_buf_get_name(buffer)
                if path == "" or vim.bo[buffer].buftype ~= "" then
                    return nil
                end

                project_dir = vim.fs.root(path, ".git") or vim.fs.dirname(path) or vim.fn.getcwd()
                local relative = vim.fn.fnamemodify(path, ":.")
                local line = vim.api.nvim_win_get_cursor(0)[1]
                return string.format("El archivo activo en Neovim es %s, línea %d.", relative, line)
            end

            codex = Terminal:new({
                cmd = function()
                    local command = vim.fn.shellescape(codex_bin)
                    if initial_context then
                        command = command .. " " .. vim.fn.shellescape(initial_context)
                        initial_context = nil
                    end
                    return command
                end,
                direction = "vertical",
                hidden = true,
                close_on_exit = false,
                dir = project_dir,
                on_open = function(term)
                    vim.cmd("wincmd L")
                    vim.cmd("vertical resize " .. math.max(45, math.floor(vim.o.columns * 0.32)))
                    vim.cmd("startinsert!")
                    vim.keymap.set("t", "<Esc><Esc>", [[<C-\><C-n>]], {
                        buffer = term.bufnr,
                        desc = "Salir del modo terminal",
                    })
                    vim.keymap.set("t", "<C-\\>", "<cmd>DevTerminal<CR>", {
                        buffer = term.bufnr,
                        desc = "Abrir terminal inferior",
                    })
                end,
                on_close = function(term)
                    if term.window and vim.api.nvim_win_is_valid(term.window) then
                        vim.wo[term.window].winfixheight = false
                        vim.wo[term.window].winfixwidth = false
                        vim.api.nvim_win_set_width(term.window, 1)
                    end
                    restore_editor_sizes()
                end,
            })

            local function codex_is_running()
                if not codex.job_id then
                    return false
                end
                return vim.fn.jobwait({ codex.job_id }, 0)[1] == -1
            end

            local function reset_finished_codex()
                if codex.job_id and not codex_is_running() then
                    codex:shutdown()
                    codex.job_id = nil
                    codex.bufnr = nil
                end
            end

            local function toggle_codex()
                if codex_bin == "" then
                    vim.notify("No se encuentra el ejecutable 'codex' en PATH", vim.log.levels.ERROR)
                    return
                end
                remember_editor_size()
                local was_open = codex:is_open()
                reset_finished_codex()
                if was_open and not codex:is_open() then
                    return
                end
                if codex:is_open() then
                    codex:close()
                    return
                end
                if not codex_is_running() then
                    initial_context = current_file_context()
                end
                codex.dir = project_dir
                codex:open(math.max(45, math.floor(vim.o.columns * 0.32)))
            end

            local function toggle_shell()
                remember_editor_size()
                current_file_context()
                shell.dir = project_dir
                if shell:is_open() then
                    shell:close()
                    return
                end

                local reopen_codex = codex:is_open()
                if reopen_codex then
                    codex:close()
                end
                shell:open(15)
                if reopen_codex then
                    local editor_window
                    for _, window in ipairs(vim.api.nvim_tabpage_list_wins(0)) do
                        local buffer = vim.api.nvim_win_get_buf(window)
                        local filetype = vim.bo[buffer].filetype
                        if vim.bo[buffer].buftype == "" and filetype ~= "NvimTree" and filetype ~= "trouble" then
                            editor_window = window
                            break
                        end
                    end
                    if editor_window then
                        vim.api.nvim_set_current_win(editor_window)
                    end
                    codex:open(math.max(45, math.floor(vim.o.columns * 0.32)))
                end
            end

            local function open_workspace()
                remember_editor_size()
                local context = current_file_context()
                local editor_window = vim.api.nvim_get_current_win()
                if not shell:is_open() then
                    shell.dir = project_dir
                    shell:open(15)
                end
                if codex_bin == "" then
                    vim.notify("No se encuentra el ejecutable 'codex' en PATH", vim.log.levels.ERROR)
                    return
                end
                reset_finished_codex()
                if not codex_is_running() then
                    initial_context = context
                end
                if not codex:is_open() then
                    codex.dir = project_dir
                    if vim.api.nvim_win_is_valid(editor_window) then
                        vim.api.nvim_set_current_win(editor_window)
                    end
                    codex:open(math.max(45, math.floor(vim.o.columns * 0.32)))
                end
            end

            local function send_current_file()
                local context = current_file_context()
                if not context then
                    vim.notify("El buffer actual no corresponde a un archivo", vim.log.levels.WARN)
                    return
                end
                reset_finished_codex()
                if not codex_is_running() then
                    initial_context = context
                    codex.dir = project_dir
                    codex:toggle(math.max(45, math.floor(vim.o.columns * 0.32)))
                    return
                end
                if not codex:is_open() then
                    codex:open(math.max(45, math.floor(vim.o.columns * 0.32)))
                end
                codex:send(context .. " Úsalo como contexto para mi siguiente petición.")
            end

            vim.keymap.set({ "n", "t" }, "<leader>ac", toggle_codex, {
                desc = "Codex AI",
            })
            vim.keymap.set({ "n", "t" }, "<leader>t", toggle_shell, {
                desc = "Terminal",
            })
            vim.keymap.set({ "n", "t" }, "<C-\\>", toggle_shell, {
                desc = "Terminal",
            })
            vim.keymap.set({ "n", "t" }, "<leader>aa", open_workspace, {
                desc = "Terminal + Codex",
            })
            vim.keymap.set("n", "<leader>af", send_current_file, {
                desc = "Enviar archivo activo a Codex",
            })
            vim.api.nvim_create_user_command("Codex", toggle_codex, {
                desc = "Abrir o cerrar Codex AI",
            })
            vim.api.nvim_create_user_command("DevTerminal", toggle_shell, {
                desc = "Abrir o cerrar la terminal del proyecto",
            })
            vim.api.nvim_create_user_command("CodexWorkspace", open_workspace, {
                desc = "Abrir la terminal y Codex simultáneamente",
            })
            vim.api.nvim_create_user_command("CodexFile", send_current_file, {
                desc = "Enviar el archivo activo a Codex AI",
            })
        end,
    },

    {
        "folke/trouble.nvim",
        cmd = "Trouble",
        dependencies = { "nvim-tree/nvim-web-devicons" },
        keys = {
            { "<leader>xx", "<cmd>Trouble diagnostics toggle<CR>", desc = "Problemas" },
            { "<leader>xX", "<cmd>Trouble diagnostics toggle filter.buf=0<CR>", desc = "Problemas del archivo" },
            { "<leader>cs", "<cmd>Trouble symbols toggle focus=false<CR>", desc = "Símbolos" },
            { "<C-S-m>", "<cmd>Trouble diagnostics toggle<CR>", desc = "Problemas" },
        },
        opts = { focus = true },
    },

    {
        "folke/which-key.nvim",
        event = "VeryLazy",
        opts = {
            preset = "modern",
            delay = 300,
            spec = {
                { "<leader>f", group = "Buscar" },
                { "<leader>g", group = "Git" },
                { "<leader>x", group = "Problemas" },
                { "<leader>c", group = "Código" },
                { "<leader>u", group = "Interfaz" },
            },
        },
    },

    {
        "stevearc/conform.nvim",
        cmd = { "ConformInfo" },
        event = { "BufWritePre" },
        keys = {
            {
                "<A-S-f>",
                function()
                    require("conform").format({ async = true, lsp_format = "fallback" })
                end,
                mode = { "n", "v" },
                desc = "Formatear documento",
            },
            {
                "<leader>cf",
                function()
                    require("conform").format({ async = true, lsp_format = "fallback" })
                end,
                mode = { "n", "v" },
                desc = "Formatear documento",
            },
        },
        opts = {
            formatters_by_ft = {
                c = { "clang_format" },
                cpp = { "clang_format" },
                lua = { "stylua" },
                python = { "ruff_format" },
                javascript = { "prettier" },
                javascriptreact = { "prettier" },
                typescript = { "prettier" },
                typescriptreact = { "prettier" },
                json = { "prettier" },
                css = { "prettier" },
                html = { "prettier" },
                markdown = { "prettier" },
            },
        },
    },
}
