# HX18 — ESP32 + 18 MG90S

Firmware pentru **Adafruit Feather ESP32 V2**, două PCA9685 și modelul CAD HX18. Deschide `HX18Controller/HX18Controller.ino` în Arduino IDE; implementarea este în `controller.cpp`, iar matematica portabilă în `robot_core.h`. Nu cere Wi-Fi sau librărie PCA externă.

**Boot-ul dezactivează toate ieșirile. ARM rămâne blocat până când cele18 servouri și cele2 oscilatoare sunt verificate fizic în config.h și operatorul trimite CAL_ACK.** Valorile implicite de direcție/calibrare sunt nevalidate. CAD-ul și software-ul nu pot determina spline-ul/horn-ul real sau toleranțele servourilor cumpărate.

## Conexiuni

| Feather ESP32 V2 | PCA9685 A și B |
|---|---|
| 3V | VCC logic pe ambele plăci |
| GND | GND pe ambele plăci și masa comună a distribuției servourilor |
| GPIO22 / SDA | SDA pe ambele plăci |
| GPIO20 / SCL | SCL pe ambele plăci |
| GPIO27 | OE pe ambele plăci |

A=`0x40`; B=`0x41`, jumper A0 închis pe B. Pull-up I²C la3,3V. Pinii22/20 sunt pentru **Feather ESP32 V2**, nu pentru un DevKit ESP32 generic.

Distribuția servourilor: firele **roșii direct la bus5V extern**, maro direct la busGND în stea; numai orange/PWM merge la ieșirile PCA. **V+ pe PCA rămâne neconectat**: curentul agregat al celor18 servouri nu trece prin traseele breakout-urilor. Urmează ghidul electric al proiectului pentru sursă, siguranțe, cabluri și condensatori. ESP32/USB/3V nu alimentează servourile.

**OE necesită pull-up extern la3,3V.** Două breakout-uri Adafruit au fiecare pull-down OE10kΩ; în paralel rezultă5kΩ. Folosește pull-up **1kΩ** (~2,75V la reset), sau îndepărtează R7 de pe ambele plăci și folosește pull-up10kΩ. Verifică OE HIGH cu Feather în reset. OE HIGH oprește semnalul, nu alimentarea. Susține robotul la dezactivare și folosește întrerupător fizic pe sursa servourilor.

## Maparea cablurilor

CAD L1..L6 are direcții radiale0°,60°,120°,180°,240°,300°. Ordinea fiecărui picior: YAW/coxa, HIP/femur, KNEE/tibia. Indicii seriali sunt0..17.

| Picior | Indici YAW/HIP/KNEE | Placă / canale |
|---|---|---|
| L1 | 0,1,2 | 0x40 / 0,1,2 |
| L2 | 3,4,5 | 0x40 / 3,4,5 |
| L3 | 6,7,8 | 0x40 / 6,7,8 |
| L4 | 9,10,11 | 0x41 / 0,1,2 |
| L5 | 12,13,14 | 0x41 / 3,4,5 |
| L6 | 15,16,17 | 0x41 / 6,7,8 |

Canalele9..15 ale fiecărei plăci sunt FULL_OFF. Verifică impulsurile cu osciloscop/logic-analyzer înainte de primul ansamblu încărcat. Nominal50Hz, PRE_SCALE121, oscilator25MHz. Măsoară fiecare placă: `oscillatorHz = frecvența PWM măsurată ×4096×122`. Introdu valorile și marchează `oscillatorVerified[0]`, `[1]` separat. Validarea cere valori finite20–30MHz. BENCH permite măsurarea cu valorile nominale, fără să deblocheze ARM.

## Poza și mersul

Coxa30mm, femur42mm, tibia80mm, offset lateral al contactului13,5mm. Neutral CAD: femur absolut−25°, tibia absolut−95°, deci **genunchi relativ−70°**. `Pose` este delta joint-urilor CAD, în grade: yaw pozitiv rotește în sens opus unghiului radial matematic; hip pozitiv crește unghiul femurului; knee pozitiv crește unghiul relativ tibiei.

Stand pentru mers: coordonata radială contact față de șold25mm, z față de șold−97,44554284mm. IK rezolvă unghiurile. Neutral CAD rămâne referința de montaj a horn-urilor.

WALK pregătește picioarele **18 secunde, unul odată**, ținând celelalte coordonate fixe. Apoi accelerează viteza corpului printr-un ceas comun în3s. Gait: corp+Y, ordine swing L1,L4,L2,L5,L3,L6, ciclu de 18 secunde, swing de 3 secunde/picior, pas±6mm, lift6mm. Cinci picioare sunt comandate în stance. Stance-ul liniar cere aceeași viteză relativă la corp, 0,8 mm/s, tuturor picioarelor plantate; swing-ul quintic-Hermite se leagă cu aceeași viteză la contact. Lift-ul are viteză și accelerație zero la contact. Aceste condiții evită comenzi incompatibile care ar trage picioarele plantate cu viteze diferite.

STOP **ține XY-ul picioarelor plantate** și coboară piciorul aflat în aer în2s. Nu mută toate picioarele plantate spre neutral. O nouă comandă WALK reface prepoziționarea din coordonatele ținute; este respinsă până când modelul tuturor contactelor este așezat.

Limite joint: yaw±25°, hip/knee±15°, plus braț orizontal proiectat șold→contact≤35mm, **inclusiv offsetul13,5mm**. Rate limiting:12°/s, accelerație30°/s²; dt măsurat, actualizări nominal50Hz. IK imposibil, impuls invalid și poză limitată în viteză care depășește anvelopa dezactivează ieșirile. Nu se taie arbitrar unghiurile ca să mascăm un punct imposibil.

Cinci contacte sunt presupunerea traiectoriei. Fără senzori de contact/IMU/encodere, software-ul nu confirmă contactele sau stabilitatea fizică. Gait-ul necesită teste progresive cu greutate mică, pe teren plat; nu este validat fizic.

## Calibrare

1. Susține corpul. Pentru primul impuls de centrare, **scoate horn-ul servo-ului**. Un servo hobby nu comunică poziția reală; primul impuls nu poate garanta o rampă lină dintr-o poziție necunoscută.
2. Încarcă firmware-ul implicit. Folosește consola cu heartbeat. `DISARM`, `BENCH_ACK`, `BENCH 0`: numai acel canal este activ, la1500µs nominal. `STEP -5`..`STEP 5` testează±50µs nominal,3°/s. `DISARM` înainte de cablare/montarea horn-ului. Repetă0..17.
3. Montează horn-urile astfel încât centrul să corespundă neutralului CAD. Determină individual direcția, zero-ul, raportulµs/grad și capetele fără frecare. În `config.h`: `centerUs`, `usPerDegree`, `offsetDegrees`, `sign`, `minimumUs`, `maximumUs`, `verified`. `sign=+1` înseamnă impuls mai mare pentru delta CAD pozitivă. Cele18 semne+1 livrate trebuie măsurate; nu sunt o validare a oglinzirii.
4. Capete implicite conservatoare1200–1800µs. Validarea permite numai1000–2000µs. Relația este `centerUs + sign × usPerDegree × (deltaCAD + offsetDegrees)`; offsetul corectează diferența dintre centrul real și horn-ul montat.
5. Marchează toate calibrările reale `verified=true`, ambele oscilatoare verificate, apoi `calibrationReviewed=true`. Reîncarcă. **Nu** modifica aceste confirmări doar ca să treci de interlock.
6. Pune mecanismul în neutral CAD, corpul susținut. `CAL_ACK`, `ARM`: rampă5s neutral→stand compact. După READY, verifică stand-ul și apoi `WALK`. Începe cu un picior și greutate mică; măsoară curentul, temperaturile și lipsa frecărilor înainte de întregul robot.

BENCH este numai unealta de centrare:1500µs+10µs/grad comandat,±50µs. Nu folosește curba robotului calibrat și nu testează automat capetele. Configurația calibrată se aplică în ARM/WALK.

## Compilare și operare

Arduino IDE: pachet **esp32 by Espressif Systems3.x**, placă **Adafruit Feather ESP32 V2**. Deschide `.ino`, Verify, apoi Upload. Firmware-ul folosește task watchdog ESP-IDF5.x din core3.x. Verify nu face Upload.

```sh
arduino-cli compile --fqbn esp32:esp32:adafruit_feather_esp32_v2 HX18Controller
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python serial_console.py /dev/cu.usbserial-PORTUL-TAU
```

Consola trimite PING la250ms și **nu armează automat**. Ctrl+C/EOF trimite DISARM. Comenzi: STATUS, PING, DISARM, CAL_ACK, ARM, WALK, STOP, BENCH_ACK, BENCH0..17, STEP−5..5 (cu spațiu după BENCH/STEP). Lipsa PING1,5s dezactivează ieșirile. După FAULT: DISARM, verificare, confirmare din nou; eroarea de inițializare I²C cere verificare și reset. Deschiderea Serial poate reseta placa; resetul începe dezactivat.

I²C100kHz, timeout10ms, verificarea ACK la fiecare scriere. Pauză de control>100ms: OE HIGH; task watchdog1s: panic/reset la loop complet blocat. Pull-up-ul fizic OE dezactivează la reset. Watchdog-ul nu înlocuiește întrerupătorul fizic.

ADC baterie **dezactivat**: `batteryDividerRatio=0`, prag0; activarea fără valori reale nu compilează. Pin34=A2/ADC1. Alege/măsoară divizorul, respectă limita ADC și stabilește pragul pentru sursa/bateria reală. ADC nu înlocuiește protecția hardware de subtensiune.

## Verificare

`./test.sh`: FK↔IK pe27 combinații joint;360.000 ținte pe60s;108.006 ținte startup; viteză comună a stance-ului; limitarea accelerației; calibrări/oscilatoare invalide; ARM/watchdog logic și rollover millis; simulare Wire/Serial inclusiv canal17, I²C failure, stall, heartbeat, comenzi lungi/control characters. E2E într-o copie **doar pentru test**, cu calibrările confirmate: rampă5s, WALK54s, STOP5s cu XY păstrat, restart27s, DISARM. Sursele livrate rămân necalibrate. Testul E2E verifică și pozele după limitarea vitezei: cel mult un picior modelat este cu peste 0,25 mm deasupra planului de sprijin, atât la prima pornire, cât și după restart. Aceasta este o verificare software; contactele fizice nu sunt măsurate.

ASan/UBSan active pe host. Compile real verificat: ArduinoCLI1.5.1, Espressif core3.3.12, FQBN esp32:esp32:adafruit_feather_esp32_v2;365.681bytes flash,25.140bytes RAM; fără Upload. Core:100% linii,100% funcții,92,77% ramuri. Acoperirea core este în `VALIDATION.json` și raportul executat în `build/coverage.txt`; nu reprezintă acoperirea driverelor ESP32 sau validare fizică. `gait-targets.csv` conține301 frame-uri×6 picioare pentru audit CAD; `startup-targets.csv`601×6. `tests/export_gait.cpp` le regenerează. `gait-targets-cycle12.csv` păstrează setul anterior folosit pentru audit CAD; `GAIT-TIMING-EQUIVALENCE.json` demonstrează că toate cele 1.806 rânduri au aceleași unghiuri, XYZ și etichete swing după trecerea la ciclul de 18 secunde. Geometria este identică, numai timpii diferă.

Compile real opțional în test.sh: `HX18_ARDUINO_CLI=/cale/arduino-cli HX18_ARDUINO_CONFIG=/cale/config.yaml ./test.sh`. Nu se face Upload. Testele host folosesc Clang17+; pe macOS, xcrun llvm-cov/llvm-profdata generează raportul.

## Surse primare

- [NXP PCA9685](https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf): OE, FULL_OFF, MODE1/2, prescaler, sleep/wake/restart, auto-increment.
- [Espressif Arduino ESP32 I²C](https://docs.espressif.com/projects/arduino-esp32/en/latest/api/i2c.html) și [Wire.h](https://github.com/espressif/arduino-esp32/blob/master/libraries/Wire/src/Wire.h): pini, buffer, timeout și ACK.
- [Espressif watchdog](https://docs.espressif.com/projects/esp-idf/en/stable/esp32/api-reference/system/wdts.html): init/reconfigure/status/reset.
- [Adafruit Feather ESP32 V2 pinouts](https://learn.adafruit.com/adafruit-esp32-feather-v2/pinouts): SDA22/SCL20, GPIO27, ADC1.
