# config/stat_variants.py

# Map possible stat variants to canonical form
STAT_VARIANTS = {
    "assists": ["assist", "assists"],
    "goals": ["goal", "goals", "scored"],
    "bonus": ["bonus", "bps"],  # bps also maps here
    "clean_sheets": ["clean sheet", "clean sheets", "cs"],
    "creativity": ["creativity"],
    "bps": ["bps", "bonus point system"],
    "goals_conceded": ["conceded", "goals conceded", "goals_allowed"],
    "goals_scored": ["goals scored", "scored goals"],
    "ict_index": ["ict", "ict index"],
    "influence": ["influence"],
    "minutes": ["minutes", "mins", "played minutes"],
    "own_goals": ["own goal", "own goals"],
    "penalties_missed": ["penalty missed", "penalties missed", "pen_missed"],
    "penalties_saved": ["penalty saved", "penalties saved", "pen_saved"],
    "red_cards": ["red card", "red cards"],
    "saves": ["save", "saves"],
    "selected": ["selected", "ownership"],
    "threat": ["threat"],
    "total_points": ["total points", "points", "total"],
    "transfers_balance": ["transfers balance", "transfer balance"],
    "transfers_in": ["transfers in", "transfer in", "transfers_in"],
    "transfers_out": ["transfers out", "transfer out", "transfers_out"],
    "value": ["value", "price", "market value"],
    "yellow_cards": ["yellow card", "yellow cards", "yc"],
    "form": ["form", "current form"],
}
