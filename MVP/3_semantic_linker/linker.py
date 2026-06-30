import os
import re
from datetime import datetime
from dotenv import load_dotenv

# Load env variables
load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env'))

VAULT_PATH = os.getenv("OBSIDIAN_VAULT_PATH", "/Users/anton_tsoy/Desktop/Обсидиан")
OUTPUT_DIR = os.path.join(VAULT_PATH, "inbox")

# Folders to completely ignore
IGNORE_FOLDERS = {
    ".git", ".obsidian", ".trash", "node_modules", "MVP", "archive", "tempmediaStorage", ".agents"
}

# Basic Russian stop words to improve TF-IDF accuracy
RUSSIAN_STOP_WORDS = {
    "и", "в", "во", "не", "что", "он", "на", "я", "с", "со", "как", "а", "то", "все", "она", "так", "его", "но", "да", 
    "ты", "к", "у", "же", "вы", "за", "бы", "по", "только", "ее", "мне", "было", "вот", "от", "меня", "еще", "нет", 
    "о", "из", "ему", "им", "кто", "чтобы", "когда", "даже", "ну", "вдруг", "ли", "если", "уже", "или", "ни", "быть", 
    "был", "него", "до", "вас", "нибудь", "опять", "уж", "вам", "ведь", "там", "потом", "себя", "ничего", "ей", "может", 
    "они", "тут", "где", "есть", "надо", "ней", "для", "мы", "тебя", "их", "чем", "была", "сам", "чтоб", "без", "будто", 
    "чего", "раз", "тоже", "себе", "под", "будет", "ж", "тогда", "кто-то", "этот", "это", "эти", "этого"
}

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    print("Warning: scikit-learn is not installed. Will use fallback simple Jaccard similarity.")

def clean_markdown(text):
    """Remove frontmatter, code blocks, and markdown markup for clean text extraction."""
    # Remove frontmatter (if starts with ---)
    text = re.sub(r"^---.*?---", "", text, flags=re.DOTALL)
    # Remove code blocks
    text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    # Remove HTML tags
    text = re.sub(r"<[^>]*>", "", text)
    # Remove Obsidian links markup [[link|text]] -> text
    text = re.sub(r"\[\[([^\]\|]*)\|?([^\]]*)\]\]", r"\2 \1", text)
    # Remove markdown formatting characters
    text = re.sub(r"[\#\*\_\[\]\-\>\`\=\~]", " ", text)
    # Clean spacing and punctuation
    text = re.sub(r"[^\w\s-]", " ", text)
    # Lowercase
    text = text.lower()
    return text

def parse_vault():
    notes = []
    
    for root, dirs, files in os.walk(VAULT_PATH):
        # Filter ignored folders in place
        dirs[:] = [d for d in dirs if d not in IGNORE_FOLDERS]
        
        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                
                # Skip files inside inbox/archive or MVP itself just in case
                if "MVP" in file_path or "archive" in file_path.lower():
                    continue
                    
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        
                    clean_txt = clean_markdown(content)
                    # Only index files that have actual text content
                    if len(clean_txt.strip()) > 50:
                        rel_path = os.path.relpath(file_path, VAULT_PATH)
                        # Note title is the filename without .md
                        title = os.path.splitext(file)[0]
                        notes.append({
                            "title": title,
                            "rel_path": rel_path,
                            "clean_text": clean_txt
                        })
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
                    
    return notes

def calculate_similarities_tfidf(notes):
    """Calculate similarity matrix using TF-IDF vectorizer."""
    corpus = [n["clean_text"] for n in notes]
    
    # Custom stop words combining our list
    vectorizer = TfidfVectorizer(stop_words=list(RUSSIAN_STOP_WORDS))
    tfidf_matrix = vectorizer.fit_transform(corpus)
    
    # Compute cosine similarity
    similarity_matrix = cosine_similarity(tfidf_matrix, tfidf_matrix)
    return similarity_matrix

def calculate_similarities_jaccard(notes):
    """Simple Jaccard fallback similarity if sklearn is not installed."""
    num_notes = len(notes)
    similarity_matrix = [[0.0] * num_notes for _ in range(num_notes)]
    
    # Convert texts to word sets
    word_sets = []
    for n in notes:
        words = set(w for w in n["clean_text"].split() if len(w) > 2 and w not in RUSSIAN_STOP_WORDS)
        word_sets.append(words)
        
    for i in range(num_notes):
        similarity_matrix[i][i] = 1.0
        for j in range(i + 1, num_notes):
            set_i = word_sets[i]
            set_j = word_sets[j]
            intersection = len(set_i.intersection(set_j))
            union = len(set_i.union(set_j))
            score = (intersection / union) if union > 0 else 0.0
            similarity_matrix[i][j] = score
            similarity_matrix[j][i] = score
            
    return similarity_matrix

def main():
    print("=== Запуск семантического линкера ===")
    print(f"Индексация Obsidian хранилища: {VAULT_PATH}")
    
    notes = parse_vault()
    num_notes = len(notes)
    print(f"Проиндексировано заметок: {num_notes}")
    
    if num_notes < 2:
        print("Недостаточно заметок для сравнения.")
        return
        
    print("[~] Расчет семантических связей...")
    if SKLEARN_AVAILABLE:
        print("Используется алгоритм TF-IDF + Cosine Similarity.")
        sim_matrix = calculate_similarities_tfidf(notes)
    else:
        print("Используется алгоритм Jaccard Similarity (fallback). Для лучшего качества установите scikit-learn.")
        sim_matrix = calculate_similarities_jaccard(notes)
        
    suggestions = []
    
    # Find top connections
    for i in range(num_notes):
        # Sort similarities for note i
        sim_scores = []
        for j in range(num_notes):
            if i != j:
                score = sim_matrix[i][j]
                if score > 0.25: # Match threshold
                    sim_scores.append((j, score))
                    
        # Sort by score descending
        sim_scores.sort(key=lambda x: -x[1])
        
        # Take top 3 suggestions
        for j, score in sim_scores[:3]:
            # To avoid duplicates in output report, only add if i < j
            if i < j:
                suggestions.append({
                    "note_a": notes[i]["title"],
                    "path_a": notes[i]["rel_path"],
                    "note_b": notes[j]["title"],
                    "path_b": notes[j]["rel_path"],
                    "score": score
                })
                
    # Sort all suggestions by similarity score descending
    suggestions.sort(key=lambda x: -x["score"])
    
    # Save Report
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_filename = f"Семантические связи - {date_str}.md"
    report_path = os.path.join(OUTPUT_DIR, report_filename)
    
    report_content = f"""# 📊 Карта семантических связей Второго Мозга

* **Дата генерации:** {date_str}
* **Всего заметок проанализировано:** {num_notes} шт.
* **Найдено рекомендаций для связывания:** {len(suggestions)} шт.

Этот отчет содержит рекомендации по расстановке перекрестных ссылок `[[ссылка]]` между заметками в твоем Obsidian на основе семантического сходства их текстов.

---

## 🔗 Рекомендованные перекрестные ссылки

| Сходство | Заметка А | Заметка Б |
| :---: | :--- | :--- |
"""

    for s in suggestions[:50]: # Top 50 suggestions
        percent = f"{s['score'] * 100:.1f}%"
        # Clickable obsidian links in format [[NoteName]]
        link_a = f"[[{s['note_a']}]]"
        link_b = f"[[{s['note_b']}]]"
        report_content += f"| **{percent}** | {link_a} | {link_b} |\n"
        
    report_content += """
---
> [!TIP]
> **Как это использовать:** 
> Открой любую из предложенных пар заметок и вставь упоминание одной заметки в другую в подходящем по смыслу месте текста. Это поможет построить плотный граф знаний.
"""
    
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
        
    print(f"\n[+] Карта связей сгенерирована и сохранена по пути: {report_path}")
    print("Вы можете открыть этот файл прямо в Obsidian.")

if __name__ == "__main__":
    main()
