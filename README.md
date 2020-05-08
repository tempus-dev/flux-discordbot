# Flux
[![Build Status](https://travis-ci.com/tempus-dev/flux-discordbot.svg?branch=master)](https://travis-ci.com/tempus-dev/flux-discordbot)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Your one stop shop for everything productivity. Flux is specifically designed to help you stay on track, and make sure your peers work together well too!

## Quick Information Display

This allows for you to see what projects you've got open and what the status is on it.
Each project has it's own channel, where the bot keeps everything up to date.

## Assignments

You can assign tasks to members, they can assign volunteer tasks to themselves, and more! These all contribute towards the end goal of the project.

## Reward system

With assignments, you can reward your team for getting stuff done early/on time! One might get 500 points for completing a certain task early, and could get promoted for it!
This gives good incentive to make sure everyone is on task and productive. But as with any reward system, bad behavior is punished. Missing deadlines will deduct points.

## Reminders

We make sure to constantly check up with your team, to keep them working. This removes any excuses that "I forgot" or "I didn't realize I was doing this!".
They can dismiss these reminders by claiming they've completed the assigned task, and the task'll get sent to the team lead to make sure it's been done.
If the task wasn't done properly/well, it can be sent back. Naturally, if a task wasn't completed at all and they claim they did, points can be deducted.

## Leaderboard

Now, a toggleable leaderboard that shows who does the most and gets the most done is always helpful. This is a quick and easy way to see who's underperforming.

## Development instructions

```bash
git clone https://github.com/tempus-dev/flux-discordbot
cd flux-discordbot
python3 -m pip install -r requirements.txt
python3 -m pip install -r requirements-dev.txt # Optional, install dev dependencies
cp config.json.example config.json # make sure to edit config.json
python3 main.py
```
