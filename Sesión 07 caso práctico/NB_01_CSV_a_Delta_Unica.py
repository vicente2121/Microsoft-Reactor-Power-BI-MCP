# Databricks/Fabric notebook source
# Data Days DP-600 - Caso final
# Objetivo: leer un CSV subido manualmente al Lakehouse y guardarlo como una tabla Delta unica.

from pyspark.sql.functions import col, trim, to_date


# 1. Ruta del archivo en el Lakehouse default del notebook.
# En Fabric, adjunta LH_Ventas360_Bronze como Lakehouse default.
source_path = "Files/landing/ventas360_sabana_unica.csv"
target_table = "ventas360_delta_unica"


# 2. Leer el CSV como DataFrame Spark.
df_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("sep", ",")
    .option("encoding", "UTF-8")
    .option("inferSchema", "true")
    .load(source_path)
)

display(df_raw.limit(10))


# 3. Aplicar tipado minimo para que la tabla Delta quede usable.
df_delta = (
    df_raw
    .withColumn("VentaID", trim(col("VentaID")))
    .withColumn("FechaVenta", to_date(col("FechaVenta"), "yyyy-MM-dd"))
    .withColumn("ClienteID", trim(col("ClienteID")))
    .withColumn("ClienteNombre", trim(col("ClienteNombre")))
    .withColumn("ProductoID", trim(col("ProductoID")))
    .withColumn("ProductoNombre", trim(col("ProductoNombre")))
    .withColumn("RegionID", trim(col("RegionID")))
    .withColumn("RegionNombre", trim(col("RegionNombre")))
    .withColumn("VendedorID", trim(col("VendedorID")))
    .withColumn("VendedorNombre", trim(col("VendedorNombre")))
    .withColumn("Cantidad", col("Cantidad").cast("int"))
    .withColumn("PrecioUnitario", col("PrecioUnitario").cast("decimal(18,2)"))
    .withColumn("CostoUnitario", col("CostoUnitario").cast("decimal(18,2)"))
    .withColumn("DescuentoPct", col("DescuentoPct").cast("decimal(10,4)"))
    .withColumn("ImporteBruto", col("ImporteBruto").cast("decimal(18,2)"))
    .withColumn("ImporteDescuento", col("ImporteDescuento").cast("decimal(18,2)"))
    .withColumn("ImporteNeto", col("ImporteNeto").cast("decimal(18,2)"))
    .withColumn("CostoTotal", col("CostoTotal").cast("decimal(18,2)"))
    .withColumn("Margen", col("Margen").cast("decimal(18,2)"))
    .withColumn("FechaCarga", to_date(col("FechaCarga"), "yyyy-MM-dd"))
)

display(df_delta.limit(10))


# 4. Escribir como tabla Delta unica en el Lakehouse.
(
    df_delta.write
    .mode("overwrite")
    .format("delta")
    .option("overwriteSchema", "true")
    .saveAsTable(target_table)
)


# 5. Validar que la tabla Delta quedo disponible.
df_check = spark.read.table(target_table)

print(f"Tabla creada: {target_table}")
print(f"Filas cargadas: {df_check.count()}")

display(df_check.limit(10))


# 6. Perfilado inicial para explicar en vivo.
display(df_check.groupBy("RegionNombre").count())
display(df_check.groupBy("EstadoPedido").count())

duplicados = (
    df_check
    .groupBy("VentaID")
    .count()
    .where(col("count") > 1)
)

display(duplicados)
