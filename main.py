import tls_client
import asyncio
import pandas as pd
import json
import logging
import os
import subprocess
import sys
from remove_last import remove_last_entries_with_same_url
from config import Config
import argparse
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

semaphore = asyncio.Semaphore(Config.CONCURRENCY)
timeout = asyncio.Semaphore(Config.TIMEOUT)

def write_cookies(cookies):
    with open(Config.COOKIE_FILE, 'w') as f:
        f.write(cookies)

async def fetch(session, url, headers, namespase=None):
    log = f"Fetching URL: {url} for {namespase}" if namespase else f"Fetching URL: {url}"
    logger.info(log)
    
    async with semaphore:
        async with timeout:
            try:
                response = session.get(url, headers=headers)
                logger.info(f"Response status code: {response.status_code}")
                if response.status_code == 200:
                    return response.text
                else:
                    logger.warning(f"Failed to fetch {url} with status code {response.status_code}")
                    return None
            except (tls_client.exceptions.TLSClientException, asyncio.TimeoutError) as e:
                logger.error(f"TLS Client error fetching {url}: {e}")
                remove_last_entries_with_same_url()
                sys.exit(1)

async def process_url(session, base_url, headers):
    logger.info(f"Processing URL: {base_url}")
    url_id = base_url.split("/")[-1].upper()
    urls = f'https://api-search.dickssportinggoods.com/catalog-productdetails/v4/byPartNumber/15108?id={url_id}&inventory=true&clearance=false'
    
    try:
        response_text = await fetch(session, urls, headers)
        if response_text is None:
            return None
        
        data = json.loads(response_text)
        logger.info("Successfully parsed JSON response")
        
        colors = extract_colors(data)
        logger.info(f"Extracted colors: {colors}")
        
        if len(colors) == 1:
            logger.info("Processing single color")
            return await process_single_color(session, data, colors[0], base_url, headers)
        else:
            logger.info(f"Processing multiple colors: {len(colors)}")
            return await process_multiple_colors(session, data, colors, base_url, headers)
    except: 
        pass

def extract_colors(data):
    colors = []
    for sku in data['productsData'][0]['skus']:
        defining_attributes = sku.get('definingAttributes', [])
        for attr in defining_attributes:
            if attr['name'] == 'Color':
                colors.append(attr['value'])
    return list(set(colors))

async def process_single_color(session, data, color, base_url, headers):
    sizes, widths, prices, sale_prices = extract_product_details(data, color)
    product_info = extract_product_info(data, color)
    category_dict = await get_category_info(session, data, headers)
    image_dict = await get_image_info(session, data, color, headers)
    
    data_dict = create_data_dict(base_url, product_info, category_dict, prices, sale_prices, sizes, widths, image_dict)
    save_to_csv(data_dict)

async def process_multiple_colors(session, data, colors, base_url, headers):
    for color in colors:
        sizes, widths, prices, sale_prices = extract_product_details(data, color)
        product_info = extract_product_info(data, color)
        category_dict = await get_category_info(session, data, headers)
        image_dict = await get_image_info(session, data, color, headers)
        
        data_dict = create_data_dict(base_url, product_info, category_dict, prices, sale_prices, sizes, widths, image_dict)
        save_to_csv(data_dict)

def extract_product_details(data, color):
    sizes, widths, prices, sale_prices = [], [], [], []
    for sku in data['productsData'][0]['skus']:
        defining_attributes = sku.get('definingAttributes', [])
        if defining_attributes and defining_attributes[0]['value'] == color:
            prices.append(sku['prices']['listPrice'])
            sale_prices.append(sku['prices']['offerPrice'])
            extract_size_width(sku, sizes, widths)
    return sizes, widths, prices, sale_prices

def extract_size_width(sku, sizes, widths):
    defining_attributes = sku.get('definingAttributes', [])
    for attr in defining_attributes:
        if attr['name'] == 'Shoe Width':
            widths.append(attr['value'])
        if attr['name'] in ['Shoe Size', 'Size']:
            sizes.append(attr['value'].replace(' ', '_'))

def extract_product_info(data, color):
    product_info = {}
    product_info['name'] = data['productsData'][0]['style']['name']
    for attr in data['productsData'][0]['style']['descriptiveAttributes']:
        if attr['name'] == 'Gender':
            product_info['gender'] = attr['value']
        if attr['name'] == 'Brand':
            product_info['brand'] = attr['value']
    product_info.update(extract_product_codes(data, color))
    return product_info

def extract_product_codes(data, color):
    for sku in data['productsData'][0]['skus']:
        if sku['definingAttributes'][0]['value'] == color:
            return {
                'productcode1': sku['partNumber'],
                'productcode2': sku['parentPartNumber'],
                'productcode3': sku['catentryId'],
                'productcode4': sku['parentCatentryId'],
                'sku': sku['parentPartNumber']
            }
    return {}

async def get_category_info(session, data, headers):
    cat_list = data['productsData'][0]['style']['primaryCategory']
    api_url = f'https://api-search.dickssportinggoods.com/seo-category/v1/categories/identifier/{cat_list}?storeId=15108'
    response_text = await fetch(session, api_url, headers)
    if response_text:
        data = json.loads(response_text)
        categories = [bd['name'] for bd in data.get('breadCrumbDetails', [])]
    else:
        categories = ['Home']
    return {f'Category{i}': categories[i-1] if i <= len(categories) else "-" for i in range(1, 7)}

async def get_image_info(session, data, color, headers):
    key = data['productsData'][0]['skus'][0]['parentPartNumber']
    api_key = f"{key}_{color.replace(' ', '_').replace('/', '_')}_is"
    api_url = f'https://dks.scene7.com/is/image/GolfGalaxy/{api_key}?req=set,json,UTF-8&labelkey=label&handler=customScene7Handler'
    response_text = await fetch(session, api_url, headers)
    if response_text:
        data = json.loads(response_text.replace('/*jsonp*/customScene7Handler(', '').replace(',"");', ''))
        image_urls = ['https://dks.scene7.com/is/image/' + img_sku['s']['n'] + '?qlt=70&wid=1920&fmt=pjpeg&op_sharpen=1' for img_sku in data['set']['item']]
    else:
        image_urls = []
    return {f'Image{i}': image_urls[i-1] if i < len(image_urls) else "-" for i in range(1, 13)}

def create_data_dict(base_url, product_info, category_dict, prices, sale_prices, sizes, widths, image_dict):
    price_data = min([float(price) for price in prices if price])
    sale_price_data = min([float(price) for price in sale_prices if price]) if sale_prices else '-'
    if price_data == sale_price_data:
        sale_price_data = '-'
    
    data_dict = {
        "NO": "-", "pcurl": base_url, 'mburl': '-',
        "Name": product_info['name'], "Brand": product_info['brand'],
        "ProductCode1": product_info['productcode1'], "ProductCode2": product_info['productcode2'],
        'ProductCode3': product_info['productcode3'], 'ProductCode4': product_info['productcode4'],
        'ProductCode5': '-', "Sku": product_info['sku'],
        "Color": product_info.get('color', ''), "Width": ' '.join(list(set(widths))),
        "Gender": product_info['gender']
    }
    data_dict.update(category_dict)
    data_dict.update({"facetCategory": '-', "Price": price_data, "SalePrice": sale_price_data, "Currency": "$"})
    data_dict.update({f'Description{i}': "-" for i in range(21)})
    data_dict.update({"Size": ' '.join(list(set(sizes)))})
    data_dict.update(image_dict)
    data_dict.update({"Thumbnail": '-'})
    return data_dict

def save_to_csv(data_dict):
    data_df = pd.DataFrame.from_dict([data_dict])
    if not os.path.isfile(Config.OUTPUT_FILE):
        data_df.to_csv(Config.OUTPUT_FILE, mode='w', header=True, index=False, encoding='utf-8')
    else:
        data_df.to_csv(Config.OUTPUT_FILE, mode='a', header=False, index=False, encoding='utf-8')
    logger.info(f"Saved data for {data_dict['Name']} to CSV.")

def parse_arguments():
    parser = argparse.ArgumentParser(description='Process URLs from a CSV file.')
    parser.add_argument('-I', '--input-file', required=True, help='Path to the input CSV file.')
    return parser.parse_args()
        
async def main():
    args = parse_arguments()
    input_file = Path(args.input_file)
    df = pd.read_csv(input_file, encoding='latin1')
    session = tls_client.Session(client_identifier="chrome_110")
    urls = pd.read_csv(Config.OUTPUT_FILE)["pcurl"].tolist() if os.path.isfile(Config.OUTPUT_FILE) else None

    tasks = []
    for _, row in df.iterrows():
        if urls and row['pd_links'] in urls:
            logger.info(f"Skipping {row['pd_links']} as it's already processed.")
            continue
        task = process_url(session, row['pd_links'], Config.HEADERS) 
        tasks.append(task)
        
    await asyncio.gather(*tasks)
    input_file.unlink()
    sys.exit(0)

if __name__ == '__main__':
    asyncio.run(main())
    
