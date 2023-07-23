import aiohttp
import config
import asyncio
import json

async def toggleTvStatus(session, status):
    print("TV operation: " + ("On" if status else "Off") + " requested")
    if not await getTvStatus(session):
        print("TV not Found in your network.")
        return None
    print("TV Found in your network.")

    headers = {
        "Accept": "*/*",
        "Accept-Language": "en-IN,en-US;q=0.9,en-GB;q=0.8,en;q=0.7,hi;q=0.6",
        "Connection": "keep-alive",
        "Content-Type": "text/plain;charset=UTF-8",
        "Origin": "null",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
        "X-Auth-PSK": config.tv_key,
    }

    payload = {
        "method": "setPowerStatus",
        "version": "1.0",
        "id": 1,
        "params": [
            {
                "status": status
            }
        ]
    }

    try:
        async with session.post(config.tv_api_url, json=payload, headers=headers, timeout=5) as response:
            response_data = await response.json()
            response.raise_for_status()  # Raise an exception for any HTTP error status codes
            if response.status == 200:
                tv_status = True  # Assuming you have a function to parse TV status from the API response
                return tv_status
            else:
                print(f"API request failed with status code {response.status}.")
                return None
    except aiohttp.ClientError as e:
        print(f"Request error: {e}")
        return None
    except json.JSONDecodeError as e:
        print(f"Unable to parse API response JSON: {e}")
        return None

def parse_tv_status(response_data):
    try:
        status = response_data.get("result", [{}])[0].get("status", "")
        print("TV status:", status)
        return True
    except (IndexError, KeyError):
        print("Error parsing TV status from API response.")
        return False

async def getTvStatus(session):
    headers = {
        'Accept': '*/*',
        'Cache-Control': 'no-cache',
        'Content-Type': 'application/json; charset=UTF-8',
        'Pragma': 'no-cache',
        'X-Auth-PSK': config.tv_key
    }
    data = {
        'method': 'getPowerStatus',
        'params': [],
        'id': 50,
        'version': '1.0'
    }

    try:
        async with session.post(config.tv_api_url, headers=headers, json=data, timeout=5) as response:
            response_data = await response.json()
            response.raise_for_status()  # Raise an exception for any HTTP error status codes
            isTvAvailable = parse_tv_status(response_data)
            if isTvAvailable:
                print("Request succeeded. Response:")
                print(response_data)
            else:
                print("TV not Found in your network.")
            return isTvAvailable
    except asyncio.TimeoutError:
        print("API request timed out. Please check your network connection or try again later.")
        return False
    except aiohttp.ClientError as e:
        print(f"Request error: {e}")
        return False
    except json.JSONDecodeError as e:
        print(f"Unable to parse API response JSON: {e}")
        return False
