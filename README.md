# Opus

Your one stop shop for everything productivity. Opus is specifically designed to help you stay on track, and make sure your peers work together well too!



## Detailed Feature List 

This details all the features of the bot. 


### Quick Information Display

This allows for you to see what projects you've got open and what the status is on it.
Each project has it's own channel, where the bot keeps everything up to date.

### Assignments 

You can assign tasks to members, they can assign volunteer tasks to themselves, and more! These all contribute towards the end goal of the project.

### Reward system

With assignments, you can reward your team for getting stuff done early/on time! One might get 500 points for completing a certain task early, and could get promoted for it!
This gives good incentive to make sure everyone is on task and productive. But as with any reward system, bad behavior is punished. Missing deadlines will deduct points.

### Reminders

We make sure to constantly check up with your team, to keep them working. This removes any excuses that "I forgot" or "I didn't realize I was doing this!".
They can dismiss these reminders by claiming they've completed the assigned task, and the task'll get sent to the team lead to make sure it's been done.
If the task wasn't done properly/well, it can be sent back. Naturally, if a task wasn't completed at all and they claim they did, points can be deducted.

### Leaderboard

Now, a togglable leaderboard that shows who does the most and gets the most done is always helpful. This is a quick and easy way to see who's underperforming.



## Development instructions

Below contains everything related to the development of the bot.


### Prerequisites

- Make sure you're using minimum Python 3.6.
- Have a MongoDB server setup somewhere, that'll be required to have all the functions of the bot properly started.
- If not using Windows, make sure to install uvloop! `python3 -m pip install uvloop`

### Run Bot

- Start by installing the requirements with `python3 -m pip install -r requirements.txt`
- Then do `python3 main.py` to have it start!

### Rules

- Don't copy any code at all, it should all be written by you.
- Only use open source libraries.
- Make sure to keep up with the task assigned to you.