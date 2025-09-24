Let's start planning the market behavior.

At the end of this phase, we should have two additional simulation options to select in the GUI.

In both versions:
    - Instead of goods spawning on the grid, each agent's home starts with a random endowment of goods (we will need to decide upon a distribution rule)
    - The agents remove the goods from their home inventory (and place them in their personal/carry inveotry), and then continue with their behavior logic
    - Utility is determined for each agent by their total inventories (home + personal carry)

The first: Bilateral Exchange
    - Agents seek the nearest agent that they have not yet traded with (tiebreaks by agent id num in case of equidistance).
    - They then pathfind to adjacent squares.
    - When they are on adjacent squares, they engage in trade if there is a possibility of mutual gains from trade (we will have to decide upon the bargaining rule or exchange ratios). If they cannot mutually gain from trade, they move on in their search
    - After each trade, they repeat this process until everyone has attempted to trade with each other at least once.
    - Once an agent has traded with every other agent, return to their home and deposit their goods.
The second: Market Exchange
    - A "marketplace" centralized on the NxN grid (defaults to a 2x2 area, configurable)
    - Agents can buy from and sell to the marketplace, but not directly with each other.
    - Once an agent has retrieved their initial endowment from their home, they travel to the marketplace and begin a day of trading. The agent will remain at the marketplace and attempt to make additional net-utility trades with the marketplace each turn for at least 5 turns. After 5 turns, if the agent can no longer make net-benficial trades, the agent returns home.
    - Market prices are determined locally -- that is, supply and demand are determined only by agents currently in the marketplace and their current inventories plus whatever items have been sold to the marketplace and not yet purchased by other agents. Agents can only trade with the marketplace at market price ratios.
    - The marketplace is initially stocked with a small assortment of goods to ensure at least one initial trade can begin
    - 

