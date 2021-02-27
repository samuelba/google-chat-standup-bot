# Google Chat Standup Bot

This is a Google Chat bot to ask the users the three standup questions. 
After the questions have been answered, the bot will publish the answers to the group chat of the team. 
The standup questions can be either triggered automatically by a user configurable schedule, or manually by the user.

## Supported Slash Commands

| Command | Description |
| ------- | ----------- |
| `/standup` | Triggers the standup questions. This can also retrigger the standup questions, if you made a mistake. |
| `/users [TEAM]` | List the users of the bot, optional filtered by the team. |
| `/teams` | List the available teams. |
| `/add_team TEAM` | Add a new team. |
| `/set_team_webhook "TEAM" WEBHOOK` | Set the webhook for the team. |
| `/join_team TEAM` | Trigger to join another team. Will display an interactive card with teams to join. |
| `/schedules` | List the schedules. |
| `/enable_schedule WEEKDAY` | Enable the schedule of the weekday. |
| `/disable_schedule WEEKDAY` | Disable the schedule of the weekday. |
| `/change_schedule_time WEEKDAY TIME` | Change the schedule time of the weekday. |

## Google Chat Setup

TBD

## Traefik

For the Traefik reverse proxy setup look at my [cloud-services](https://github.com/samuelba/cloud-services/tree/master/traefik) repository.
