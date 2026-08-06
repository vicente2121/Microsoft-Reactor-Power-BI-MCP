# Data Days DP-600 - Notebook Silver Medallion
# Objetivo: tomar la tabla Delta de Bronze y crear una unica tabla Silver limpia.
# Las dimensiones y la fact final se crean despues en Gold/Oro.

from pyspark.sql import Window
from pyspark.sql.functions import (
    col,
    concat_ws,
    current_timestamp,
    initcap,
    lower,
    row_number,
    sha2,
    to_date,
    trim,
    upper,
    when,
)


# ORIGEN BRONZE
source_path = "abfss://Sesion_07Charlas@onelake.dfs.fabric.microsoft.com/LK_bronce.Lakehouse/Tables/dbo/ventas360_delta_unica"

# DESTINO SILVER EN LK_PLATA
target_schema = "dbo"
silver_table = f"{target_schema}.silver_ventas360_limpia"

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {target_schema}")


# 1. Leer tabla Delta Bronze desde OneLake.
df = spark.read.format("delta").load(source_path)


# 2. Limpieza, tipado y normalizacion Silver.
df_silver = (
    df
    .withColumn("VentaID", trim(col("VentaID")))
    .withColumn("FechaVenta", to_date(col("FechaVenta")))
    .withColumn("Anio", col("Anio").cast("int"))
    .withColumn("MesNumero", col("MesNumero").cast("int"))
    .withColumn("MesNombre", initcap(trim(col("MesNombre"))))
    .withColumn("ClienteID", upper(trim(col("ClienteID"))))
    .withColumn("ClienteNombre", initcap(trim(col("ClienteNombre"))))
    .withColumn(
        "SegmentoCliente",
        when((col("SegmentoCliente").isNull()) | (trim(col("SegmentoCliente")) == ""), "Sin clasificar")
        .otherwise(initcap(trim(col("SegmentoCliente"))))
    )
    .withColumn("IndustriaCliente", initcap(trim(col("IndustriaCliente"))))
    .withColumn("ProductoID", upper(trim(col("ProductoID"))))
    .withColumn("ProductoNombre", trim(col("ProductoNombre")))
    .withColumn("CategoriaProducto", initcap(trim(col("CategoriaProducto"))))
    .withColumn("MarcaProducto", trim(col("MarcaProducto")))
    .withColumn("RegionID", upper(trim(col("RegionID"))))
    .withColumn(
        "RegionNombre",
        when(upper(trim(col("RegionNombre"))) == "LATAM", "Latam")
        .otherwise(initcap(trim(col("RegionNombre"))))
    )
    .withColumn("Pais", initcap(trim(col("Pais"))))
    .withColumn("ResponsableRegionEmail", lower(trim(col("ResponsableRegionEmail"))))
    .withColumn("VendedorID", upper(trim(col("VendedorID"))))
    .withColumn("VendedorNombre", initcap(trim(col("VendedorNombre"))))
    .withColumn("CanalVenta", initcap(trim(col("CanalVenta"))))
    .withColumn("EstadoPedido", initcap(trim(col("EstadoPedido"))))
    .withColumn("MetodoPago", initcap(trim(col("MetodoPago"))))
    .withColumn("Cantidad", col("Cantidad").cast("int"))
    .withColumn("PrecioUnitario", col("PrecioUnitario").cast("decimal(18,2)"))
    .withColumn("CostoUnitario", col("CostoUnitario").cast("decimal(18,2)"))
    .withColumn("DescuentoPct", col("DescuentoPct").cast("decimal(10,4)"))
    .withColumn("ImporteBruto", col("ImporteBruto").cast("decimal(18,2)"))
    .withColumn("ImporteDescuento", col("ImporteDescuento").cast("decimal(18,2)"))
    .withColumn("ImporteNeto", col("ImporteNeto").cast("decimal(18,2)"))
    .withColumn("CostoTotal", col("CostoTotal").cast("decimal(18,2)"))
    .withColumn("Margen", col("Margen").cast("decimal(18,2)"))
    .withColumn("FechaCarga", to_date(col("FechaCarga")))
    .withColumn("FechaProcesoSilver", current_timestamp())
)


# 3. Detectar posibles duplicados de negocio sin eliminarlos.
business_key_cols = [
    "FechaVenta",
    "ClienteID",
    "ProductoID",
    "RegionID",
    "VendedorID",
    "CanalVenta",
    "EstadoPedido",
    "Cantidad",
    "ImporteNeto",
    "Margen",
]

df_silver = df_silver.withColumn(
    "HashVentaNegocio",
    sha2(concat_ws("||", *[col(c).cast("string") for c in business_key_cols]), 256)
)

w_dup = Window.partitionBy("HashVentaNegocio").orderBy(col("VentaID"))

df_silver = (
    df_silver
    .withColumn("NumeroDuplicadoNegocio", row_number().over(w_dup))
    .withColumn("EsDuplicadoNegocio", col("NumeroDuplicadoNegocio") > 1)
)


# 4. Guardar tabla Silver limpia.
(
    df_silver.write
    .mode("overwrite")
    .format("delta")
    .option("overwriteSchema", "true")
    .saveAsTable(silver_table)
)


# 5. Validaciones.
df_check = spark.read.table(silver_table)

print(f"Tabla Silver creada: {silver_table}")
print(f"Filas cargadas: {df_check.count()}")
print(f"Columnas cargadas: {len(df_check.columns)}")

display(df_check.limit(10))

print("Conteo por region:")
display(df_check.groupBy("RegionNombre").count())

print("Conteo por estado:")
display(df_check.groupBy("EstadoPedido").count())

print("Posibles duplicados de negocio:")
display(
    df_check
    .where(col("EsDuplicadoNegocio") == True)
    .select("VentaID", "FechaVenta", "ClienteID", "ProductoID", "RegionID", "ImporteNeto", "Margen")
)
