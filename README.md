<p align="center">
  <a href="https://github.com/Yasin-Dev81/tribon-sokhanrani-bot" target="_blank" rel="noopener noreferrer">
<!--     <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/Yasin-Dev81/tribon-sokhanrani-bot/master/logo.jpg">
      <img width="160" height="160" src="https://raw.githubusercontent.com/Yasin-Dev81/tribon-sokhanrani-bot/master/logo.jpg">
    </picture> -->
  </a>
</p>

<h1 align="center"/>Tribon Sokhanrani Bot</h1>

<p align="center">
    Telegram Bot Powered by <a href="https://github.com/pyrogram/pyrogram">Pyrogram</a>
</p>

<br/>

## Table of Contents

- [Overview](#overview)
- [Features](#Features)
- [Configuration](#configuration)
- [How to use](#how_to_use)
- [Donation](#donation)

# Overview
This Telegram bot is designed to streamline educational and task management processes, offering tailored functionalities for different user roles, including admins, mentors, and users. Below is an outline of its core features

# Features
- Definition of new exercise
- Exercise management
- Viewing the necessary training information such as question title, question text, deadline, etc. for mentor and user
- Viewing the necessary information of the exercise along with a summary report of the status of that exercise's assignments for the admin
- Creating and managing users
- Support for **several types of users (online, in-person, etc.) and defining separate exercises for each group**
- Creating and managing teachers (mentors)
- Task management
- Viewing the unanalyzed (uncorrected) assignments and assigning them to the mentor
- Send notifications separately for users, teachers, admins and all users
- View performance report for admin

# Preview
- [How to use a bot on the user side](https://t.me/sokhanrani/1389)
- [Database structure](https://t.me/sokhanrani/1389)

<p align="center">
  <b>Admin Panel</b> | <b>Mentor Panel</b>
</p>
<p align="center">
  <a href="https://github.com/Yasin-Dev81/tribon-sokhanrani-bot" target="_blank" rel="noopener noreferrer">
    <img src="https://raw.githubusercontent.com/Yasin-Dev81/tribon-sokhanrani-bot/master/admin-panel.jpg" alt="Admin Panel Screenshot" width="300" height="625">
  </a>
  <a href="https://github.com/Yasin-Dev81/tribon-sokhanrani-bot" target="_blank" rel="noopener noreferrer">
    <img src="https://raw.githubusercontent.com/Yasin-Dev81/tribon-sokhanrani-bot/master/teacher-panel.jpg" alt="Mentor Panel Screenshot" width="300" height="625">
  </a>
</p>



# Configuration

> You can set settings below using environment variables or placing them in `.env` file.

| Variable                                 | Description                                                                                                              |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------------------ |
| TELL_CONFIG                              | Telegram Config                                                                                                          |
| BOT_TOKEN                                | Telegram Api                                                                                                             |
| BOT_TOKEN                                | Telegram Api                                                                                                             |
| API_HASH                                 | Telegram Api                                                                                                             |
| SQLALCHEMY_DATABASE_URL                  | Database URL ([SQLAlchemy's docs](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls))                    |
| ADMINS_LIST_ID                           | List of Admins                                                                                                           |
| GROUP_CHAT_ID                            | Group ID for save media                                                                                                  |
| PRACTICES_PER_PAGE                       | pagination                                                                                                               |
| LEARN_URL                                | url for usage learn                                                                                                      |


# How to use

Follow the steps below to set up the Tribon bot on your server:

## Step 1: Update the System  
Run the following command to update your system's package list:  
```bash
sudo apt-get update
```

## Step 2: Install Docker  
Download and install Docker using the official installation script:  
```bash
curl -fsSL https://get.docker.com | sh
```

## Step 3: Clone the Repository  
Clone the Tribon bot's repository to your system:  
```bash
git clone https://github.com/Yasin-Dev81/tribon-sokhanrani-bot.git /opt/tribon
```

## Step 4: Navigate to the Project Directory  
Move into the project directory where the bot files are located:  
```bash
cd /opt/tribon
```

## Step 5: Configure Environment Variables  
Edit the `.env` file to configure the necessary environment variables for the bot. Use the following command to open the file in a text editor:  
```bash
nano .env
```
> **Note:** Replace placeholder values in the `.env` file with the appropriate configuration details, such as API keys or database credentials.  

## Step 6: Start the Bot  
Launch the bot using Docker Compose:  
```bash
docker compose up -d
```
This command will build and start the bot in detached mode.  

## You're Done!  
The Tribon bot is now deployed and running. Use the following command to verify that the container is active:  
```bash
docker ps
```

Enjoy using your bot!

# Donation

If you found Marzban useful and would like to support its development, you can make a donation in one of the following crypto networks:
- Bitcoin network: `bc1qpys2nefgsjjgae3g3gqy9crsv3h3rm96tlkz0v`

Thank you for your support!
