set -e

# Pre is needed for Dev pre releases
python -m pip install --extra-index-url https://pypi.org/simple --pre -U -r requirements.txt
python -m pip install --extra-index-url https://pypi.org/simple -U -r requirements_tests.txt
