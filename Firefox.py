import asyncio
from selenium import webdriver
from aiohttp import ClientSession
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, WebDriverException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service
import base64
from geopy.geocoders import Nominatim
from geopy.distance import geodesic
import os

async def send_data_via_webhook(session, order_data):
    webhook_url = 'https://webhook.site/20b9d417-0555-4675-9910-c51128883903'
    try:
        async with session.post(webhook_url, json=order_data) as response:
            content_type = response.headers.get('Content-Type', '')
            if 'application/json' in content_type:
                return await response.json()
            else:
                # Handhaben Sie nicht-JSON-Antworten hier
                return {"status": response.status, "reason": response.reason, "content_type": content_type}
    except Exception as e:
        print(f"Webhook Fehler: {e}")
        return None
async def get_distance(origin, destination):
    geolocator = Nominatim(user_agent="distance_calculator")
    try:
        location1 = geolocator.geocode(origin)
        location2 = geolocator.geocode(destination)
        
        if location1 is None or location2 is None:
            print("Eine oder beide Adressen konnten nicht gefunden werden.")
            return None
        
        coords1 = (location1.latitude, location1.longitude)
        coords2 = (location2.latitude, location2.longitude)
        
        distance = geodesic(coords1, coords2).kilometers
        return distance
    except Exception as e:
        print("Fehler bei der Berechnung der Entfernung:", e)
        return None

# Beispieladressen
start_address = "Normannenstraße 28, 10365 Berlin, Deutschland"
end_address = "Libauer Str. 12, 10245 Berlin, Deutschland"

async def process_order(driver, order_element):
    try:
        price = order_element.find_element(By.CSS_SELECTOR, 'td._css-fHeobO').text
        pickup_address = order_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(3)').text
        destination_address = order_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(4)').text
        driver_name = order_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(5)').text
        driver_surname = order_element.find_element(By.CSS_SELECTOR, 'td:nth-of-type(6)').text
        distance = await get_distance(pickup_address, destination_address)
        order_data = {
            "preis": price,
            "abholadresse": pickup_address,
            "zieladresse": destination_address,
            "Entfernung" : f"{distance:.2f}",
            "fahrer_name": driver_name,
            "fahrer_nachname": driver_surname,

        }
        

        async with ClientSession() as session:
            
            response = await send_data_via_webhook(session, order_data)
            print("Webhook Response:", response)
            print(order_data)
            await asyncio.gather(timerx(driver))
        

        
    except Exception as e:
        print(f"")

async def timerx(driver):
    await asyncio.sleep(6)
    # Warten, dann Button klicken
    ''' WebDriverWait(driver, 1).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, "button._css-fBvEmy._css-jWnSEI"))
    ).click()'''
    print("Button geklickt")


async def main():
    profile_directory = "/home/alaaddin/snap/firefox/common/.mozilla/firefox/t0wsmiqo.default"
    options = FirefoxOptions()
    
    # Setzen Sie den Pfad zum Profil
    options.add_argument("-profile")
    options.add_argument(profile_directory)
    
    # Initialisieren Sie den WebDriver mit den angegebenen Optionen
    driver = webdriver.Firefox(options=options)
    
    # Fügen Sie Ihre Testlogik hier ein
    driver.get("https://vsdispatch.uber.com/")
    print(driver.get_cookies())
    await asyncio.sleep(1)
    with open('../../../../../Downloads/Start.txt', 'w') as f:
        f.write(driver.print_page())
    previous_order_count = 0
    while True:
        await asyncio.sleep(0.1)  # Polling-Intervall
        current_orders = driver.find_elements(By.CSS_SELECTOR, 'tr.MuiTableRow-root')
        if (len(current_orders)) == 0:
            print("failed")
            await asyncio.sleep(1)
            with open('Error.txt', 'w') as f:
                f.write(driver.print_page())
            driver.get("https://vsdispatch.uber.com/")
            await asyncio.sleep(1)
            with open('Redirect.txt', 'w') as f:
                f.write(driver.print_page())
        elif (len(current_orders)) != previous_order_count:
            for order in current_orders[previous_order_count:]:
                asyncio.create_task(process_order(driver, order))
            previous_order_count = len(current_orders)


asyncio.run(main())
