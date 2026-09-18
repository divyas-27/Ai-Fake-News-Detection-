import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer, ENGLISH_STOP_WORDS
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
import joblib
import os
import re
import warnings
from nltk.stem import PorterStemmer

stemmer = PorterStemmer()
stop_words = ENGLISH_STOP_WORDS

# Suppress scikit-learn version compatibility warnings
warnings.filterwarnings('ignore', category=UserWarning, message='.*Trying to unpickle estimator.*')

MODEL_VERSION = 2

# Expanded training dataset with clearer real and fake language patterns.
training_examples = [
    ("Local hospital opens a new pediatric wing for children.", 0),
    ("Official weather forecast predicts rain tomorrow afternoon.", 0),
    ("City council approves new park for families and children.", 0),
    ("Scientists verify the composition of a new mineral discovery.", 0),
    ("New study shows benefits of daily exercise for heart health.", 0),
    ("Stock market reaches an all-time high after positive economic data.", 0),
    ("Company launches a new smartphone model with advanced features.", 0),
    ("Government announces a new tax policy for small businesses.", 0),
    ("Economic growth reported in Q4 with 2.5% increase.", 0),
    ("Climate change affects global weather patterns worldwide.", 0),
    ("University opens a new research lab for medical studies.", 0),
    ("Police solve a major robbery case in downtown area.", 0),
    ("Local school wins national science award for innovation.", 0),
    ("New vaccine developed for a common cold strain.", 0),
    ("Agricultural exports rise after a strong harvest season.", 0),
    ("Researchers publish a study on renewable energy solutions.", 0),
    ("Health officials issue a flu prevention guide for winter.", 0),
    ("Transportation service expands bus routes in the city.", 0),
    ("Museum opens an exhibition of ancient artifacts.", 0),
    ("Space agency confirms successful satellite launch.", 0),
    ("Federal government passes new environmental protection law.", 0),
    ("Medical researchers find cure for rare genetic disease.", 0),
    ("Technology company announces breakthrough in quantum computing.", 0),
    ("International peace treaty signed by world leaders.", 0),
    ("New bridge construction completed ahead of schedule.", 0),
    ("The Federal Reserve announced a rate cut as inflation eased.", 0),
    ("Scientists at the University of Cambridge said regular exercise improves heart health.", 0),
    ("Officials confirmed that the city will expand public transit next year.", 0),
    ("The report from the health ministry said vaccine availability is improving.", 0),
    ("A panel of economists said the latest data points to steady growth.", 0),
    ("A new study published by researchers found that sleep improves memory.", 0),
    ("The court ruled that the new policy will take effect next month.", 0),
    ("The company said it will open a new factory in the region next spring.", 0),
    ("The police department announced that investigators arrested two suspects in the burglary case.", 0),
    ("The mayor said the city will begin repair work on the bridge next week.", 0),
    ("According to the latest census data, the population of the region grew by 3 percent.", 0),
    ("Officials said the new water treatment plant will improve supply in the district.", 0),
    ("The health ministry reported that influenza cases declined after the vaccination campaign.", 0),
    ("A university team said its experiment confirmed the results of the earlier study.", 0),
    ("Aliens have landed in New York City and taken over the government.", 1),
    ("Celebrity spotted with three heads in Hollywood.", 1),
    ("Man claims to have invented a time machine that travels to the future.", 1),
    ("Cats can now speak English fluently after secret experiments.", 1),
    ("Zombies rise from the dead in a small town in Texas.", 1),
    ("Unicorns found in the Amazon rainforest by explorers.", 1),
    ("Moon landing was actually filmed in Hollywood studios.", 1),
    ("Bigfoot captured on video in a national park.", 1),
    ("Elvis Presley seen alive in a grocery store in Las Vegas.", 1),
    ("Shocking secret reveals Hollywood clones of celebrities.", 1),
    ("Fake news claims the president can fly and has superpowers.", 1),
    ("Hoax report says the ocean turned green overnight globally.", 1),
    ("Conspiracy claims the Earth is flat and covered by an ice wall.", 1),
    ("Miracle cure promises to heal any disease instantly.", 1),
    ("Clickbait headline says you won't believe what happened next.", 1),
    ("Fake news article says dinosaurs are alive today in Africa.", 1),
    ("False claim says the moon is made of cheese.", 1),
    ("Report says a politician secretly owns a spaceship.", 1),
    ("Story claims a secret clone army is controlling the news.", 1),
    ("News says a celebrity discovered a real unicorn in her backyard.", 1),
    ("Online rumors claim the city is haunted by ghosts.", 1),
    ("Sensational story about aliens building pyramids in Egypt.", 1),
    ("Fake report claims vaccines cause people to become robots.", 1),
    ("Conspiracy theory says the government hides alien technology.", 1),
    ("Hoax article claims scientists found life on Mars yesterday.", 1),
    ("False news says the president declared martial law secretly.", 1),
    ("Clickbait story about a man who can talk to animals.", 1),
    ("Fake claim that the internet will be shut down next week.", 1),
    ("Rumors spread about a secret society controlling world events.", 1),
    ("Sensational headline about a city that disappeared overnight.", 1),
    ("Breaking news says the government is hiding a time travel program.", 1),
    ("A shocking video supposedly proves that the moon landing was staged.", 1),
    ("The article claimed that a secret committee is controlling the weather from a hidden base.", 1),
    ("A viral post said that a celebrity was spotted in a secret underground city.", 1),
    ("The report claimed that scientists discovered a cure for aging overnight.", 1),
    ("A conspiracy website said the vaccine contains hidden microchips.", 1),
    ("The story claimed that the government secretly replaced the moon with a hologram.", 1),
    ("The headline warned that the internet will shut down in 24 hours.", 1),
    ("An anonymous source said the president is secretly a robot.", 1),
    ("Breaking news says aliens landed in New York and the government is hiding it.", 1),
    ("The article claims the moon landing was faked in a Hollywood studio.", 1),
    ("Officials confirmed that the city will open a new transit line next month.", 0),
    ("A panel of doctors announced a new study showing lower blood pressure after a simple diet change.", 0),
    ("The government released a statement confirming tax reforms and budget measures.", 0),
]


def preprocess_text(text):
    """Normalize text consistently for both training and prediction."""
    if not isinstance(text, str):
        text = str(text)

    text = text.lower()
    text = re.sub(r'<[^>]+>', ' ', text)
    text = re.sub(r'http\S+|www\.[^\s]+', ' ', text)
    text = re.sub(r'\d+', ' ', text)
    text = re.sub(r'[^a-z\s]', ' ', text)
    text = re.sub(r'\s+', ' ', text).strip()

    tokens = [word for word in text.split() if word not in stop_words]
    stems = [stemmer.stem(word) for word in tokens]
    return ' '.join(stems)


def heuristic_prediction(text):
    """Use lightweight heuristics to catch obvious fake claims before falling back to the model."""
    if not isinstance(text, str) or not text.strip():
        return None

    normalized_text = re.sub(r'[^a-z\s]', ' ', text.lower())
    suspicious_terms = [
        'alien', 'aliens', 'secretly', 'robot', 'hoax', 'rumor', 'conspir', 'fake', 'unicorn',
        'ghost', 'zombi', 'shocking', 'hidden', 'mystery', 'viral', 'moon', 'hollywood',
        'studio', 'superpower', 'time travel', 'spacecraft', 'microchip', 'anonymous source',
        'anonymous', 'source'
    ]
    real_terms = [
        'official', 'confirmed', 'announced', 'study', 'research', 'according', 'policy',
        'hospital', 'school', 'police', 'court', 'government', 'econom', 'vaccine', 'minister',
        'data', 'public', 'transit', 'budget', 'measure'
    ]

    suspicious_hits = sum(1 for term in suspicious_terms if term in normalized_text)
    real_hits = sum(1 for term in real_terms if term in normalized_text)

    if suspicious_hits >= 2 and suspicious_hits >= real_hits:
        return 'Fake', 0.95, 'Suspicious wording patterns strongly suggest a fake claim.'
    if real_hits >= 2 and real_hits > suspicious_hits:
        return 'Real', 0.93, 'The wording appears consistent with a factual or official report.'
    return None


def train_model():
    """Train the fake news detection model with consistent preprocessing."""
    df = pd.DataFrame(training_examples, columns=['text', 'label'])
    df['text'] = df['text'].apply(preprocess_text)

    x_train, x_test, y_train, y_test = train_test_split(
        df['text'], df['label'], test_size=0.25, random_state=42, stratify=df['label']
    )

    tfidf_vectorizer = TfidfVectorizer(
        stop_words='english',
        max_df=0.95,
        min_df=1,
        ngram_range=(1, 2),
        max_features=6000,
        sublinear_tf=True
    )

    tfidf_train = tfidf_vectorizer.fit_transform(x_train)
    tfidf_test = tfidf_vectorizer.transform(x_test)

    classifier = LogisticRegression(
        max_iter=4000,
        class_weight='balanced',
        solver='liblinear',
        random_state=42
    )
    classifier.fit(tfidf_train, y_train)

    y_pred = classifier.predict(tfidf_test)
    score = accuracy_score(y_test, y_pred)
    print(f'Accuracy: {round(score * 100, 2)}%')
    print('Classification Report:')
    print(classification_report(y_test, y_pred, target_names=['Real', 'Fake']))

    model_dir = 'models'
    if not os.path.exists(model_dir):
        os.makedirs(model_dir)

    joblib.dump(classifier, os.path.join(model_dir, 'pac_model.pkl'))
    joblib.dump(tfidf_vectorizer, os.path.join(model_dir, 'tfidf_vectorizer.pkl'))
    joblib.dump(classifier, os.path.join(model_dir, 'model.pkl'))
    joblib.dump(tfidf_vectorizer, os.path.join(model_dir, 'vectorizer.pkl'))
    with open(os.path.join(model_dir, 'model_version.txt'), 'w', encoding='utf-8') as handle:
        handle.write(str(MODEL_VERSION))

    return classifier, tfidf_vectorizer


def load_model():
    """Load the saved trained model and vectorizer if available, otherwise train them."""
    model_candidates = [os.path.join('models', 'model.pkl'), os.path.join('models', 'pac_model.pkl')]
    vectorizer_candidates = [os.path.join('models', 'vectorizer.pkl'), os.path.join('models', 'tfidf_vectorizer.pkl')]
    version_path = os.path.join('models', 'model_version.txt')

    model_path = next((p for p in model_candidates if os.path.exists(p)), None)
    vectorizer_path = next((p for p in vectorizer_candidates if os.path.exists(p)), None)

    if model_path and vectorizer_path and os.path.exists(version_path):
        try:
            with open(version_path, 'r', encoding='utf-8') as handle:
                saved_version = int(handle.read().strip())
            if saved_version == MODEL_VERSION:
                pac = joblib.load(model_path)
                tfidf_vectorizer = joblib.load(vectorizer_path)
                return pac, tfidf_vectorizer
        except Exception as exc:
            print(f'Model load failed: {exc}. Training new model...')

    print('Saved model is outdated or missing; training a new model now...')
    return train_model()


def predict_news(text, pac, tfidf_vectorizer):
    """Predict if news is fake or real using heuristics and the trained model."""
    heuristic_result = heuristic_prediction(text)
    if heuristic_result:
        return heuristic_result

    cleaned_text = preprocess_text(text)

    try:
        tfidf_input = tfidf_vectorizer.transform([cleaned_text])
        prediction = pac.predict(tfidf_input)[0]

        if hasattr(pac, 'predict_proba'):
            proba = pac.predict_proba(tfidf_input)[0]
            confidence = float(max(proba))
        else:
            confidence = 0.7

        label = 'Real' if int(prediction) == 0 else 'Fake'
        if confidence < 0.7:
            reasons = "Low Confidence - Please verify this news from trusted sources."
        else:
            reasons = (
                "Model analysis indicates this news is likely real."
                if label == 'Real'
                else "Model analysis indicates this news is likely fake."
            )

        return label, confidence, reasons

    except Exception:
        return 'Real', 0.5, "Fallback detection used due to an internal processing error."


# Load or train the model when the module is imported
pac_model, tfidf_vectorizer = load_model()