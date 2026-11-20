const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("CertificateRegistry", function () {
  let registry, admin, institution, otherInstitution, randomUser;

  // Sample certificate data, as if it came from the hashing/IPFS scripts
  const certId = "CERT-2026-00891";
  const ipfsCID = "bafkreia6bfwriyysdclkts36p54kjzknigsrmw3phygxpjd7a27zcwubwi";
  const fileHash = ethers.keccak256(ethers.toUtf8Bytes("sample-file-content"));
  const contentHash = ethers.keccak256(ethers.toUtf8Bytes("sample-content-fields"));

  beforeEach(async function () {
    [admin, institution, otherInstitution, randomUser] = await ethers.getSigners();

    const CertificateRegistry = await ethers.getContractFactory("CertificateRegistry");
    registry = await CertificateRegistry.deploy();

    // Authorize one institution wallet for most tests
    await registry.connect(admin).addAuthorizedIssuer(institution.address);
  });

  describe("Access control", function () {
    it("deployer is admin and an authorized issuer by default", async function () {
      expect(await registry.admin()).to.equal(admin.address);
      expect(await registry.authorizedIssuers(admin.address)).to.equal(true);
    });

    it("only admin can authorize new issuers", async function () {
      await expect(
        registry.connect(randomUser).addAuthorizedIssuer(otherInstitution.address)
      ).to.be.revertedWith("Only admin can perform this action");
    });

    it("admin can authorize and later remove an issuer", async function () {
      await registry.connect(admin).addAuthorizedIssuer(otherInstitution.address);
      expect(await registry.authorizedIssuers(otherInstitution.address)).to.equal(true);

      await registry.connect(admin).removeAuthorizedIssuer(otherInstitution.address);
      expect(await registry.authorizedIssuers(otherInstitution.address)).to.equal(false);
    });

    it("an unauthorized wallet cannot issue certificates", async function () {
      await expect(
        registry.connect(randomUser).issueCertificate(certId, ipfsCID, fileHash, contentHash)
      ).to.be.revertedWith("Not an authorized issuer");
    });
  });

  describe("Issuing certificates", function () {
    it("an authorized institution can issue a certificate", async function () {
      await expect(
        registry.connect(institution).issueCertificate(certId, ipfsCID, fileHash, contentHash)
      )
        .to.emit(registry, "CertificateIssued")
        .withArgs(certId, institution.address, ipfsCID, await getBlockTimestamp());
    });

    it("cannot issue two certificates with the same certId", async function () {
      await registry.connect(institution).issueCertificate(certId, ipfsCID, fileHash, contentHash);
      await expect(
        registry.connect(institution).issueCertificate(certId, ipfsCID, fileHash, contentHash)
      ).to.be.revertedWith("Certificate ID already exists");
    });
  });

  describe("Verifying certificates", function () {
    it("returns correct data for an issued certificate", async function () {
      await registry.connect(institution).issueCertificate(certId, ipfsCID, fileHash, contentHash);

      const result = await registry.verifyCertificate(certId);
      expect(result.ipfsCID).to.equal(ipfsCID);
      expect(result.fileHash).to.equal(fileHash);
      expect(result.contentHash).to.equal(contentHash);
      expect(result.issuer).to.equal(institution.address);
      expect(result.revoked).to.equal(false);
      expect(result.exists).to.equal(true);
    });

    it("exists=false for a certId that was never issued", async function () {
      const result = await registry.verifyCertificate("CERT-DOES-NOT-EXIST");
      expect(result.exists).to.equal(false);
    });
  });

  describe("Revoking certificates", function () {
    beforeEach(async function () {
      await registry.connect(institution).issueCertificate(certId, ipfsCID, fileHash, contentHash);
    });

    it("the original issuer can revoke their own certificate", async function () {
      await expect(registry.connect(institution).revokeCertificate(certId))
        .to.emit(registry, "CertificateRevoked");

      const result = await registry.verifyCertificate(certId);
      expect(result.revoked).to.equal(true);
    });

    it("a different institution CANNOT revoke someone else's certificate", async function () {
      await registry.connect(admin).addAuthorizedIssuer(otherInstitution.address);
      await expect(
        registry.connect(otherInstitution).revokeCertificate(certId)
      ).to.be.revertedWith("Only the original issuer can revoke this certificate");
    });

    it("cannot revoke a certificate that doesn't exist", async function () {
      await expect(
        registry.connect(institution).revokeCertificate("CERT-DOES-NOT-EXIST")
      ).to.be.revertedWith("Certificate does not exist");
    });

    it("cannot revoke an already-revoked certificate", async function () {
      await registry.connect(institution).revokeCertificate(certId);
      await expect(
        registry.connect(institution).revokeCertificate(certId)
      ).to.be.revertedWith("Certificate is already revoked");
    });
  });

  // Helper: gets the timestamp the NEXT mined block will have, so event
  // assertions can match block.timestamp exactly.
  async function getBlockTimestamp() {
    const block = await ethers.provider.getBlock("latest");
    return block.timestamp + 1;
  }
});
