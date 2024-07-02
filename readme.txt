1. Set up virtual environemnt
2. Install pips requests beautifulsoup4
3. Sel up sql tables
    a. games tables
        results of games
        webscraping to get this data
    b. users tables
        holds their square location, like coordinates
    c. weekly results
        need to store the location of the numbers, along the top and along the side, maybe in some lsit or something?
4. poolUserSetup.py - Sets up the User table and all users with random names and random locations on the baord, using x and y coordaintes, then stores in an SQL table
5. poolBoardSetup.py - Sets up the weekly game boards for the 18 weeks of the seasons and stores in an SQL table
6. pool2023GameResults.py - getting the results of the 2023 season for the Giants, and then storing these in a table.
    Will eventually update to store 2024 game data and upload when there is a new week of data