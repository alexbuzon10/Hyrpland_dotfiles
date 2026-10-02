local group = vim.api.nvim_create_augroup("CodeLikeNvim", { clear = true })

vim.api.nvim_create_autocmd("BufReadPost", {
    group = group,
    callback = function(args)
        local mark = vim.api.nvim_buf_get_mark(args.buf, '"')
        local lines = vim.api.nvim_buf_line_count(args.buf)
        if mark[1] > 0 and mark[1] <= lines then
            pcall(vim.api.nvim_win_set_cursor, 0, mark)
        end
    end,
})

vim.api.nvim_create_autocmd("TextYankPost", {
    group = group,
    callback = function()
        vim.highlight.on_yank({ higroup = "IncSearch", timeout = 120 })
    end,
})

vim.api.nvim_create_autocmd("FileType", {
    group = group,
    pattern = { "help", "qf", "checkhealth", "lspinfo", "man" },
    callback = function(event)
        vim.keymap.set("n", "q", "<cmd>close<CR>", {
            buffer = event.buf,
            silent = true,
        })
    end,
})
