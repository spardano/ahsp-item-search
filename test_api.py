import pytest
from fastapi.testclient import TestClient

from Main import app
from Normalisasi import normalize


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:      # `with` menjalankan lifespan (membangun indeks)
        yield c


# ---- normalisasi -----------------------------------------------------------
def test_normalisasi_rasio_sama():
    assert normalize("plesteran 1:3") != ""
    assert "rasio_1_3" in normalize("1:3").split()
    assert "rasio_1_3" in normalize("Plesteran 1SP : 3PP Tebal 15mm").split()


def test_normalisasi_ukuran_dan_pecahan_dan_mutu():
    assert "40x40" in normalize("pasang keramik 40x40").split()
    assert "40x40" in normalize("Ukuran 40 cm x 40 cm").split()
    assert "frac_3_4" in normalize('DN. 3/4" (20 mm)').split()
    assert "fc_21" in normalize("f'c 21 MPa").split()
    assert "fc_21" in normalize("beton fc 21").split()


# ---- /health ---------------------------------------------------------------
def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200 and r.json()["jumlah_item"] == 2596


# ---- /search ---------------------------------------------------------------
@pytest.mark.parametrize("query,id_benar", [
    ("plesteran 1:3", "3.7.3"),
    ("bekisting sloof", "2.2.1.3.3"),
    ("cat plafon interior", "3.8.20.1"),
    ("beton fc 21 manual", "2.2.1.4.6"),
    ("plafon gypsum 9 mm", "3.5.2.1"),
])
def test_search_top1(client, query, id_benar):
    r = client.get("/search", params={"q": query, "k": 5})
    assert r.status_code == 200
    j = r.json()
    assert j["hasil"][0]["id"] == id_benar
    assert j["ada_hasil_yakin"] is True
    assert len(j["hasil"]) == 5


def test_search_query_asal_tidak_yakin(client):
    j = client.get("/search", params={"q": "makan siang"}).json()
    assert j["ada_hasil_yakin"] is False


def test_search_validasi_input(client):
    assert client.get("/search", params={"q": "a"}).status_code == 422          # terlalu pendek
    assert client.get("/search", params={"q": "beton", "k": 0}).status_code == 422
    assert client.get("/search", params={"q": "beton", "k": 21}).status_code == 422
    assert client.get("/search").status_code == 422                              # q wajib


def test_search_query_hanya_simbol(client):
    j = client.get("/search", params={"q": "!!"}).json()                         # kosong setelah normalisasi
    assert j["hasil"] == [] and j["ada_hasil_yakin"] is False


# ---- /ahsp-items -----------------------------------------------------------
def test_ahsp_items_pagination(client):
    r = client.get("/ahsp-items?page=1&page_size=20")
    assert r.status_code == 200
    j = r.json()
    assert j["total"] == 2596
    assert j["page"] == 1
    assert j["page_size"] == 20
    assert j["total_pages"] == 130
    assert len(j["items"]) == 20
    assert j["items"][0]["id"] == "1.1.1.1"


def test_ahsp_items_filter(client):
    r = client.get("/ahsp-items?divisi=PERSIAPAN&page_size=5")
    assert r.status_code == 200
    j = r.json()
    assert j["total"] > 0
    assert len(j["items"]) == 5
    assert all("PERSIAPAN" in it["divisi"].upper() for it in j["items"])


# ---- /items ----------------------------------------------------------------
def test_detail_item(client):
    r = client.get("/items/3.7.3")
    assert r.status_code == 200
    j = r.json()
    assert j["id"] == "3.7.3" and j["satuan"] == "m2"
    jenis = {k["jenis"] for k in j["komponen"]}
    assert {"tenaga_kerja", "bahan"} <= jenis
    assert all(isinstance(k["koefisien"], float) for k in j["komponen"])
    # verifikasi field harga
    first = j["komponen"][0]
    assert "harga_satuan" in first
    assert "jumlah_harga" in first
    assert "status_pencocokan" in first
    assert "nama_shs_cocok" in first
    assert isinstance(first["harga_satuan"], float)


def test_detail_item_id_dengan_tanda_pagar(client):
    r = client.get("/items/2.2.1.1.5%232")
    assert r.status_code == 200 and r.json()["id"] == "2.2.1.1.5#2"


def test_detail_item_tidak_ada(client):
    assert client.get("/items/9.9.9.9").status_code == 404
