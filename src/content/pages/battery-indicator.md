# Battery Indicator Lights

Note: When the robot is powered by the battery, please monitor the battery level carefully. If the battery power is low or nearly depleted, the robot may lose power suddenly and collapse. When only one indicator light remains on, charge or replace the battery promptly to ensure stable operation and prevent potential injury or damage caused by the robot falling due to power loss.
2.4.1 Battery Indicator Location
2.4.2 Battery Indicator Description
2.4.2.1 Battery Indicator Status (During Discharge) Battery Indicator Status Battery Level Status Description (Discharging) Description
LEDs 1–4 steady on 75%≤SOC＜100% Fully charged
LEDs 1–3 steady on, 50%≤SOC＜75% Battery level sufficient, no remaining off action required
LEDs 1–2 steady on, 25%≤SOC＜50% Normal battery level, no action remaining off required
LED 1 steady on, remaining 15%≤SOC＜25% Low battery, recharge soon off
LED 1 flashing, remaining SOC＜15% Critically low power, charge off immediately
2.4.2.2 Battery Indicator Status (During Charging)
Battery Indicator Status Battery Level Status Description (Charging) Description
LED1 breathing, LEDs 2–4 SOC＜25% Initial charging stage, low off battery
LED1 steady on, LED2 25%≤SOC＜50% Low battery, not recommended breathing, LEDs 3–4 off to disconnect power during use
LEDs 1–2 steady on, LED3 50%≤SOC＜75% Medium battery level, can be breathing, LED4 off used normally, recommended to continue charging until full
LEDs 1–3 steady on, LED4 75%≤SOC＜100% Battery nearly full, can be used breathing normally, recommended to continue charging until full
LEDs 1–4 steady on SOC=100% Fully charged, power can be disconnected
2.4.2.3 Battery Indicator Status (Other Conditions)
No. Col LED1 LED2 LED3 LED4 Status Description or
1 Gre Displays according to SOC status Normal en 2 Flashes Flashes Flashes Flashes Protection mode once once once once (overtemperature, per per per per overcurrent, or second second second second overvoltage)
3 Red Flashes Fault (requires return for once repair) per second
4 - All LEDs off Power-off (deep sleep) or very low SOC (< 39V)
