import streamlit as st
import scrapetube
from youtube_transcript_api import YouTubeTranscriptApi
import pandas as pd
import time

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="YT Guerrilla Search", page_icon="🕵️", layout="wide")

st.title("🕵️ YT Guerrilla Search")
st.markdown("### Motore di ricerca tattico per canali YouTube")
st.warning("⚠️ Modalità Volatile: I dati vengono persi se ricarichi la pagina (costo zero, niente database).")

# 2. SIDEBAR - INPUT
with st.sidebar:
    st.header("Target")
    channel_url = st.text_input("URL del Canale", placeholder="https://youtube.com/@nomecanale")
    limit = st.slider("Max Video da analizzare", 10, 100, 20)
    st.info("Consiglio: Inizia con 20 video per evitare blocchi.")
    start_btn = st.button("🚀 Avvia Scansione")

# 3. FUNZIONI CORE
def get_channel_id_from_url(url):
    # Funzione grezza per estrarre l'ID se l'utente mette l'URL completo
    # Per semplicità, in modalità guerrilla ci affidiamo a scrapetube che è intelligente
    return url

def get_transcripts(channel_input, limit_videos):
    data = []
    status_box = st.status("Infiltrazione in corso...", expanded=True)
    
    try:
        # Ottiene lista video
        status_box.write("📡 Connessione al canale...")
        videos = list(scrapetube.get_channel(channel_url=channel_input, limit=limit_videos))
        total_vids = len(videos)
        status_box.write(f"✅ Trovati {total_vids} video recenti.")
        
        progress_bar = status_box.progress(0)
        
        for i, video in enumerate(videos):
            vid_id = video['videoId']
            # Gestione sicura del titolo
            try:
                title = video['title']['runs'][0]['text']
            except:
                title = "Titolo Sconosciuto"

            status_box.write(f"📄 Scarico: {title[:30]}...")
            
            try:
                # Tenta di scaricare sottotitoli (Italiano, poi Inglese)
                transcript = YouTubeTranscriptApi.get_transcript(vid_id, languages=['it', 'en', 'en-US'])
                
                # Appiattisce il testo
                full_text = " ".join([t['text'] for t in transcript])
                
                # Salviamo ogni riga per la ricerca di precisione
                for entry in transcript:
                    data.append({
                        'video_id': vid_id,
                        'title': title,
                        'text': entry['text'],
                        'start': entry['start'],
                        'url': f"https://www.youtube.com/watch?v={vid_id}&t={int(entry['start'])}s"
                    })
                    
                # PAUSA TATTICA (Fondamentale per non farsi bannare l'IP)
                time.sleep(0.5) 
                
            except Exception as e:
                # Se fallisce (es. niente sottotitoli), ignora e vai avanti
                continue
            
            # Aggiorna barra
            progress_bar.progress((i + 1) / total_vids)
            
        status_box.update(label="Missione Compiuta ✅", state="complete", expanded=False)
        return pd.DataFrame(data)

    except Exception as e:
        status_box.update(label="Errore Critico ❌", state="error")
        st.error(f"Errore: {e}. Assicurati che l'URL sia corretto.")
        return pd.DataFrame()

# 4. LOGICA INTERFACCIA
if 'db' not in st.session_state:
    st.session_state['db'] = pd.DataFrame()

if start_btn and channel_url:
    df = get_transcripts(channel_url, limit)
    st.session_state['db'] = df
    if not df.empty:
        st.success(f"Indicizzati {len(df)} segmenti di testo.")

st.divider()

# 5. MOTORE DI RICERCA
search_query = st.text_input("🔍 Cerca parola chiave nel database estratto", placeholder="Es: bitcoin, elezioni, verità...")

if search_query and not st.session_state['db'].empty:
    # Ricerca Case-Insensitive
    results = st.session_state['db'][st.session_state['db']['text'].str.contains(search_query, case=False, na=False)]
    
    st.write(f"Risultati trovati: **{len(results)}**")
    
    # Visualizzazione pulita
    for idx, row in results.head(50).iterrows(): # Mostra solo i primi 50 per velocità
        st.markdown(f"""
        **{row['title']}**  
        ⏱️ `{int(row['start'])}s`: ...{row['text']}...  
        [▶️ GUARDA VIDEO]({row['url']})
        ---
        """)