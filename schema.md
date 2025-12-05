# Project Schemas

## Knowledge Graph (Neo4j) Schema:

### Nodes:

- Season: [season_name]
- Gameweek: [season, GW_number]
- Fixture: [season, fixture_number], kickoff_time
- Team: [name]
- Player: [player_name, player_element]
- Position: [name]

### Relationships:

- (Season) - [:HAS_GW]-> (Gameweek)
- (Gameweek) - [:HAS_FIXTURE]-> (Fixture)
- (Fixture) - [:HAS_HOME_TEAM]-> (Team)
- (Fixture) - [:HAS_AWAY_TEAM]-> (Team)
- (Player) - [:PLAYS_AS]-> (Position)
- (Player) - [:PLAYED_IN]-> (Fixture);

#### Properties:

minutes, goals_scored, assists, total_points, bonus, clean_sheets, goals_conceded, own_goals, penalties_saved, penalties_missed, yellow_cards, red_cards, saves, bps, influence, creativity, threat, ict_index, form

## `fpl_two_seasons.csv` Schema:

season,name,position,assists,bonus,bps,clean_sheets,creativity,element,fixture,goals_conceded,goals_scored,ict_index,influence,kickoff_time,minutes,own_goals,penalties_missed,penalties_saved,red_cards,saves,selected,team_a_score,team_h_score,threat,total_points,transfers_balance,transfers_in,transfers_out,value,yellow_cards,GW,form,home_team,away_team

- This .csv was used to logically construct and populate the Knowledge Graph above.

Useful numerical features: [assists,goals,bonus,clean_sheets,creativity,bps,goals_conceded,goals_scored,ict_index,influence,minutes,own_goals,penalties_missed,penalties_saved,red_cards,saves,selected,threat,total_points,transfers_balance,transfers_in,transfers_out,value,yellow_cards,form]

---
