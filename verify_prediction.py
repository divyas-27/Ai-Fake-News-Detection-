import sys
import os
root = r'C:\Users\venu gopal\OneDrive\AI FAKE NEWS DETECTION\fake news detection'
sys.path.append(root)
from model import predict_news, pac_model, tfidf_vectorizer
examples = [
    'India to Replace All Currency Notes with Digital Coins Starting Next Week',
    'Government will give ₹10 lakh to every citizen tomorrow',
    'Earth will stop rotating next week',
    'The World Health Organization reported that cases of seasonal flu are rising in several regions.',
    'Company launches a new smartphone model with advanced features.'
]
print('model files:', os.listdir(os.path.join(root,'models')))
for text in examples:
    label, confidence, reasons = predict_news(text, pac_model, tfidf_vectorizer)
    print('\nTEXT:', text)
    print('LABEL:', label)
    print('CONFIDENCE:', confidence)
    print('REASONS:', reasons)
