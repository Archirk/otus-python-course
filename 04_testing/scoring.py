import hashlib
import json


def get_score(store, phone, email, birthday=None, gender=None, first_name=None, last_name=None):
    key_parts = [
        first_name or "",
        last_name or "",
        phone or "",
        birthday if birthday is not None else ""
        #.strftime("%Y%m%d") if birthday is not None else "",
        #  1 - According to task valid dateformat is %d.%m.%Y
        #  2 - There is no mention in task to store date as datetime. And all birthday validation goes with checking
        # string like date.
    ]
    key_parts = [str(i) for i in key_parts]
    key = "uid:" + hashlib.md5("".join(key_parts)).hexdigest()
    # try get from cache,
    # fallback to heavy calculation in case of cache miss
    score = store.cache_get(key) or 0
    if score:
        return float(score)
    if phone:
        score += 1.5
    if email:
        score += 1.5
    if birthday and gender:
        score += 1.5
    if first_name and last_name:
        score += 0.5
    # cache for 60 minutes
    store.cache_set(key, score, 60 * 60)
    return score


def get_interests(store, cid):
    r = store.get("i:%s" % cid)
    return json.loads(r) if r else []
