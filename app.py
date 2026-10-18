"""
app.py  (Phase 10)
SHIFA Knowledge Assistant - Streamlit chat UI.

IMPORTANT: This app never re-processes or re-embeds documents.
It only LOADS the pre-built knowledge_base/ (faiss.index + chunks.pkl) made by build_index.py.
"""

import os

import streamlit as st
import streamlit.components.v1 as components

from retriever import load_knowledge_base
from rag_pipeline import get_groq_client, stream_answer
from embedder import get_model as load_embedding_model

APP_NAME = "SHIFA Knowledge Assistant"
TEXT_SIZES = {"Normal": 16, "Large": 19, "Extra large": 22}
USER_AVATAR = "🧑‍⚕️"
BOT_AVATAR = "🏥"

# Example questions shown as tap-able cards (English, Urdu, Roman Urdu)
EXAMPLES = [
    ("English", "What is the deposit for ICU admission?"),
    ("English", "What should I do after a needle-stick injury?"),
    ("اردو", "آئی سی یو میں داخلے کے لیے ڈپازٹ کتنا ہے؟"),
    ("اردو", "ایمرجنسی مریض کو داخل کرنے کا طریقہ کار کیا ہے؟"),
    ("Roman Urdu", "ICU mein admission ka process kya hai?"),
    ("Roman Urdu", "Needle-stick injury ke baad kya karna chahiye?"),
]


# ---------------------------------------------------------------
# Page config (must be the first Streamlit call)
# ---------------------------------------------------------------
st.set_page_config(
    page_title=APP_NAME,
    page_icon="🏥",
    layout="centered",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------
# Cached loaders - run only ONCE, not on every interaction
# ---------------------------------------------------------------
@st.cache_resource
def get_knowledge_base():
    """Loads the saved FAISS index + chunks. Documents are NOT re-processed."""
    return load_knowledge_base()


@st.cache_resource
def get_embedding_model():
    """Loads the multilingual embedding model once and keeps it in cache."""
    return load_embedding_model()


@st.cache_resource
def get_client():
    """Creates the Groq client. The API key comes from Streamlit secrets or an environment variable."""
    api_key = os.environ.get("GROQ_API_KEY")
    try:
        api_key = st.secrets.get("GROQ_API_KEY", api_key)
    except Exception:
        # Local runs may not have a .streamlit/secrets.toml file.
        pass
    if not api_key:
        st.error("GROQ_API_KEY was not found. Add it to Streamlit Cloud Secrets "
                 "or export it as an environment variable.")
        st.stop()
    return get_groq_client(api_key)


# ---------------------------------------------------------------
# Styling (colours, cards, Urdu-friendly text direction)
# ---------------------------------------------------------------
CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&family=Noto+Naskh+Arabic:wght@400;600&display=swap');

.block-container { max-width: 820px; padding-top: 2rem; padding-bottom: 6rem; }
footer { visibility: hidden; }

/* Fonts only for text blocks (so icons keep their own font) */
.stMarkdown p, .stMarkdown li, .stCaption, .stButton button p {
    font-family: 'Inter', 'Noto Naskh Arabic', system-ui, -apple-system, 'Segoe UI', sans-serif;
}
/* Each paragraph picks its own direction: Urdu reads right-to-left, English left-to-right */
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li,
.stButton button p {
    unicode-bidi: plaintext;
    text-align: start;
}
[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li {
    font-size: __SIZE__px;
    line-height: 1.75;
}

/* Hero card */
.hero {
    background: linear-gradient(135deg, #0F766E 0%, #14A89A 100%);
    color: #fff; border-radius: 22px; padding: 1.6rem 1.8rem;
    box-shadow: 0 10px 30px rgba(15,118,110,.22); margin-bottom: 1.2rem;
}
.hero-title { font-size: 1.9rem; font-weight: 700; margin: 0 0 .3rem 0; line-height: 1.2; }
.hero-sub { margin: 0; opacity: .95; font-size: 1.02rem; }
.chips span {
    display: inline-block; background: rgba(255,255,255,.18); border-radius: 999px;
    padding: .28rem .85rem; margin: .8rem .45rem 0 0; font-size: .86rem;
}
.section-label { font-weight: 600; color: #0F766E; margin: 1.1rem 0 .4rem 0; }

/* Compact header once the chat has started */
.mini-title { font-size: 1.35rem; font-weight: 700; color: #0F766E; margin: 0; }

/* Example cards and buttons */
.stButton > button {
    border-radius: 14px; border: 1px solid #CBE4E0; background: #fff;
    padding: .65rem .9rem; transition: all .15s ease;
}
.stButton > button:hover {
    border-color: #0F766E; color: #0F766E; box-shadow: 0 4px 14px rgba(15,118,110,.14);
    transform: translateY(-1px);
}

/* Chat bubbles */
[data-testid="stChatMessage"] {
    background: #FFFFFF; border: 1px solid #DDEBE9; border-radius: 18px;
    padding: .9rem 1.1rem; margin-bottom: .6rem;
}
[data-testid="stChatInput"] { border-radius: 16px; }

/* Sidebar brand */
.brand { font-size: 1.3rem; font-weight: 700; color: #0F766E; line-height: 1.25; }
.brand-sub { color: #4C6B67; font-size: .88rem; margin-bottom: .6rem; }
</style>
"""

# Small script: sets the text direction of each message by its MAJORITY script, so a sentence
# like "ICU میں داخلے کا عمل ..." is shown right-to-left. If the script cannot run, the CSS above still helps.
BIDI_JS = """
<script>
(function () {
  const doc = window.parent.document;
  if (doc.__shifaBidi) { return; }
  doc.__shifaBidi = true;
  function fix() {
    doc.querySelectorAll('[data-testid="stChatMessage"] p, [data-testid="stChatMessage"] li').forEach(function (el) {
      const t = el.textContent || "";
      const rtl = (t.match(/[\\u0600-\\u06FF]/g) || []).length;
      const ltr = (t.match(/[A-Za-z]/g) || []).length;
      const isRtl = rtl > ltr;
      el.setAttribute("dir", isRtl ? "rtl" : "ltr");
      el.style.textAlign = isRtl ? "right" : "left";
    });
  }
  new MutationObserver(fix).observe(doc.body, {subtree: true, childList: true, characterData: true});
  fix();
})();
</script>
"""


# ---------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------
def queue_question(question):
    """Called when an example card is tapped."""
    st.session_state["pending_question"] = question


def erase_everything():
    """Deletes the whole conversation from this session. Keeps only the text-size choice."""
    size = st.session_state.get("text_size", "Normal")
    st.session_state.clear()
    st.session_state["text_size"] = size
    st.session_state["just_erased"] = True


def erase_button(where):
    """A 'Erase chat' button that asks for confirmation first."""
    with st.popover("🗑️ Erase chat", use_container_width=True):
        st.write("This removes **all messages** from this session. It cannot be undone.")
        st.button("Yes, erase everything", key=f"confirm_erase_{where}",
                  on_click=erase_everything, type="primary", use_container_width=True)


def render_sources(sources):
    if not sources:
        st.caption("💡 No document was cited. Try rephrasing, or use words from the topic or department.")
        return
    with st.expander(f"📚 Sources ({len(sources)})"):
        for s in sources:
            st.markdown(f"**[{s['tag']}] {s['filename']}**  \n"
                        f"{s['department']} · Page {s['page']} · relevance {s['score']:.2f}")
            st.caption(f"“{s['excerpt']}”")


# ---------------------------------------------------------------
# App start: load knowledge base, model and client
# ---------------------------------------------------------------
with st.spinner("Getting things ready..."):
    try:
        index, chunks_db = get_knowledge_base()
    except Exception as e:   # for example: wrong or missing index files
        st.error(f"The knowledge base could not be loaded: {e}")
        st.stop()
    get_embedding_model()    # load and cache the model before the first question
    client = get_client()

if "messages" not in st.session_state:
    st.session_state["messages"] = []
if st.session_state.pop("just_erased", False):
    st.toast("Chat erased.", icon="🗑️")


# ---------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------
with st.sidebar:
    st.markdown(f'<div class="brand">🏥 {APP_NAME}</div>'
                '<div class="brand-sub">Answers from official hospital documents</div>',
                unsafe_allow_html=True)

    st.markdown("**How to use**")
    st.markdown("1. Type a question, or tap an example\n"
                "2. Read the answer\n"
                "3. Open **Sources** to double-check")
    st.markdown("**Languages:** English · اردو · Roman Urdu")

    st.markdown("---")
    st.markdown("**Text size**")
    text_size = st.radio("Text size", list(TEXT_SIZES), horizontal=True,
                         key="text_size", label_visibility="collapsed")

    st.markdown("---")
    st.markdown("**Privacy**")
    st.caption("Your chat stays in this browser session only. This app does not save it to a database. "
               "Your question and the matching document text are sent to Groq to write the answer.")
    erase_button("sidebar")

    st.markdown("---")
    n_docs = len({c["filename"] for c in chunks_db})
    departments = sorted({c["department"] for c in chunks_db})
    st.caption(f"📁 {n_docs} documents · {len(chunks_db)} sections indexed")
    st.caption("Departments: " + ", ".join(departments))

    st.warning("Demo with synthetic data. Not for real clinical use.", icon="⚠️")


st.markdown(CSS.replace("__SIZE__", str(TEXT_SIZES[text_size])), unsafe_allow_html=True)


# ---------------------------------------------------------------
# Take the new question (typed or from an example card) BEFORE drawing the page
# ---------------------------------------------------------------
typed = st.chat_input("Type your question here... (English, اردو or Roman Urdu)")
question = st.session_state.pop("pending_question", None) or typed
if question:
    st.session_state["messages"].append({"role": "user", "content": question})


# ---------------------------------------------------------------
# Welcome screen (empty chat) or compact header (chat started)
# ---------------------------------------------------------------
if not st.session_state["messages"]:
    st.markdown(
        f"""
        <div class="hero">
          <div class="hero-title">🏥 {APP_NAME}</div>
          <p class="hero-sub">Ask about hospital policies and procedures. You get a clear answer and the
          document it came from. If the answer is not in the documents, it will say so.</p>
          <div class="chips">
            <span>🌐 English · اردو · Roman Urdu</span>
            <span>📚 Sources shown</span>
            <span>🚫 No guessing</span>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-label">Try asking</div>', unsafe_allow_html=True)
    cols = st.columns(2)
    for i, (lang, q) in enumerate(EXAMPLES):
        with cols[i % 2]:
            st.button(f"{q}", key=f"example_{i}", help=lang, use_container_width=True,
                      on_click=queue_question, args=(q,))
else:
    left, right = st.columns([3, 1])
    with left:
        st.markdown(f'<p class="mini-title">🏥 {APP_NAME}</p>', unsafe_allow_html=True)
    with right:
        erase_button("main")


# ---------------------------------------------------------------
# Chat history (includes the question just asked)
# ---------------------------------------------------------------
for msg in st.session_state["messages"]:
    avatar = USER_AVATAR if msg["role"] == "user" else BOT_AVATAR
    with st.chat_message(msg["role"], avatar=avatar):
        st.markdown(msg["content"])
        if msg["role"] == "assistant":
            render_sources(msg.get("sources", []))


# ---------------------------------------------------------------
# Answer the new question (streamed)
# ---------------------------------------------------------------
if question:
    with st.chat_message("assistant", avatar=BOT_AVATAR):
        status = st.empty()
        status.markdown("🔎 *Searching the hospital documents...*")
        collected = []
        error = None

        def pieces():
            """Passes text pieces to the screen. Clears the 'searching' note at the first piece."""
            stream, state = stream_answer(question, index, chunks_db, client, top_k=4)
            pieces.state = state
            for piece in stream:
                if not collected:
                    status.empty()
                collected.append(piece)
                yield piece

        try:
            st.write_stream(pieces())
        except Exception as e:
            error = e
        status.empty()

        answer_text = "".join(collected)
        cited_sources = getattr(pieces, "state", {}).get("cited_sources", []) if error is None else []

        if error is not None:
            st.error("The answer was interrupted. Please try again in a moment.")
            if answer_text:
                answer_text += "\n\n_The answer was interrupted._"
        if answer_text:
            render_sources(cited_sources)

    if answer_text:
        st.session_state["messages"].append({
            "role": "assistant",
            "content": answer_text,
            "sources": cited_sources,
        })

# st.iframe is the newer way; older Streamlit versions only have components.html
if hasattr(st, "iframe"):
    st.iframe(BIDI_JS, height=1)
else:
    components.html(BIDI_JS, height=0)
