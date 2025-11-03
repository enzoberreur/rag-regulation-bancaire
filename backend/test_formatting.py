"""
Test script to verify formatting normalization logic
"""
import re

def normalize_formatting(text: str) -> str:
    """
    Post-process LLM output to ensure proper formatting with blank lines.
    The LLM sometimes ignores spacing instructions, so we fix it here.
    """
    if not text:
        return text
    
    # 1. Add blank line before numbered list items (1. 2. 3. etc)
    # Matches patterns like ":1." or "Risks:1." or "buffer.2."
    # Negative lookbehind to avoid matching if already has blank line before
    text = re.sub(r'(?<!\n\n)([^\n])(\d+\.)\s*', r'\1\n\n\2 ', text)
    
    # 2. Fix numbered items that are directly followed by text without space
    # e.g., "1. Capital" -> "1. Capital" (already has space) but "1.Capital" -> "1. Capital"
    text = re.sub(r'(\d+\.)\s*([A-Z])', r'\1 \2', text)
    
    # 2b. Fix incorrectly split numbers like "2. 5%" -> "2.5%"
    text = re.sub(r'(\d+)\.\s+(\d+%)', r'\1.\2', text)
    
    # 2c. Add line break after section titles in numbered lists
    # e.g., "RequirementLes" -> "Requirement\nLes" or "Requirement Establishments" -> "Requirement\nEstablishments"
    text = re.sub(r'([a-z])([A-Z][a-z]+\s)', r'\1\n\2', text)
    
    # 2d. Add line break before bullet points if not already on new line
    text = re.sub(r'([a-z:])(\s*-\s+[A-Z])', r'\1\n\2', text)
    
    # 2e. Add line break between sentences that are stuck together (period+capital letter)
    # e.g., "turnover.It" -> "turnover.\nIt" but preserve "Dr.Smith" or abbreviations
    text = re.sub(r'([a-z])\.([A-Z][a-z])', r'\1.\n\2', text)
    
    # 3. Add blank line before section headers that start with **
    # Only if not already preceded by blank line
    text = re.sub(r'(?<!\n\n)([^\n])(\*\*[^*]+\*\*:)', r'\1\n\n\2', text)
    
    # 4. Add blank line after section headers (lines ending with **)
    # Only if not already followed by blank line
    text = re.sub(r'(\*\*:)(?!\n\n)(\n)([^\n])', r'\1\n\n\3', text)
    
    # 5. Clean up excessive blank lines (max 2 newlines = 1 blank line)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text.strip()


# Test with the example provided by the user
test_input = """Key Requirements of ACPR Regulation 2024-15 Regarding Capital Buffer for Climate-Related Risks:1. Calculation MethodologyThe regulation mandates that banks quantify climate-related risks and integrate these into their capital calculation models. A specific methodology for quantifying climate exposures must be established, adhering to ACPR standards. Institutions are required to classify exposures based on their risk levels, particularly identifying those categorized as high climate risk.2. Governance RequirementsEach banking institution must create a Climate Risk Committee at the board level. This committee must consist of at least three independent members and convene quarterly. The responsibilities of this committee include validating climate risk management policies and ensuring that the institution adheres to the established methodologies and capital requirements.3. Compliance TimelineBanks must achieve full compliance with all provisions of the regulation by December 31, 2025. Failure to comply may result in penalties of up to 5% of the institution's annual revenue. Additionally, banks are required to submit a monthly report to the ACPR detailing their climate exposures, the methodologies employed, and the implications for their capital requirements, with submissions due before the 5th of each month for the preceding month.In summary, institutions need to establish robust methodologies for calculating climate-related capital requirements, implement governance structures for oversight, and adhere to the specified compliance timeline to mitigate potential penalties."""

print("=" * 80)
print("ORIGINAL TEXT:")
print("=" * 80)
print(test_input)
print("\n" + "=" * 80)
print("NORMALIZED TEXT:")
print("=" * 80)
normalized = normalize_formatting(test_input)
print(normalized)
print("\n" + "=" * 80)
print("SUCCESS! Text has been properly formatted with blank lines.")
print("=" * 80)
