
# Dick's Sporting Goods Scraper

This project contains two main Python scripts for scraping product data from Dick's Sporting Goods website and processing it.

## Scripts

### 1. split_and_save.py

This script is responsible for splitting a large CSV file into smaller chunks and creating a Docker Compose file for distributed scraping.

#### Usage:
```bash
python split_and_save.py -I <input_file> -O <output_directory> [-C <chunk_size>]
```

- `-I, --input-file`: Path to the input CSV file (required)
- `-O, --output-dir`: Path to the output directory for chunks (required)
- `-C, --chunk-size`: Size of each chunk (default: 5000)

### 2. main.py

This script performs the actual scraping of product data from Dick's Sporting Goods website using asynchronous I/O.

#### Usage:
```bash
docker-compose up
```

- `-I, --input-file`: Path to the input CSV file containing product URLs (required)

## Setup

1. Install the required dependencies:
   ```bash
   pip install pandas pyyaml tls_client asyncio
   ```

2. Set up the configuration in `config.py` (ensure this file exists with necessary constants like `CONCURRENCY`, `TIMEOUT`, `COOKIE_FILE`, `OUTPUT_FILE`, and `HEADERS`).

3. Run `split_and_save.py` to prepare the input data and Docker Compose file.

4. Run `docker-compose up` to start the scraping process.

## Output

The scraped data will be saved to the CSV file specified in the `Config.OUTPUT_FILE` setting.
