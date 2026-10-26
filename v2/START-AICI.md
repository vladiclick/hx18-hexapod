# HX18 V2 — robot hexapod MG90S cu centru ESP32

Deschide **HX18-MG90S.f3d** în Fusion: 154 instanțe, 18 articulații revolute, 134 îmbinări rigide. Sketch-ul tău original este păstrat ascuns; Original-Sketch.f3d este copia nemodificată. STEP conține geometria, iar joint-urile se păstrează în F3D.

V2 include prinderi după desenele oficiale pentru **Feather ESP32 V2 #5400, două PCA9685 #815 și Pololu D42V110F5 #5671**; baterie centrală Gens ace 450mAh 2S XT30, regulator separat pentru logică și capac demontabil. Firmware-ul este compilat pentru placa aleasă și verificat prin simulare. Modelul este un prototip: potrivirea celor 18 MG90S cumpărate, montajul cablurilor și rezistența sub sarcină trebuie verificate fizic.

- Electronics/README-WIRING.md: lista exactă de electronice, schema și calibrarea.
- Electronics/wiring.svg: diagramă vectorială cu cele 18 semnale și alimentările.
- Firmware/README.md: instalare, comenzi și testare; ARM este blocat până la calibrare.
- BOM-mechanical.csv: șuruburi, piulițe și șaibe.
- STL/: 58 piese structurale, 16 forme distincte, plus un FitCoupon.
- VERIFICARE.md și rapoartele JSON: rezultate și limite.

## Începe cu testul de potrivire

1. Printează **STL/FitCoupon.stl**, fără scalare.
2. Verifică un MG90S real în deschiderea de **23,4 × 13,0 mm**. Nu forța carcasa. Verifică și poziția urechilor, distanța între găuri și ieșirea cablului.
3. Probează brațul dublu original pe zona rotundă: gaura centrală trebuie să permită accesul la șurubul original de spline. Fantele laterale acoperă raze de aproximativ **6,8–10,7 mm**.
4. Compară cu servoul real: poziția axei față de carcasă, înălțimea urechilor și distanța până la fața brațului. Aceste cote nu sunt complet documentate de producător și sunt ipoteze de proiectare.
5. Printează și montează **un singur picior** înainte să produci restul pieselor.

[Specificația TowerPro](https://towerpro.com.tw/product/mg90s-3/) indică 22,8 × 12,2 × 28,5 mm și 13,4 g; tabelul de pe aceeași pagină indică lățime 12,4 mm. Am folosit lățimea mai mare la calculul jocului. Servourile din CAD sunt anvelope aproximative, nu modele de fabricație ale producătorului. Piesele includ 0,3 mm joc pe fiecare latură a corpului; verificarea pe servoul tău rămâne necesară.


## Printare

STL-urile sunt în **mm**, deja așezate pe pat cu Z minim 0. Nu scala și nu printa ansamblul într-o singură bucată. Cea mai mare piesă este șasiul, 138 × 119,5mm; restul încape separat pe același pat.

| Fișier | Bucăți | Gabarit STL în mm |
|---|---:|---|
| Chassis.stl | 1 | 138.0 × 119.5 × 3.0 |
| LowerDeck.stl | 1 | 74.0 × 72.0 × 6.0 |
| PowerShelf.stl | 1 | 62.4 × 71.0 × 5.0 |
| ElectronicsDeck.stl | 1 | 86.0 × 92.0 × 9.0 |
| LowerSpacer.stl | 6 | 7.0 × 7.0 × 17.0 |
| UpperSpacer.stl | 6 | 7.0 × 7.0 × 15.0 |
| GuardLower.stl | 4 | 6.4 × 6.4 × 23.0 |
| GuardUpper.stl | 4 | 6.4 × 6.4 × 14.6 |
| GuardTall.stl | 2 | 6.4 × 6.4 × 40.0 |
| CoreBridge.stl | 1 | 79.1 × 53.2 × 6.4 |
| CoreCap.stl | 1 | 87.0 × 92.0 × 2.4 |
| CoxaPlate.stl | 6 | 59.5 × 27.0 × 3.0 |
| HipBracket.stl | 6 | 38.0 × 19.0 × 43.0 |
| FemurPlate.stl | 6 | 40.0 × 27.0 × 3.0 |
| KneeMount.stl | 6 | 37.0 × 27.0 × 21.0 |
| Tibia.stl | 6 | 96.0 × 27.0 × 3.0 |
| FitCoupon.stl | 1 | 69.5 × 27.0 × 3.0 |

Punct inițial FDM: duză0,4mm, strat0,2mm, 4–5 perimetre, 5 straturi sus/jos și 25–35% umplere. Folosește profilul verificat al imprimantei tale. Plăcile sunt pe pat; HipBracket are talpa pe pat și fereastra deschisă sus; KneeMount are cadrul pe pat și turnurile în sus. GuardTall are40mm înălțime: folosește brim dacă e necesar. Nu sunt proiectate filete sau spline printate. Verifică în slicer găurile și acoperișul înclinat al HipBracket; orificiile nominale M2=2,4mm, M3=3,4mm pot necesita curățare. Principii: [ghidul Prusa pentru FDM](https://help.prusa3d.com/article/modeling-with-3d-printing-in-mind_164135).

## Ordinea de montaj

1. Montează cele șase servouri de yaw în șasiu; carcasa intră în fereastră, urechile se așază pe placă.
2. Centrează electric fiecare servo, cu alimentare și comandă adecvate, înainte să instalezi brațele. Poziția de repaus din CAD este o referință mecanică; nu garantează un anumit unghi comandat în firmware.
3. Fixează placa coxa pe brațul original cu cele două șuruburi laterale. Șurubul central de spline rămâne accesibil prin gaura mare.
4. Montează HipBracket pe coxa folosind șuruburile cu cap înecat. Piulițele sunt pe partea inferioară a plăcii coxa. Notch-ul din talpă lasă loc piuliței de la brațul yaw.
5. Montează servoul de femur în suportul deschis; fixează brațul său pe FemurPlate.
6. Fixează KneeMount de FemurPlate prin cele două turnuri. Montează servoul genunchiului pe partea opusă servoului de șold, exact ca în model.
7. Montează tibia pe brațul genunchiului. Verifică accesul la șurubul de spline și mișcarea manuală, fără cabluri întinse.

8. Repetă pentru celelalte picioare, apoi montează centrul de mai jos. Nu alimenta ansamblul nesusținut înaintea calibrării.

## Montajul centrului

1. Montează bateria în LowerDeck cu o curea și protecție moale. Oprește ghidajele să atingă rigid pouch-ul; gabaritul nominal este43×23×13mm. Lasă XT30 și G-Tech accesibile. Încărcarea2S se face extern; Feather BAT nu acceptă2S.
2. Stack-ul de jos în sus: LowerDeck3mm, LowerSpacer17mm, Chassis3mm, PowerShelf3mm, UpperSpacer15mm, ElectronicsDeck3mm: **44mm**, șase axe la raza32mm. Folosește **M3×50 introdus de sus**; capul rămâne deasupra ElectronicsDeck, piulița/șaiba sub LowerDeck. Nu introduce două șuruburi opuse în aceeași gaură.
3. Montează Pololu #5671 pe PowerShelf: patru M2×10, introduse de jos prin ferestrele de acces din șasiu. Folosește lipire directă pentru fire; conectori înalți de regulator nu sunt incluși în anvelopă. Verifică izolația și răcirea.
4. Montează cele două PCA cu opt M2×14, capetele sub ElectronicsDeck. PCB-urile sunt laZ21mm; conectorii servo privesc spre exterior. A0 închis numai pe placa0x41. VCC este3,3V; **V+ rămâne neconectat**, conform distribuției externe a puterii.
5. Montează cele patru GuardLower23mm și două GuardTall40mm. Pune CoreBridge pe primele patru, laZ38mm, apoi patru GuardUpper14,6mm. Folosește șase M2×50 prin stack-ul complet al carcasei.
6. Montează Feather bare #5400 cu patru M2×12; PCB laZ44,4mm. Folosește fire lipite scurt, fără GPIO header-e înalte. Buck-ul logic #2831 stă în cradle-ul separat, fixat cu curea izolantă, fără piulițe metalice care ating placa.
7. Montează CoreCap după verificarea mufelor și cablurilor. Nu strânge până se deformează plasticul. Carcasa este deschisă lateral pentru răcire și service; fotografiile Core-electronics.png/Core-PCA-power.png arată etajele.

Distribuția de putere, condensatoarele externe, siguranța și firele flexibile nu au geometrii comerciale validate în CAD. Alege și măsoară aceste componente înainte de montaj; nu lăsa cabluri în zona articulațiilor. Rutează firele portocalii la PCA, roșii/maro la harness-ul de putere în stea, cu bucle și strain relief. Urmează ghidul de cablare pentru 1kΩ pull-up OE și separarea alimentărilor.

## Mișcare și sarcină

Geometria piciorului: coxa30mm, femur42mm, tibia80mm; latura labei este deplasată13,5mm. Repaus CAD: femur−25°, tibia−95° absolut, genunchi−70° relativ. Drive Joint0 înseamnă această referință, nu zero electric. Limitele CAD ±25° yaw și ±15° hip/knee sunt pentru verificare fără sarcină; **nu folosi tot acest domeniu pentru mers încărcat**.

Firmware-ul implicit folosește stand compact25mm față de șold, pas±6mm, ridicare6mm, ciclu18s și un singur picior ridicat în model. Picioarele plantate au viteză comună; swing-ul intră/iese lin. WALK începe cu prepoziționare individuală; STOP păstrează XY plantat și coboară piciorul ridicat. Rampa ARM inițială se testează cu robotul suspendat.

Masa plasticului dacă piesele ar fi solide: **223.9g PLA la1,24g/cm³**; slicerul calculează masa reală. Cele18servouri au241,2g conform [TowerPro](https://towerpro.com.tw/product/mg90s-3/); electronicele principale+bateria adaugă aproximativ68g, apoi șuruburile/firele. Cântărește ansamblul; proiectul de mers presupune maximum600g ca buget de prototip, nu ca sarcină certificată.

La600g și numai trei sprijine efective, un braț conservator35mm dă aproximativ0,70kgf·cm la șold, înainte de masa segmentelor, inerție și distribuția inegală. TowerPro publică1,8kgf·cm la4,8V **stall**, fără rating continuu. Nu echivala acest calcul cu validare de rezistență sau durată de viață. Mersul lent reduce accelerațiile; jocul mecanic real din angrenaje se verifică separat. Începe cu un picior, apoi ansamblu suspendat și sprijin progresiv; măsoară curentul și temperatura.

## Editare și reproducere

F3D are istoric editabil și joint-uri reale. Parametrii hx_* sunt cote de referință ale generatorului, fără legătură automată cu toate liniile. Pentru schimbarea dimensiunilor adaptează geometria și pozițiile articulațiilor consecvent și repetă auditul. Automatizarea și testele sunt în Automation; nu rerula orientarea STL peste fișiere deja orientate.
