import json

from selenium import webdriver

# Set up the webdriver
driver = webdriver.Chrome()

# Navigate to the page
driver.get("https://www.espn.com/mlb/injuries")

# Wait for the page to load
driver.implicitly_wait(10)

# Get the page source
page_source = driver.page_source

# Find all the table elements in the page source
tables = page_source.split('<table')

with open("playersTeamsAndPositions.json", "r", encoding='utf8') as json_file:
    data = json.load(json_file)
    # Iterate through each table element
    for table in tables[1:]:
        # Split the table element by rows
        rows = table.split('<tr')
        # Iterate through each row
        for row in rows[2:]:
            # Split the row by columns
            import re

            # Define the regular expression
            pattern = r'href=".*?\/id\/\d*?">(.*?)<\/a>.*?<span class="TextStatus TextStatus--.*? plain">(.*?)<\/span>'

            # Extract the desired text using the regular expression
            match = re.search(pattern, row)
            name = match.group(1)
            status = match.group(2)
            for pl in data:
                if name == pl['fullName']:
                    pl["injuryStatus"] = status

    # Close the webdriver
    driver.quit()
with open("playersTeamsAndPositions.json", "w") as json_file:
    json_file.write(json.dumps(data))
