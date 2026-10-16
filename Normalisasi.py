"""Normalisasi teks AHSP.
 
Satu-satunya tempat untuk menambah aturan penyamaan penulisan. Fungsi normalize()
dipakai SAMA PERSIS untuk teks item dan teks query, supaya bentuk yang artinya
sama menghasilkan token yang sama.
 
Menambah aturan baru:
  - sinonim kata  -> tambahkan pasangan di SINONIM
  - pola angka    -> tambahkan satu re.sub di normalize(), lalu ukur dampaknya
Setiap perubahan di sini mengubah indeks, jadi mesin harus dibangun ulang (restart API).
"""
import re

NUM = r"\d+(?:_\d+)?"
FRAKSI_UNICODE = {"½": " 1/2 ", "¼": " 1/4 ", "¾": " 3/4 ", "⅓": " 1/3 ", "⅔": " 2/3 "}

#Kamus Sinonim 
SINONIM = {
    "acuan": "bekisting", "bekesting": "bekisting",
    "pengecatan": "cat", "mengecat": "cat",
    "plafond": "plafon",
    "pengecoran": "cor",
    "pemasangan": "pasang",
    "penggalian": "galian",
    "fondasi": "pondasi",
    "pembesian": "penulangan",
    "closet": "kloset", "wc": "kloset",
}

def normalize(text: str) -> str:
    text = text.lower()

    #WARNING: DONT REORDER THE NUMBER.

    #1. samakan karakter
    text = text.replace("’", "'").replace("m²", "m2").replace("m³", "m3").replace("×", "x")

    #2. ubah rasio camouran ke standar yang sama "1SP : 3PP", "1 sp:3 pp", "1:3"  ->  rasio_1_3
    #    (huruf sp/pp dibuang karena query user biasanya hanya menulis "1:3")
    text = re.sub(r"(\d+)\s*[a-z]{0,2}\s*:\s*(\d+)\s*[a-z]{0,2}(?:\s*:\s*(\d+)\s*[a-z]{0,2})?", 
                  lambda m: "rasio_" + "_".join(g for g in m.groups() if g), text)

    # 3. angka desimal: "19,3" atau "0.75"  ->  19_3 / 0_75 (agar tanda baca tidak memecahnya)
    text = re.sub(r"\bf['’]?c['’]?\s*(\d+(?:_\d+)?)", r"fc_\1", text)

    # 4. ukuran: "40 cm x 40 cm", "40x40", "40 x 40 cm"  ->  40x40
    for _ in range(2):
        text = re.sub(rf"({NUM})\s*(?:cm|mm|m)?\s*x\s*({NUM})", r"\1x\2", text)

    # 5. pecahan: "3/4", "1-1/2"  ->  frac_3_4
    text = re.sub(r"(\d+)\s*/\s*(\d+)", r"frac_\1_\2", text)
 
    # 6. angka menempel satuan: "15mm" -> "15 mm"
    text = re.sub(r"(\d)(mm|cm|kg|mpa|m2|m3)\b", r"\1 \2", text)
 
    # 7. buang tanda baca (garis bawah dipertahankan), rapikan spasi
    text = re.sub(r"[^a-z0-9_\s]", " ", text)
 
    # 8. sinonim: ganti tiap kata dengan bentuk bakunya
    return " ".join(SINONIM.get(tok, tok) for tok in text.split())

    

