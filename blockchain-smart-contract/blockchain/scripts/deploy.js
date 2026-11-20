const hre = require("hardhat");

async function main() {
  console.log("Deploying CertificateRegistry...");

  const CertificateRegistry = await hre.ethers.getContractFactory("CertificateRegistry");
  const registry = await CertificateRegistry.deploy();
  await registry.waitForDeployment();

  const address = await registry.getAddress();
  console.log("\nCertificateRegistry deployed to:", address);
  console.log("Deployer/admin address:", (await hre.ethers.getSigners())[0].address);
  console.log("\nSave this contract address — your Flask backend's .env file needs it as CONTRACT_ADDRESS.");
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
