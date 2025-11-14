"""
Deploy Solidity Smart Contracts to Ethereum Network
Run this script to compile and deploy contracts
"""

import os
import json
import subprocess
from solcx import compile_standard, install_solc
from blockchain.ethereum_integration import EthereumIntegration


def compile_contract(contract_path: str, contract_name: str) -> dict:
    """Compile Solidity contract"""
    print(f"Compiling {contract_name}...")
    
    # Install Solidity compiler version
    install_solc('0.8.19')
    
    with open(contract_path, 'r') as f:
        source_code = f.read()
    
    compiled_sol = compile_standard({
        "language": "Solidity",
        "sources": {
            contract_path: {
                "content": source_code
            }
        },
        "settings": {
            "outputSelection": {
                "*": {
                    "*": ["abi", "evm.bytecode", "evm.bytecode.sourceMap"]
                }
            },
            "optimizer": {
                "enabled": True,
                "runs": 200
            }
        }
    }, solc_version="0.8.19")
    
    # Extract contract data
    contract_data = compiled_sol["contracts"][contract_path][contract_name]
    
    return {
        "abi": contract_data["abi"],
        "bytecode": contract_data["evm"]["bytecode"]["object"]
    }


def save_compiled_contract(contract_data: dict, output_path: str):
    """Save compiled contract to JSON file"""
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(contract_data, f, indent=2)
    
    print(f"Compiled contract saved to: {output_path}")


def main():
    """Main deployment function"""
    print("=" * 60)
    print("Villain Food App - Smart Contract Deployment")
    print("=" * 60)
    
    # Contract paths
    base_dir = os.path.dirname(os.path.dirname(__file__))
    contracts_dir = os.path.join(base_dir, 'blockchain', 'contracts')
    
    order_contract_path = os.path.join(contracts_dir, 'VillainOrderContract.sol')
    token_contract_path = os.path.join(contracts_dir, 'VillainToken.sol')
    
    # Compile contracts
    print("\n1. Compiling Contracts...")
    print("-" * 60)
    
    try:
        # Compile Order Contract
        order_contract_data = compile_contract(
            order_contract_path,
            'VillainOrderContract'
        )
        order_output = os.path.join(contracts_dir, 'VillainOrderContract.json')
        save_compiled_contract(order_contract_data, order_output)
        
        # Compile Token Contract
        token_contract_data = compile_contract(
            token_contract_path,
            'VillainToken'
        )
        token_output = os.path.join(contracts_dir, 'VillainToken.json')
        save_compiled_contract(token_contract_data, token_output)
        
        print("\n✓ Contracts compiled successfully!")
        
    except Exception as e:
        print(f"\n✗ Compilation error: {e}")
        print("\nNote: Make sure py-solc-x is installed: pip install py-solc-x")
        return
    
    # Deploy contracts
    print("\n2. Deploying Contracts to Ethereum...")
    print("-" * 60)
    
    eth = EthereumIntegration()
    
    if not eth.is_connected():
        print("\n⚠ Not connected to Ethereum network")
        print("Set ETHEREUM_RPC_URL environment variable to connect")
        print("Example: export ETHEREUM_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY")
        return
    
    if not eth.account:
        print("\n⚠ No account configured")
        print("Set ETHEREUM_PRIVATE_KEY environment variable")
        print("WARNING: Never commit private keys to version control!")
        return
    
    # Deploy Order Contract
    print("\nDeploying VillainOrderContract...")
    order_address = eth.deploy_order_contract()
    
    if order_address:
        print(f"✓ Order contract deployed at: {order_address}")
        
        # Save deployment info
        deployment_info = {
            "network": os.environ.get('ETHEREUM_RPC_URL', 'local'),
            "order_contract_address": order_address,
            "deployed_by": eth.account.address,
            "token_contract_address": None
        }
        
        deployment_file = os.path.join(contracts_dir, 'deployment.json')
        with open(deployment_file, 'w') as f:
            json.dump(deployment_info, f, indent=2)
        
        print(f"\n✓ Deployment info saved to: {deployment_file}")
    else:
        print("✗ Failed to deploy order contract")
    
    print("\n" + "=" * 60)
    print("Deployment Complete!")
    print("=" * 60)


if __name__ == '__main__':
    main()

