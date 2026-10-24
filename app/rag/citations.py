import re

CITATION_RE = re.compile(r"\[(\d+)\]")


def extract_citations(text: str, num_sources: int) -> tuple[list[int], list[int]]:
    cited = {int(match) for match in CITATION_RE.findall(text)}
    valid = sorted(number for number in cited if 1 <= number <= num_sources)
    invalid = sorted(number for number in cited if not 1 <= number <= num_sources)
    return valid, invalid
