import argparse
import json
import socket
from datetime import datetime

import requests

# =====================================================
# OBTENER IP LOCAL
# =====================================================

def obtener_ip_local():

    try:

        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        s.connect(("8.8.8.8", 80))

        ip = s.getsockname()[0]

        s.close()

        return ip

    except Exception:

        return "127.0.0.1"

# =====================================================
# CONFIG FRONTEND
# =====================================================

FRONT_IP = obtener_ip_local()

FRONT_PORT = 8000

FRONT_URL = f"http://{FRONT_IP}:{FRONT_PORT}/task"

FRONT_LOCAL_URL = f"http://127.0.0.1:{FRONT_PORT}/task"

# =====================================================
# PARSER
# =====================================================

parser = argparse.ArgumentParser()

parser.add_argument(
    "--Peticion",
    required=True,
    help="Archivo JSON de petición"
)

args = parser.parse_args()

# =====================================================
# LEER JSON
# =====================================================

try:

    with open(args.Peticion, "r") as file:

        data = json.load(file)

except Exception as e:

    print("\nERROR LEYENDO JSON")

    print(e)

    exit()

# =====================================================
# GENERAR METADATA
# =====================================================

data["FrontendURL"] = FRONT_URL

data["FrontendIP"] = FRONT_IP

data["FrontendPort"] = FRONT_PORT

data["timestamp"] = datetime.now().strftime("%H:%M:%S")

# =====================================================
# MOSTRAR PETICIÓN
# =====================================================

print("\n==============================")
print("PETICIÓN GENERADA")
print("==============================")

print(json.dumps(data, indent=4))

# =====================================================
# ENVIAR A FASTAPI
# =====================================================

try:

    response = requests.post(
        FRONT_LOCAL_URL,
        json=data
    )

    print("\n==============================")
    print("RESPUESTA DE FASTAPI")
    print("==============================")

    print(json.dumps(response.json(), indent=4))

except Exception as e:

    print("\nERROR CONECTANDO A FASTAPI")

    print(e)