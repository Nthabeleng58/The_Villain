/**
 * MetaMask Integration for Villain Food App
 * Handles wallet connection, payment processing, and transaction management
 */

class MetaMaskIntegration {
    constructor() {
        this.web3 = null;
        this.account = null;
        this.chainId = null;
        this.isConnected = false;
        this.lastTxHash = null;  // Store last transaction hash
    }

    /**
     * Check if MetaMask is installed
     */
    async checkMetaMask() {
        if (typeof window.ethereum !== 'undefined') {
            this.web3 = window.ethereum;
            return true;
        }
        return false;
    }

    /**
     * Connect to MetaMask wallet
     */
    async connectWallet() {
        try {
            if (!await this.checkMetaMask()) {
                throw new Error('MetaMask is not installed. Please install MetaMask extension.');
            }

            // Request account access
            const accounts = await window.ethereum.request({
                method: 'eth_requestAccounts'
            });

            if (accounts.length === 0) {
                throw new Error('No accounts found. Please unlock MetaMask.');
            }

            this.account = accounts[0];
            this.chainId = await window.ethereum.request({ method: 'eth_chainId' });
            this.isConnected = true;

            // Listen for account changes
            window.ethereum.on('accountsChanged', (accounts) => {
                if (accounts.length === 0) {
                    this.disconnect();
                } else {
                    this.account = accounts[0];
                }
            });

            // Listen for chain changes
            window.ethereum.on('chainChanged', (chainId) => {
                this.chainId = chainId;
                window.location.reload();
            });

            return {
                success: true,
                account: this.account,
                chainId: this.chainId
            };
        } catch (error) {
            console.error('MetaMask connection error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get current account
     */
    async getAccount() {
        if (!await this.checkMetaMask()) {
            return null;
        }

        try {
            const accounts = await window.ethereum.request({
                method: 'eth_accounts'
            });
            
            if (accounts.length > 0) {
                this.account = accounts[0];
                this.isConnected = true;
                return this.account;
            }
            return null;
        } catch (error) {
            console.error('Error getting account:', error);
            return null;
        }
    }

    /**
     * Get account balance
     */
    async getBalance() {
        if (!this.account || !this.web3) {
            return null;
        }

        try {
            const balance = await window.ethereum.request({
                method: 'eth_getBalance',
                params: [this.account, 'latest']
            });
            
            // Convert from Wei to ETH
            const balanceInEth = parseInt(balance, 16) / Math.pow(10, 18);
            return balanceInEth;
        } catch (error) {
            console.error('Error getting balance:', error);
            return null;
        }
    }

    /**
     * Send ETH payment
     */
    async sendPayment(toAddress, amountInEth, orderId) {
        try {
            if (!this.account) {
                throw new Error('Wallet not connected');
            }

            // Convert ETH to Wei
            const amountInWei = (parseFloat(amountInEth) * Math.pow(10, 18)).toString(16);
            const amountHex = '0x' + amountInWei;

            // Estimate gas
            const gasEstimate = await window.ethereum.request({
                method: 'eth_estimateGas',
                params: [{
                    from: this.account,
                    to: toAddress,
                    value: amountHex
                }]
            });

            // Send transaction
            const txHash = await window.ethereum.request({
                method: 'eth_sendTransaction',
                params: [{
                    from: this.account,
                    to: toAddress,
                    value: amountHex,
                    gas: gasEstimate,
                    data: '0x' // Optional: can include order ID in data
                }]
            });

            // Store transaction hash
            this.lastTxHash = txHash;

            return {
                success: true,
                txHash: txHash,
                orderId: orderId
            };
        } catch (error) {
            console.error('Payment error:', error);
            return {
                success: false,
                error: error.message
            };
        }
    }

    /**
     * Get transaction receipt
     */
    async getTransactionReceipt(txHash) {
        try {
            const receipt = await window.ethereum.request({
                method: 'eth_getTransactionReceipt',
                params: [txHash]
            });
            return receipt;
        } catch (error) {
            console.error('Error getting receipt:', error);
            return null;
        }
    }

    /**
     * Wait for transaction confirmation
     */
    async waitForTransaction(txHash, maxWaitTime = 60000) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < maxWaitTime) {
            const receipt = await this.getTransactionReceipt(txHash);
            if (receipt && receipt.blockNumber) {
                return receipt;
            }
            await new Promise(resolve => setTimeout(resolve, 2000));
        }
        
        throw new Error('Transaction confirmation timeout');
    }

    /**
     * Disconnect wallet
     */
    disconnect() {
        this.account = null;
        this.chainId = null;
        this.isConnected = false;
    }

    /**
     * Format address for display
     */
    formatAddress(address) {
        if (!address) return '';
        return `${address.slice(0, 6)}...${address.slice(-4)}`;
    }

    /**
     * Check if connected to correct network
     */
    async checkNetwork() {
        if (!this.web3) return false;
        
        try {
            const chainId = await window.ethereum.request({ method: 'eth_chainId' });
            // Support multiple networks: Mainnet (0x1), Sepolia (0xaa36a7), Local (0x539)
            const supportedNetworks = ['0x1', '0xaa36a7', '0x539', '0x7a69'];
            return supportedNetworks.includes(chainId);
        } catch (error) {
            return false;
        }
    }

    /**
     * Switch to supported network
     */
    async switchNetwork(chainId = '0xaa36a7') { // Default to Sepolia testnet
        try {
            await window.ethereum.request({
                method: 'wallet_switchEthereumChain',
                params: [{ chainId: chainId }]
            });
            return true;
        } catch (error) {
            // If network doesn't exist, try to add it
            if (error.code === 4902) {
                return await this.addNetwork(chainId);
            }
            return false;
        }
    }

    /**
     * Add network to MetaMask
     */
    async addNetwork(chainId) {
        const networkConfig = {
            '0xaa36a7': { // Sepolia
                chainId: '0xaa36a7',
                chainName: 'Sepolia Test Network',
                nativeCurrency: { name: 'ETH', symbol: 'ETH', decimals: 18 },
                rpcUrls: ['https://sepolia.infura.io/v3/'],
                blockExplorerUrls: ['https://sepolia.etherscan.io']
            }
        };

        const config = networkConfig[chainId];
        if (!config) return false;

        try {
            await window.ethereum.request({
                method: 'wallet_addEthereumChain',
                params: [config]
            });
            return true;
        } catch (error) {
            console.error('Error adding network:', error);
            return false;
        }
    }
}

// Create global instance
window.metaMask = new MetaMaskIntegration();

