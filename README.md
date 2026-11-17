# renewable_production
Wind and solar production model, using windpowerlib and pvlib, validated against actuals.

The aim is to model an onshore wind farm, an offshore wind farm, and a solar farm with historical weather data and calculate annual yield. Then calculate the capture rate against baseload price.

2026 Data sources:
1. ENTSO-E Transparenct Plateform: Day-ahead prices and wind and solar energy productions (15-min)
2. Open-Meteo historical API: Weather data (hourly)
3. Danish Energy Agency Master Data Register of Wind Turbines: Wind farm data and production data (monthly)

