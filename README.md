<h1 align="center"/>Tribon Sokhanrani Bot</h1>

<p align="center">
    Telegram Bot Powered by <a href="https://github.com/pyrogram/pyrogram">Pyrogram</a>
</p>

<br/>
<p align="center">
    <a href="#">
        <img src="https://img.shields.io/github/actions/workflow/status/gozargah/marzban/build.yml?style=flat-square" />
    </a>
    <a href="https://hub.docker.com/r/gozargah/marzban" target="_blank">
        <img src="https://img.shields.io/docker/pulls/gozargah/marzban?style=flat-square&logo=docker" />
    </a>
    <a href="#">
        <img src="https://img.shields.io/github/license/gozargah/marzban?style=flat-square" />
    </a>
    <a href="https://t.me/gozargah_marzban" target="_blank">
        <img src="https://img.shields.io/badge/telegram-group-blue?style=flat-square&logo=telegram" />
    </a>
    <a href="#">
        <img src="https://img.shields.io/badge/twitter-commiunity-blue?style=flat-square&logo=twitter" />
    </a>
    <a href="#">
        <img src="https://img.shields.io/github/stars/gozargah/marzban?style=social" />
    </a>
</p>



## Table of Contents

- [Overview](#overview)
  - [Why using Marzban?](#why-using-marzban)
    - [Features](#features)
- [Installation guide](#installation-guide)
- [Configuration](#configuration)
- [API](#api)
- [Backup](#backup)
- [Telegram Bot](#telegram-bot)
- [Marzban CLI](#marzban-cli)
- [Marzban Node](#marzban-node)
- [Webhook notifications](#webhook-notifications)
- [Donation](#donation)
- [License](#license)
- [Contributors](#contributors)

# Overview

pass

### Features

- Built-in **Web UI**
- Fully **REST API** backend
- [**Multiple Nodes**](#marzban-node) support (for infrastructure distribution & scalability)
- Supports protocols **Vmess**, **VLESS**, **Trojan** and **Shadowsocks**
- **Multi-protocol** for a single user
- **Multi-user** on a single inbound
- **Multi-inbound** on a **single port** (fallbacks support)
- **Traffic** and **expiry date** limitations
- **Periodic** traffic limit (e.g. daily, weekly, etc.)
- **Subscription link** compatible with **V2ray** _(such as V2RayNG, OneClick, Nekoray, etc.)_, **Clash** and **ClashMeta**
- Automated **Share link** and **QRcode** generator
- System monitoring and **traffic statistics**
- Customizable xray configuration
- **TLS** and **REALITY** support
- Integrated **Telegram Bot**
- Integrated **Command Line Interface (CLI)**
- **Multi-language**
- **Multi-admin** support (WIP)

# Installation guide

Run the following command

```bash
sudo bash -c "$(curl -sL https://github.com/Gozargah/Marzban-scripts/raw/master/marzban.sh)" @ install
```

Once the installation is complete:

- You will see the logs that you can stop watching them by closing the terminal or pressing `Ctrl+C`
- The Marzban files will be located at `/opt/marzban`
- The configuration file can be found at `/opt/marzban/.env` (refer to [configurations](#configuration) section to see variables)
- The data files will be placed at `/var/lib/marzban`
- You can access the Marzban dashboard by opening a web browser and navigating to `http://YOUR_SERVER_IP:8000/dashboard/` (replace YOUR_SERVER_IP with the actual IP address of your server)

Next, you need to create a sudo admin for logging into the Marzban dashboard by the following command

```bash
marzban cli admin create --sudo
```

That's it! You can login to your dashboard using these credentials

To see the help message of the Marzban script, run the following command

```bash
marzban --help
```

If you are eager to run the project using the source code, check the section below

# Configuration

> You can set settings below using environment variables or placing them in `.env` file.

| Variable                                 | Description                                                                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| SUDO_USERNAME                            | Superuser's username                                                                                                     |
| SUDO_PASSWORD                            | Superuser's password                                                                                                     |
| SQLALCHEMY_DATABASE_URL                  | Database URL ([SQLAlchemy's docs](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls))                    |
| UVICORN_HOST                             | Bind application to this host (default: `0.0.0.0`)                                                                       |
| UVICORN_PORT                             | Bind application to this port (default: `8000`)                                                                          |
| UVICORN_UDS                              | Bind application to a UNIX domain socket                                                                                 |
| UVICORN_SSL_CERTFILE                     | SSL certificate file to have application on https                                                                        |
| UVICORN_SSL_KEYFILE                      | SSL key file to have application on https                                                                                |
| XRAY_JSON                                | Path of Xray's json config file (default: `xray_config.json`)                                                            |
| XRAY_EXECUTABLE_PATH                     | Path of Xray binary (default: `/usr/local/bin/xray`)                                                                     |
| XRAY_ASSETS_PATH                         | Path of Xray assets (default: `/usr/local/share/xray`)                                                                   |
| XRAY_SUBSCRIPTION_URL_PREFIX             | Prefix of subscription URLs                                                                                              |
| XRAY_FALLBACKS_INBOUND_TAG               | Tag of the inbound that includes fallbacks, needed in the case you're using fallbacks                                    |
| XRAY_EXCLUDE_INBOUND_TAGS                | Tags of the inbounds that shouldn't be managed and included in links by application                                      |
| CUSTOM_TEMPLATES_DIRECTORY               | Customized templates directory (default: `app/templates`)                                                                |
| CLASH_SUBSCRIPTION_TEMPLATE              | The template that will be used for generating clash configs (default: `clash/default.yml`)                               |
| SUBSCRIPTION_PAGE_TEMPLATE               | The template used for generating subscription info page (default: `subscription/index.html`)                             |
| HOME_PAGE_TEMPLATE                       | Decoy page template (default: `home/index.html`)                                                                         |
| TELEGRAM_API_TOKEN                       | Telegram bot API token  (get token from [@botfather](https://t.me/botfather))                                            |
| TELEGRAM_ADMIN_ID                        | Numeric Telegram ID of admin (use [@userinfobot](https://t.me/userinfobot) to found your ID)                             |
| TELEGRAM_PROXY_URL                       | Run Telegram Bot over proxy                                                                                              |
| JWT_ACCESS_TOKEN_EXPIRE_MINUTES          | Expire time for the Access Tokens in minutes, `0` considered as infinite (default: `1440`)                               |
| DOCS                                     | Whether API documents should be available on `/docs` and `/redoc` or not (default: `False`)                              |
| DEBUG                                    | Debug mode for development (default: `False`)                                                                            |
| WEBHOOK_ADDRESS                          | Webhook address to send notifications to. Webhook notifications will be sent if this value was set.                      |
| WEBHOOK_SECRET                           | Webhook secret will be sent with each request as `x-webhook-secret` in the header (default: `None`)                      |
| NUMBER_OF_RECURRENT_NOTIFICATIONS        | How many times to retry if an error detected in sending a notification (default: `3`)                                    |
| RECURRENT_NOTIFICATIONS_TIMEOUT          | Timeout between each retry if an error detected in sending a notification in seconds (default: `180`)                    |
| NOTIFY_REACHED_USAGE_PERCENT             | At which percentage of usage to send the warning notification (default: `80`)                                            |
| NOTIFY_DAYS_LEFT                         | When to send warning notifaction about expiration (default: `3`)                                                         |
| USERS_AUTODELETE_DAYS                    | Delete expired (and optionally limited users) after this many days (Negative values disable this feature, default: `-1`) |
| USER_AUTODELETE_INCLUDE_LIMITED_ACCOUNTS | Weather to include limited accounts in the auto-delete feature (default: `False`)                                        |
| USE_CUSTOM_JSON_DEFAULT                  | Enable custom JSON config for ALL supported clients (default: `False`)                                                   |
| USE_CUSTOM_JSON_FOR_V2RAYNG              | Enable custom JSON config only for V2rayNG (default: `False`)                                                            |
| USE_CUSTOM_JSON_FOR_STREISAND            | Enable custom JSON config only for Streisand (default: `False`)                                                          |
| USE_CUSTOM_JSON_FOR_V2RAYN               | Enable custom JSON config only for V2rayN (default: `False`)                                                             |

# Backup

It's always a good idea to backup your Marzban files regularly to prevent data loss in case of system failures or accidental deletion. Here are the steps to backup Marzban:

1. By default, all Marzban important files are saved in `/var/lib/marzban` (Docker versions). Copy the entire `/var/lib/marzban` directory to a backup location of your choice, such as an external hard drive or cloud storage.
2. Additionally, make sure to backup your env file, which contains your configuration variables, and also, your Xray config file. If you installed Marzban using marzban-scripts (recommended installation approach), the env and other configurations should be inside `/opt/marzban/` directory.

By following these steps, you can ensure that you have a backup of all your Marzban files and data, as well as your configuration variables and Xray configuration, in case you need to restore them in the future. Remember to update your backups regularly to keep them up-to-date.

# Donation

If you found Marzban useful and would like to support its development, you can make a donation in one of the following crypto networks:

- TRON network (TRC20): `TX8kJoDcowQPBFTYHAJR36GyoUKP1Xwzkb`
- ETH, BNB, MATIC network (ERC20, BEP20): `0xFdc9ad32454FA4fc4733270FCc12ddBFb68b83F7`
- Bitcoin network: `bc1qpys2nefgsjjgae3g3gqy9crsv3h3rm96tlkz0v`
- Dogecoin network: `DJAocBAu8y6LwhDKUktLAyzV8xyoFeHH6R`
- TON network: `EQAVf-7hAXHlF-jmrKE44oBwN7HGQFVBLAtrOsev5K4qR4P8`

Thank you for your support!

<p align="center">
  <a href="https://github.com/gozargah/marzban" target="_blank" rel="noopener noreferrer" >
    <img src="https://github.com/Gozargah/Marzban-docs/raw/master/screenshots/preview.png" alt="Marzban screenshots" width="600" height="auto">
  </a>
</p>
