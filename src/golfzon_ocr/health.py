"""
Health check endpoints for monitoring and deployment.
"""
import streamlit as st
from sqlalchemy import text
from golfzon_ocr.db import get_engine
from golfzon_ocr.config import config


def health_check() -> dict:
    """
    Perform basic health check.
    
    Returns:
        dict: Health status with 'status' and 'checks' keys
    """
    checks = {
        "application": "healthy",
        "database": "unknown"
    }
    
    # Check database connection
    try:
        engine = get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        checks["database"] = "healthy"
    except Exception as e:
        checks["database"] = f"unhealthy: {str(e)}"
    
    # Determine overall status
    overall_status = "healthy" if all(
        check == "healthy" for check in checks.values()
    ) else "unhealthy"
    
    return {
        "status": overall_status,
        "environment": config.ENVIRONMENT,
        "checks": checks
    }


def render_health_page():
    """Render health check page for Streamlit."""
    st.set_page_config(page_title="Health Check", page_icon="🏥")
    
    st.title("🏥 Health Check")
    
    health = health_check()
    
    # Display status
    status_color = "🟢" if health["status"] == "healthy" else "🔴"
    st.markdown(f"## {status_color} Status: {health['status'].upper()}")
    
    st.markdown(f"**Environment:** {health['environment']}")
    
    st.markdown("### Checks")
    for check_name, check_status in health["checks"].items():
        check_icon = "✅" if check_status == "healthy" else "❌"
        st.markdown(f"- **{check_name}:** {check_icon} {check_status}")
    
    # Return JSON for API endpoints
    if st.checkbox("Show JSON"):
        st.json(health)

