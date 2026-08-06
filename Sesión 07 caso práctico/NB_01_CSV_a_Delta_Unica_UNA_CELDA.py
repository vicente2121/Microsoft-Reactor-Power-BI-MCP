# Data Days DP-600 - Notebook en una sola celda
# Objetivo: leer el CSV subido manualmente al Lakehouse y crear una tabla Delta unica.

from pyspark.sql.functions import col, trim, to_date

source_path = "Files/landing/ventas360_sabana_unica.csv"
target_table = "ventas360_delta_unica"

df_raw = (
    spark.read
    .format("csv")
    .option("header", "true")
    .option("sep", ",")
    .option("encoding", "UTF-8")
    .option("inferSchema", "true")
    .load(source_path)
)

df_delta = (
    df_raw
    .withColumn("VentaID", trim(col("VentaID")))
    .withColumn("FechaVenta", to_date(col("FechaVenta"), "yyyy-MM-dd"))
    .withColumn("ClienteID", trim(col("ClienteID")))
    .withColumn("ClienteNombre", trim(col("ClienteNombre")))
    .withColumn("SegmentoCliente", trim(col("SegmentoCliente")))
    .withColumn("IndustriaCliente", trim(col("IndustriaCliente")))
    .withColumn("ProductoID", trim(col("ProductoID")))
    .withColumn("ProductoNombre", trim(col("ProductoNombre")))
    .withColumn("CategoriaProducto", trim(col("CategoriaProducto")))
    .withColumn("MarcaProducto", trim(col("MarcaProducto")))
    .withColumn("RegionID", trim(col("RegionID")))
    .withColumn("RegionNombre", trim(col("RegionNombre")))
    .withColumn("Pais", trim(col("Pais")))
    .withColumn("ResponsableRegionEmail", trim(col("ResponsableRegionEmail")))
    .withColumn("VendedorID", trim(col("VendedorID")))
    .withColumn("VendedorNombre", trim(col("VendedorNombre")))
    .withColumn("CanalVenta", trim(col("CanalVenta")))
    .withColumn("EstadoPedido", trim(col("EstadoPedido")))
    .withColumn("MetodoPago", trim(col("MetodoPago")))
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

(
    df_delta.write
    .mode("overwrite")
    .format("delta")
    .option("overwriteSchema", "true")
    .saveAsTable(target_table)
)

df_check = spark.read.table(target_table)

print(f"Tabla Delta creada: {target_table}")
print(f"Filas cargadas: {df_check.count()}")
print(f"Columnas: {len(df_check.columns)}")

display(df_check.limit(10))
display(df_check.groupBy("RegionNombre").count())
display(df_check.groupBy("EstadoPedido").count())
display(
    df_check
    .groupBy("VentaID")
    .count()
    .where(col("count") > 1)
)
