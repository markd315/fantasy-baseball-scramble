import json

from selenium import webdriver

# Set up the webdriver
driver = webdriver.Firefox()

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
    for table in tables:
      # Split the table element by rows
      rows = table.split('<tr')
      # Iterate through each row
      for row in rows:
        # Split the row by columns
        cols = row.split('<td')
        # Print the 0th and 3rd columns
        print(cols[0].text, cols[3].text)
        for pl in data:
            if cols[0].text == pl['fullName']:
                pl["injuryStatus"] = cols[3].text

    # Close the webdriver
    driver.quit()