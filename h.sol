// SPDX-License-Identifier: MIT 
pragma solidity ^0.8.20; 
 
contract ContractFarming { 
    enum ContractStatus { Created, Accepted, Delivered, Disputed, Completed } 
 
    struct FarmingContract { 
        uint256 id; 
        address payable farmer; 
        address payable buyer; 
        string cropDetails; 
        uint256 price; 
        uint256 deliveryDate; 
        ContractStatus status; 
    } 
 
    uint256 public contractCount; 
    mapping(uint256 => FarmingContract) public contracts; 
     
    event ContractCreated(uint256 contractId, address farmer, string cropDetails, uint256 price); 
    event ContractAccepted(uint256 contractId, address buyer); 
    event ContractDelivered(uint256 contractId); 
    event ContractDisputed(uint256 contractId); 
    event PaymentReleased(uint256 contractId, address farmer); 
    event RefundIssued(uint256 contractId, address buyer); 
 
    function createContract(string memory _cropDetails, uint256 _price, uint256 _deliveryDate) 
external { 
        require(_deliveryDate > block.timestamp, "Invalid delivery date"); 
 
        contractCount++; 
        contracts[contractCount] = FarmingContract( 
            contractCount,  
            payable(msg.sender),  
            payable(address(0)),  
            _cropDetails,  
            _price,  
            _deliveryDate,  
            ContractStatus.Created 
        ); 
 
        emit ContractCreated(contractCount, msg.sender, _cropDetails, _price); 
    } 
 
    function acceptContract(uint256 _contractId) external payable { 
        FarmingContract storage farmingContract = contracts[_contractId]; 
        require(farmingContract.status == ContractStatus.Created, "Contract not available"); 
        require(msg.value == farmingContract.price, "Incorrect payment amount"); 
 
        farmingContract.buyer = payable(msg.sender); 
        farmingContract.status = ContractStatus.Accepted; 
 
        emit ContractAccepted(_contractId, msg.sender); 
    } 
 
    function confirmDelivery(uint256 _contractId) public { 
        FarmingContract storage farmingContract = contracts[_contractId]; 
        require(msg.sender == farmingContract.farmer, "Only farmer can confirm"); 
        require(farmingContract.status == ContractStatus.Accepted, "Contract not in accepted state"); 
 
        farmingContract.status = ContractStatus.Delivered; 
        farmingContract.farmer.transfer(farmingContract.price); 
         
        emit ContractDelivered(_contractId); 
        emit PaymentReleased(_contractId, farmingContract.farmer); 
    } 
 
    function disputeContract(uint256 _contractId) external { 
        FarmingContract storage farmingContract = contracts[_contractId]; 
        require(msg.sender == farmingContract.buyer, "Only buyer can dispute"); 
        require(farmingContract.status == ContractStatus.Accepted, "Contract not in accepted state"); 
 
        farmingContract.status = ContractStatus.Disputed; 
 
        emit ContractDisputed(_contractId); 
    } 
 
    function resolveDispute(uint256 _contractId, bool refundBuyer) external { 
    // Assuming an admin or arbitration mechanism exists 
    FarmingContract storage farmingContract = contracts[_contractId]; 
    require(farmingContract.status == ContractStatus.Disputed, "No dispute to resolve"); 
 
    if (refundBuyer) { 
        farmingContract.buyer.transfer(farmingContract.price); 
        emit RefundIssued(_contractId, farmingContract.buyer); 
    } else { 
        farmingContract.farmer.transfer(farmingContract.price); 
        emit PaymentReleased(_contractId, farmingContract.farmer); 
    } 
 
    farmingContract.status = ContractStatus.Completed; 
} 
}