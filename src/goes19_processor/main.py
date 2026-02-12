# src/goes19_processor/main.py

import click
from .download.aws_noaa import download_goes_files   # Asegúrate de que el import esté correcto


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """CLI para procesar datos del satélite GOES-19"""
    pass


# ← Aquí va el comando viejo si lo querés mantener como backup (opcional)
# @cli.command()
# ... (el download viejo sin las opciones nuevas)


# ← Este es el nuevo comando completo que reemplaza al viejo
@cli.command()
@click.option("--product", default="ABI-L1b-RadF", show_default=True,
              help="Producto (ej: ABI-L1b-RadF, ABI-L2-LSTF, GLM-L2-LCFA)")
@click.option("--year", required=True, help="Año (ej: 2026)")
@click.option("--day", required=True, help="Día del año (001-366)")
@click.option("--hour", required=True, help="Hora UTC (00-23)")
@click.option("--band", default=None, help="Banda para ABI (01-16)")
@click.option("--output-dir", default="data/raw", show_default=True,
              help="Directorio de salida")
@click.option("--all", is_flag=True, help="Descargar TODOS los archivos en el prefijo/hora")
@click.option("--file-name", default=None, help="Descargar archivo específico por nombre exacto")
@click.option("--start-time", default=None, help="Inicio del rango (YYYY-MM-DD_HH:MM)")
@click.option("--end-time", default=None, help="Fin del rango (YYYY-MM-DD_HH:MM)")
@click.option("--overwrite", is_flag=True, help="Forzar descarga aunque el archivo exista")
def download(product, year, day, hour, band, output_dir, all, file_name, start_time, end_time, overwrite):
    """Descarga archivos de GOES-19 desde AWS NOAA con opciones flexibles"""
    downloaded = download_goes_files(
        product=product,
        year=year,
        day_of_year=day,
        hour=hour,
        band=band,
        output_dir=output_dir,
        all_files=all,
        file_name=file_name,
        start_time=start_time,
        end_time=end_time,
        overwrite=overwrite
    )

    if downloaded:
        for path in downloaded:
            click.echo(f"Descargado: {path}")
    else:
        click.echo("No se descargaron archivos.")


if __name__ == "__main__":
    cli()
