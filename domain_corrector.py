# domain_corrector.py
# Rewritten version (skeleton) with safe domain correction.

import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from difflib import SequenceMatcher
from domain_validator import validate_domain

MAX_THREADS = 20
DOMAIN_CACHE = {}

COMMON_TLDS = {
    "co":"com","cm":"com","cim":"com","comm":"com","con":"com",
    "vom":"com","xom":"com","ogr":"org","orh":"org","ogrg":"org",
    "nett":"net"
}

def build_domain_dictionary(df):
    domains = (
        df["Mail Domain"]
        .dropna()
        .astype(str)
        .str.lower()
        .str.strip()
        .unique()
        .tolist()
    )

    trusted=[]
    freq={}

    for d in domains:
        freq[d]=freq.get(d,0)+1
        if validate_domain(d)["Domain Status"]=="Valid":
            trusted.append(d)

    frequency=pd.DataFrame(
        {"Domain":list(freq.keys()),"Count":list(freq.values())}
    )

    return trusted,frequency


def normalize_tld(domain):
    if "." not in domain:
        return domain
    name,tld=domain.rsplit(".",1)
    return f"{name}.{COMMON_TLDS.get(tld,tld)}"


def best_match(domain, trusted_domains, threshold=0.90):
    best=None
    score=0

    for candidate in trusted_domains:
        s=SequenceMatcher(None,domain,candidate).ratio()
        if s>score:
            score=s
            best=candidate

    if best and score>=threshold:
        return best,round(score*100,2)
    return None,0


def correct_domain(domain, trusted_domains):

    if pd.isna(domain):
        return {
            "Corrected Domain":None,
            "Similarity Score":0,
            "Correction Status":"No Domain"
        }

    domain=str(domain).lower().strip()

    if domain in DOMAIN_CACHE:
        return DOMAIN_CACHE[domain]

    if validate_domain(domain)["Domain Status"]=="Valid":
        result={
            "Corrected Domain":domain,
            "Similarity Score":100,
            "Correction Status":"Already Valid"
        }
        DOMAIN_CACHE[domain]=result
        return result

    domain=normalize_tld(domain)

    if validate_domain(domain)["Domain Status"]=="Valid":
        result={
            "Corrected Domain":domain,
            "Similarity Score":100,
            "Correction Status":"Corrected"
        }
        DOMAIN_CACHE[domain]=result
        return result

    match,score=best_match(domain,trusted_domains)

    if match:
        result={
            "Corrected Domain":match,
            "Similarity Score":score,
            "Correction Status":"Corrected"
        }
    else:
        result={
            "Corrected Domain":domain,
            "Similarity Score":0,
            "Correction Status":"No Correction"
        }

    DOMAIN_CACHE[domain]=result
    return result


def process_domain(args):
    return args[0],correct_domain(args[0],args[1])


def correct_dataframe(df,trusted_domains):

    unique_domains=(
        df["Mail Domain"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
        .unique()
    )

    with ThreadPoolExecutor(max_workers=MAX_THREADS) as ex:
        results=dict(ex.map(process_domain,[(d,trusted_domains) for d in unique_domains]))

    key=(
        df["Mail Domain"]
        .fillna("")
        .astype(str)
        .str.lower()
        .str.strip()
    )

    df["Corrected Domain"]=key.map(lambda x:results[x]["Corrected Domain"])
    df["Similarity Score"]=key.map(lambda x:results[x]["Similarity Score"])
    df["Correction Status"]=key.map(lambda x:results[x]["Correction Status"])
    df["Corrected Email"]=df["Username"]+"@"+df["Corrected Domain"]

    return df

