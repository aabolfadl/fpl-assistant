# Test Queries for All Cypher Templates

## PLAYER PERFORMANCE & COMPARISON (9 queries)

1. **PLAYER_STATS_GW_SEASON**

   - "What were Mohamed Salah's stats in gameweek 5 of the 2021-22 season?"

2. **COMPARE_PLAYERS_BY_TOTAL_POINTS**

   - "Compare Erling Haaland and Harry Kane by total points"

3. **COMPARE_PLAYERS_BY_SPECIFIC_STAT_TOTAL_ALL_TIME**

   - "Compare Mohamed Salah and Kevin De Bruyne in total assists"

4. **COMPARE_PLAYERS_BY_SPECIFIC_STAT_AVG**

   - "Compare Bukayo Saka and Phil Foden by average goals scored"

5. **PLAYER_CAREER_STATS_TOTALS**

   - "Show me Mohamed Salah's career stats totals"

6. **PLAYER_SPECIFIC_STAT_SUM**

   - "How many goals has Harry Kane scored in total?"

7. **PLAYER_SPECIFIC_STAT_AVG**

   - "What is Kevin De Bruyne's average assists per game?"

8. **PLAYER_SPECIFIC_STAT_SUM_SPECIFIC_SEASON**

   - "How many clean sheets did Ederson get in the 2022-23 season?"

9. **PLAYER_SPECIFIC_STAT_AVG_SPECIFIC_SEASON**
   - "What was Mohamed Salah's average goals scored in the 2021-22 season?"

## TOP PERFORMERS & LEADERBOARDS (8 queries)

10. **TOP_PLAYERS_BY_STAT**

    - "Who are the top 5 players by total goals scored?"

11. **TOP_PLAYERS_BY_POSITION_IN_POINTS**

    - "Show me the top 5 midfielders by total points"

12. **TOP_PLAYERS_BY_POSITION_IN_FORM**

    - "Who are the top 5 forwards by form?"

13. **TOP_PLAYERS_UNDER_BUDGET_SPECIFIC_POSITION_SPECIFIC_SEASON**

    - "Show me the best defenders under 6.0 in the 2022-23 season (limit 5)"

14. **TOP_SUM_OF_SPECIFIC_STAT_LEADERS**

    - "Who are the top 5 assist leaders?"

15. **TOP_SUM_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION**

    - "Who are the top 5 goalkeepers by clean sheets?"

16. **TOP_AVG_OF_SPECIFIC_STAT_LEADERS**

    - "Who has the best average bonus points? Show top 5"

17. **TOP_AVG_OF_SPECIFIC_STAT_LEADERS_SPECIFIC_POSITION**
    - "Which 5 strikers have the best average goals scored?"

## COMPOUND & DERIVED STATS (9 queries)

18. **MOST_CARDS_LEADERS**

    - "Who are the top 5 players with the most yellow and red cards?"

19. **MOST_GOAL_CONTRIBUTIONS**

    - "Show me the top 5 players by goal contributions (goals + assists)"

20. **MINUTES_PER_POINT_LEADERS**

    - "Who has the best minutes per point ratio? Top 5"

21. **PLAYER_MINUTES_PER_POINT**

    - "What is Mohamed Salah's minutes per point ratio?"

22. **PLAYER_MINUTES_PER_POINT_SPECIFIC_SEASON**

    - "What was Erling Haaland's minutes per point ratio in the 2022-23 season?"

23. **PLAYER_TOTAL_CARDS**

    - "How many cards has Casemiro received in total?"

24. **PLAYER_GOAL_CONTRIBUTIONS**

    - "What are Harry Kane's total goal contributions?"

25. **PLAYER_GOAL_CONTRIBUTIONS_SPECIFIC_SEASON**

    - "How many goal contributions did Mohamed Salah have in the 2021-22 season?"

26. **PLAYER_TOTAL_CARDS_SPECIFIC_SEASON**
    - "How many cards did Bruno Fernandes get in the 2022-23 season?"

## TEAM ANALYSIS & AGGREGATES (14 queries)

27. **GET_TEAM_DEFENSE_STRENGTH**

    - "What is Liverpool's average goals conceded per game?"

28. **GET_TEAM_DEFENSE_STRENGTH_SPECIFIC_SEASON**

    - "What was Man City's defensive strength in the 2022-23 season?"

29. **GET_TEAM_ATTACK_STRENGTH**

    - "What is Arsenal's average goals scored per game?"

30. **GET_TEAM_ATTACK_STRENGTH_SPECIFIC_SEASON**

    - "What was Liverpool's attack strength in the 2021-22 season?"

31. **TEAM_AVG_GOALS_CONCEDED_HOME_AWAY**

    - "Show me Chelsea's average goals conceded at home vs away"

32. **LEADING_TEAMS_BY_CLEAN_SHEETS**

    - "Which teams have the most clean sheets? Top 5"

33. **TEAM_TOTAL_CLEAN_SHEETS_SPECIFIC_SEASON**

    - "How many clean sheets did Man City have in the 2022-23 season?"

34. **TEAM_TOTAL_CLEAN_SHEETS_ALL_SEASONS**

    - "What are Liverpool's total clean sheets across all seasons?"

35. **TEAM_TOTAL_GOALS_SCORED_SPECIFIC_SEASON**

    - "How many goals did Arsenal score in the 2022-23 season?"

36. **TEAM_TOTAL_GOALS_SCORED_ALL_SEASONS**

    - "What are Man City's total goals scored across all seasons?"

37. **LEADING_TEAMS_BY_GOALS_SCORED**

    - "Which are the top 5 teams by goals scored?"

38. **GET_FIXTURES_BETWEEN_TEAMS**

    - "Show me all fixtures between Liverpool and Man Utd"

39. **PLAYER_POINTS_VS_SPECIFIC_TEAM**
    - "How many points has Mohamed Salah scored against Man Utd?"

## PLAYER VALUE & RECENT PERFORMANCE (2 queries)

40. **TOP_VALUE_FOR_MONEY_SPECIFIC_POSITION**

    - "Which defenders offer the best value for money? Top 5"

41. **PLAYER_LAST_N_FIXTURES_PERFORMANCE**
    - "Show me Erling Haaland's last 5 fixtures and points"

## PLAYER APPEARANCES, SPLITS & CONSISTENCY (9 queries)

42. **PLAYER_MAX_SPECIFIC_STAT_SINGLE_MATCH**

    - "What is the maximum goals scored by Harry Kane in a single match?"

43. **PLAYER_FIXTURE_COUNT_SPECIFIC_SEASON**

    - "How many matches did Bukayo Saka play in the 2022-23 season?"

44. **PLAYER_FIXTURE_COUNT_TOTAL**

    - "How many total matches has Kevin De Bruyne appeared in?"

45. **PLAYER_POINTS_HOME_VS_AWAY**

    - "Show me Mohamed Salah's points at home vs away"

46. **PLAYER_BEST_PERFORMANCE_AGAINST_WHICH_OPPONENTS**

    - "Against which teams has Erling Haaland performed best? Top 5"

47. **PLAYER_WORST_PERFORMANCE_AGAINST_WHICH_OPPONENTS**

    - "Against which teams has Harry Kane struggled most? Top 5"

48. **TEAM_MOST_IMPACTFUL_PLAYER**

    - "Who is the most impactful player for Liverpool?"

49. **POSITION_BEST_AVG_POINTS**

    - "Which position has the best average points?"

50. **POSITION_PLAYERS_COUNT**

    - "How many players are there in each position?"

51. **LEAST_CONSISTENT_PLAYERS**
    - "Who are the 5 most inconsistent players?"

---

## Notes:

- Replace player/team names with actual names from your database
- For queries with `$limit`, the number in the prompt (5, 10) will be used
- For queries with `$budget`, use a realistic FPL price (e.g., 6.0, 10.5)
- For `$stat_property`, use valid properties from your schema (goals_scored, assists, clean_sheets, bonus, etc.)
- Seasons should be in format "2021-22" or "2022-23"
- Gameweeks should be numbers 1-38
