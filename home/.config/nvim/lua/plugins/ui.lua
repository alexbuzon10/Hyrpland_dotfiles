return {
    {
        "Mofiqul/vscode.nvim",
        lazy = false,
        priority = 1000,
        config = function()
            require("vscode").setup({
                style = "dark",
                transparent = true,
                italic_comments = true,
                italic_inlayhints = true,
                underline_links = true,
                disable_nvimtree_bg = true,
                terminal_colors = true,
            })
            vim.cmd.colorscheme("vscode")
        end,
    },

    { "nvim-tree/nvim-web-devicons", lazy = true },

    {
        "nvim-tree/nvim-tree.lua",
        version = "v1.*",
        dependencies = { "nvim-tree/nvim-web-devicons" },
        keys = {
            { "<C-b>", "<cmd>NvimTreeToggle<CR>", desc = "Explorador" },
            { "<leader>e", "<cmd>NvimTreeFindFileToggle<CR>", desc = "Explorador: archivo actual" },
        },
        opts = {
            disable_netrw = true,
            hijack_netrw = true,
            sync_root_with_cwd = true,
            respect_buf_cwd = true,
            update_focused_file = { enable = true, update_root = false },
            view = { width = 34, side = "left", signcolumn = "yes" },
            renderer = {
                group_empty = true,
                highlight_git = true,
                root_folder_label = false,
                icons = {
                    show = { file = true, folder = true, folder_arrow = true, git = true },
                    glyphs = {
                        folder = { arrow_closed = "", arrow_open = "" },
                        git = {
                            unstaged = "M", staged = "S", unmerged = "U",
                            renamed = "R", untracked = "U", deleted = "D", ignored = "I",
                        },
                    },
                },
            },
            filters = { dotfiles = false },
            git = { enable = true, ignore = false },
        },
    },

    {
        "akinsho/bufferline.nvim",
        version = "*",
        dependencies = { "nvim-tree/nvim-web-devicons" },
        event = "VeryLazy",
        opts = {
            options = {
                mode = "buffers",
                numbers = "none",
                diagnostics = "nvim_lsp",
                separator_style = "thin",
                show_buffer_close_icons = true,
                show_close_icon = false,
                always_show_bufferline = true,
                offsets = {
                    { filetype = "NvimTree", text = "EXPLORADOR", text_align = "center", separator = true },
                },
            },
        },
    },

    {
        "nvim-lualine/lualine.nvim",
        dependencies = { "nvim-tree/nvim-web-devicons" },
        event = "VeryLazy",
        opts = {
            options = {
                theme = "auto",
                globalstatus = true,
                component_separators = { left = "│", right = "│" },
                section_separators = { left = "", right = "" },
                disabled_filetypes = { statusline = { "NvimTree" } },
            },
            sections = {
                lualine_a = { "mode" },
                lualine_b = { "branch", "diff" },
                lualine_c = {
                    {
                        "filename",
                        path = 1,
                        symbols = { modified = " ●", readonly = " ", unnamed = "[Sin nombre]" },
                    },
                },
                lualine_x = { "diagnostics", "encoding", "filetype" },
                lualine_y = { "progress" },
                lualine_z = { "location" },
            },
        },
    },

    {
        "lukas-reineke/indent-blankline.nvim",
        main = "ibl",
        event = { "BufReadPost", "BufNewFile" },
        opts = {
            indent = { char = "│", tab_char = "│" },
            scope = { enabled = true, show_start = false, show_end = false },
        },
    },
}
