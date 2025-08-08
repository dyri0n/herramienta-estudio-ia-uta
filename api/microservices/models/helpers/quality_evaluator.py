import spacy
import re
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import language_tool_python

class QualityEvaluator:
    def __init__(self):
        self.nlp = spacy.load("en_core_web_sm")
        self.tool = language_tool_python.LanguageTool('en-US')

    # --- Relevance ---
    def shared_entities(self, context, answer):
        doc1 = self.nlp(context)
        doc2 = self.nlp(answer)
        entities1 = {ent.text.lower() for ent in doc1.ents}
        entities2 = {ent.text.lower() for ent in doc2.ents}
        if not entities1:
            return 0.5
        return len(entities1 & entities2) / len(entities1)

    def tfidf_similarity(self, context, answer):
        vect = TfidfVectorizer().fit([context, answer])
        tfidf = vect.transform([context, answer])
        score = cosine_similarity(tfidf.getrow(0), tfidf.getrow(1))[0][0]
        return min(score, 1.0)


    def score_relevance(self, context, answer):
        entity_score = self.shared_entities(context, answer)
        tfidf_score = self.tfidf_similarity(context, answer)
        return (entity_score + tfidf_score) / 2

    # --- Accuracy ---
    def keyword_overlap(self, question, answer):
        stopwords = {"what", "which", "how", "where", "why", "is", "are", "was", "the", "a", "an", "of", "to", "in"}
        q_words = set(question.lower().split()) - stopwords
        a_words = set(answer.lower().split())
        if not q_words:
            return 0.5
        match = q_words & a_words
        return len(match) / len(q_words)

    def score_accuracy(self, question, answer):
        return min(self.keyword_overlap(question, answer), 1.0)

    # --- Coherence ---
    def correct_punctuation(self, answer):
        return answer[0].isupper() and answer.strip().endswith(".")

    def has_repetitions(self, answer):
        tokens = answer.lower().split()
        return any(tokens[i] == tokens[i+1] for i in range(len(tokens)-1))

    def grammar_errors(self, answer):
        errors = self.tool.check(answer)
        return len(errors)

    def score_coherence(self, answer):
        p_score = 1.0 if self.correct_punctuation(answer) else 0.5
        rep_score = 0.0 if self.has_repetitions(answer) else 1.0
        err_score = max(0.0, 1.0 - self.grammar_errors(answer) / 5.0)
        return (p_score + rep_score + err_score) / 3.0

    # --- Final Evaluation ---
    def evaluate(self, context, question, answer):
        relevance = self.score_relevance(context, answer)
        accuracy = self.score_accuracy(question, answer)
        coherence = self.score_coherence(answer)

        return {
            "relevance": round(relevance, 3),
            "accuracy": round(accuracy, 3),
            "coherence": round(coherence, 3)
        }
    
    # --- Average quality score ---
    def get_quality_of(self, context, question, answer):
        scores = self.evaluate(context, question, answer)
        average_score = sum(scores.values()) / 3
        return round(average_score, 3)
