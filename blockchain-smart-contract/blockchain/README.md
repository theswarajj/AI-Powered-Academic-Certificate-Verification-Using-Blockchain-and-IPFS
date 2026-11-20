# Certificate Registry Smart Contract

## Setup
1. npm install
2. npx hardhat compile
3. npx hardhat test          (runs the full test suite - 12 tests)
4. npx hardhat run scripts/deploy.js --network hardhat    (deploy locally)

## Deploying to a real testnet (Polygon Amoy)
1. Copy .env.example to .env
2. Fill in AMOY_RPC_URL (get one free from Alchemy or Infura)
3. Fill in PRIVATE_KEY (your MetaMask test wallet's private key - NEVER your real wallet)
4. Get free test MATIC from a Polygon Amoy faucet
5. npx hardhat run scripts/deploy.js --network amoy
6. Copy the printed contract address - your Flask backend needs it
