@echo off
echo ========================================
echo   EquiMind Backend Quick Test (curl)
echo ========================================
echo.

set BASE_URL=http://localhost:8000

echo [1/7] Testing /status endpoint...
curl -s %BASE_URL%/status | python -m json.tool
echo.
echo.

echo [2/7] Testing /entities endpoint...
curl -s %BASE_URL%/entities | python -m json.tool 
echo.
echo.

echo [3/7] Testing /events endpoint...
curl -s "%BASE_URL%/events?limit=5" | python -m json.tool
echo.
echo.

echo [4/7] Testing /incidents endpoint...
curl -s %BASE_URL%/incidents | python -m json.tool
echo.
echo.

echo [5/7] Testing /predict endpoint...
curl -s -X POST %BASE_URL%/predict ^
  -H "Content-Type: application/json" ^
  -d "{\"proto\":\"tcp\",\"service\":\"http\",\"state\":\"CON\",\"attack_cat\":\"Normal\",\"sbytes\":1000,\"dbytes\":2000,\"stcpb\":0,\"dtcpb\":0,\"response_body_len\":500,\"sloss\":0,\"dloss\":0,\"spkts\":10,\"dpkts\":8,\"swin\":8192,\"dwin\":8192,\"dmean\":1500,\"ct_src_dport_ltm\":1,\"ct_dst_sport_ltm\":1,\"trans_depth\":1,\"ct_ftp_cmd\":0,\"ct_flw_http_mthd\":1,\"is_ftp_login\":0,\"is_sm_ips_ports\":0,\"dur\":10.5,\"rate\":100,\"sload\":1000,\"dload\":2000,\"sinpkt\":100,\"dinpkt\":125,\"sjit\":0.1,\"djit\":0.1,\"tcprtt\":50,\"synack\":10,\"ackdat\":5}" | python -m json.tool
echo.
echo.

echo [6/7] Testing /metrics endpoint...
curl -s %BASE_URL%/metrics | findstr "equimind_events_total equimind_risk_score"
echo.
echo.

echo [7/7] Testing invalid entity ID...
curl -s %BASE_URL%/entity/invalid_id | python -m json.tool
echo.
echo.

echo ========================================
echo   All tests completed!
echo ========================================
pause
