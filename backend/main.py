# Add to main.py

from backend.enhanced_signals import router as enhanced_signals_router

# Include the enhanced signals router
app.include_router(enhanced_signals_router, prefix="/api/signals", tags=["Enhanced Signals"])

# Serve the enhanced signals HTML content
@app.get("/static/enhanced_signals_content.html")
async def get_enhanced_signals_content():
    """Serve the enhanced signals page content"""
    try:
        with open("frontend/static/enhanced_signals_content.html", "r") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Enhanced signals content not found")

# Update existing signals route to include backward compatibility
@app.get("/signals/active")
async def get_active_signals_legacy(current_user: dict = Depends(get_current_user)):
    """Legacy endpoint - redirect to enhanced signals"""
    return RedirectResponse(url="/api/signals/enhanced")
