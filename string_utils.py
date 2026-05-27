def count_words(text):
    """Count the number of words in a string."""
    if not text or not text.strip():
        return 0
    return len(text.split())


def reverse_string(text):
    """Reverse a string."""
    return text[::-1]


def is_palindrome(text):
    """Check if a string is a palindrome (case-insensitive)."""
    cleaned = text.lower().replace(" ", "")
    return cleaned == cleaned[::-1]
