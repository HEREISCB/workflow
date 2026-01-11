"""
AI Workflow Builder - FastAPI Application
"""
import os
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import router
from app.engine.executor import init_executor


# Load environment variables
load_dotenv()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan - initialize resources"""
    # Initialize workflow executor with API key
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        init_executor(api_key)
        print("✅ Workflow executor initialized")
    else:
        print("⚠️  OPENAI_API_KEY not set - LLM nodes will fail")
    
    yield
    
    # Cleanup on shutdown
    print("👋 Shutting down workflow builder")


app = FastAPI(
    title="AI Workflow Builder",
    description="Context-driven AI agent workflow builder using LangGraph",
    version="1.0.0",
    lifespan=lifespan
)

# CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(router, prefix="/api")


@app.get("/")
async def root():
    return {
        "name": "AI Workflow Builder",
        "version": "1.0.0",
        "docs": "/docs"
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}
