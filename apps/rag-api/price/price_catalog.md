# FF EAI Robotics Price Catalog

This file is optimized for price retrieval in the `price` vector store.

## Retrieval Notes

- `MSRP` means the public list price currently shown in the source file.
- If a price is written as `base price + software/add-on package`, answer with both parts explicitly.
- If the user asks "how much" without naming a model, ask which model or series they mean.
- Source of truth: `ff_eai_robotics_specs.md`.

## All Models

| Series | Model | MSRP | Price Structure | Positioning | Key Purchase Notes |
|---|---|---|---|---|---|
| Futurist | Futurist | $34,900 + $5,000 | device + add-on package | Entry level full-size humanoid robot | Includes 1 robot without dexterous hand and 1 pad controller; secondary development not supported |
| Futurist | Futurist Ultra | $119,990 + $20,000 | device + add-on package | Professional level full-size humanoid robot | Includes 28 DOF upgrade, 6-DOF dexterous hand, pad controller, Orin AGX, 5G, cameras, LiDAR, microphone, display, and secondary development support |
| Master | Master | $19,990 + $3,000 | device + software kits | Entry level small-size humanoid robot | Includes robot device and remote controller; II/LM platform and OTA not supported |
| Master | Master Edu | $27,990 + $10,000 | device + software kits | Education level small-size humanoid robot | Includes robot device, remote controller, OTA, II platform, and LM platform support |
| Master | Master Ultra | $49,990 + $15,000 | device + software kits | Professional level small-size humanoid robot | Includes 30 DOF upgrade, Orin NX, 3D LiDAR, more cameras, 4G/5G, VR, II/LM platform, and secondary development support |
| Aegis | Aegis | $2,490 | standalone device price | Entry level quadruped robot without controller | Controller and app connection are not included |
| Aegis | Aegis Pro | $4,490 | standalone device price | Entry level quadruped robot with controller | Includes controller, app connection, and 1 customized costume |
| Aegis | Aegis Edu | $8,990 + $1,000 | device + software/add-on package | Education level quadruped robot | Supports secondary development |
| Aegis | Aegis Ultra | $9,990 + $3,000 | device + software/add-on package | Industry level quadruped robot | Includes pad controller, app connection, expansion support, Nvidia Orin NX 16G, and IP54 |
| Aegis | Aegis Ultra+ | $17,990 + $5,000 | device + software/add-on package | Industry level quadruped robot | Adds LiDAR and wireless antenna on top of Aegis Ultra level configuration |
| Aegis | Aegis Ultra-W+ | $19,990 + $5,000 | device + software/add-on package | Industry level wheeled robot | Wheeled version with LiDAR and wireless antenna |

## Quick Answer Format

When answering a pricing question, prefer this format:

`<Model> MSRP is <price>.`

If the source price contains two parts, prefer:

`<Model> MSRP is <base price> + <software/add-on price>.`

## Comparison Hints

- Lowest listed price in the source file: `Aegis` at `$2,490`.
- Highest listed price in the source file: `Futurist Ultra` at `$119,990 + $20,000`.
- Full-size humanoid series: `Futurist`, `Futurist Ultra`.
- Small-size humanoid series: `Master`, `Master Edu`, `Master Ultra`.
- Quadruped / wheeled series: `Aegis`, `Aegis Pro`, `Aegis Edu`, `Aegis Ultra`, `Aegis Ultra+`, `Aegis Ultra-W+`.
