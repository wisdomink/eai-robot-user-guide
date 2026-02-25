# Battery Indicator Lights

Note:
When the robot is powered by the battery, please monitor the battery level carefully. If the battery power is low or nearly depleted, the robot may lose power suddenly and collapse. When only one indicator light remains on, charge or replace the battery promptly to ensure stable operation and prevent potential injury or damage caused by the robot falling due to power loss.

## Battery Indicator Location

![](/images/docx/battery-indicator-1.png)

## Battery Indicator Description

### Battery Indicator Status (During Discharge)

| Battery Indicator Status (Discharging) | Battery Level Description | Status Description |
| --- | --- | --- |
| LEDs 1–4 steady on | 75%≤SOC＜100% | Fully charged |
| LEDs 1–3 steady on, remaining off | 50%≤SOC＜75% | Battery level sufficient, no action required |
| LEDs 1–2 steady on, remaining off | 25%≤SOC＜50% | Normal battery level, no action required |
| LED 1 steady on, remaining off | 15%≤SOC＜25% | Low battery, recharge soon |
| LED 1 flashing, remaining off | SOC＜15% | Critically low power, charge immediately |

### Battery Indicator Status (During Charging)

| Battery Indicator Status (Charging) | Battery Level Description | Status Description |
| --- | --- | --- |
| LED1 breathing, LEDs 2–4 off | SOC＜25% | Initial charging stage, low battery |
| LED1 steady on, LED2 breathing, LEDs 3–4 off | 25%≤SOC＜50% | Low battery, not recommended to disconnect power during use |
| LEDs 1–2 steady on, LED3 breathing, LED4 off | 50%≤SOC＜75% | Medium battery level, can be used normally, recommended to continue charging until full |
| LEDs 1–3 steady on, LED4 breathing | 75%≤SOC＜100% | Battery nearly full, can be used normally, recommended to continue charging until full |
| LEDs 1–4 steady on | SOC=100% | Fully charged, power can be disconnected |

### Battery Indicator Status (Other Conditions)

| No. | Color | LED1 | LED2 | LED3 | LED4 | Status Description |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Green | Displays according to SOC status | | | | Normal |
| 2 | - | Flashes once per second | Flashes once per second | Flashes once per second | Flashes once per second | Protection mode (overtemperature, overcurrent, or overvoltage) |
| 3 | Red | Flashes once per second | | | | Fault (requires return for repair) |
| 4 | - | All LEDs off | | | | Power-off (deep sleep) or very low SOC (< 39V) |
