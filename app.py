import streamlit as st
import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
import pandas as pd
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="YT Guerrilla Search", page_icon="🕵️", layout="wide")
st.title("🕵️ YT Guerrilla Search")

# --- MEMORIA (SESSION STATE) ---
# Questo serve a non far dimenticare i dati quando premi invio
if 'db' not in st.session_state:
    st.session_state['db'] = pd.DataFrame()

# --- SIDEBAR (INPUT) ---
with st.sidebar:
    st.header("1. Configurazione")
    channel_url = st.text_input("URL Canale", placeholder="https://youtube.com/@canale")
    limit = st.slider("Numero video", 10, 50, 20)
    
    # Il bottone serve SOLO a scaricare
    start_btn = st.button("🚀 SCARICA DATI")

# --- FUNZIONE DI SCARICAMENTO ---
def get_transcripts(url, max_vid):
    data = []
    status = st.status("Infiltrazione...", expanded=True)
    try:
        videos = list(scrapetube.get_channel(channel_url=url, limit=max_vid))
        total = len(videos)
        bar = status.progress(0)
        
        for i, video in enumerate(videos):
            try:
                vid_id = video['videoId']
                title = video['title']['runs'][0]['text']
                status.write(f"Prendo: {title[:20]}...")
                
                # Scarica transcript
                ts = YouTubeTranscriptApi.get_transcript(vid_id, languages=['it', 'en', 'en-US'])
                
                for row in ts:
                    data.append({
                        'title': title,
                        'text': row['text'],
                        'start': row['start'],
                        'url': f"https://www.youtube.com/watch?v={vid_id}&t={int(row['start'])}s"
                    })
                time.sleep(0.2) # Pausa anti-ban
            except:
                continue
            bar.progress((i+1)/total)
            
        status.update(label="Fatto! ✅", state="complete", expanded=False)
        return pd.DataFrame(data)
    except Exception as e:
        status.update(label="Errore ❌", state="error")
        st.error(f"Errore URL: {e}")
        return pd.DataFrame()

# --- LOGICA DI ESECUZIONE (IL PUNTO CRITICO) ---

# 1. SE premi il bottone, scarica e SALVA IN MEMORIA
if start_btn and channel_url:
    df_new = get_transcripts(channel_url, limit)
    st.session_state['db'] = df_new # <--- Salviamo nella cassaforte
    if not df_new.empty:
        st.success(f"Caricati {len(df_new)} frammenti.")

# --- BARRIERA DI SEPARAZIONE ---
# Tutto quello che c'è qui sotto viene eseguito SEMPRE, 
# anche se non hai appena premuto il bottone, perché legge dalla memoria.

st.divider()
st.header("2. Ricerca Tattica")

# Controlliamo se la memoria è vuota
if st.session_state['db'].empty:
    st.info("👈 Inserisci un canale a sinistra e premi Scarica per iniziare.")
else:
    # LA RICERCA È QUI, FUORI DAL BLOCCO DEL BOTTONE
    query = st.text_input("Cosa cerchi?", placeholder="Es: inflazione, bitcoin, verità...")
    
    if query:
        # Filtra usando i dati in memoria
        mask = st.session_state['db']['text'].str.contains(query, case=False, na=False)
        results = st.session_state['db'][mask]
        
        st.subheader(f"Trovati: {len(results)}")
        
        # Mostra risultati
        for i, row in results.head(50).iterrows():
            st.markdown(f"""
            > **{row['text']}**  
            Video: *{row['title']}* | [👉 Vai al punto esatto]({row['url']})
            """)
            st.divider()
