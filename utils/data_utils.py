# utils/data_utils.py
import base64
import io
import pandas as pd

def parse_contents(contents, filename):
    """
    Recibe el contenido codificado y el nombre del archivo,
    devuelve un DataFrame de pandas.
    """
    if contents is None or filename is None:
        return None

    content_type, content_string = contents.split(",")

    # Decodificar el contenido base64
    decoded = base64.b64decode(content_string)

    try:
        # Según la extensión del archivo, usamos read_csv o read_excel
        if filename.lower().endswith(".csv"):
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif filename.lower().endswith((".xls", ".xlsx")):
            df = pd.read_excel(io.BytesIO(decoded))
        else:
            return None
    except Exception as e:
        print("Error al leer el archivo:", e)
        return None

    return df


def df_from_store(data_json):
    """Convierte el JSON guardado en Data a un DataFrame pandas."""
    if data_json is None:
        return None
    return pd.read_json(data_json, orient="split")
