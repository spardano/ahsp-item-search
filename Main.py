
"""API pencarian AHSP.
 
Jalankan:   uvicorn main:app --reload
Dokumentasi interaktif: http://127.0.0.1:8000/docs
"""
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel
