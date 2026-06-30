# src/api/main.py
from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse
import pandas as pd
from src.access.rbac import get_current_user, require_permission
from src.pii.anonymizer import MedVietAnonymizer

app = FastAPI(title="MedViet Data API", version="1.0.0")
anonymizer = MedVietAnonymizer()

# --- ENDPOINT 1 ---
@app.get("/api/patients/raw")
@require_permission(resource="patient_data", action="read")
async def get_raw_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về raw patient data (chỉ admin được phép).
    Load từ data/raw/patients_raw.csv
    Trả về 10 records đầu tiên dưới dạng JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv", dtype={"cccd": str, "so_dien_thoai": str})
        records = df.head(10).to_dict(orient="records")
        return JSONResponse(content=records)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 2 ---
@app.get("/api/patients/anonymized")
@require_permission(resource="training_data", action="read")
async def get_anonymized_patients(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về anonymized data (ml_engineer và admin được phép).
    Load raw data → anonymize → trả về JSON.
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv", dtype={"cccd": str, "so_dien_thoai": str})
        df_anon = anonymizer.anonymize_dataframe(df)
        return JSONResponse(content=df_anon.to_dict(orient="records"))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 3 ---
@app.get("/api/metrics/aggregated")
@require_permission(resource="aggregated_metrics", action="read")
async def get_aggregated_metrics(
    current_user: dict = Depends(get_current_user)
):
    """
    Trả về aggregated metrics (data_analyst, ml_engineer, admin).
    Ví dụ: số bệnh nhân theo từng loại bệnh (không có PII).
    """
    try:
        df = pd.read_csv("data/raw/patients_raw.csv", dtype={"cccd": str, "so_dien_thoai": str})
        counts = df["benh"].value_counts().to_dict()
        return JSONResponse(content={"disease_counts": counts})
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# --- ENDPOINT 4 ---
@app.delete("/api/patients/{patient_id}")
@require_permission(resource="patient_data", action="delete")
async def delete_patient(
    patient_id: str,
    current_user: dict = Depends(get_current_user)
):
    """
    Chỉ admin được xóa. Các role khác nhận 403.
    """
    return {"status": "success", "message": f"Patient {patient_id} deleted."}

@app.get("/health")
async def health():
    return {"status": "ok", "service": "MedViet Data API"}
