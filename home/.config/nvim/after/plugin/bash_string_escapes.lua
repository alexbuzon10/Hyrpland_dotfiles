local namespace = vim.api.nvim_create_namespace("bash_string_escapes")

local string_nodes = {
    ansi_c_string = true,
    heredoc_body = true,
    raw_string = true,
    string_content = true,
}

local function set_highlight()
    -- Un blanco suave que se adapta al tema: gris claro en VS Code y
    -- gris azulado en OneDark, en vez de usar blanco puro.
    vim.api.nvim_set_hl(0, "BashStringEscape", { link = "Normal" })
end

local function highlight_node(bufnr, node, seen)
    local start_row, start_col, end_row, end_col = node:range()

    for row = start_row, end_row do
        local line = (vim.api.nvim_buf_get_lines(bufnr, row, row + 1, false)[1] or "")
        local from = row == start_row and start_col or 0
        local to = row == end_row and end_col or #line
        local text = line:sub(from + 1, to)
        local ranges = {}

        -- Primero captura códigos ANSI completos para que `\\033[0m` o
        -- `\\e[38;5;214m` se lean como una sola secuencia especial.
        for _, pattern in ipairs({
            [=[\033%[[%d;:?]*[A-Za-z]]=],
            [=[\e%[[%d;:?]*[A-Za-z]]=],
            [=[\x1[bB]%[[%d;:?]*[A-Za-z]]=],
        }) do
            local offset = 1
            while true do
                local first, last = text:find(pattern, offset)
                if not first then
                    break
                end
                table.insert(ranges, { first, last })
                offset = last + 1
            end
        end

        -- Conserva el comportamiento general para `\\n`, `\\t`, `\\c`, etc.
        local offset = 1
        while true do
            local first, last = text:find([=[\.]=], offset)
            if not first then
                break
            end
            local covered = false
            for _, range in ipairs(ranges) do
                if first >= range[1] and first <= range[2] then
                    covered = true
                    break
                end
            end
            if not covered then
                table.insert(ranges, { first, last })
            end
            offset = last + 1
        end

        for _, range in ipairs(ranges) do
            local col = from + range[1] - 1
            local key = row .. ":" .. col
            if not seen[key] then
                vim.api.nvim_buf_add_highlight(bufnr, namespace, "BashStringEscape", row, col, from + range[2])
                seen[key] = true
            end
        end
    end
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

    local seen = {}
    local function visit(node)
        if string_nodes[node:type()] then
            highlight_node(bufnr, node, seen)
        end
        for child in node:iter_children() do
            visit(child)
        end
    end

    for _, tree in ipairs(parser:parse()) do
        visit(tree:root())
    end
end

set_highlight()

local group = vim.api.nvim_create_augroup("BashStringEscapes", { clear = true })
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
        set_highlight()
        refresh(vim.api.nvim_get_current_buf())
    end,
})
