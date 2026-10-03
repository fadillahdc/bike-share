# Bike Sharing Analysis

Proyek analisis data Bike Sharing Dataset (2011–2012) beserta dashboard interaktif.

- **Notebook analisis:** `notebook.ipynb`
- **Dashboard:** Streamlit + Plotly (interaktif: hover, zoom, filter)
- **Live dashboard:** https://fdc-bikeshare.streamlit.app/

Visualisasi mengikuti prinsip desain dan integritas data: satu warna aksen (biru) hanya untuk menyorot informasi utama, abu-abu untuk pembanding, judul grafik berupa pesan utama, dan sumbu bar chart selalu dimulai dari nol.

## Struktur Folder

```
bike-share/
├── dashboard/
│   ├── dashboard.py
│   └── main_data.csv
├── data/
│   ├── day.csv
│   └── hour.csv
├── notebook.ipynb
├── README.md
├── requirements.txt
└── url.txt
```

## Setup Environment - Anaconda

```
conda create --name bike-share python=3.11
conda activate bike-share
pip install -r requirements.txt
```

## Setup Environment - Shell/Terminal

```
mkdir proyek_analisis_data
cd proyek_analisis_data
pipenv install
pipenv shell
pip install -r requirements.txt
```

## Run Streamlit App

Jalankan dari folder utama proyek (`bike-share/`):

```
streamlit run dashboard/dashboard.py
```
