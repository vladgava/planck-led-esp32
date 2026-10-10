# Measuring Planck's constant with an ESP32 and four LEDs

An LED only starts conducting above a certain voltage, and that voltage depends on its colour: a blue LED needs more than a red one. The voltage is tied to the energy of the photons the LED emits, and a photon's energy is *E = hc/λ*. So if you measure the voltage of LEDs of different colours and plot it against 1/λ, you get a straight line with slope *hc/e*. From that slope you can read off Planck's constant.

I did this with an ESP32 and the LEDs from a beginner starter kit. No lab equipment, no multimeter.

<p align="center">
  <img src="figures/setup.jpg" width="380" alt="The whole setup on a breadboard: ESP32, one LED, one 220 Ω resistor">
</p>

## Result

**h ≈ 7.8 × 10⁻³⁴ J·s**, with a fit uncertainty of ± 1.1 × 10⁻³⁴.

The accepted value is 6.63 × 10⁻³⁴ J·s, so my result is 18 % too high, which is about one standard error away.

![Voltage at 1 mA against 1/λ, with the linear fit](figures/planck_fit.png)

| LED    | wavelength I assumed | voltage at 1 mA | spread over 4 runs |
|--------|----------------------|-----------------|--------------------|
| Red    | 630 nm               | 1.810 V         | 4 mV               |
| Yellow | 590 nm               | 1.905 V         | 3 mV               |
| Green  | 525 nm               | 2.366 V         | 2 mV               |
| Blue   | 470 nm               | 2.549 V         | 3 mV               |

The four runs of each LED agree within a few millivolts, which is far smaller than how far the points sit from the line (50 to 100 mV). So the 18 % doesn't come from noise in the measurement. It comes from somewhere systematic, and the section on limits below is my best account of where.

## How it works

Everything is done by the ESP32 itself:

```
GPIO25 (DAC) ──┬── LED anode
               └── GPIO34   reads Va

LED cathode ──┬── 220 Ω ── GND
              └── GPIO35   reads Vb

voltage across the LED = Va − Vb
current                = Vb / 220 Ω
```

The DAC steps the voltage up in 256 increments. At each step the ESP32 waits 5 ms, then reads both pins (each reading is the average of 64 samples). From Va and Vb it gets the LED voltage and the current. As soon as the current crosses 1 mA, it interpolates between the last two steps to get the LED voltage at exactly 1 mA, and stops at 2 mA so the LED isn't pushed any further.

A few details that mattered:

- The resistor voltage is only about 0.2 V at 1 mA, where the ESP32 ADC is at its worst. GPIO35 uses the 0 dB attenuation setting, which gives much better resolution at low voltages. GPIO34 sees up to about 3 V, so it uses 11 dB.
- Voltages come from `analogReadMilliVolts`, which uses the chip's factory calibration instead of a raw count.
- I picked 1 mA because it's low enough that the LED isn't stressed and the series resistance of the LED barely matters.

The analysis is a straight-line fit of voltage against 1/λ in `analysis/fit_planck.py`. The slope times *e/c* is h.

## What limits the accuracy

**The wavelengths are not measured.** I used typical values for 5 mm LEDs of these colours (630, 590, 525 and 470 nm). The real LEDs can easily be 10 to 20 nm off. I ran a quick simulation with ± 10 nm on each wavelength and ± 10 mV on each voltage, and it gives a spread in h of about ± 0.75 × 10⁻³⁴, the same size as the scatter I see. This is my main suspect.

**The ADC isn't perfect.** If the voltage readings are off by 3 % in gain, h moves between 7.6 and 8.1 × 10⁻³⁴.

**Four points is not many.** With four points the 95 % interval on h is about ± 4.8 × 10⁻³⁴. The result is consistent with the accepted value, but it doesn't test it very tightly.

**The model is a simplification.** The voltage at a fixed current is not exactly the band gap. The fit has an intercept of −0.52 V that soaks up part of that. The green LED is the point that sits furthest from the line (97 mV above it, against +5 mV for red, −57 mV for yellow and −46 mV for blue).

**The resistor is 220 Ω ± 5 %.** That moves the voltage at 1 mA by a few millivolts, which is negligible here.

## Run it yourself

1. Build the circuit above with one LED at a time.
2. Flash `firmware/iv_led/iv_led.ino`, open the Serial Monitor at 115200 baud and send `r`, `y`, `g` or `b`.
3. Copy the `RESULT` lines into `data/vled_at_1mA.csv`.
4. Run `python analysis/fit_planck.py` (add `--lang ro` for Romanian labels on the plot).

You'll need an ESP32 dev board, a 220 Ω resistor, four 5 mm LEDs and a breadboard.

## What I'd do next

- Measure the wavelengths with a CD used as a diffraction grating.
- Check the ADC against a multimeter.
- Fit the whole I–V curve with the Shockley equation instead of reading one point.
- Add a violet and an infrared LED to stretch the line.

## Files

```
firmware/iv_led/iv_led.ino     sweep and measurement on the ESP32
analysis/fit_planck.py         fit, uncertainties, plot
data/vled_at_1mA.csv           raw voltages
figures/                       plots and a photo of the setup
```
