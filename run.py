#!/usr/bin/env python3
"""Entry point for the CaseLoad application."""

from app import create_app

app = create_app()


def main():
    """Run the application."""
    app.run(debug=True)


if __name__ == "__main__":
    main()
