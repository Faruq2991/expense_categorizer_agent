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

    # Remove common noise patterns (currencies, transaction types, telecom, food chains)
    text = re.sub(r'pos trxn|usd|ghs|kes|eur|gbp|jpy|aud|cad|chf|cny|sek|nzd|mxn|sgd|hkd|nok|krw|try|rub|inr|brl|zar|dkk|pln|thb|myr|php|idr|czk|huf|ils|clp|aed|cop|sar|twd|vnd|uah|ron|egp|ngn|kwd|bhd|omr|qtr|bgn|hrk|isk|mdl|mkd|rsd|sll|srd|syp|tjs|tmt|uzs|xaf|xcd|xof|xpf|yer|zmw|zwl', '', text)
    text = re.sub(r'\b(?:momo|mobile money)\b', 'mobile_money', text)
    text = re.sub(r'\b(?:airtel|vodafone|mtn|glo)\b', 'telecom', text)
    text = re.sub(r'\b(?:uber eats|ubereats)\b', 'uber_eats', text)
    text = re.sub(r'\b(?:kfc|mcdonalds|burger king)\b', 'fast_food', text)

    # Remove currency symbols
    text = re.sub(r'[€$£¥₹]', '', text)

    # Remove common transaction identifiers and references
    text = re.sub(r'\b(?:trxn id|ref|auth|transaction|trans|id)\b\s*\S*', '', text) # e.g., TRXN ID: 12345, Ref: ABCDE
    
    # Remove dates (various formats)
    text = re.sub(r'\d{1,2}[-/.]\d{1,2}[-/.]\d{2,4}', '', text) # e.g., 07-25-2023, 07/25/23
    text = re.sub(r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\b\s*\d{1,2}(?:st|nd|rd|th)?(?:,\s*\d{4})?', '', text) # e.g., Jul 25, 2023

    # Remove times (various formats)
    text = re.sub(r'\d{1,2}:\d{2}(?:\s*[ap]m)?', '', text) # e.g., 14:30, 2:30 PM

    # Remove card/bank related terms
    text = re.sub(r'\b(?:visa|mastercard|card|bank|acct|account)\b', '', text)

    # Remove common transaction verbs/phrases
    text = re.sub(r'\b(?:payment|purchase|transfer|withdrawal|deposit|paid for|bought|from)\b', '', text)

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
        "Bought a new gadget from Amazon $150.00",
        "TRXN ID: 987654 - Online Purchase 2023-07-25", # New test case
        "VISA Card Payment at SuperMart 07/25/23 10:00 AM", # New test case
        "Transfer to John Doe Ref: XYZ123", # New test case
        "Withdrawal from ATM 123 Main St", # New test case
        "Deposit to Savings Account", # New test case
        "AMZN*Prime 12.99", # New test case
        "SQ *STARBUCKS COFFEE", # New test case
        "Payment for utilities bill on 2023.07.25 at 11:45", # New test case
        "Online purchase from example.com", # New test case
        "Mobile money transfer to momo wallet" # New test case
    ]

    print("--- Text Normalization Test Cases ---")
    for text in test_cases:
        normalized = normalize_text(text)
        print(f"Original: {text}\nNormalized: {normalized}\n")
