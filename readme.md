# Restaurant Rankings

Scripts I used to [rank the restaurants in my city](https://developers.google.com/maps/documentation/javascript/cloud-setup).

## Usage Instructions

To use this project for your own city, follow these steps:

1. **Run the `gc_places_api_scraper.py` script:**
    - Ensure you have your own centered coordinates for your city to replace the following in `main()`:
        ```python
        # Colorado Springs coordinates
        CENTER_LAT = 38.878400
        CENTER_LNG = -104.767914
        RADIUS_KM = 15
        ```
    - Place your API key in a file named `gcp_key.txt`. Get your own API key from [Google Cloud Platform](https://developers.google.com/maps/documentation/javascript/cloud-setup).

    ```bash
    python gc_places_api_scraper.py
    ```

    This outputs `restaurants.json` with a crude sorting. Do some cleanup to remove fake restaurants at the bottom that don't have reviews and such.

2. **Run the `wilson_script`:**

    ```bash
    python wilson_script.py restaurants.json restaurants_wilson_ranked.json --confidence 0.95
    ```

    This outputs a `.json` file with all the restaurants ranked in order of Wilson interval score.