@echo off
echo ========================================
echo   Testing Restored APIs
echo ========================================
echo.

set BASE_URL=http://localhost:8000

echo [1/6] Testing /network/topology...
curl -s %BASE_URL%/network/topology | python -m json.tool | head -n 20
echo.
echo.

echo [2/6] Testing /health/models...
curl -s %BASE_URL%/health/models | python -m json.tool
echo.
echo.

echo [3/6] Testing /health/validate...
curl -s -X POST %BASE_URL%/health/validate | python -m json.tool
echo.
echo.

echo [4/6] Testing /simulation/stats...
curl -s %BASE_URL%/simulation/stats | python -m json.tool
echo.
echo.

echo [5/6] Testing /entity/u01/action/monitor...
curl -s -X POST %BASE_URL%/entity/u01/action/monitor | python -m json.tool
echo.
echo.

echo [6/6] Testing /logs/export...
curl -s "%BASE_URL%/logs/export?format=json&limit=5" | python -m json.tool | head -n 30
echo.
echo.

echo ========================================
echo   All restored APIs tested!
echo ========================================
pause
