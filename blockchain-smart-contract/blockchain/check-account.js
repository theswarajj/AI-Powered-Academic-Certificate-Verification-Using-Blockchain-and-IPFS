// Diagnostic: prints the wallet address your PRIVATE_KEY in .env actually
// corresponds to, and its balance on Sepolia. Run with:
//   npx hardhat run scripts/check-account.js --network sepolia

const hre = require("hardhat");

async function main() {
    const [signer] = await hre.ethers.getSigners();

    if (!signer) {
        console.log("[FAIL] No signer found — PRIVATE_KEY in .env is likely missing or empty.");
        return;
    }

    const address = await signer.getAddress();
    const balance = await hre.ethers.provider.getBalance(address);

    console.log("Address derived from your PRIVATE_KEY:", address);
    console.log("Balance on Sepolia:", hre.ethers.formatEther(balance), "ETH");
    console.log("\nCompare the address above to your MetaMask address.");
    console.log("If they don't match, your .env has the wrong private key.");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});