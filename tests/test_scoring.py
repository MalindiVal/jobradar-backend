from types import SimpleNamespace
from app.services.scoring import score_offer

def test_matching_offer_scores_higher():
    profile = SimpleNamespace(
        keywords=["développeur full stack"], skills=["React", "Python", "SQL"],
        locations=["Dijon"], duration_months=36, contract_type="Alternance"
    )
    matching = {"title": "Alternant Développeur Full Stack", "location": "Dijon",
                "duration_months": 36, "contract_type": "Alternance",
                "description": "React Python SQL"}
    unrelated = {"title": "Assistant commercial", "location": "Lyon",
                 "duration_months": 12, "contract_type": "CDI", "description": ""}
    assert score_offer(matching, profile)[0] > score_offer(unrelated, profile)[0]
