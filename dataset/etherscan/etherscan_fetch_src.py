import argparse
import os
import requests


def fetch_cluster_srcs(cluster, contracts_amount, api_key):
    DIR = 'dataset/etherscan/'
    addresses_file = DIR + [filename for filename in os.listdir(DIR) if filename.startswith(f'cluster_{cluster}')][0]
    
    save_src_dir = f'dataset/etherscan/cluster_{cluster}/'
    if not os.path.exists(save_src_dir):
        os.makedirs(save_src_dir)
    
    contracts_fetched = 0
    with open(addresses_file) as file:
        for contract_address in file:
            c = contract_address.rstrip() 
            if contracts_amount and contracts_fetched >= contracts_amount:
                return
            
            fetch_src(c, save_src_dir, api_key)
            contracts_fetched += 1

def fetch_src(address, save_src_dir, api_key):
    url = f'https://api.etherscan.io/api?module=contract&action=getsourcecode&address={address}&apikey={api_key}'
    r = requests.get(url, allow_redirects=True).json()
    
    if r['status'] != '1':
        raise Exception(f'Failed to get SOURCE CODE for address {address} with error message: {r["result"]}')

    src_file = f'{save_src_dir}/{r["result"][0]["ContractName"]}.sol'
    if os.path.exists(src_file):
        return
        
    with open(src_file, 'w') as f:
        f.write(r["result"][0]["SourceCode"])

    print(f'{r["result"][0]["ContractName"]}.sol (addr {address} fetched successfully)')

def launch_argument_parser():
    parser = argparse.ArgumentParser()

    # Contract parameters
    parser.add_argument("-c", "--cluster", help="Cluster to be fetched from Etherscan. Either 0 (small contracts) or 1 (large contracts)",
                        action="store", dest="cluster", type=int)
    parser.add_argument("-n", "--number_of_contracts", help="Number of contracts to be fetched .",
                        action="store", dest="number_of_contracts", type=int)
    parser.add_argument("-k", "--api-key", help="Etherscan API key (see https://etherscan.io/apis).",
                        action="store", dest="api_key", type=str)

    args = parser.parse_args()

    if args.cluster == None:
        parser.error("--cluster argument is required.")

    if args.number_of_contracts and args.number_of_contracts <= 0:
        parser.error("--number_of_contracts argument must be an integer > 0.")

    return args

def main():
    args = launch_argument_parser()
    
    fetch_cluster_srcs(args.cluster, args.number_of_contracts, args.api_key)


if '__main__' == __name__:
    main()
