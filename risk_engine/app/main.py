# app/main.py

from fastapi import FastAPI, File, UploadFile
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.inference import preprocess, predict_mlp, explain_mlp
from app.risk_engine import compute_risk
from app.preprocess import preprocess_user_input
import asyncio
import os
from pathlib import Path

app = FastAPI(title="Zero Trust Risk Engine")

# Add CORS middleware to allow requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def root():
    """Serve the frontend HTML file."""
    frontend_path = Path(__file__).parent / "frontend.html"
    if frontend_path.exists():
        return FileResponse(frontend_path, media_type="text/html")
    return {"message": "Zero Trust Risk Engine API - Use POST /predict with flow data"}


@app.post("/predict")
async def predict(flow: dict):
    """
    Predict risk score for a network flow.
    
    Accepts either:
    1. Simplified user input (primary features) - automatically derives all features
    2. Full feature vector (all 45+ features) - uses directly
    
    Args:
        flow: Dictionary with network flow information
              - If simplified: protocol, service, state, attack_cat, src_bytes, dst_bytes, 
                src_packets, dst_packets, duration, src_loss, dst_loss
              - If full: all model features
    
    Returns:
        JSON with mlp_score, risk_score, and risk_level
    """
    
    # Check if this is simplified input (missing full features)
    required_full_features = {
        "proto", "service", "state", "attack_cat",
        "sbytes", "dbytes", "stcpb", "dtcpb", "response_body_len",
        "sloss", "dloss", "spkts", "dpkts", "swin", "dwin", "dmean",
        "ct_src_dport_ltm", "ct_dst_sport_ltm", "trans_depth",
        "ct_ftp_cmd", "ct_flw_http_mthd", "is_ftp_login", "is_sm_ips_ports",
        "dur", "rate", "sload", "dload", "sinpkt", "dinpkt",
        "sjit", "djit", "tcprtt", "synack", "ackdat"
    }
    
    # If simplified input detected, derive features
    if not all(f in flow for f in required_full_features):
        # Use preprocessing layer for simplified input
        flow = preprocess_user_input(flow)
    
    # Preprocess the (now complete) feature set
    x = preprocess(flow)

    # Run model prediction concurrently
    mlp_task = asyncio.to_thread(predict_mlp, x)

    mlp_score = await asyncio.gather(mlp_task)

    risk_score, risk_level = compute_risk(mlp_score)

    return {
        "mlp_score": float(mlp_score[0]),
        "risk_score": [risk_score, risk_level],
        "derived_features": {k: v for k, v in flow.items() if k not in ["proto", "service", "state", "attack_cat"]}
    }


@app.post("/explain")
async def explain(flow: dict):
    """
    Explain a prediction using SHAP values.
    
    This endpoint provides explainable AI insights by computing
    SHAP (SHapley Additive exPlanations) values for the model's prediction.
    """
    x = preprocess(flow)
    
    # Run SHAP explanation (this can be slow, so use threading)
    explanation = await asyncio.to_thread(explain_mlp, x)
    
    return explanation