# <p align="center">🥷 ByNinja Trading Bot</p>

### Automated Crypto Trading Integration
Run automated trading strategies locally, execute operations on the **Binance** spot market, and monitor performance via **Telegram**.

The **ByNinja** core engine utilizes a multi-layer Exponential Moving Average (EMA) trend continuation algorithm designed for high-momentum assets. The system performs real-time scanning of configured trading pairs, filtering entry points based on structural breakouts and volume confirmations.

[**Official Website**](https://byninja-trading.com) | [**Documentation**](https://byninja-trading.com/documentation) | [**Knowledge Base**](https://byninja-trading.com/knowledge-base) | [**X (Twitter)**](https://x.com/ByNinjaTrading)

<br>

## Getting Started

> [!TIP]
> To ensure maximum security and low-latency execution, it is recommended to deploy the bot on a dedicated local machine or a private VPS instance.

### [Quick Start](https://byninja-trading.com/documentation/quick-start)
* **Environment Setup** – Preparing the host environment (Python 3.10+).
* **Python Virtual Environment** – Isolating dependencies using `venv`.
* **Install Dependencies** – Installing required modules via `pip`.

### [Binance Setup](https://byninja-trading.com/documentation/binance-setup)
* **Create Binance Account** – Step-by-step account onboarding.
* **Generate API Keys** – Creating secure connection credentials.
* **API Permissions Guide** – Configuring "Enable Spot Trading" without withdrawal permissions.
* **Security Recommendations** – IP whitelisting and key rotation best practices.

### [Telegram Setup](https://byninja-trading.com/documentation/telegram-setup)
* **Create Telegram Bot** – Registering a new bot instance via `@BotFather`.
* **Get Bot Token** – Acquiring secure credentials for remote API control.
* **Get Chat ID** – Restricting bot interaction to your specific Telegram account.

### [Bot Configuration](https://byninja-trading.com/documentation/bot-configuration)
* **Configure Trading Symbols** – Setting up target trading pairs and tickers.
* **Configure Risk Settings** – Defining custom Stop Loss, Take Profit, and position sizing parameters in `config.py`.

### [First Launch](https://byninja-trading.com/documentation/first-launch)
* **Start Scripts** – Initializing the execution engine and watchdog modules.
* **Expected Startup Logs** – Verifying API connectivity and synchronization states upon startup.

### [Telegram Commands](https://byninja-trading.com/documentation/telegram-commands)
* **Trading Commands** – Executing manual operations via chat.
* **Position Management** – Viewing and adjusting active trades.
* **Emergency Commands** – Instant panic-sell and global execution halt switches.
* **Monitoring Commands** – Fetching status updates, current PnL, and runtime metrics.

<br>

## Features & Architecture

- **Multi-Process Design**: Low-latency execution with dedicated processes for market monitoring and order routing.
- **EMA Engine**: Rule-based entry confirmation coupled with automated order tracking.
- **Persistence System**: Position state recovery mechanism to prevent data loss during sudden crashes.
- **Watchdog System**: Auto-restart automation ensuring 24/7 runtime stability.
- **Telegram Control**: Comprehensive interactive command interface for remote management.

<br>

## Legal & Compliance
- [Privacy Policy](https://byninja-trading.com/privacy-policy)
- [Risk Disclosure](https://byninja-trading.com/risk-disclosure)
- [Disclaimer](https://byninja-trading.com/disclaimer)
- [Terms of Service](https://byninja-trading.com/terms-of-service)

**Disclosure:** Links provided within the documentation may contain affiliate parameters. Project development is partially supported via optional exchange referral allocations.

<br>

<p align="center">
  <a href="https://www.binance.com/register?ref=487123052" target="_blank">
    <img src="https://img.shields.io/badge/Binance-F3BA2F?style=for-the-badge&logo=binance&logoColor=black" alt="Binance">
  </a>
  <a href="https://x.com/ByNinjaTrading" target="_blank">
    <img src="https://img.shields.io/badge/X_(Twitter)-000000?style=for-the-badge&logo=x&logoColor=white" alt="X (Twitter)">
  </a>
  <img src="https://img.shields.io/badge/Python-3.10+-black?style=for-the-badge&logo=python&logoColor=F3BA2F" alt="Python">
  <img src="https://img.shields.io/badge/Telegram-26A5E4?style=for-the-badge&logo=telegram&logoColor=white" alt="Telegram">
  <a href="https://partner.bybit.com/b/161454" target="_blank">
    <img src="https://img.shields.io/badge/Bybit-000000?style=for-the-badge&logo=bybit&logoColor=F3BA2F" alt="Bybit">
  </a>
</p>

<p align="center">
  Licensed under the <a href="./LICENSE">Apache License 2.0</a>.
</p>