import pandas as pd
from pathlib import Path
import yaml
import argparse


def split_and_save_csv(input_file, output_dir, chunk_size):
    input_file = Path(input_file)
    base_path = Path(__file__).parent
    data = pd.read_csv(base_path / input_file)
    chunks = [data[i:i+chunk_size] for i in range(0, len(data), chunk_size)]
    output_path = base_path / output_dir
    output_path.mkdir(parents=True, exist_ok=True)
    
    for i, chunk in enumerate(chunks):
        output_file = f'{input_file.stem}_chunk_{i+1}.csv'
        chunk.to_csv(output_path / output_file, index=False)

def build_docker_compose(output_dir):
  docker_compose_file = Path(__file__).parent / 'docker-compose.yml'
  input_files_dir = Path(__file__).parent / output_dir
  chunk_files = list(input_files_dir.glob('*.csv'))

  services = {  
      'services': {
          'scraper-base': {
              'build': {
                  'context': '.',
                  'dockerfile': 'Dockerfile'
              },
              'restart': 'on-failure',
              'environment': ['PYTHONUNBUFFERED=1'],
              'volumes': ['.:/usr/src/app'],
              'deploy': {
                  'restart_policy': {
                      'condition': 'on-failure',
                      'delay': '5s'
                  }
              }
          }
      }
  }

  for i, chunk_file in enumerate(chunk_files, 1):
      service_name = f'scraper-{i}'
      services['services'][service_name] = {
          'extends': 'scraper-base',
          'container_name': f'scraper_container_{i}',
          'environment': [
              'PYTHONUNBUFFERED=1',
              f'INPUT_FILE=/usr/src/app/{output_dir}/{chunk_file.name}'
          ]
      }

  with open(docker_compose_file, 'w') as f:
      yaml.dump(services, f, default_flow_style=False)

def parse_arguments():
    parser = argparse.ArgumentParser(description='Split and save CSV file.')
    parser.add_argument('-I', '--input-file', required=True, help='Path to the input CSV file.')
    parser.add_argument('-C', '--chunk-size', type=int, default=5000, help='Size of each chunk.')
    parser.add_argument('-O', '--output-dir', required=True, help='Path to the output directory.')
    return parser.parse_args()

def main():
    args = parse_arguments()
    split_and_save_csv(args.input_file, args.output_dir, args.chunk_size)
    build_docker_compose(args.output_dir,)

if __name__ == "__main__":
    main()
          

