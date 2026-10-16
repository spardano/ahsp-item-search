
"""API pencarian AHSP.
 
Jalankan:   uvicorn main:app --reload
Dokumentasi interaktif: http://127.0.0.1:8000/docs
"""
import os
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, Query
from pydantic import BaseModel

from Search import SearchUnit

_mesin: Optional[SearchUnit] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    #index dibangun sekali saat server menyala, bukan di tiap request
    global _mesin
    _mesin = SearchUnit(os.getenv("AHSP_DATA_DIR", "."))
    yield
    _mesin = None

def get_mesin()-> SearchUnit:
    if _mesin is None:
        raise HTTPException(status_code=503, detail="Pencarian belum siap")
    return _mesin

app = FastAPI(
    title="AHSP Search API",
    version="0.1.0",
    description="Mencari item AHSP Bidang Cipta Karya (SE Dirjen Bina Konstruksi 182/SE/Dk/2025) "
                "dari teks bebas, dan mengambil komponen koefisien untuk perhitungan harga satuan.",
    lifespan=lifespan
)

#response
class HasilCari(BaseModel):
    id: str
    uraian: str
    satuan: str
    divisi: str
    kategori: str
    tipe: str
    skor: float

class ResponseCari(BaseModel):
    query_ternormalisasi: str
    ada_hasil_yakin: bool
    hasil: List[HasilCari]

class Komponen(BaseModel):
    urutan: int
    jenis: str
    kode_komponen: str
    nama_komponen: str
    satuan: str
    koefisien: float
    perlu_cek: bool

class DetailItem(BaseModel):
    id: str
    uraian: str
    satuan: str
    divisi: str
    kategori: str
    subkategori: str
    tipe: str
    sumber: str
    ref_permen: str
    komponen: List[Komponen]


#end-point
@app.get("/health")
def health(mesin: SearchUnit = Depends(get_mesin)):
    return {"status": "ok", "jumlah_item": len(mesin.items)}

@app.get("/search", response_model=ResponseCari)
def search(
    q: str = Query(..., min_length=2, max_length=200, description="Teks pekerjaan, mis. 'plesteran 1:3"),
    k: int = Query(5, ge=1, le=20, description="Jumlah Kandidat"),
    mesin: SearchUnit = Depends(get_mesin),
):
    """Kembalikan k kandidat item AHSP.
 
    `ada_hasil_yakin=false` berarti tidak ada item yang cukup mirip sama sekali.
    `true` BUKAN jaminan kandidat pertama benar: skor tidak bisa membedakan benar dan salah,
    jadi antarmuka sebaiknya selalu membiarkan user memilih dari daftar.
    """
    return mesin.cari(q, k)

@app.get("/items/{item_id:path}", response_model=DetailItem)
def detail_item(item_id: str, mesin: SearchUnit = Depends(get_mesin)):
    """Detail satu item beserta komponen (tenaga kerja, bahan, alat) dan koefisiennya.
 
    Catatan: sebagian ID memuat '#' (mis. '2.2.1.1.5#2', kode ganda di dokumen sumber);
    tulis sebagai %23 di URL.
    """
    hasil = mesin.detail(item_id)
    if hasil is None:
        raise HTTPException(status_code=404, detail=f"Item '{item_id}' tidak ditemukan")
    return hasil
