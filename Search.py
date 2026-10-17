"""Mesin pencarian AHSP: TF-IDF (kata + potongan huruf) di atas teks yang sudah dinormalisasi.
 
Tidak bergantung pada FastAPI, jadi bisa diuji dan dipakai dari notebook.
"""
from __future__ import annotations
from pathlib import Path
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from Normalisasi import normalize

BOBOT_KATA = 0.5
SKOR_MIN = 0.25

class SearchUnit:
    def __init__(self, folder_data: str | Path = "."):
        folder = Path(folder_data)
        self.items = pd.read_csv(folder / "ahsp_items.csv", dtype=str).fillna("")
        file_prices = folder / "ahsp_components_with_prices.csv"
        file_comp = folder / "ahsp_components.csv"
        if file_prices.exists():
            df_comp = pd.read_csv(file_prices, dtype=str).fillna("")
            if file_comp.exists():
                df_old = pd.read_csv(file_comp, dtype=str).fillna("")
                if "perlu_cek" in df_old.columns:
                    df_comp = df_comp.merge(
                        df_old[["item_id", "urutan", "perlu_cek"]],
                        on=["item_id", "urutan"],
                        how="left"
                    ).fillna("")
        else:
            df_comp = pd.read_csv(file_comp, dtype=str).fillna("")

        self.komponen = df_comp
        self._index_komponen = {k: g for k, g in self.komponen.groupby("item_id", sort=False)}
        self.index_komponen = self._index_komponen

        #teks yang dicari: uraian + kategori (kategori untuk membedakan item mirip)
        teks = (self.items["uraian"] + " " + self.items["kategori"]).map(normalize)
        self._vec_kata = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r"(?u)\b\w+\b")
        self._vec_char = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5))
        self._X_kata = self._vec_kata.fit_transform(teks)
        self._X_char = self._vec_char.fit_transform(teks)
        self._pos_id = {id_: n for n, id_ in enumerate(self.items["id"])}



    def skor(self, query: str):
        """Skor kemiripan query terhadap SEMUA item, 
        atau None bila query kosong setelah normalisasi."""
        q = normalize(query)
        if not q:
            return None, q
        s_kata = cosine_similarity(self._vec_kata.transform([q]), self._X_kata)[0]
        s_char = cosine_similarity(self._vec_char.transform([q]), self._X_char)[0]
        return BOBOT_KATA * s_kata + (1 - BOBOT_KATA) * s_char, q

    def cari(self, query: str, k: int = 5) -> dict:
        skor, q = self.skor(query)
        if skor is None:
            return {"query_ternormalisasi": q, "ada_hasil_yakin": False, "hasil": []}
        top = skor.argsort()[::-1][:k]
        hasil = []
        for i in top:
            r = self.items.iloc[i]
            hasil.append({
                "id": r["id"], "uraian": r["uraian"], "satuan": r["satuan"],
                "divisi": r["divisi"], "kategori": r["kategori"],
                "subkategori": r["subkategori"], "tipe": r["tipe"],
                "skor": round(float(skor[i]), 3),
            })

        return {"query_ternormalisasi": q, "ada_hasil_yakin": bool(hasil and hasil[0]["skor"] >= SKOR_MIN),
                "hasil": hasil}


    def detail(self, item_id: str) -> dict | None:
        n = self._pos_id.get(item_id)
        if n is None:
            return None
        r = self.items.iloc[n]
        g = self._index_komponen.get(item_id)
        
        komponen = []
        if g is not None:
            satuan_col = "satuan_komponen" if "satuan_komponen" in g.columns else "satuan"
            has_prices = "harga_satuan" in g.columns
            for c in g.itertuples():
                status_pencocokan = getattr(c, "status_pencocokan", "") or None
                perlu_cek_raw = getattr(c, "perlu_cek", "")
                is_perlu_cek = (perlu_cek_raw in ["1", "true", "True", 1, True]) or (status_pencocokan == "Unmatched")

                harga_satuan = None
                jumlah_harga = None
                nama_shs_cocok = None
                if has_prices:
                    nama_shs = getattr(c, "nama_shs_cocok", "")
                    nama_shs_cocok = str(nama_shs) if nama_shs else None

                    hs = getattr(c, "harga_satuan", "")
                    if hs != "" and not pd.isna(hs):
                        try:
                            harga_satuan = float(hs)
                        except (ValueError, TypeError):
                            harga_satuan = None

                    jh = getattr(c, "jumlah_harga", "")
                    if jh != "" and not pd.isna(jh):
                        try:
                            jumlah_harga = float(jh)
                        except (ValueError, TypeError):
                            jumlah_harga = None

                satuan = getattr(c, satuan_col, "")

                komponen.append({
                    "urutan": int(c.urutan),
                    "jenis": c.jenis,
                    "kode_komponen": c.kode_komponen,
                    "nama_komponen": c.nama_komponen,
                    "satuan": satuan,
                    "koefisien": float(c.koefisien),
                    "perlu_cek": is_perlu_cek,
                    "nama_shs_cocok": nama_shs_cocok,
                    "harga_satuan": harga_satuan,
                    "jumlah_harga": jumlah_harga,
                    "status_pencocokan": status_pencocokan,
                })

        return {"id": r["id"], "uraian": r["uraian"], "satuan": r["satuan"],
                "divisi": r["divisi"], "kategori": r["kategori"], "subkategori": r["subkategori"],
                "tipe": r["tipe"], "sumber": r["sumber"], "ref_permen": r["ref_permen"],
                "komponen": komponen}

    def list_items(
        self,
        page: int = 1,
        page_size: int = 20,
        divisi: str | None = None,
        kategori: str | None = None,
    ) -> dict:
        df = self.items
        if isinstance(divisi, str) and divisi.strip():
            df = df[df["divisi"].str.contains(divisi.strip(), case=False, na=False)]
        if isinstance(kategori, str) and kategori.strip():
            df = df[df["kategori"].str.contains(kategori.strip(), case=False, na=False)]

        total = len(df)
        total_pages = max(1, (total + page_size - 1) // page_size) if total > 0 else 0

        start = (page - 1) * page_size
        end = start + page_size
        sliced = df.iloc[start:end]

        items = [
            {
                "id": r.id,
                "uraian": r.uraian,
                "satuan": r.satuan,
                "divisi": r.divisi,
                "kategori": r.kategori,
                "subkategori": getattr(r, "subkategori", ""),
                "tipe": getattr(r, "tipe", ""),
                "sumber": getattr(r, "sumber", "") or None,
                "ref_permen": getattr(r, "ref_permen", "") or None,
                "jumlah_komponen": int(r.jumlah_komponen) if getattr(r, "jumlah_komponen", "") and str(r.jumlah_komponen).isdigit() else None,
            }
            for r in sliced.itertuples()
        ]

        return {
            "total": total,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "items": items,
        }