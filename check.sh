pyright src
pylint src --disable=C0411
flake8 src --ignore=I100,I101,I201,I202
ruff check src
