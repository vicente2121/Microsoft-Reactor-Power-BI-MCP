# Convenciones del equipo de datos

## Nomenclatura
- Medidas en español natural, con espacios: "Ventas Netas", "Beneficio Total"
  (no snake_case ni prefijos de tabla)
- Todas las medidas viven en la tabla oculta "_Medidas", nunca dentro de
  Ventas, Presupuesto ni ninguna dimensión
- Columnas técnicas (IdProducto, IdCliente, IdTienda...) se dejan ocultas

## Reglas de negocio del modelo
- Ventas incluye filas con Estado = "Devuelta" y Cantidad negativa: por
  defecto, las medidas de "Ventas Netas" y "Beneficio Total" las EXCLUYEN
  salvo que se pida explícitamente lo contrario
- Presupuesto se compara contra Ventas Netas por Tienda y AñoMes, nunca por
  Fecha exacta

## Estilo DAX
- Usar VAR para cualquier expresión reutilizada más de una vez
- Nada de CALCULATE anidados sin comentario explicativo
- Cada medida lleva una descripción en lenguaje de negocio, no solo técnica

## Flujo de trabajo
- Nunca commitear directo a main: rama `feature/<tarea>`
- Todo cambio del agente se revisa como diff antes de commit