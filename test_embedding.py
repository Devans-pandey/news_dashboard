from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

print("Loading model...")
model = SentenceTransformer('all-MiniLM-L6-v2')

text1 = "India launches strike on Pakistan border"
text2 = "Cross-border attack by India reported"
text3 = "India sends medical aid to Iran"

emb1 = model.encode(text1)
emb2 = model.encode(text2)
emb3 = model.encode(text3)

sim12 = cosine_similarity([emb1], [emb2])[0][0]
sim13 = cosine_similarity([emb1], [emb3])[0][0]

print("\nSimilarity (same topic):", sim12)
print("Similarity (different topic):", sim13)