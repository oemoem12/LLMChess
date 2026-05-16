"""LLM Chess - Play chess against local LLMs."""

from chess_app import main as _main
from chess_app import __version__


def main():
    _main()


if __name__ == "__main__":
    main()