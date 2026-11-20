require("@nomicfoundation/hardhat-toolbox");
require("dotenv").config();

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.20",
  networks: {
    // Local in-memory blockchain for development/testing — free, instant,
    // resets every time. This is what we use to test the contract logic
    // before ever touching a real testnet.
    hardhat: {},

    // Polygon Amoy testnet — free test tokens, fast, cheap. Fill in
    // AMOY_RPC_URL and PRIVATE_KEY in your .env file when you're ready
    // to deploy for real (see the deployment guide).
    amoy: {
      url: process.env.AMOY_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },

    // Sepolia (Ethereum testnet) — an alternative to Amoy if you prefer it.
    sepolia: {
      url: process.env.SEPOLIA_RPC_URL || "",
      accounts: process.env.PRIVATE_KEY ? [process.env.PRIVATE_KEY] : [],
    },
  },
};
