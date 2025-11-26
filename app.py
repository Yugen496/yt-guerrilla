import streamlit as st
import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
import pandas as pd
import time

# --- CONFIGURAZIONE ---
st.set_page_config(page_title="YT Debugger", page_icon="🛠️", layout="wide")

st.title("🛠️ YT Search - Modalità Sicura")
st.info("Questa modalità mostra la ricerca PRIMA di scaricare, per evitare che sparisca.")

# --- MEMORIA ---
if 'db' not in st.session_state:
    st.session_state['db'] = pd.DataFrame()

# =========================================================
# 1. IL MOTORE DI RICERCA (SPOSTATO IN ALTO)
# =========================================================
st.divider()
st.subheader("🔎 Area Ricerca")

col1, col2 = st.columns([3, 1])
with col1:
    # Input di ricerca
    query = st.text_input("Scrivi parola chiave e premi INVIO:", key="search_box")

if query:
    if st.session_state['db'].empty:
        st.warning("⚠️ Il database è vuoto. Devi scaricare i dati dalla colonna a sinistra (o usare il bottone Test).")
    else:
        # Esegue la ricerca
        mask = st.session_state['db']['text'].str.contains(query, case=False, na=False)
        results = st.session_state['db'][mask]
        
        if results.empty:
            st.error(f"❌ Nessuna corrispondenza per '{query}'")
        else:
            st.success(f"✅ Trovati {len(results)} risultati.")
            for i, row in results.head(20).iterrows():
                with st.expander(f"📺 {row['title']} (a {int(row['start'])}s)"):
                    st.write(f"... {row['text']} ...")
                    st.markdown(f"[👉 Vai al Video]({row['url']})")

st.divider()

# =========================================================
# 2. LA SIDEBAR (IL DOWNLOAD)
# =========================================================
with st.sidebar:
    st.header("Gestione Dati")
    
    # --- TEST DI EMERGENZA ---
    if st.button("🛠️ CARICA DATI DI TEST (Senza YouTube)"):
        # Crea un database finto per vedere se il sito funziona
        fake_data = [{
            'title': 'Video Test Breaking Italy',
            'text': 'Questa è una prova per vedere se la ricerca funziona. Parola chiave: inflazione.',
            'start': 10,
            'url': 'https://google.com'
        },
        {
            'title': 'Video Test 2',
            'text': 'Qui parliamo di Bitcoin e criptovalute.',
            'start': 50,
            'url': 'https://google.com'
        }]
        st.session_state['db'] = pd.DataFrame(fake_data)
        st.success("Dati finti caricati! Prova a cercare 'inflazione' o 'bitcoin' a destra.")

    st.markdown("---")
    
    # --- DOWNLOAD REALE ---
    target_url = st.text_input("URL Canale", value="https://www.youtube.com/@breakingitaly")
    limit_val = st.slider("Num Video", 5, 50, 10)
    
    if st.button("📥 SCARICA DA YOUTUBE"):
        status_box = st.status("Avvio connessione...", expanded=True)
        try:
            # 1. Scrapetube
            status_box.write("📡 Contatto YouTube...")
            # PROVA AD USARE L'ID CANALE SE L'URL FALLISCE
            videos = list(scrapetube.get_channel(channel_url=target_url, limit=limit_val))
            
            if not videos:
                status_box.update(label="❌ Canale non trovato o bloccato.", state="error")
            else:
                status_box.write(f"✅ Trovati {len(videos)} video. Scarico testi...")
                new_data = []
                bar = status_box.progress(0)
                
                for i, v in enumerate(videos):
                    try:
                        vid = v['videoId']
                        title = v['title']['runs'][0]['text']
                        
                        # Scarica Transcript
                        try:
                            # Prende il primo disponibile
                            t_list = YouTubeTranscriptApi.list_transcripts(vid)
                            tr = next(iter(t_list)).fetch()
                            
                            for row in tr:
                                new_data.append({
                                    'title': title,
                                    'text': row['text'],
                                    'start': row['start'],
                                    'url': f"https://www.youtube.com/watch?v={vid}&t={int(row['start'])}s"
                                })
                        except:
                            pass # Niente sottotitoli
                            
                    except:
                        pass
                    
                    time.sleep(0.1)
                    bar.progress((i+1)/len(videos))
                
                if len(new_data) > 0:
                    st.session_state['db'] = pd.DataFrame(new_data)
                    status_box.update(label=f"✅ Fatto! {len(new_data)} righe scaricate.", state="complete")
                else:
                    status_box.update(label="⚠️ Video trovati, ma zero testi.", state="error")

        except Exception as e:
            status_box.update(label="❌ CRASH", state="error")
            st.error(f"Errore tecnico: {str(e)}")
