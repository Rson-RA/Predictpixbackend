// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";

contract PredictionMarket is Ownable, ReentrancyGuard {
    struct Market {
        uint256 id;
        string title;
        string description;
        uint256 endTime;
        uint256 resolutionTime;
        uint256 totalPool;
        uint256 yesPool;
        uint256 noPool;
        uint8 creatorFeePercentage;
        uint8 platformFeePercentage;
        bool isResolved;
        bool outcome;
        address creator;
    }

    struct Prediction {
        uint256 marketId;
        address user;
        uint256 amount;
        bool predictedOutcome;
        bool isClaimed;
    }

    // Constants
    uint256 public constant MIN_MARKET_DURATION = 1 hours;
    uint256 public constant MIN_RESOLUTION_DELAY = 1 hours;
    uint8 public constant MAX_FEE_PERCENTAGE = 10;

    // State variables
    uint256 public marketCount;
    mapping(uint256 => Market) public markets;
    mapping(uint256 => Prediction[]) public predictions;
    mapping(address => uint256) public userBalances;
    mapping(uint256 => mapping(address => uint256)) public userPredictions;

    // Events
    event MarketCreated(
        uint256 indexed marketId,
        address indexed creator,
        string title,
        uint256 endTime
    );
    event PredictionMade(
        uint256 indexed marketId,
        address indexed user,
        uint256 amount,
        bool predictedOutcome
    );
    event MarketResolved(
        uint256 indexed marketId,
        bool outcome,
        uint256 totalPool
    );
    event RewardClaimed(
        uint256 indexed marketId,
        address indexed user,
        uint256 amount
    );

    constructor() Ownable() {}

    function createMarket(
        string memory title,
        string memory description,
        uint256 endTime,
        uint256 resolutionTime,
        uint8 creatorFeePercentage,
        uint8 platformFeePercentage
    ) external {
        require(bytes(title).length > 0, "Title cannot be empty");
        require(endTime > block.timestamp + MIN_MARKET_DURATION, "Invalid end time");
        require(
            resolutionTime >= endTime + MIN_RESOLUTION_DELAY,
            "Invalid resolution time"
        );
        require(
            creatorFeePercentage + platformFeePercentage <= MAX_FEE_PERCENTAGE,
            "Total fees too high"
        );

        uint256 marketId = marketCount++;
        markets[marketId] = Market({
            id: marketId,
            title: title,
            description: description,
            endTime: endTime,
            resolutionTime: resolutionTime,
            totalPool: 0,
            yesPool: 0,
            noPool: 0,
            creatorFeePercentage: creatorFeePercentage,
            platformFeePercentage: platformFeePercentage,
            isResolved: false,
            outcome: false,
            creator: msg.sender
        });

        emit MarketCreated(marketId, msg.sender, title, endTime);
    }

    function placePrediction(
        uint256 marketId,
        bool predictedOutcome
    ) external payable nonReentrant {
        Market storage market = markets[marketId];
        require(block.timestamp < market.endTime, "Market closed");
        require(msg.value > 0, "Amount must be greater than 0");

        // Update pools
        market.totalPool += msg.value;
        if (predictedOutcome) {
            market.yesPool += msg.value;
        } else {
            market.noPool += msg.value;
        }

        // Create prediction
        predictions[marketId].push(
            Prediction({
                marketId: marketId,
                user: msg.sender,
                amount: msg.value,
                predictedOutcome: predictedOutcome,
                isClaimed: false
            })
        );

        // Update user's prediction amount
        userPredictions[marketId][msg.sender] += msg.value;

        emit PredictionMade(marketId, msg.sender, msg.value, predictedOutcome);
    }

    function resolveMarket(
        uint256 marketId,
        bool outcome
    ) external onlyOwner {
        Market storage market = markets[marketId];
        require(block.timestamp >= market.resolutionTime, "Too early to resolve");
        require(!market.isResolved, "Market already resolved");

        market.isResolved = true;
        market.outcome = outcome;

        emit MarketResolved(marketId, outcome, market.totalPool);
    }

    function claimReward(uint256 marketId) external nonReentrant {
        Market storage market = markets[marketId];
        require(market.isResolved, "Market not resolved");

        uint256 totalUserPredictions = userPredictions[marketId][msg.sender];
        require(totalUserPredictions > 0, "No predictions to claim");

        uint256 rewardAmount = calculateReward(
            marketId,
            msg.sender,
            market.outcome
        );
        require(rewardAmount > 0, "No rewards to claim");

        // Mark predictions as claimed
        for (uint256 i = 0; i < predictions[marketId].length; i++) {
            if (
                predictions[marketId][i].user == msg.sender &&
                predictions[marketId][i].predictedOutcome == market.outcome &&
                !predictions[marketId][i].isClaimed
            ) {
                predictions[marketId][i].isClaimed = true;
            }
        }

        // Update user's prediction amount
        userPredictions[marketId][msg.sender] = 0;

        // Transfer reward
        (bool success, ) = msg.sender.call{value: rewardAmount}("");
        require(success, "Transfer failed");

        emit RewardClaimed(marketId, msg.sender, rewardAmount);
    }

    function calculateReward(
        uint256 marketId,
        address user,
        bool outcome
    ) public view returns (uint256) {
        Market storage market = markets[marketId];
        if (!market.isResolved) return 0;

        uint256 totalUserPredictions = userPredictions[marketId][user];
        if (totalUserPredictions == 0) return 0;

        uint256 winningPool = outcome ? market.yesPool : market.noPool;
        if (winningPool == 0) return 0;

        // Calculate total fees
        uint256 totalFees = (market.totalPool *
            (market.creatorFeePercentage + market.platformFeePercentage)) / 100;
        uint256 poolAfterFees = market.totalPool - totalFees;

        // Calculate proportional share
        return (totalUserPredictions * poolAfterFees) / winningPool;
    }

    function getMarket(uint256 marketId)
        external
        view
        returns (
            string memory title,
            string memory description,
            uint256 endTime,
            uint256 resolutionTime,
            uint256 totalPool,
            uint256 yesPool,
            uint256 noPool,
            bool isResolved,
            bool outcome
        )
    {
        Market storage market = markets[marketId];
        return (
            market.title,
            market.description,
            market.endTime,
            market.resolutionTime,
            market.totalPool,
            market.yesPool,
            market.noPool,
            market.isResolved,
            market.outcome
        );
    }

    function getUserPredictions(uint256 marketId, address user)
        external
        view
        returns (uint256)
    {
        return userPredictions[marketId][user];
    }

    // Emergency functions
    function emergencyWithdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
} 