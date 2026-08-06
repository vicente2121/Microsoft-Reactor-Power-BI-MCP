-- Data Days DP-600 - Warehouse Gold / Oro
-- Objetivo: crear modelo dimensional desde Silver.
-- Origen: [LK_plata].[dbo].[silver_ventas360_limpia]

DROP TABLE IF EXISTS dbo.gold_fact_ventas;
DROP TABLE IF EXISTS dbo.gold_dim_fecha;
DROP TABLE IF EXISTS dbo.gold_dim_cliente;
DROP TABLE IF EXISTS dbo.gold_dim_producto;
DROP TABLE IF EXISTS dbo.gold_dim_region;
DROP TABLE IF EXISTS dbo.gold_dim_vendedor;

-- DIM FECHA
CREATE TABLE dbo.gold_dim_fecha
AS
SELECT
    YEAR(FechaVenta) * 10000 + MONTH(FechaVenta) * 100 + DAY(FechaVenta) AS FechaKey,
    FechaVenta,
    Anio,
    MesNumero,
    MesNombre,
    DATEPART(QUARTER, FechaVenta) AS Trimestre,
    DAY(FechaVenta) AS Dia
FROM (
    SELECT DISTINCT
        FechaVenta,
        Anio,
        MesNumero,
        MesNombre
    FROM [LK_plata].[dbo].[silver_ventas360_limpia]
    WHERE FechaVenta IS NOT NULL
) f;

-- DIM CLIENTE
CREATE TABLE dbo.gold_dim_cliente
AS
SELECT
    ROW_NUMBER() OVER (ORDER BY ClienteID) AS ClienteKey,
    ClienteID,
    ClienteNombre,
    SegmentoCliente,
    IndustriaCliente
FROM (
    SELECT DISTINCT
        ClienteID,
        ClienteNombre,
        SegmentoCliente,
        IndustriaCliente
    FROM [LK_plata].[dbo].[silver_ventas360_limpia]
    WHERE ClienteID IS NOT NULL
) c;

-- DIM PRODUCTO
CREATE TABLE dbo.gold_dim_producto
AS
SELECT
    ROW_NUMBER() OVER (ORDER BY ProductoID) AS ProductoKey,
    ProductoID,
    ProductoNombre,
    CategoriaProducto,
    MarcaProducto
FROM (
    SELECT DISTINCT
        ProductoID,
        ProductoNombre,
        CategoriaProducto,
        MarcaProducto
    FROM [LK_plata].[dbo].[silver_ventas360_limpia]
    WHERE ProductoID IS NOT NULL
) p;

-- DIM REGION
CREATE TABLE dbo.gold_dim_region
AS
SELECT
    ROW_NUMBER() OVER (ORDER BY RegionID) AS RegionKey,
    RegionID,
    RegionNombre,
    Pais,
    ResponsableRegionEmail
FROM (
    SELECT DISTINCT
        RegionID,
        RegionNombre,
        Pais,
        ResponsableRegionEmail
    FROM [LK_plata].[dbo].[silver_ventas360_limpia]
    WHERE RegionID IS NOT NULL
) r;

-- DIM VENDEDOR
CREATE TABLE dbo.gold_dim_vendedor
AS
SELECT
    ROW_NUMBER() OVER (ORDER BY VendedorID) AS VendedorKey,
    VendedorID,
    VendedorNombre
FROM (
    SELECT DISTINCT
        VendedorID,
        VendedorNombre
    FROM [LK_plata].[dbo].[silver_ventas360_limpia]
    WHERE VendedorID IS NOT NULL
) v;

-- FACT VENTAS
CREATE TABLE dbo.gold_fact_ventas
AS
SELECT
    s.VentaID,
    df.FechaKey,
    dc.ClienteKey,
    dp.ProductoKey,
    dr.RegionKey,
    dv.VendedorKey,
    s.CanalVenta,
    s.EstadoPedido,
    s.MetodoPago,
    s.Cantidad,
    s.PrecioUnitario,
    s.CostoUnitario,
    s.DescuentoPct,
    s.ImporteBruto,
    s.ImporteDescuento,
    s.ImporteNeto,
    s.CostoTotal,
    s.Margen,
    s.FechaVenta,
    s.FechaCarga,
    s.FechaProcesoSilver,
    s.HashVentaNegocio
FROM [LK_plata].[dbo].[silver_ventas360_limpia] s
LEFT JOIN dbo.gold_dim_fecha df
    ON s.FechaVenta = df.FechaVenta
LEFT JOIN dbo.gold_dim_cliente dc
    ON s.ClienteID = dc.ClienteID
LEFT JOIN dbo.gold_dim_producto dp
    ON s.ProductoID = dp.ProductoID
LEFT JOIN dbo.gold_dim_region dr
    ON s.RegionID = dr.RegionID
LEFT JOIN dbo.gold_dim_vendedor dv
    ON s.VendedorID = dv.VendedorID
WHERE s.EsDuplicadoNegocio = 0;

-- VALIDACIONES
SELECT COUNT(*) AS FilasFactVentas
FROM dbo.gold_fact_ventas;

SELECT SUM(ImporteNeto) AS VentasTotales
FROM dbo.gold_fact_ventas;

SELECT SUM(Margen) AS MargenTotal
FROM dbo.gold_fact_ventas;

SELECT
    r.RegionNombre,
    SUM(f.ImporteNeto) AS Ventas
FROM dbo.gold_fact_ventas f
INNER JOIN dbo.gold_dim_region r
    ON f.RegionKey = r.RegionKey
GROUP BY r.RegionNombre
ORDER BY Ventas DESC;
