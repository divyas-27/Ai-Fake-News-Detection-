from model import predict_news, pac_model, tfidf_vectorizer


def test_obvious_fake_claims_are_flagged_as_fake():
    label, confidence, _ = predict_news(
        "An anonymous source said the president is secretly a robot.",
        pac_model,
        tfidf_vectorizer,
    )

    assert label == "Fake"
    assert confidence >= 0.7
