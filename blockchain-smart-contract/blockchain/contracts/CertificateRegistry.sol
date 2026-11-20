// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title CertificateRegistry
 * @notice Stores tamper-evident records of academic certificates.
 *
 * Design principle: the actual certificate FILE lives off-chain (IPFS).
 * This contract only stores what's needed to PROVE a certificate is
 * genuine and unmodified: a hash of the file, the IPFS CID pointing to
 * it, who issued it, when, and whether it's been revoked. Small, cheap,
 * immutable — exactly what a blockchain is good at.
 */
contract CertificateRegistry {
    struct Certificate {
        string certId;          // human-readable certificate ID, e.g. "CERT-2026-00891"
        string ipfsCID;          // where the actual file lives on IPFS
        bytes32 fileHash;         // SHA-256 hash of the file (tamper-evidence anchor)
        bytes32 contentHash;      // SHA-256 hash of just the extracted fields
        address issuer;           // which institution's wallet issued this
        uint256 timestamp;        // when it was issued (block timestamp)
        bool revoked;             // has the issuer revoked this certificate?
        bool exists;              // distinguishes "never issued" from "issued but revoked"
    }

    // certId => Certificate record. We hash the certId string to a bytes32
    // key for cheaper storage lookups.
    mapping(bytes32 => Certificate) private certificates;

    // Which wallet addresses are allowed to issue certificates.
    // This is your access-control root: only registered institutions can issue.
    mapping(address => bool) public authorizedIssuers;

    address public admin;

    event CertificateIssued(string certId, address indexed issuer, string ipfsCID, uint256 timestamp);
    event CertificateRevoked(string certId, address indexed issuer, uint256 timestamp);
    event IssuerAuthorized(address indexed issuer);
    event IssuerRevoked(address indexed issuer);

    modifier onlyAdmin() {
        require(msg.sender == admin, "Only admin can perform this action");
        _;
    }

    modifier onlyAuthorizedIssuer() {
        require(authorizedIssuers[msg.sender], "Not an authorized issuer");
        _;
    }

    constructor() {
        admin = msg.sender;
        authorizedIssuers[msg.sender] = true; // deployer is authorized by default, for convenience
    }

    // ---------- Admin: manage which institutions can issue ----------

    function addAuthorizedIssuer(address issuer) external onlyAdmin {
        authorizedIssuers[issuer] = true;
        emit IssuerAuthorized(issuer);
    }

    function removeAuthorizedIssuer(address issuer) external onlyAdmin {
        authorizedIssuers[issuer] = false;
        emit IssuerRevoked(issuer);
    }

    // ---------- Core: issue, verify, revoke ----------

    function issueCertificate(
        string calldata certId,
        string calldata ipfsCID,
        bytes32 fileHash,
        bytes32 contentHash
    ) external onlyAuthorizedIssuer {
        bytes32 key = keccak256(abi.encodePacked(certId));
        require(!certificates[key].exists, "Certificate ID already exists");

        certificates[key] = Certificate({
            certId: certId,
            ipfsCID: ipfsCID,
            fileHash: fileHash,
            contentHash: contentHash,
            issuer: msg.sender,
            timestamp: block.timestamp,
            revoked: false,
            exists: true
        });

        emit CertificateIssued(certId, msg.sender, ipfsCID, block.timestamp);
    }

    function verifyCertificate(string calldata certId) external view returns (
        string memory ipfsCID,
        bytes32 fileHash,
        bytes32 contentHash,
        address issuer,
        uint256 timestamp,
        bool revoked,
        bool exists
    ) {
        bytes32 key = keccak256(abi.encodePacked(certId));
        Certificate memory cert = certificates[key];
        return (cert.ipfsCID, cert.fileHash, cert.contentHash, cert.issuer, cert.timestamp, cert.revoked, cert.exists);
    }

    function revokeCertificate(string calldata certId) external {
        bytes32 key = keccak256(abi.encodePacked(certId));
        Certificate storage cert = certificates[key];

        require(cert.exists, "Certificate does not exist");
        require(cert.issuer == msg.sender, "Only the original issuer can revoke this certificate");
        require(!cert.revoked, "Certificate is already revoked");

        cert.revoked = true;
        emit CertificateRevoked(certId, msg.sender, block.timestamp);
    }
}
