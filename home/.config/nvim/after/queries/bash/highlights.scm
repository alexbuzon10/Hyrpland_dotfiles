; extends

; El nombre solo es amarillo cuando forma parte de `$foo` o `${foo}`.
[
  (simple_expansion
    (variable_name) @variable.expansion)
  (expansion
    (variable_name) @variable.expansion)
] (#set! priority 110)

; Los delimitadores de una sustitución de comando tienen un color propio.
; La captura específica evita cambiar también `$foo`, `${foo}` o `$((...))`.
(command_substitution
  "$(" @punctuation.command-substitution
  ")" @punctuation.command-substitution)
  (#set! priority 120)

; Opciones de comandos (`-r`, `-algo`, `--color=auto`, etc.).
; Al limitarlo a argumentos `word` no afecta a números negativos ni asignaciones.
((command
  argument: (word) @argument.option)
  (#match? @argument.option "^--?[^[:space:]]"))
  (#set! priority 125)
