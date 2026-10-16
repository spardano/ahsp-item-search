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
        self.komponen = pd.read_csv(folder / "ahsp_components.csv", dtype={"item_id": str}).fillna("")
        self.index_komponen = {k: g for k, g in self.komponen.groupby("item_id", sort=False)}

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