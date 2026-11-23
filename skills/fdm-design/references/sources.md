# Sources and confidence

Collected 2026-11-23. Keys are used in the other reference files.
Confidence: **P** primary (vendor profile, standard, datasheet, official wiki), **S** secondary
(blog, test by a third party, other skill, forum), **U** unverified (no first-hand source was
obtained; listed so nobody mistakes it for checked).

## Vendor profiles, documentation and standards

| Key | Source | Conf. | Used for |
|---|---|---|---|
| `bambu-common` | Bambu Studio `fdm_process_common.json`, https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/process/fdm_process_common.json | P | `enable_support` 0, `support_threshold_angle` 30, `support_type` tree(auto), line widths 0.42/0.45, 2 walls, 3 top/bottom layers, `xy_hole_compensation` 0 |
| `bambu-a1-020` | Bambu Studio `0.20mm Standard @BBL A1.json`, https://raw.githubusercontent.com/bambulab/BambuStudio/master/resources/profiles/BBL/process/0.20mm%20Standard%20%40BBL%20A1.json | P | `elefant_foot_compensation` 0.075 |
| `bambu-wiki-support` | https://wiki.bambulab.com/en/software/bambu-studio/support | P | threshold measured from horizontal |
| `bambu-wiki-bridge` | https://wiki.bambulab.com/en/software/bambu-studio/parameter/bridge | P | 100 % overhanging walls labelled "Overhang wall" without warning |
| `bambu-cli` | https://github.com/bambulab/BambuStudio/wiki/Command-Line-Usage | P | CLI flags (not exercised by this repository's tests) |
| `orca-cli` | https://www.orcaslicer.com/wiki/cli/cli_actions | P | CLI flags (not exercised) |
| `orca-bridging` | https://github.com/OrcaSlicer/OrcaSlicer_WIKI/blob/main/print_settings/quality/quality_settings_bridging.md | P | "Bridge counterbore hole" option |
| `bambu-petg-hf-tds` | https://store.bblcdn.com/3a230e260a3a47c2b0db0156e07eef91.pdf | P | PETG HF HDT 62/69 °C, Tg 66 °C |
| Bambu TDS V3.0 (via a third-party summary) | not linked first-hand | S | HDT for PLA/PETG Basic, ABS, ASA |
| `bambu-x1e-guide` | https://csm.bblcdn.com/hub/default/5b4f3ddfa7ff4719913a05e0215e5188.pdf | P | starting profile in the previous version of this skill |
| `prusa-modeling` | https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135 | P | line width 0.45, perimeter thicknesses, 45–60° overhangs, precision ≥ 0.2 mm, moving-part clearance ≥ 0.3 mm |
| `stratasys-fdm` | https://www.stratasys.com/siteassets/sdm/content---website-storage/design-guides/dg_sdm_fdm_0725a.pdf | P | bosses with gussets/ribs |
| `usbc-compliance` | USB Type-C Compliance Document rev 1.2, https://www.usb.org/sites/default/files/USB_Type-C_Compliance_Document_rev_1_2.pdf | P | plug overmould 12.35 × 6.5, plug length 6.65 ± 0.10 |
| USB-C 12.85 × 7.0 ECN | not obtained | U | relaxed overmould limit |
| HDMI 1.3/1.4 specification | quoted second-hand | S | Type A plug shell and receptacle; bend figure values garbled → U |
| `tia-568` | TIA/EIA-568-B.1 §10.2.1.1, https://www.csd.uoc.gr/~hy435/material/TIA-EIA-568-B.1.pdf | P | UTP bend radius 4 × / 8 × diameter |
| SATA 3.x specification | quoted | P | 1 m internal cable, 50 mating cycles; no bend radius in spec |
| `molex-ffc` | Molex FFC product specification PDF | P | flex-life test radii R10 / R4 (test condition, not a minimum) |
| `wiki-modular` | https://en.wikipedia.org/wiki/Modular_connector | S | RJ45 plug size |
| `wiki-keystone` | https://en.wikipedia.org/wiki/Keystone_module | S | keystone face and cutout (plus forum/vendor pages, medium confidence) |

## Tests, articles and guides

| Key | Source | Conf. | Used for |
|---|---|---|---|
| `hubs-fdm` | https://www.hubs.com/knowledge-base/how-design-parts-fdm-3d-printing/ | S | 45° overhang, < 5 mm bridges, weak pins < ⌀5 |
| `hubs-snap` | https://www.hubs.com/knowledge-base/how-design-snap-fit-joints-3d-printing/ | S | 0.5 mm snap-fit clearance |
| `rahix` | https://blog.rahix.de/design-for-3d-printing/ | S | teardrops, flat-topped holes, two-layer counterbore bridge, ±0.1 per face, back-side inserts unreliable |
| `hackaday-sacrificial` | https://hackaday.com/2017/10/17/sacrificial-bridge-avoids-3d-printed-supports/ | S | sacrificial bridge |
| `ual-cci` | https://wiki.cci.arts.ac.uk/books/digital-fabrication-lab/page/design-the-clearance-and-tolerance-readme | S | H2D hinge/slide/pin clearances |
| `cnck-tips` | https://www.cnckitchen.com/blog/tips-and-tricks-for-heat-set-inserts | S | insert hole and installation practice |
| `cnck-datasheets` | https://www.cnckitchen.com/blog/are-our-heat-set-insert-datasheets-wrong | S | printed holes ~0.25 mm undersize, M3 4.2 mm CAD bore |
| `cnck-threads` | https://www.cnckitchen.com/blog/helicoils-threaded-insets-and-embedded-nuts-in-3d-prints-strength-amp-strength-assessment | S | 1 N·m vs 3 N·m in PETG |
| `loftsmith` | https://loftsmith.com/guides/heat-set-insert-hole-size | S (second-hand) | insert bore table and the conflicting M4–M6 values |
| `sovol-bosses` | https://www.sovol3d.com/blogs/news/3d-printing-with-heat-set-inserts-design-strong-screw-bosses-that-last | S (second-hand) | boss root fillet R1.5–3, root failure |
| `innostation` | https://www.innostation3d.com/en/blogs/3d-college/ribs-gussets-fillets-and-bosses-shaping-a-single-3d-printed-part-so-it-breaks-where-you-want | S | ribs printed upright |
| `mandarin3d` | https://mandarin3d.com/blog/cantilever-snap-fit-design | S (second-hand) | snap-fit strain formula and design strains |
| `crimpdeq-pr` | https://github.com/crimpdeq/crimpdeq-case/pull/7 | S | USB-C wall recess practice, plug probe |
| `count-fidget-issue` | https://github.com/dudgeon/count-fidget/issues/4 | S | same USB-C failure |
| `gcode-bridge-issue` | https://github.com/KKawamura1/3d-printer/issues/99 | S | real G-code containing `; FEATURE: Bridge` |
| `prusa-cli-bug` | https://github.com/prusa3d/PrusaSlicer/issues/14705 | S | PrusaSlicer CLI support-detection bug report |

## Agent skills and repositories

Licences were checked with the GitHub API at research time.

| Key | Repository | Licence | How it is used here |
|---|---|---|---|
| `alexlenk` | https://github.com/alexlenk/3d-printing | MIT | Adapted ideas: deviations need approval; negative test for every check ("A check that cannot fail proves nothing"); printed USB-C, DC jack and finger-space numbers; snap-fit example; opening at the cable end |
| `print3d-designer` | https://github.com/gjaloyan/print3d-designer | MIT | Adapted ideas: slicer CLI pitfalls; normal-based overhang tiers; PETG overhang/bridge numbers; walls as line-width multiples |
| `b123d-print` | https://github.com/KD5RYN/b123d-print | MIT | Adapted ideas: numbered rules; fit table; 10 mm bridge default; fix order (orient → chamfer → split → teardrop → support); measure, don't eyeball |
| `openscad-skill` | https://github.com/pthompson8594/openscad-skill | MIT-0 | Idea: self-tests with planted defects |
| `text-to-cad` | https://github.com/earthtojake/text-to-cad | MIT | Idea: separate skill directories per concern, slicing in the loop |
| `cad-khana` | https://github.com/cyberchitta/cad-khana | Apache-2.0 | Idea only: report what was checked as well as what was found |
| `partsmith` | https://github.com/evnchn/partsmith | MIT | Idea only: printability checks as a test suite |
| flowful-ai/cad-skill | https://github.com/flowful-ai/cad-skill | PolyForm Noncommercial | Ideas only (build-volume check, mating check, review checklist); no text or code copied |
| Shpigford/nurb | https://github.com/Shpigford/nurb | FSL-1.1-MIT | Not used beyond the existence of a printability rule list; no text or code copied |
| slashmad/SlashCAD | https://github.com/slashmad/SlashCAD | GPL-3.0 | Idea only (search axis orientations for least overhang); no code copied |
| swh/openscad-skill, andreahaku/openscad_claude_skill, Ericonaldo/Claude-CAD-skill | GitHub | none | Not used |

No text or code in this repository is copied verbatim from any of the above; scripts are
independent implementations. Short quoted phrases are attributed where they appear.

## Open items (to measure before relying on them)

1. HDMI plug overmould dimensions: measure your cables.
2. Your actual SATA and USB-C cables: lengths, overmoulds, bend behaviour.
3. Literal G-code feature names for support and overhang walls in your slicer version.
4. The two conflicting M4–M6 insert bore tables: use the supplier drawing.
5. Fit clearances for your printer + material: print the coupon ladder.
6. Material shrinkage percentages: no vendor figures found.
7. Slant3D, Maker's Muse and Ruiz, *Engineering Design for 3D Printing*: not consulted first-hand.
