// Interacts with your DEPLOYED contract on Sepolia — issues one real
// certificate using the actual hash and CID from your earlier hashing
// and IPFS scripts, then verifies it back. This proves the whole
// Storage + Blockchain layer works together end to end.
//
// Run with: npx hardhat run scripts/interact.js --network sepolia

const hre = require("hardhat");

// EDIT THIS to your real deployed contract address:
const CONTRACT_ADDRESS = "0x099aA35Af18acA4D03d010E861b02A4A790846Ab";

// Real values from your earlier scripts (hash_certificate.py + pinata_storage.py)
const certId = "CERT-2026-00891";
const ipfsCID = "bafkreia6bfwriyysdclkts36p54kjzknigsrmw3phygxpjd7a27zcwubwi";
const fileHash = "0x1e096d1463121896a9cb7e7f78a4e54d41a5165b6f3e0d77a47f06bf915a81b2";
const contentHash = "0x4afa3b23234da069ea8b2bbb3f5d40576096b6ee55c5b34e39d58e062e79ecd4";

async function main() {
    const registry = await hre.ethers.getContractAt("CertificateRegistry", CONTRACT_ADDRESS);

    console.log("Issuing certificate on-chain...");
    console.log("  certId:", certId);
    console.log("  ipfsCID:", ipfsCID);

    const tx = await registry.issueCertificate(certId, ipfsCID, fileHash, contentHash);
    console.log("\nTransaction sent:", tx.hash);
    console.log("Waiting for confirmation...");
    await tx.wait();
    console.log("[OK] Confirmed on-chain.");

    console.log("\nView this transaction at:");
    console.log(`  https://sepolia.etherscan.io/tx/${tx.hash}`);

    console.log("\nNow verifying it back from the blockchain...");
    const result = await registry.verifyCertificate(certId);
    console.log("\n--- On-chain record ---");
    console.log("  ipfsCID   :", result.ipfsCID);
    console.log("  fileHash  :", result.fileHash);
    console.log("  issuer    :", result.issuer);
    console.log("  timestamp :", new Date(Number(result.timestamp) * 1000).toISOString());
    console.log("  revoked   :", result.revoked);
    console.log("  exists    :", result.exists);

    console.log("\nSUCCESS — real certificate issued and verified on Sepolia.");
}

main().catch((error) => {
    console.error(error);
    process.exitCode = 1;
});