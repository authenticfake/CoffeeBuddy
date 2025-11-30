## TODO_NEXT

- Implement channel-scoped rate limiting to guard against slash-command flooding and provide clearer Slack error messaging.
- Introduce background retention job that prunes runs/preferences beyond `data_retention_days` without manual admin intervention.
- Expand reminder scheduling to support multiple offsets (e.g., runner + participants) configurable per channel.
- Add audit export endpoints or integrations (e.g., pushing `ChannelAdminAction` records to SIEM) for enterprise compliance teams.
- Provide localization scaffolding to prepare for multilingual UX once pilot feedback requests it.