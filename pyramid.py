from db import Summary


def get_pyramid(session, model_id):
    summaries = session.query(Summary).filter_by(model_id=model_id)\
        .order_by(Summary.tier.desc(), Summary.start_timestamp.desc()).all()
    
    by_tier = {}
    for s in summaries:
        by_tier.setdefault(s.tier, []).append(s)
    return by_tier
