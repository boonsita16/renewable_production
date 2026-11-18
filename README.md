# renewable_production
Wind and solar production model, using windpowerlib and pvlib, validated against actuals.

The aim is to model an onshore wind farm, an offshore wind farm, and a solar farm with historical weather data and calculate annual yield. Then calculate the capture rate against baseload price.

2025 Data sources:
1. ENTSO-E Transparenct Plateform: Day-ahead prices and wind and solar energy productions (15-min)
2. Open-Meteo historical API: Weather data (hourly)
3. Danish Energy Agency Master Data Register of Wind Turbines: Wind farm data and production data (monthly)

Selected wind farms and solar farm:
OFFSHORE WIND FARM
Name: Viborg
Turbine model, count: SWT 3.6-120, 1
Lat, lon: 56.577906° N, 11.184753° E
2025 annual production (GWh): 1529.29

ONSHORE WIND FARM
Name: Norddjurs
Turbine model, count: V136-4.2 MW, 1
Lat, lon: 56.370991° N, 9.442570° E
2025 annual production (GWh): 25.77

SOLAR FARM
Name: Glejbjerg Solar Park
Capacity MW: 148.2
Module count: 238368
Inverter Counts: 572
Lat, lon: 55.5221, 8.8277
Expected annual production (GWh): 153
Tilt, azimuth, tracking assumption: 20, 180 (assume), fixed-tilt mounting system

