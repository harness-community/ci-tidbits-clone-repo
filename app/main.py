"""Entrypoint for the clone demo.

The pipeline does not build an image. It only proves that a Harness Git
connector fetched this file into the CI workspace.
"""

APP_NAME = "tidbits-clone-demo"
VERSION = "1.0.0"


def greeting() -> str:
    return f"{APP_NAME} {VERSION} — fetched with a Harness Git connector"


if __name__ == "__main__":
    print(greeting())
