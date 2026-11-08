# Nova Cinema — alpha 0.1.0

Fork sperimentale non ufficiale di **NOVA Video Player 6.6.4**, con una home Android TV cinematografica: sfondo del contenuto selezionato, titolo, trama e copertine navigabili con il telecomando. Non è affiliato ad Apple, Cinaura o agli sviluppatori NOVA.

## Download per Fire TV / Downloader

**APK:** https://github.com/AntonioR-dev/nova-cinema/releases/latest/download/nova-cinema.apk

La prima versione è una **alpha firmata con chiave di sviluppo**, non una release stabile. Si installa come **Nova Cinema** (`dev.antonior.novacinema`) accanto a NOVA: non importa automaticamente libreria, impostazioni o password dell'altra app.

## Prima configurazione

1. Installa l'APK e concedi l'accesso ai contenuti richiesto dall'app.
2. Configura la condivisione SMB nelle sorgenti di rete, come in NOVA.
3. Configura la tua chiave API TMDb nelle impostazioni del fork per attivare ricerca metadati, copertine e sfondi. Nessuna chiave personale è pubblicata nel repository.
4. Indicizza i video e prova la selezione delle copertine con il telecomando.

Questa versione usa immagini di sfondo; **non riproduce trailer automatici**. SMB e player non sono stati ottimizzati o riscritti. È stata mantenuta la base NOVA 6.6.4; non è una promessa di miglioramenti prestazionali.

## Stato dei test

Compilazione Android, firma APK e test automatici vengono verificati prima della pubblicazione. Nessun dispositivo Fire Stick è collegato all'ambiente di sviluppo: aspetto reale, telecomando, decodifica hardware e streaming sulla rete dell'utente richiedono una prova sul dispositivo.

## Compilazione

Richiede Git, Python 3.11+, JDK 17 e Android SDK (platform `android-37.0`, build-tools `36.0.0`). Struttura: cartella `Video` con questo checkout; `MediaLib` e `FileCoreLibrary` come cartelle sorelle.

```bash
python build-support/prepare.py
python -m unittest discover -s tests -p 'test_*.py' -v
./gradlew --no-daemon --console=plain -Puniversal assembleNoamazonDebug -x :FileCoreLibrary:ndkBuild -x :MediaLib:ndkBuild
```

`prepare.py` scarica i repository MediaLib/FileCoreLibrary agli esatti commit della release, applica la patch TMDb di questo fork e verifica SHA-256 dell'APK ufficiale usato **solo come fonte delle librerie native**. Non copia risorse, bytecode, firme o credenziali dell'app ufficiale. La build non è una ricompilazione indipendente dei codec nativi. Le sorgenti native corrispondenti sono specificate nel manifest ufficiale incluso in `build-support/manifest-v6.6.4.xml`, reperibili nei repository `nova-video-player` indicati dal manifest. Licenze e attribuzioni originali restano valide.

Il workflow **Nova Cinema APK** ripete preparazione, test e compilazione e conserva l'APK come artifact. La chiave debug generata dal CI non è necessariamente la stessa della build scaricabile: gli artifact CI non sono aggiornamenti firmati della release pubblicata.

## Progetto originale

Questo repository contiene il frontend e l'interfaccia di NOVA. Progetto principale: https://github.com/nova-video-player/aos-AVP . NOVA deriva da Archos Video Player Community Edition. Vedi `LICENSE.txt` e gli avvisi originali per le condizioni di licenza.
