# author: Pattapol Sirimangklanurak
# date: 08-10-2025
# description: This script provides functions to clean and standardize company and fund names.

import pandas as pd
import re as re

LOWER_EXCEPTIONS = {'of', 'the', 'and', 'for', 'in'}

ACRONYMS = {...}

REMOVE_SUFFIXES = [
    r'\bpublic company limited\b', r'\bpublic co\.? ltd\.?\b', r'\bpcl\b',
    r'\bco\.? ltd\.?\b', r'\bcompany limited\b', r'\blimited\b', r'\bltd\.?\b',
    r'\bberhad\b', r'\binc\.?\b', r'\bcorp\.?\b', r'\bco\b', r'\bgroup\b', r'\'s',
    r'\b[0-9]+(?:[\/\-\s%_]*[0-9]+)+\b', r'\bplc\b', r'\bllc\b', r'\bag\b', r'\bbhd\b', 
    r'\bberhadb', r'\bpte\b', r'\bL\bL\bC', r'\bL.L.C-ADR\b', r'\bprivate\b'
]

REMOVE_PHRASES = [
    r'\bwhich is registered\b', r'\bregistered by\b', r'\bregistered\b', r'\bwhich is registered_Equity Instrument\b',
    r'\bwhich are registered\b', r'\band its affiliates\b', r'\band its affiliates,\b', r'\bwhich are\b', r'\bwho are\b', 
    r'\b[0-9]+(?:[\/\-\s%_]*[0-9]+)+\b', r'\bwho are registered\b', r'\blong-term\b', r'\blimited-legal\b', r'\(type a\)', r'\(type b\)',
    r'\(type c\)', r'\(public company\)', r'\bdr\b', r'\bset[0-9]\b', r'\bbranch\b', r'\bthai\sequity\b', r'\bequity\b', 
    r'\bdividend\sequity\b', r'\bjumbo\b', r'\blong-term\sequity\b', r'\bdividend\b', r'\bindex\b', r'\bset[0-9]+\b',
    r'\([^\)]*$', r'^[^\(]*\)', r'\(\d+\)'
]

MOVE_TO_PARENS = [ # terms to relocate to parentheses
     ]

OVERRIDE_ASSET_MANAGERS = {
    # override keys
}

# Main function to clean names
# @param text: input string to clean
# @param in_asset_handler: flag to indicate if called from asset handler
# @return: cleaned string
def clean_name(text, in_asset_handler=False):
    if pd.isna(text):
        return ''

    text = str(text).strip().lower()
    original_text = text
    text = re.sub(r'\b([a-z])\.(?=[a-z]\.)', r'\1', text)
    text = re.sub(r'\.', '', text)
    
    text = re.sub(r'\s+', ' ', text)

    text = re.sub(r'[\s.,;:]+$', '', text)
    text = re.sub(r'^[\s.,;:]+', '', text)

    for pattern in REMOVE_SUFFIXES:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    for pattern in REMOVE_PHRASES:
        text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    if ' by ' in text:
        text = text.split(' by ')[-1].strip()

    if ('fund' in text or 'open-ended fund' in text) and 'provident fund' not in text and not in_asset_handler:
        return format_asset_management(text)

    if '-' in text:
        text = text.split('-')[0].strip()

    text = relocate_keywords(text)

    text = re.sub(r'\s*[,.;]+\s*', ' ', text).strip()
    text = re.sub(r'\s+', ' ', text)

    text = title_case(text)
    
    text = re.sub(r'\(([^)]+)\)', lambda m: f"({smart_capitalize_parens(m.group(1))})", text)
    text = re.sub(r'\(\s*\)', '', text)

    return text

# Helper function to format asset management names
# @param text: input string to format
# @return: formatted asset management name
def format_asset_management(text):
    text = re.sub(r'\s+', ' ', text).strip()

    reversed_match = re.match(r'^open[-\s]?ended fund,\s*(.*)', text, re.IGNORECASE)
    if reversed_match:
        reversed_name = reversed_match.group(1).strip()

        override_key = reversed_name.lower()
        for key in OVERRIDE_ASSET_MANAGERS:
            if override_key.startswith(key):
                return f"{OVERRIDE_ASSET_MANAGERS[key]} Asset Management"

        cleaned = clean_name(reversed_name, in_asset_handler=True)
        return f"{cleaned} Asset Management"

    fund_keywords = [
        r'open[-\s]?ended fund', r'mutual fund', r'(balanced|growth|income|equity|portfolio)\s+(fund|plan)?',
        r'\bfund\b', r'\bfunds\b', r'\basset management\b', r'\bopen\b'
    ]

    fund_pattern = re.compile('|'.join(fund_keywords), flags=re.IGNORECASE)
    match = fund_pattern.search(text)

    if match:
        for key in OVERRIDE_ASSET_MANAGERS:
            if key in text.lower():
                return f"{OVERRIDE_ASSET_MANAGERS[key]} Asset Management"

        manager_part = text[:match.start()].strip()
        cleaned = clean_name(manager_part, in_asset_handler=True)
        return f"{cleaned} Asset Management"

    parts = re.split(r'[-,]', text)
    for part in parts:
        if any(term in part.lower() for term in ['asset management', 'fund', 'amc']):
            name = clean_name(part, in_asset_handler=True)
            return f"{name} Asset Management"

    return clean_name(text, in_asset_handler=True)

# Helper function to relocate specific keywords to parentheses
# @param text: input string to process
# @return: processed string with keywords relocated
def relocate_keywords(text):
    if '(' in text and ')' in text:
        return text

    found_terms = []
    for term in MOVE_TO_PARENS:
        pattern = rf'(?<!\bfor\s)(?<!\bof\s)(?<!\bthe\s)\b{re.escape(term)}\b'
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            found_terms.append(match.group())
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

    text = re.sub(r'\s+', ' ', text).strip()
    if found_terms:
        return f"{text} ({' '.join(found_terms)})"
    return text

# Helper function for smart capitalization
# @param word: input word to capitalize
# @return: smartly capitalized word
def smart_capitalize(word):
    if word.upper() in ACRONYMS:
        return word.upper()
    if word.lower() in LOWER_EXCEPTIONS:
        return word.lower()
    if '-' in word:
        return '-'.join([smart_capitalize(w) for w in word.split('-')])
    return word.capitalize()

# Helper function to convert text to title case with exceptions
# @param text: input string to convert
# @return: title-cased string
def title_case(text):
    words = text.split()
    if not words:
        return ''
    
    result = [smart_capitalize_first(words[0])]

    result += [smart_capitalize(word) if word.lower() not in LOWER_EXCEPTIONS else word.lower() for word in words[1:]]
    return ' '.join(result)

# Helper function to smartly capitalize content within parentheses
# @param content: input string within parentheses
# @return: smartly capitalized string
def smart_capitalize_parens(content):
    words = content.strip().split()
    if not words:
        return content
    words[0] = smart_capitalize(words[0])
    return ' '.join(words)

# Helper function to smartly capitalize the first word
# @param word: input word to capitalize
# @return: smartly capitalized first word
def smart_capitalize_first(word):
    if word.upper() in ACRONYMS:
        return word.upper()
    if '-' in word:
        return '-'.join([smart_capitalize_first(w) for w in word.split('-')])
    return word.capitalize()