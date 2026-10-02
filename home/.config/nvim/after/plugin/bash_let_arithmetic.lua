local namespace = vim.api.nvim_create_namespace("bash_let_arithmetic")

local function highlight_range(bufnr, group, row, start_col, end_col)
    vim.api.nvim_buf_set_extmark(bufnr, namespace, row, start_col, {
        end_col = end_col,
        hl_group = group,
        priority = 130,
    })
end

local function refresh(bufnr)
    if not vim.api.nvim_buf_is_valid(bufnr) or vim.bo[bufnr].filetype ~= "sh" then
        return
    end

    vim.api.nvim_buf_clear_namespace(bufnr, namespace, 0, -1)

    local ok, parser = pcall(vim.treesitter.get_parser, bufnr, "bash")
    if not ok or not parser then
        return
    end

    local function visit(node)
        if node:type() == "command" then
            local name = node:field("name")[1]
            if name and vim.treesitter.get_node_text(name, bufnr) == "let" then
                for child in node:iter_children() do
                    if child:type() == "word" then
                        local text = vim.treesitter.get_node_text(child, bufnr)
                        local variable, operator, value = text:match("^([%a_][%w_]*)([%+%-%*/%%]?=)(.*)$")

                        if variable and value ~= "" then
                            local row, col = child:range()
                            local operator_start = col + #variable
                            local value_start = operator_start + #operator

                            highlight_range(bufnr, "@operator.bash", row, operator_start, value_start)

                            -- Los literales numéricos usan exactamente el mismo grupo
                            -- que el resto de números del tema activo.
                            if value:match("^%d+$") then
                                highlight_range(bufnr, "@number.bash", row, value_start, value_start + #value)
                            end
                        end
                    end
                end
            end
        end

        for child in node:iter_children() do
            visit(child)
        end
    end

    for _, tree in ipairs(parser:parse()) do
        visit(tree:root())
    end
end

local group = vim.api.nvim_create_augroup("BashLetArithmeticHighlights", { clear = true })
vim.api.nvim_create_autocmd({ "BufEnter", "FileType", "TextChanged", "TextChangedI" }, {
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
