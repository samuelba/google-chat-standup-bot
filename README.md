# Google Chat Standup Bot

This is a Google Chat bot to ask the users the three standup questions. 
After the questions have been answered, the bot will publish the answers to the group chat of the team. 
The standup questions can be either triggered automatically by a user configurable schedule, or manually by the user.

## Supported Slash Commands

| Command | Description | id |
| ------- | ----------- | ---|
| `/standup` | Triggers the standup questions. This can also retrigger the standup questions, if you made a mistake. | 6 |
| `/users [TEAM]` | List the users of the bot, optional filtered by the team. | 5 |
| `/teams` | List the available teams. | 3 |
| `/add_team TEAM` | Add a new team. | 1 |
| `/set_team_webhook "TEAM" WEBHOOK` | Set the webhook for the team. | 2 |
| `/join_team TEAM` | Trigger to join another team. Will display an interactive card with teams to join. | 4 |
| `/schedules` | List the schedules. | 10 |
| `/enable_schedule WEEKDAY` | Enable the schedule of the weekday. | 8 |
| `/disable_schedule WEEKDAY` | Disable the schedule of the weekday. | 7 |
| `/change_schedule_time WEEKDAY TIME` | Change the schedule time of the weekday. | 9 |

## Google Chat Setup

TBD

## Traefik

For the Traefik reverse proxy setup look at my [cloud-services](https://github.com/samuelba/cloud-services/tree/master/traefik) repository.
