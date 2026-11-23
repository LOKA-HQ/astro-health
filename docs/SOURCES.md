# Sources and how the numbers were chosen

This file explains where every threshold, shift and constant used by the
personalised and location-aware vitals logic comes from, and which values
are engineering choices with no source. The sources were read and checked
on 18 November 2026.

> Prototype for a hackathon. Nothing here has been clinically validated and
> none of it is medical guidance. Every value marked *engineering choice*
> and every shift derived from a small study needs review by a flight
> surgeon before any real use.

Where the code lives: `backend/app/services/environments.py` (shifts,
absolute overrides, `REFERENCES`) and `backend/app/services/personalization.py`
(statistical constants and absolute limits). `GET /api/v1/environments`
returns the same evidence from the API.

## How shifts were chosen

1. A shift is applied only where published measurements show a consistent
   change **and** relaxing the limit does not risk masking a real problem.
2. Where the evidence is mixed or missing, the shift is 0. The way to adapt
   is then the crew member's own baseline (`baseline_environment`).
3. When the evidence gives a range, the value that makes the limit more
   sensitive (or less relaxed) is used.
4. A shift that develops gradually is applied gradually, and not at all when
   the time spent in the environment is unknown (`days_in_environment`).

Values this review removed because no source supports them: heart-rate and
sleep shifts in microgravity, blood-pressure, stress, SpO2 and temperature
shifts for launch, a heart-rate shift in cabin altitude, and the "wider
tolerance" (spread) factors for every environment.

## Environment shifts

| Environment | Indicator | Shift | Evidence |
|---|---|---|---|
| Atmosphere (aircraft) | SpO2 | -3 points | Arterial O2 saturation is 96% at sea level and 93% at 7,500 ft; the regulatory cabin limit is 8,000 ft [5] |
| Atmosphere | Heart rate | 0 | No consistent change documented in the source [5] |
| Launch / re-entry / landing | Resting heart rate | +30 bpm | Apollo Commanders peaked near 120 bpm (range 94-153) at touchdown; liftoff adds a 10-20 bpm spike [6]. +30 over the generic warning of 90 keeps a 120 bpm peak from being flagged |
| Launch / re-entry / landing | Heart-rate absolute ceiling | 160 bpm (instead of 150) | The highest value reported in Shuttle crews was 160 bpm on the first stand after landing [7] |
| ISS / Mars transit | Body temperature | +1.0 C, ramped over 75 days | Resting core temperature +1.01 C in 11 ISS astronauts, plateau around day 75 [1]. Not applied when `days_in_environment` is unknown, so early-flight fever is not hidden |
| ISS / Mars transit | Systolic blood pressure | -7 mmHg | About 10 mmHg lower in 8 astronauts [2]; 7 mmHg lower seated systolic, not significant, in 9 astronauts [3]. The smaller figure is used, on systolic only |
| ISS / Mars transit | Resting heart rate | 0 | Unchanged in both studies [2][3] |
| ISS / Mars transit | Sleep hours | 0 | ISS crews are scheduled 8.5 h but sleep about 6 h [4]. Moving the limit would hide the sleep deficiency the data describe |
| Mars transit | All | as ISS | Assumption: deep-space transit is treated as low Earth orbit; there are no human vitals data beyond it |
| Mars surface | All | 0 | The cardiovascular effects of 0.38 g are unknown and direct long-term human evidence does not exist [8][9] |

## Statistical constants (personal thresholds)

| Constant | Value | Source |
|---|---|---|
| Spread | 1.4826 x median absolute deviation | Equals 1 / 0.6745, the scaling of the modified Z-score [10] |
| Critical multiplier `K_CRITICAL` | 3.5 | Iglewicz and Hoaglin recommend flagging modified Z-scores above 3.5 as potential outliers [10] |
| Warning multiplier `K_WARNING` | 2.5 | Leys et al. (2013) suggest 2.5 as the cut-off for MAD-based outlier detection [11] |
| Spread floor per indicator | 0.3 C, 0.5 SpO2 points, 0.5 h sleep, 3 bpm, 3-5 mmHg, ... | *Engineering choice*: stops a very steady person getting a hair-trigger |
| Days held out of the baseline | 7 | *Engineering choice* so a developing problem is not learned as normal |
| Minimum history | 7 days | *Engineering choice*; below it the generic thresholds are used |
| Tighten-only indicators | sleep hours, sleep quality, stress, mood | Even when the baseline is outside the normal range, limits are never looser than the generic ones. Chronic short sleep is a deficiency to flag (ISS crews average about 6 h against 8.5 h scheduled [4]), not a personal normal. Heart rate, blood pressure, temperature and SpO2 may relax |

## Absolute safety limits

Beyond these a reading is always critical, whatever the personal baseline.

| Indicator | Limit | Basis |
|---|---|---|
| Resting heart rate, high | 150 bpm | AHA ACLS tachyarrhythmia algorithm describes the rate as typically 150/min or more [12] |
| Resting heart rate, low | 40 bpm | *Engineering choice*: below the generic critical of 50 so trained crew with a slow resting rate are not alarmed |
| SpO2, low | 90% | Healthy adults at the 8,000 ft cabin limit stay at or above 90% (PaO2 above 60 mmHg), so below it is hypoxaemia [5] |
| Systolic / diastolic, high | 180 / 120 mmHg | AHA hypertensive crisis: above 180 systolic and/or above 120 diastolic [13] |
| Systolic / diastolic, low | 80 / 50 mmHg | *Engineering choice*, no guideline cited |
| Body temperature, high | 40.0 C | Mayo Clinic: heat stroke is a core temperature of 40 C (104 F) or higher [14] |
| Body temperature, low | 35.0 C | Mayo Clinic: hypothermia is a body temperature below 35 C (95 F) [15] |

## Generic thresholds (`data/health_thresholds.json`)

These pre-date the personalised logic and are the fixed limits used by
default. What was and was not checked in this review:

| Indicator | Basis | Checked |
|---|---|---|
| Blood pressure | AHA categories: normal below 120/80, stage 2 hypertension from 140/90, crisis above 180/120 [13]. The warning limit of 140/90 matches the start of stage 2; the critical limit of 160 systolic is a project choice | Yes |
| Sleep hours | CDC: adults need at least 7 hours [16]. The warning at 6 h and critical at 5 h are project choices | Yes (7 h) |
| Resting heart rate | Normal range 60-100 bpm is the commonly used clinical convention; the warning at 90, critical at 100 and low at 50 are project choices | Not re-verified |
| SpO2 | 96% at sea level in healthy adults [5]; the 95% normal bound and the warning/critical limits are conventions | Partly |
| Body temperature | Hypothermia and heat-stroke limits as above [14][15]; the fever threshold of 38.0 C is the usual convention | Partly |
| Sleep quality, stress, mood, steps | App-defined scores and proxies, no external standard | n/a |
| Lab panels | Reference ranges ship with the NASA OSDR data (`ref_min` / `ref_max`) | From the data |

The `note` fields in that file that previously cited NASA-STD-3001 and a
NASA sleep recommendation were replaced with the statements above, because
those attributions could not be verified.

## Data sources

| Data | Source |
|---|---|
| Clinical and immune labs, omics | NASA OSDR, Inspiration4 studies (OSD-569, 571, 575, 656) |
| Space-weather events | NASA DONKI API |
| Proton flux (GOES-18) | NOAA SWPC |
| Reference dose rates (ISS, Mars transit, Mars surface) | MSL RAD measurements, Zeitlin et al. 2013 and Hassler et al. 2014 (cited by the original data preparation; not re-checked in this review) |
| Vitals time series | Synthetic, generated by the project |

## Known gaps

- Every shift comes from studies of 8 to 11 astronauts or from a handful of
  Apollo Commanders. Individual variation is large.
- Launch data cover lunar ascent and descent and Shuttle landing. No
  Earth-launch heart-rate series was found, so Earth ascent is assumed to be
  similar.
- Nothing was found on vitals at 0.38 g, so the Mars-surface profile only
  documents the gap.
- Core temperature in [1] was estimated with a forehead heat-flux sensor, not
  measured at the core directly.
- Resting versus ambulatory measurements differ between studies, which is
  one reason the blood-pressure evidence is mixed.

## References

1. Stahn AC, Werner A, et al. Increased core body temperature in astronauts during long-duration space missions. *Scientific Reports* 7:16180 (2017). https://pmc.ncbi.nlm.nih.gov/articles/PMC5701078
2. Norsk P, Asmar A, Damgaard M, Christensen NJ. Fluid shifts, vasodilatation and ambulatory blood pressure reduction during long duration spaceflight. *J Physiol* (2015). Summary: https://www.sciencedaily.com/releases/2015/01/150114101638.htm
3. Hughson RL, Peterson SD, Yee NJ, Greaves DK. Cardiac output by pulse contour analysis does not match the increase measured by rebreathing during human spaceflight. *J Appl Physiol* 123(5):1145-1149 (2017). https://pmc.ncbi.nlm.nih.gov/articles/PMC5792103
4. Barger LK, et al. Prevalence of sleep deficiency and use of hypnotic drugs in astronauts before, during, and after spaceflight. *Lancet Neurology* (2014). Summary: https://www.news-medical.net/news/20140810/Space-missions-affect-sleep-patterns-in-astronauts.aspx
5. National Research Council. *The Airliner Cabin Environment and the Health of Passengers and Crew* (2002), Table 5-3 and the discussion of FAR 25.841. https://www.nationalacademies.org/read/10238/chapter/7
6. Petersen D, Charvat J, Somers J, Lee SMC, Pattarini J, Stenger MB, Van Baalen M. Apollo Commander cardiovascular data during lunar ascent and descent. NASA LSAH / JSC, NTRS 20200001709. https://ntrs.nasa.gov/api/citations/20200001709/downloads/20200001709.pdf
7. Charles JB, Fritsch-Yelle JM, Whitson PA, et al. Cardiovascular Deconditioning. Extended Duration Orbiter Medical Project, NASA JSC (1996), NTRS 20040201532. https://ntrs.nasa.gov/api/citations/20040201532/downloads/20040201532.pdf
8. Clement G. International roadmap for artificial gravity research. *npj Microgravity* 3:29 (2017). https://www.nature.com/articles/s41526-017-0034-8
9. Jones HW. The Partial Gravity of the Moon and Mars Appears Insufficient to Maintain Human Health. ICES 2021, NTRS 20210019591. https://ntrs.nasa.gov/citations/20210019591
10. NIST/SEMATECH e-Handbook of Statistical Methods, section 1.3.5.17, Detection of outliers (modified Z-score, Iglewicz and Hoaglin). https://itl.nist.gov/div898/handbook/eda/section3/eda35h.htm
11. Leys C, Ley C, Klein O, Bernard P, Licata L. Detecting outliers: do not use standard deviation around the mean, use absolute deviation around the median. *J Exp Soc Psychol* 49(4):764-766 (2013). The 2.5 threshold is attributed to it in https://easystats.github.io/performance/articles/check_outliers
12. American Heart Association. ACLS tachyarrhythmia algorithm (2025). https://cpr.heart.org/-/media/CPR-Files/CPR-Guidelines-Files/2025-Accessible/Algorithm-ACLS-Tachyarrhythmia-LngDscrp-250726-Ed.pdf
13. American Heart Association. Understanding blood pressure readings. https://heart.org/bplevels
14. Mayo Clinic. Heat stroke. https://www.mayoclinic.org/diseases-conditions/heat-stroke/symptoms-causes/syc-20353581
15. Mayo Clinic. Hypothermia: first aid. https://www.mayoclinic.org/first-aid/first-aid-hypothermia/basics/art-20056624
16. CDC. About sleep and your heart health. https://cdc.gov/heart-disease/about/sleep-and-heart-health.html
