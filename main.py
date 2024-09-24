import asyncio
import random
import ssl
import json
import time
import uuid
from loguru import logger
import aiohttp

# Fungsi untuk menghapus proxy yang tidak valid dan menyimpannya ke file
async def connect_to_wss(socks5_proxy, user_id, valid_proxies, failed_proxies_file, valid_proxies_file):
    device_id = str(uuid.uuid3(uuid.NAMESPACE_DNS, socks5_proxy))
    logger.info(f"Device ID: {device_id} for proxy {socks5_proxy}")
    
    while True:
        try:
            await asyncio.sleep(random.randint(1, 10) / 10)
            custom_headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
            }
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            uri = "wss://proxy.wynd.network:4650/"

            # Set up aiohttp session with proxy
            async with aiohttp.ClientSession() as session:
                async with session.ws_connect(
                    uri, 
                    ssl=ssl_context, 
                    headers=custom_headers, 
                    proxy=socks5_proxy
                ) as websocket:
                    
                    async def send_ping():
                        while True:
                            send_message = json.dumps(
                                {"id": str(uuid.uuid4()), "version": "1.0.0", "action": "PING", "data": {}}
                            )
                            logger.debug(send_message)
                            await websocket.send_str(send_message)
                            await asyncio.sleep(20)

                    asyncio.create_task(send_ping())

                    while True:
                        response = await websocket.receive()
                        message = json.loads(response.data)
                        logger.info(message)
                        if message.get("action") == "AUTH":
                            auth_response = {
                                "id": message["id"],
                                "origin_action": "AUTH",
                                "result": {
                                    "browser_id": device_id,
                                    "user_id": user_id,
                                    "user_agent": custom_headers['User-Agent'],
                                    "timestamp": int(time.time()),
                                    "device_type": "extension",
                                    "version": "2.5.0"
                                }
                            }
                            logger.debug(auth_response)
                            await websocket.send_str(json.dumps(auth_response))

                        elif message.get("action") == "PONG":
                            pong_response = {"id": message["id"], "origin_action": "PONG"}
                            logger.debug(pong_response)
                            await websocket.send_str(json.dumps(pong_response))
                
                # Jika berhasil koneksi, simpan proxy ke valid_proxies_file
                if socks5_proxy not in valid_proxies:
                    valid_proxies.append(socks5_proxy)
                with open(valid_proxies_file, 'a') as f:
                    f.write(f"{socks5_proxy}\n")

        except Exception as e:
            logger.error(f"Error with proxy {socks5_proxy}: {e}")
            
            # Hapus proxy yang gagal dari daftar valid
            if socks5_proxy in valid_proxies:
                valid_proxies.remove(socks5_proxy)
            
            # Simpan proxy gagal ke file
            with open(failed_proxies_file, 'a') as f:
                f.write(f"{socks5_proxy}\n")
            
            break  # Hentikan loop untuk proxy yang gagal

async def main():
    # TODO: Update user_id
    _user_id = 'UIDgrass'
    # TODO: Update proxy list
    socks5_proxy_list = [
        'socks5://nng123-zone-resi-region-fr-st-auvergnerhônealpes-city-rivedegier:pass123@22affb5a12efdfc7.gto.eu.pyproxy.io:16666',

        # proxy lainnya...
    ]
    
    valid_proxies = []  # Daftar proxy valid
    failed_proxies_file = 'gagalproxy.txt'  # Nama file untuk proxy yang gagal
    valid_proxies_file = 'validproxy.txt'  # Nama file untuk proxy yang valid

    tasks = [asyncio.ensure_future(connect_to_wss(i, _user_id, valid_proxies, failed_proxies_file, valid_proxies_file)) for i in socks5_proxy_list]
    await asyncio.gather(*tasks)

if __name__ == '__main__':
    asyncio.run(main())
