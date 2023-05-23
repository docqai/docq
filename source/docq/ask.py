"""This implements the 'Ask' feature in the app."""
from datetime import timedelta


def question(input, space):
    return f"This is the answer to your question: {input}"


def history(cutoff, size, space):
    return list(map(lambda x: (f"{cutoff}-{x}", cutoff - timedelta(hours=x), f"This is message {str(x)}", x % 2 == 0), range(size, 0, -1)))
