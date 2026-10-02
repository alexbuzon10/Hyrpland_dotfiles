local namespace = vim.api.nvim_create_namespace("shebang_as_comment")

local function refresh(bufnr)
    if not vim.api.nvim_buf_is_valid(bufnr) then
        return
    end

    vim.api.nvim_buf_clear_namespace(bufnr, namespace, 0, 1)

    local first_line = vim.api.nvim_buf_get_lines(bufnr, 0, 1, false)[1]
    if first_line and first_line:match("^#!") then
        vim.api.nvim_buf_set_extmark(bufnr, namespace, 0, 0, {
            end_col = #first_line,
            hl_group = "Comment",
            priority = 140,
        })
    end
end

local group = vim.api.nvim_create_augroup("ShebangAsComment", { clear = true })

vim.api.nvim_create_autocmd({ "BufEnter", "BufWinEnter", "TextChanged", "TextChangedI" }, {
    group = group,
    pattern = "*",
    callback = function(args)
        refresh(args.buf)
    end,
})

vim.api.nvim_create_autocmd("ColorScheme", {
    group = group,
    callback = function()
        refresh(vim.api.nvim_get_current_buf())
    end,
})
