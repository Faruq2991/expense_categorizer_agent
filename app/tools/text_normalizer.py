import re

def normalize_text(text: str) -> str:
    """
    Normalizes expense descriptions by:
    - Converting to lowercase.
    - Removing common noise (e.g., 'POS TRXN', 'USD', currency symbols).
    - Replacing common abbreviations or variations with a standard form.
    - Removing extra whitespace.
    """
    text = text.lower()

    # Remove common noise patterns
    text = re.sub(r'pos trxn|usd|ghs|kes|eur|gbp|jpy|aud|cad|chf|cny|sek|nzd|mxn|sgd|hkd|nok|krw|try|rub|inr|brl|zar|dkk|pln|thb|myr|php|idr|czk|huf|ils|clp|aed|cop|sar|twd|vnd|uah|ron|egp|ngn|kwd|bhd|omr|qtr|bgn|hrk|isk|mdl|mkd|rsd|sll|srd|syp|tjs|tmt|uzs|xaf|xcd|xof|xpf|yer|zmw|zwl', '', text)
    text = re.sub(r'\b(?:momo|mobile money)\b', 'mobile_money', text)
    text = re.sub(r'\b(?:airtel|vodafone|mtn|glo)\b', 'telecom', text)
    text = re.sub(r'\b(?:uber eats|ubereats)\b', 'uber_eats', text)
    text = re.sub(r'\b(?:kfc|mcdonalds|burger king)\b', 'fast_food', text)

    # Remove currency symbols
    text = re.sub(r'[€$£¥₹]', '', text)

    # Remove special characters and numbers, keep only letters and spaces
    text = re.sub(r'[^a-z\s]', '', text)

    # Remove extra whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text

if __name__ == "__main__":
    test_cases = [
        "POS TRXN - Groceries USD 50.00",
        "Uber ride to airport GHS 25.50",
        "Momo payment for electricity bill",
        "KFC order via UberEats",
        "Monthly subscription Netflix",
        "Airtel data bundle purchase",
        "Salary deposit from employer",
        "Dinner at a fancy restaurant EUR 120",
        "Bought a new gadget from Amazon $150.00"
    ]

    print("--- Text Normalization Test Cases ---")
    for text in test_cases:
        normalized = normalize_text(text)
        print(f"Original: {text}\nNormalized: {normalized}\n")
