return {
    {
        "olimorris/onedarkpro.nvim",
        lazy = false,
        opts = {
            highlights = {
                -- Número de la línea activa: blanco propio de cada variante OneDarkPro.
                CursorLineNr = { fg = "${white}" },
            },
            options = {
                transparency = true,
                terminal_colors = true,
            },
        },
    },
}
