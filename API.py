from fastapi import FastAPI
from datetime import datetime, timedelta
import asyncio
import json
import os
import re

import mysql.connector
from dotenv import load_dotenv

load_dotenv()

# =====================================================
# CONFIGURACIÓN
# =====================================================

DELAY_SECONDS = 10
RUNNING_SIMULATION_SECONDS = 10

all_jobs = {}

# =====================================================
# FASTAPI
# =====================================================

app = FastAPI(
    title="Frontend API"
)

# =====================================================
# CONEXIÓN A MYSQL
# =====================================================

def conectar_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

# =====================================================
# EJECUTAR QUERY DESDE JSON
# =====================================================

def ejecutar_query_desde_json(data):
    query = data.get("Query")

    if not query:
        return {"error": "No existe Query en el JSON"}

    try:
        connection = conectar_db()
        cursor = connection.cursor(dictionary=True)

        print("\n==============================")
        print("EJECUTANDO QUERY")
        print("==============================")
        print(query)

        cursor.execute(query)
        resultado = cursor.fetchall()

        cursor.close()
        connection.close()

        return resultado

    except Exception as e:
        return {"error": str(e)}

# =====================================================
# CALCULAR HORA APROXIMADA DE FINALIZACIÓN
# =====================================================

def calcular_hora_final(timestamp_recibido, walltime):
    if not walltime:
        return timestamp_recibido.strftime("%H:%M:%S")

    numeros = re.findall(r"\d+", str(walltime))

    if not numeros:
        return timestamp_recibido.strftime("%H:%M:%S")

    numero = int(numeros[0])
    walltime_lower = str(walltime).lower()

    if "hora" in walltime_lower:
        timestamp_final = timestamp_recibido + timedelta(hours=numero)
    elif "min" in walltime_lower:
        timestamp_final = timestamp_recibido + timedelta(minutes=numero)
    elif "seg" in walltime_lower:
        timestamp_final = timestamp_recibido + timedelta(seconds=numero)
    else:
        timestamp_final = timestamp_recibido

    return timestamp_final.strftime("%H:%M:%S")

# =====================================================
# PROCESAR PETICIÓN INDEPENDIENTE
# =====================================================

async def procesar_peticion(job_id):
    data = all_jobs[job_id]

    # =================================================
    # WAITING
    # =================================================

    data["status"] = "WAITING"
    data["queued_at"] = datetime.now().strftime("%H:%M:%S")

    data.setdefault("history", []).append({
        "status": "WAITING",
        "time": data["queued_at"]
    })

    print("\n==============================")
    print("PETICIÓN ENCOLADA / WAITING")
    print("==============================")
    print(f"Job ID: {job_id}")
    print(f"Esperando {DELAY_SECONDS} segundos antes de ejecutar...")

    await asyncio.sleep(DELAY_SECONDS)

    # =================================================
    # RUNNING
    # =================================================

    data["status"] = "RUNNING"
    data["started_at"] = datetime.now().strftime("%H:%M:%S")

    data["history"].append({
        "status": "RUNNING",
        "time": data["started_at"]
    })

    print("\n==============================")
    print("PETICIÓN EN EJECUCIÓN / RUNNING")
    print("==============================")
    print(f"Job ID: {job_id}")

    resultado_query = ejecutar_query_desde_json(data)

    print("\n==============================")
    print("RESULTADO DEL QUERY")
    print("==============================")
    print(json.dumps(resultado_query, indent=4))

    data["resultado"] = resultado_query

    # Simulación para que el estado RUNNING pueda verse en el dashboard
    await asyncio.sleep(RUNNING_SIMULATION_SECONDS)

    # =================================================
    # COMPLETED
    # =================================================

    data["status"] = "COMPLETED"
    data["completed_at"] = datetime.now().strftime("%H:%M:%S")

    data["history"].append({
        "status": "COMPLETED",
        "time": data["completed_at"]
    })

    print("\n==============================")
    print("PETICIÓN COMPLETADA")
    print("==============================")
    print(json.dumps(data, indent=4))

# =====================================================
# HOME
# =====================================================

@app.get("/")
async def home():
    return {
        "status": "Frontend API activo"
    }

# =====================================================
# RECIBIR PETICIÓN
# =====================================================

@app.post("/task")
async def recibir_peticion(data: dict):
    timestamp_recibido = datetime.now()
    timestamp_texto = timestamp_recibido.strftime("%H:%M:%S")

    job_id = f"job_{len(all_jobs) + 1}"

    walltime = data.get("WallTime")
    hora_final = calcular_hora_final(timestamp_recibido, walltime)

    data["job_id"] = job_id
    data["status"] = "QUEUED"
    data["timestamp_recibido"] = timestamp_texto
    data["estimated_finish"] = hora_final

    data["history"] = [
        {
            "status": "QUEUED",
            "time": timestamp_texto
        }
    ]

    all_jobs[job_id] = data

    print("\n==============================")
    print("NUEVA PETICIÓN RECIBIDA / QUEUED")
    print("==============================")
    print(json.dumps(data, indent=4))

    asyncio.create_task(procesar_peticion(job_id))

    return {
        "status": "Petición recibida y encolada",
        "job_id": job_id,
        "timestamp_recibido": timestamp_texto,
        "estimated_finish": hora_final,
        "message": f"La petición se ejecutará después de {DELAY_SECONDS} segundos"
    }

# =====================================================
# DASHBOARD
# =====================================================

@app.get("/dashboard")
async def dashboard():
    jobs = list(all_jobs.values())

    pending_jobs = [
        job for job in jobs
        if job["status"] in ["QUEUED", "WAITING"]
    ]

    running_jobs = [
        job for job in jobs
        if job["status"] == "RUNNING"
    ]

    completed_jobs = [
        job for job in jobs
        if job["status"] == "COMPLETED"
    ]

    dashboard_data = {
        "total_jobs": len(jobs),
        "pending_count": len(pending_jobs),
        "running_count": len(running_jobs),
        "completed_count": len(completed_jobs),
        "pending_jobs": pending_jobs,
        "running_jobs": running_jobs,
        "completed_jobs": completed_jobs
    }

    print("\n==============================")
    print("DASHBOARD GENERADO")
    print("==============================")
    print(json.dumps(dashboard_data, indent=4))

    return dashboard_data