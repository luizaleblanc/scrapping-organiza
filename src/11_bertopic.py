"""Etapa 11 — Modelagem de tópicos com BERTopic e preparação da Etapa 4 (guia, Etapas 3 e 4).

Usa EXCLUSIVAMENTE as cópias redigidas geradas pelo passo 7 (`reviews_critical_redacted.csv`)
das duas lojas (Google Play e App Store). Nunca lê `reviews_critical.csv` nem a chave de máscaras.

Modo padrão: modelagem separada por idioma (`pt`, `en`, `es`), deduplicando avaliações
idênticas compartilhadas entre Espanha e México na Google Play para evitar duplicidade no
corpus em espanhol. Use `--juntos` para modelar todos os idiomas em conjunto.

Saídas (pasta privada `data/topicos/<grupo>/`):
  - review_topics.csv       : review_id, metadados preservados, content (redigido), topic, probability
  - topic_info.csv          : topic, n, palavras_chave (top 10), c_v
  - representative_docs.csv : até 5 avaliações representativas por tópico (por similaridade ao centroide)
  - intertopic_map.html     : mapa intertópicos (Plotly)
  - similarity_matrix.html  : matriz de similaridade entre tópicos (Plotly)
  - triagem_topicos.csv     : planilha da Etapa 4 (sem tópico -1, decisões vazias para revisão humana)

Métricas gravadas em `outputs/funnel_metrics.json` sob `11_bertopic_<grupo>`.

Uso:
  python src/11_bertopic.py                       # padrão: separado por idioma (pt, en, es)
  python src/11_bertopic.py --idiomas pt en es    # idiomas específicos
  python src/11_bertopic.py --juntos              # todos os idiomas em conjunto
"""
import argparse
import importlib.metadata as md
import math
import platform
import re
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C  # noqa: E402
from rules import update_metrics, write_csv  # noqa: E402

SEED = getattr(C, "SEED", 42)
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
UMAP_PARAMS = dict(n_neighbors=15, n_components=5, min_dist=0.0, metric="cosine", random_state=SEED)
HDBSCAN_PARAMS = dict(
    min_cluster_size=15,
    min_samples=None,  # padrão HDBSCAN (= min_cluster_size = 15); registrado explicitamente conforme guia
    metric="euclidean",
    cluster_selection_method="eom",
    prediction_data=True,
)
TOP_N_WORDS = 10
MIN_TOPIC_SIZE_FILTER = 15
N_REP_DOCS = 5
TOPICS_ROOT = C.DATA / "topicos"

REDACTION_MARKER_RE = re.compile(
    r"\[(?:NOME|APP|MARCA|LOCAL|EMAIL|PHONE|CPF|URL|HANDLE|POSSIBLE_PHONE_OR_NUMBER)\]",
    re.IGNORECASE,
)
TOKEN_RE = re.compile(r"(?u)\b[a-zA-ZáéíóúâêôãõçñÁÉÍÓÚÂÊÔÃÕÇÑ]{2,}\b")

# Stopwords gramaticais por idioma, usadas APENAS no CountVectorizer (c-TF-IDF das palavras-chave),
# nunca antes da geração dos embeddings.
STOPWORDS = {
    "pt": sorted({
        "a", "ao", "aos", "aquela", "aquelas", "aquele", "aqueles", "aquilo", "as", "ate", "até",
        "com", "como", "da", "das", "de", "dela", "delas", "dele", "deles", "depois", "do", "dos",
        "e", "ela", "elas", "ele", "eles", "em", "entre", "era", "eram", "essa", "essas", "esse",
        "esses", "esta", "está", "estão", "estas", "estava", "estavam", "este", "estes", "estou",
        "eu", "foi", "fomos", "for", "fora", "foram", "fosse", "fossem", "fui", "ha", "há", "haja",
        "isso", "isto", "ja", "já", "la", "lá", "lhe", "lhes", "lo", "mas", "me", "mesmo", "meu",
        "meus", "minha", "minhas", "muito", "na", "nas", "nem", "no", "nos", "nós", "nossa",
        "nossas", "nosso", "nossos", "num", "numa", "o", "os", "ou", "para", "pela", "pelas",
        "pelo", "pelos", "por", "porque", "pra", "pro", "qual", "quando", "que", "quem", "sao",
        "são", "se", "seja", "sejam", "sem", "ser", "sera", "será", "serao", "serão", "seu",
        "seus", "so", "só", "somos", "sou", "sua", "suas", "ta", "tá", "tambem", "também", "te",
        "tem", "têm", "tenho", "ter", "teu", "teus", "teve", "tinha", "tinham", "toda", "todas",
        "todo", "todos", "tu", "tua", "tuas", "tudo", "um", "uma", "umas", "uns", "vai", "vão",
        "vc", "voce", "você", "voces", "vocês", "vos", "dos", "das", "pelo", "pela", "ainda",
        "aqui", "assim", "bem", "cada", "dia", "entao", "então", "esta", "estao", "estar",
        "faz", "fazer", "fez", "fica", "ficar", "ficou", "mais", "menos", "nada", "nao", "não",
        "onde", "outra", "outras", "outro", "outros", "pode", "poder", "pois", "pouco", "quase",
        "sim", "sobre", "tão", "tao", "vez", "vezes", "ja", "ne", "né", "eh", "é",
    }),
    "en": sorted({
        "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are",
        "aren", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both",
        "but", "by", "can", "could", "did", "didn", "do", "does", "doesn", "doing", "don", "down",
        "during", "each", "few", "for", "from", "further", "get", "got", "had", "hadn", "has",
        "hasn", "have", "haven", "having", "he", "her", "here", "hers", "herself", "him",
        "himself", "his", "how", "i", "if", "in", "into", "is", "isn", "it", "its", "itself",
        "just", "ll", "m", "ma", "me", "might", "more", "most", "must", "my", "myself", "no",
        "nor", "not", "now", "o", "of", "off", "on", "once", "only", "or", "other", "our", "ours",
        "ourselves", "out", "over", "own", "re", "s", "same", "she", "should", "so", "some",
        "such", "t", "than", "that", "the", "their", "theirs", "them", "themselves", "then",
        "there", "these", "they", "this", "those", "through", "to", "too", "under", "until", "up",
        "ve", "very", "was", "wasn", "we", "were", "weren", "what", "when", "where", "which",
        "while", "who", "whom", "why", "will", "with", "won", "would", "y", "you", "your",
        "yours", "yourself", "yourselves", "really", "also", "even", "still", "much", "one", "two",
    }),
    "es": sorted({
        "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con", "contra", "cual",
        "cuando", "de", "del", "desde", "donde", "durante", "e", "el", "él", "ella", "ellas",
        "ellos", "en", "entre", "era", "erais", "eran", "eras", "eres", "es", "esa", "esas",
        "ese", "eso", "esos", "esta", "está", "estaba", "estaban", "estado", "estais", "estamos",
        "estan", "están", "estar", "estas", "estás", "este", "esto", "estos", "estoy", "fue",
        "fuera", "fueron", "fui", "ha", "habia", "había", "habian", "habían", "haber", "hace",
        "hacen", "hacer", "hacia", "han", "has", "hasta", "hay", "he", "hemos", "la", "las", "le",
        "les", "lo", "los", "mas", "más", "me", "mi", "mí", "mis", "mucho", "muchos", "muy",
        "nada", "ni", "no", "nos", "nosotras", "nosotros", "nuestra", "nuestras", "nuestro",
        "nuestros", "o", "os", "otra", "otras", "otro", "otros", "para", "pero", "poco", "por",
        "porque", "que", "qué", "quien", "quienes", "se", "sea", "sean", "segun", "según", "ser",
        "sera", "será", "si", "sí", "sido", "siempre", "sin", "sobre", "sois", "solo", "sólo",
        "somos", "son", "soy", "su", "sus", "tambien", "también", "tan", "tanto", "te", "teneis",
        "tenemos", "tener", "tengo", "ti", "tiene", "tienen", "toda", "todas", "todo", "todos",
        "tu", "tú", "tus", "tuve", "tuvo", "un", "una", "unas", "uno", "unos", "usted", "ustedes",
        "va", "vamos", "van", "vez", "ya", "yo", "asi", "así", "aqui", "aquí", "bien", "cada",
        "dia", "día", "entonces", "esta", "esto", "puede", "puedo", "solo", "ver",
    }),
}

REDACTED_SOURCES = [
    ("br", "pt", "google_play", C.BRASIL / "google_play_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
    ("br", "pt", "app_store", C.BRASIL / "app_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
    ("us", "en", "google_play", C.market_dir("us") / "google_play_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
    ("us", "en", "app_store", C.market_dir("us") / "app_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
    ("es", "es", "google_play", C.market_dir("es") / "google_play_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
    ("es", "es", "app_store", C.market_dir("es") / "app_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
    ("mx", "es", "google_play", C.market_dir("mx") / "google_play_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
    ("mx", "es", "app_store", C.market_dir("mx") / "app_store" / "reviews_para_ia" / "reviews_critical_redacted.csv"),
]


def clean_for_embedding(text):
    """Converte para minúsculas e remove marcadores de censura APENAS para embedding/c-TF-IDF."""
    s = "" if pd.isna(text) else str(text)
    s = REDACTION_MARKER_RE.sub(" ", s)
    return " ".join(s.lower().split())


def stopwords_for(group):
    if group in STOPWORDS:
        return STOPWORDS[group]
    return sorted(set().union(*STOPWORDS.values()))


def load_redacted_corpus(sources=None):
    """Carrega SOMENTE as cópias redigidas (passo 7) e gera review_id estável."""
    frames = []
    for market, lang_group, store, path in (sources or REDACTED_SOURCES):
        if not path.exists():
            raise SystemExit(f"Arquivo redigido ausente: {path}. Rode src/07_build_ai_share.py antes.")
        df = pd.read_csv(path, encoding="utf-8-sig", dtype={"at": str})
        if not df["app_mask_id"].astype(str).str.fullmatch(r"APP_\d{3}").all():
            raise SystemExit(f"{path}: encontrado app_mask_id fora do padrão APP_xxx.")
        df["market"] = market
        df["lang_group"] = lang_group
        df["store"] = store
        frames.append(df)
    full = pd.concat(frames, ignore_index=True)
    full["content"] = full["content"].fillna("").astype(str)
    full["text_embed"] = full["content"].map(clean_for_embedding)
    full = full.sort_values(
        ["market", "store", "app_mask_id", "at", "content"], kind="mergesort"
    ).reset_index(drop=True)
    full.insert(0, "review_id", [f"R{i:05d}" for i in range(1, len(full) + 1)])
    return full


def deduplicate_group(df):
    """Remove duplicatas exatas entre mercados distintos do mesmo idioma (ex.: ES e MX na Google Play).

    Dentro do mesmo mercado e loja, a deduplicação exata já ocorreu na Etapa 1 (sobre o texto
    antes da redação NER), evitando descartar relatos distintos que só ficaram iguais após a
    substituição de entidades por [NOME]/[APP]/[MARCA].
    """
    n_raw = int(len(df))
    if df["market"].nunique() > 1:
        out = df.drop_duplicates(
            subset=["lang_group", "store", "app_mask_id", "at", "score", "content"], keep="first"
        )
    else:
        out = df
    removed_dup = n_raw - int(len(out))
    # Descarta eventuais textos que ficaram vazios após remover marcadores de censura
    empty_after_strip = int((out["text_embed"].str.strip() == "").sum())
    out = out[out["text_embed"].str.strip() != ""].reset_index(drop=True)
    return out, {
        "n_raw_redacted": n_raw,
        "removed_cross_market_duplicates": int(removed_dup),
        "removed_empty_after_marker_strip": empty_after_strip,
        "n_input": int(len(out)),
    }


def compute_cv_numpy(topic_words_list, tokenized_docs, window_size=110):
    """Implementação fiel de c_v (Röder et al., 2015) em NumPy como fallback quando gensim não está disponível."""
    eps = 1e-12
    vocab = sorted({w for words in topic_words_list for w in words})
    if not vocab:
        return [None] * len(topic_words_list)
    word2idx = {w: i for i, w in enumerate(vocab)}
    n_vocab = len(vocab)
    # Contagem em janelas deslizantes (boolean sliding window)
    n_windows = 0
    word_count = np.zeros(n_vocab, dtype=np.float64)
    co_count = np.zeros((n_vocab, n_vocab), dtype=np.float64)
    for doc in tokenized_docs:
        if not doc:
            continue
        if len(doc) <= window_size:
            windows = [doc]
        else:
            windows = [doc[i:i + window_size] for i in range(len(doc) - window_size + 1)]
        for win in windows:
            n_windows += 1
            present = sorted({word2idx[w] for w in win if w in word2idx})
            if not present:
                continue
            for idx_a in present:
                word_count[idx_a] += 1.0
                for idx_b in present:
                    co_count[idx_a, idx_b] += 1.0
    if n_windows == 0:
        return [None] * len(topic_words_list)
    p_w = word_count / n_windows
    p_ij = co_count / n_windows

    scores = []
    for words in topic_words_list:
        idxs = [word2idx[w] for w in words if w in word2idx and word_count[word2idx[w]] > 0]
        if len(idxs) < 2:
            scores.append(None)
            continue
        # Matriz NPMI dentro do conjunto de palavras do tópico (segmentação S_one_set)
        sub_pij = p_ij[np.ix_(idxs, idxs)]
        sub_pw = p_w[idxs]
        denom = np.outer(sub_pw, sub_pw)
        num = np.log((sub_pij + eps) / denom)
        den = -np.log(sub_pij + eps)
        npmi = num / np.where(den == 0, eps, den)
        np.fill_diagonal(npmi, 1.0)
        # Vetor do conjunto completo = soma das linhas (gamma = 1)
        set_vec = npmi.sum(axis=0)
        set_norm = np.linalg.norm(set_vec)
        if set_norm == 0:
            scores.append(0.0)
            continue
        row_norms = np.linalg.norm(npmi, axis=1)
        cos = (npmi @ set_vec) / np.where(row_norms * set_norm == 0, eps, row_norms * set_norm)
        scores.append(round(float(np.mean(cos)), 4))
    return scores


def compute_cv_per_topic(topic_words_by_id, docs_embed, stop_words):
    """Calcula coerência c_v por tópico usando gensim (padrão) ou fallback Röder et al. (2015)."""
    sw = set(stop_words)
    tokenized_docs = [[t for t in TOKEN_RE.findall(d) if t not in sw] for d in docs_embed]
    topic_ids = sorted(topic_words_by_id.keys())
    try:
        from gensim.corpora.dictionary import Dictionary
        from gensim.models.coherencemodel import CoherenceModel

        dictionary = Dictionary(tokenized_docs)
        valid_ids, valid_words = [], []
        for tid in topic_ids:
            words = [w for w in topic_words_by_id[tid] if w in dictionary.token2id]
            if len(words) >= 2:
                valid_ids.append(tid)
                valid_words.append(words)
        cv_map = {tid: None for tid in topic_ids}
        if valid_words:
            cm = CoherenceModel(
                topics=valid_words,
                texts=tokenized_docs,
                dictionary=dictionary,
                coherence="c_v",
                processes=1,
            )
            per_topic = cm.get_coherence_per_topic()
            for tid, score in zip(valid_ids, per_topic):
                cv_map[tid] = round(float(score), 4) if score is not None and not math.isnan(score) else None
        return cv_map, "gensim"
    except ImportError:
        raw_words = [topic_words_by_id[tid] for tid in topic_ids]
        scores = compute_cv_numpy(raw_words, tokenized_docs)
        return dict(zip(topic_ids, scores)), "roder2015_numpy"


def select_representative_docs(df, embeddings, n_rep=N_REP_DOCS):
    """Seleciona até `n_rep` avaliações representativas por tópico (>= 0) por similaridade ao centroide."""
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    unit = embeddings / np.where(norms == 0, 1.0, norms)
    rep_rows = []
    for tid in sorted(t for t in df["topic"].unique() if t >= 0):
        idxs = np.where(df["topic"].values == tid)[0]
        centroid = unit[idxs].mean(axis=0)
        c_norm = np.linalg.norm(centroid)
        if c_norm > 0:
            centroid = centroid / c_norm
        sims = unit[idxs] @ centroid
        # Ordenação determinística: maior similaridade, maior probabilidade, menor review_id
        order = sorted(
            range(len(idxs)),
            key=lambda j: (-float(sims[j]), -float(df.iloc[idxs[j]]["probability"]), str(df.iloc[idxs[j]]["review_id"])),
        )[:n_rep]
        for rank, j in enumerate(order, 1):
            row = df.iloc[idxs[j]]
            rep_rows.append({
                "topic": int(tid),
                "rank": rank,
                "review_id": row["review_id"],
                "market": row["market"],
                "store": row["store"],
                "app_mask_id": row["app_mask_id"],
                "score": row["score"],
                "probability": round(float(row["probability"]), 4),
                "centroid_similarity": round(float(sims[j]), 4),
                "content": row["content"],
            })
    return pd.DataFrame(rep_rows)


def build_triage_table(topic_info_df, rep_df):
    """Prepara `triagem_topicos.csv` (Etapa 4), excluindo tópico -1 e com decisões vazias."""
    valid = topic_info_df[topic_info_df["topic"] >= 0].sort_values(["n", "topic"], ascending=[False, True])
    examples_by_topic = {}
    if not rep_df.empty:
        for tid, grp in rep_df.groupby("topic"):
            examples_by_topic[int(tid)] = grp.sort_values("rank")["content"].tolist()
    rows = []
    for r in valid.itertuples():
        ex = examples_by_topic.get(int(r.topic), [])
        rows.append({
            "topic": int(r.topic),
            "n": int(r.n),
            "palavras_chave": r.palavras_chave,
            "exemplo_1": ex[0] if len(ex) > 0 else "",
            "exemplo_2": ex[1] if len(ex) > 1 else "",
            "exemplo_3": ex[2] if len(ex) > 2 else "",
            "c_v": r.c_v,
            "decisao": "",
            "categoria_exclusao": "",
            "motivo": "",
        })
    return pd.DataFrame(rows)


def package_versions():
    pkgs = ["bertopic", "umap-learn", "hdbscan", "sentence-transformers", "scikit-learn", "gensim", "plotly", "numpy"]
    out = {"python": platform.python_version()}
    for p in pkgs:
        try:
            out[p] = md.version(p)
        except md.PackageNotFoundError:
            out[p] = "not_installed"
    return out


def run_group(group, df_raw, embedding_model, mode):
    from bertopic import BERTopic
    from hdbscan import HDBSCAN
    from sklearn.feature_extraction.text import CountVectorizer
    from umap import UMAP

    df, dedup_stats = deduplicate_group(df_raw)
    print(f"\n=== [{group}] {dedup_stats['n_raw_redacted']} redigidas -> {dedup_stats['n_input']} únicas "
          f"(dup entre mercados: {dedup_stats['removed_cross_market_duplicates']}) ===", flush=True)

    docs_embed = df["text_embed"].tolist()
    embeddings = embedding_model.encode(docs_embed, batch_size=64, show_progress_bar=False)
    embeddings = np.asarray(embeddings, dtype=np.float32)

    sw = stopwords_for(group)
    umap_model = UMAP(**UMAP_PARAMS)
    hdbscan_model = HDBSCAN(**HDBSCAN_PARAMS)
    vectorizer_model = CountVectorizer(stop_words=sw, token_pattern=TOKEN_RE.pattern)

    topic_model = BERTopic(
        embedding_model=embedding_model,
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        top_n_words=TOP_N_WORDS,
        nr_topics=None,
        calculate_probabilities=False,
        verbose=False,
    )
    topics, probs = topic_model.fit_transform(docs_embed, embeddings=embeddings)
    probs_arr = np.asarray(probs)
    if probs_arr.ndim == 2:
        probs_1d = probs_arr.max(axis=1)
    else:
        probs_1d = probs_arr

    df["topic"] = [int(t) for t in topics]
    df["probability"] = [round(float(p), 4) for p in probs_1d]

    topic_counts = Counter(df["topic"])
    valid_tids = sorted(t for t in topic_counts if t >= 0)
    topic_words_by_id = {
        tid: [w for w, _ in (topic_model.get_topic(tid) or [])[:TOP_N_WORDS]]
        for tid in valid_tids
    }
    cv_map, cv_backend = compute_cv_per_topic(topic_words_by_id, docs_embed, sw)

    info_rows = []
    if -1 in topic_counts:
        info_rows.append({"topic": -1, "n": int(topic_counts[-1]), "palavras_chave": "", "c_v": None})
    for tid in valid_tids:
        info_rows.append({
            "topic": int(tid),
            "n": int(topic_counts[tid]),
            "palavras_chave": ", ".join(topic_words_by_id[tid]),
            "c_v": cv_map.get(tid),
        })
    topic_info_df = pd.DataFrame(info_rows)
    rep_df = select_representative_docs(df, embeddings, n_rep=N_REP_DOCS)
    triage_df = build_triage_table(topic_info_df, rep_df)

    out_dir = TOPICS_ROOT / group
    out_dir.mkdir(parents=True, exist_ok=True)
    review_cols = [
        "review_id", "market", "store", "lang_group", "app_mask_id",
        "score", "lang", "at", "compound", "content", "topic", "probability",
    ]
    write_csv(df[[c for c in review_cols if c in df.columns]], out_dir / "review_topics.csv")
    write_csv(topic_info_df, out_dir / "topic_info.csv")
    write_csv(rep_df, out_dir / "representative_docs.csv")
    write_csv(triage_df, out_dir / "triagem_topicos.csv")

    html_files = {}
    if len(valid_tids) >= 3:
        try:
            topic_model.visualize_topics().write_html(str(out_dir / "intertopic_map.html"))
            html_files["intertopic_map"] = True
        except Exception as exc:
            print(f"  [aviso] intertopic_map falhou: {exc}", flush=True)
            html_files["intertopic_map"] = False
    else:
        html_files["intertopic_map"] = False
    if len(valid_tids) >= 2:
        try:
            topic_model.visualize_heatmap().write_html(str(out_dir / "similarity_matrix.html"))
            html_files["similarity_matrix"] = True
        except Exception as exc:
            print(f"  [aviso] similarity_matrix falhou: {exc}", flush=True)
            html_files["similarity_matrix"] = False
    else:
        html_files["similarity_matrix"] = False

    n_input = dedup_stats["n_input"]
    n_outliers = int(topic_counts.get(-1, 0))
    n3 = n_input - n_outliers
    small_tids = [tid for tid in valid_tids if topic_counts[tid] < MIN_TOPIC_SIZE_FILTER]
    small_reviews = int(sum(topic_counts[tid] for tid in small_tids))
    small_cvs = [cv_map[tid] for tid in small_tids if cv_map.get(tid) is not None]
    n4 = n3 - small_reviews
    all_cvs = [cv_map[tid] for tid in valid_tids if cv_map.get(tid) is not None]
    kept_tids = [tid for tid in valid_tids if topic_counts[tid] >= MIN_TOPIC_SIZE_FILTER]
    kept_cvs = [cv_map[tid] for tid in kept_tids if cv_map.get(tid) is not None]

    metrics = {
        "mode": mode,
        "group": group,
        "markets": sorted(df["market"].unique().tolist()),
        "stores": sorted(df["store"].unique().tolist()),
        **dedup_stats,
        "n_topics": int(len(valid_tids)),
        "n_outliers": n_outliers,
        "pct_outliers": round(100 * n_outliers / n_input, 2) if n_input else 0.0,
        "n3_after_outliers": int(n3),
        "small_clusters_lt_15": {
            "count": int(len(small_tids)),
            "reviews": small_reviews,
            "mean_c_v": round(float(np.mean(small_cvs)), 4) if small_cvs else None,
        },
        "n4_after_small_clusters": int(n4),
        "n_topics_ge_15": int(len(kept_tids)),
        "c_v_mean_all_topics": round(float(np.mean(all_cvs)), 4) if all_cvs else None,
        "c_v_median_all_topics": round(float(np.median(all_cvs)), 4) if all_cvs else None,
        "c_v_mean_topics_ge_15": round(float(np.mean(kept_cvs)), 4) if kept_cvs else None,
        "c_v_min": round(float(min(all_cvs)), 4) if all_cvs else None,
        "c_v_max": round(float(max(all_cvs)), 4) if all_cvs else None,
        "c_v_backend": cv_backend,
        "html_visualizations": html_files,
        "hyperparameters": {
            "embedding_model": EMBEDDING_MODEL,
            "umap": UMAP_PARAMS,
            "hdbscan": HDBSCAN_PARAMS,
            "vectorizer": {
                "stop_words_lang": group if group in STOPWORDS else "pt+en+es",
                "stop_words_count": len(sw),
                "token_pattern": TOKEN_RE.pattern,
            },
            "top_n_words": TOP_N_WORDS,
            "nr_topics": None,
            "seed": SEED,
        },
        "versions": package_versions(),
    }
    update_metrics(f"11_bertopic_{group}", metrics)
    print(
        f"[{group}] {n_input} docs -> {len(valid_tids)} tópicos | "
        f"outliers (-1): {n_outliers} ({metrics['pct_outliers']}%) -> N3={n3} | "
        f"clusters <15: {len(small_tids)} ({small_reviews} docs) -> N4={n4} | "
        f"c_v média={metrics['c_v_mean_all_topics']} ({cv_backend})",
        flush=True,
    )
    return metrics


def main():
    if C.MARKET != "br":
        raise SystemExit("Rode este script sem MARKET (ou MARKET=br).")
    ap = argparse.ArgumentParser()
    ap.add_argument("--juntos", action="store_true", help="modela todos os idiomas em conjunto")
    ap.add_argument("--idiomas", nargs="+", choices=["pt", "en", "es"], default=["pt", "en", "es"],
                    help="idiomas a modelar no modo separado (padrão: pt en es)")
    args = ap.parse_args()

    from sentence_transformers import SentenceTransformer

    corpus = load_redacted_corpus()
    print(f"Carregando modelo de embeddings: {EMBEDDING_MODEL}", flush=True)
    embedding_model = SentenceTransformer(EMBEDDING_MODEL)

    if args.juntos:
        run_group("juntos", corpus, embedding_model, mode="juntos")
    else:
        for lang in args.idiomas:
            sub = corpus[corpus["lang_group"] == lang].copy()
            run_group(lang, sub, embedding_model, mode="por_idioma")


if __name__ == "__main__":
    main()
