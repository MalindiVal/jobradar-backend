

def score_offer(offer: dict, profile) -> tuple[int, str]:
    title = (offer.get("title") or "").lower()
    location = (offer.get("location") or "").lower()
    text = " ".join([title, offer.get("description") or "", " ".join(offer.get("skills") or [])]).lower()
    keywords = [str(x).lower() for x in (profile.keywords or [])]
    skills = [str(x).lower() for x in (profile.skills or [])]
    locations = [str(x).lower() for x in (profile.locations or [])]
    keyword_hits = [x for x in keywords if x in title]
    skill_hits = [x for x in skills if x in text]
    location_hit = any(x in location for x in locations)
    duration_hit = offer.get("duration_months") == profile.duration_months
    score = min(35, round(35 * len(set(skill_hits)) / max(1, min(5, len(skills)))))
    score += 25 if keyword_hits else 8 if any(x in title for x in ["développeur", "ingenieur", "ingénieur"]) else 0
    score += 15 if location_hit else 0
    score += 15 if duration_hit else 0
    score += 10 if (offer.get("contract_type") or "").lower() == profile.contract_type.lower() else 0
    reasons = []
    if skill_hits: reasons.append("Compétences : " + ", ".join(sorted(set(skill_hits))[:8]))
    if keyword_hits: reasons.append("Métier recherché : " + ", ".join(keyword_hits))
    if location_hit: reasons.append("Localisation recherchée")
    if duration_hit: reasons.append("Durée compatible")
    return min(100, score), ". ".join(reasons) or "Correspondance limitée avec le profil."
